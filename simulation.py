"""
simulation.py – SimPy Discrete-Event Simulation Engine (Liters / LPM)
Runs variable-duration household water-usage simulation.
"""

import simpy
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

from fixtures import (
    FIXTURE_LIBRARY, FIXTURE_KEYS, BACKGROUND_DRIP_LPM,
    get_fixture, get_modified_fixture,
)
from pricing import compute_cost
from users import generate_all_events, DEFAULT_USERS


@dataclass
class SimState:
    """Holds the full state and results of a simulation run."""
    total_minutes: int = 1440
    warmup_minutes: int = 60

    # Per-minute log (list of dicts)
    minute_log: list = field(default_factory=list)

    # Per-fixture totals
    fixture_liters: dict = field(default_factory=lambda: {k: 0.0 for k in FIXTURE_KEYS})
    fixture_uses: dict = field(default_factory=lambda: {k: 0 for k in FIXTURE_KEYS})
    fixture_active_minutes: dict = field(default_factory=lambda: {k: 0.0 for k in FIXTURE_KEYS})

    # Aggregates (after warmup)
    cumulative_liters: float = 0.0
    cumulative_cost: float = 0.0
    flow_lpm: float = 0.0
    peak_flow_lpm: float = 0.0
    drip_liters: float = 0.0

    # Hourly aggregates
    hourly_liters: dict = field(default_factory=lambda: {h: 0.0 for h in range(24)})
    hourly_fixture_liters: dict = field(
        default_factory=lambda: {h: {k: 0.0 for k in FIXTURE_KEYS} for h in range(24)}
    )

    # Event log
    events: list = field(default_factory=list)
    alerts: list = field(default_factory=list)

    # Leak injection
    leak_active: bool = False
    leak_liters: float = 0.0

    # Pricing
    pricing_scheme: str = "flat"


def run_single_day(
    seed: int = 42,
    duration_minutes: int = 1440,
    warmup_minutes: int = 60,
    fixture_overrides: dict | None = None,
    garden_time: int | None = None,
    leak_gpm: float = 0.0,
    leak_onset: int | None = None,
    pricing_scheme: str = "flat",
    num_days: int = 1,
) -> SimState:
    """Run a simulation for the specified duration."""

    total_minutes = num_days * 1440 if num_days > 1 else duration_minutes
    rng = np.random.default_rng(seed)

    state = SimState(
        total_minutes=total_minutes,
        warmup_minutes=warmup_minutes,
        pricing_scheme=pricing_scheme,
    )

    # Reset per-fixture tracking based on actual total
    for k in FIXTURE_KEYS:
        state.fixture_liters[k] = 0.0
        state.fixture_uses[k] = 0
        state.fixture_active_minutes[k] = 0.0

    # Reset hourly based on total hours
    total_hours = total_minutes // 60
    state.hourly_liters = {h: 0.0 for h in range(total_hours)}
    state.hourly_fixture_liters = {h: {k: 0.0 for k in FIXTURE_KEYS} for h in range(total_hours)}

    # Build fixture overrides dict
    fix_dict = None
    if fixture_overrides:
        fix_dict = {}
        for k, overrides in fixture_overrides.items():
            fix_dict[k] = get_modified_fixture(k, **overrides)

    # Generate all events
    events = generate_all_events(
        rng, users=DEFAULT_USERS,
        fixture_overrides=fix_dict, garden_time=garden_time,
        num_days=num_days,
    )

    # Build active-fixture map per minute
    active_map = {}
    for ev in events:
        start = ev["minute"]
        dur = int(max(1, round(ev["duration_min"])))
        for t in range(start, min(start + dur, total_minutes)):
            if t not in active_map:
                active_map[t] = []
            active_map[t].append(ev)

    # Leak injection
    leak_lpm = leak_gpm if leak_gpm > 0 else 0.0
    leak_start = leak_onset
    if leak_lpm > 0 and leak_start is None:
        leak_start = int(rng.choice([
            rng.integers(0, 5 * 60),        # 00:00-05:00
            rng.integers(10 * 60, 14 * 60), # 10:00-14:00
        ]))

    # ── Simulate minute by minute ───────────────────────────────────────────
    cumulative_liters = 0.0
    cumulative_cost = 0.0
    event_set = set()

    for minute in range(total_minutes):
        hour = minute // 60
        day_minute = minute % 1440
        day_hour = day_minute // 60

        # Compute flow at this minute
        flow_this_minute = 0.0
        active_fixtures = {}

        # Active user events
        if minute in active_map:
            for ev in active_map[minute]:
                fk = ev["fixture_key"]
                fl = ev["flow_lpm"]
                flow_this_minute += fl
                active_fixtures[fk] = active_fixtures.get(fk, 0.0) + fl

                # Track event
                ev_id = id(ev)
                if ev_id not in event_set:
                    event_set.add(ev_id)
                    if minute >= warmup_minutes:
                        state.fixture_uses[fk] += 1
                        state.events.append({
                            "minute": minute, "fixture": fk,
                            "flow_lpm": fl, "duration": ev["duration_min"],
                            "user": ev["user"],
                            "liters": fl * ev["duration_min"],
                        })

                if minute >= warmup_minutes:
                    state.fixture_liters[fk] += fl
                    state.fixture_active_minutes[fk] += 1.0

        # Background drip
        drip = BACKGROUND_DRIP_LPM
        flow_this_minute += drip

        # Leak
        leak_flow = 0.0
        if leak_lpm > 0 and leak_start is not None and minute >= leak_start:
            leak_flow = leak_lpm
            flow_this_minute += leak_flow
            state.leak_active = True

        if minute >= warmup_minutes:
            liters_this_minute = flow_this_minute  # 1 min × LPM = L
            cumulative_liters += liters_this_minute
            state.drip_liters += drip
            state.leak_liters += leak_flow

            # Hourly tracking
            if hour in state.hourly_liters:
                state.hourly_liters[hour] += liters_this_minute
                for fk, fl in active_fixtures.items():
                    if fk in state.hourly_fixture_liters.get(hour, {}):
                        state.hourly_fixture_liters[hour][fk] += fl

            # Peak flow
            if flow_this_minute > state.peak_flow_lpm:
                state.peak_flow_lpm = flow_this_minute

            # Cost (flat rate per minute simplification)
            cumulative_cost = compute_cost(cumulative_liters, pricing_scheme)

        # Log
        time_h = minute / 60.0
        day_num = minute // 1440
        state.minute_log.append({
            "minute": minute,
            "hour": round(time_h, 4),
            "day": day_num,
            "day_hour": day_hour,
            "flow_lpm": round(flow_this_minute, 4),
            "cumulative_liters": round(cumulative_liters, 2),
            "cumulative_cost": round(cumulative_cost, 4),
        })

    state.cumulative_liters = round(cumulative_liters, 2)
    state.cumulative_cost = round(cumulative_cost, 4)
    state.flow_lpm = 0.0

    return state


def run_replications(
    n: int = 30,
    base_seed: int = 1000,
    duration_minutes: int = 1440,
    warmup_minutes: int = 60,
    fixture_overrides: dict | None = None,
    garden_time: int | None = None,
    leak_gpm: float = 0.0,
    pricing_scheme: str = "flat",
    num_days: int = 1,
) -> list[SimState]:
    """Run n independent replications."""
    states = []
    for i in range(n):
        s = run_single_day(
            seed=base_seed + i,
            duration_minutes=duration_minutes,
            warmup_minutes=warmup_minutes,
            fixture_overrides=fixture_overrides,
            garden_time=garden_time,
            leak_gpm=leak_gpm,
            pricing_scheme=pricing_scheme,
            num_days=num_days,
        )
        states.append(s)
    return states


def states_to_dataframe(states: list[SimState]) -> pd.DataFrame:
    """Convert replication results to summary DataFrame."""
    rows = []
    for i, s in enumerate(states):
        row = {
            "replication": i + 1,
            "total_liters": s.cumulative_liters,
            "total_cost": s.cumulative_cost,
            "peak_flow_lpm": s.peak_flow_lpm,
            "drip_liters": s.drip_liters,
            "leak_liters": s.leak_liters,
            "n_events": len(s.events),
        }
        for k in FIXTURE_KEYS:
            row[f"{k}_liters"] = round(s.fixture_liters.get(k, 0), 2)
            row[f"{k}_uses"] = s.fixture_uses.get(k, 0)
            row[f"{k}_active_min"] = round(s.fixture_active_minutes.get(k, 0), 2)
        rows.append(row)
    return pd.DataFrame(rows)
