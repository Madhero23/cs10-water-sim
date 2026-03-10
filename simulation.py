"""
simulation.py – SimPy Discrete-Event Simulation Engine
Runs a 24-hour household water-usage simulation at 1-minute resolution.
"""

import simpy
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

from fixtures import Fixture, get_fixture
from users import (
    generate_all_events, DEFAULT_USERS, UserProfile,
    GARDEN_DEFAULT_TIME, hm,
)
from pricing import compute_cost_for_gallons, gallons_to_m3
from leak_detector import check_for_leaks, LeakAlert


MINUTES_PER_DAY = 1440


@dataclass
class SimState:
    """Mutable simulation state tracked minute-by-minute."""
    active_fixtures: dict = field(default_factory=dict)   # key → remaining_min
    flow_gpm: float = 0.0
    cumulative_gallons: float = 0.0
    cumulative_cost: float = 0.0
    minute_log: list = field(default_factory=list)         # list of per-minute dicts
    fixture_gallons: dict = field(default_factory=lambda: {
        "shower": 0.0, "faucet": 0.0, "toilet": 0.0,
        "washing_machine": 0.0, "dishwasher": 0.0, "garden": 0.0, "leak": 0.0,
    })
    alerts: list = field(default_factory=list)
    events_log: list = field(default_factory=list)


def _build_active_map(events: list[dict]) -> dict[int, list[dict]]:
    """Index events by their start minute."""
    by_minute: dict[int, list[dict]] = {}
    for ev in events:
        m = max(0, min(ev["minute"], MINUTES_PER_DAY - 1))
        by_minute.setdefault(m, []).append(ev)
    return by_minute


def run_single_day(
    seed: int = 42,
    users: list[UserProfile] | None = None,
    fixture_overrides: dict | None = None,
    garden_time: int | None = None,
    leak_gpm: float = 0.0,
    callback=None,
) -> SimState:
    """
    Run one 24-hour simulation and return the final SimState.

    Parameters
    ----------
    seed : int
        PRNG seed for reproducibility.
    users : list[UserProfile], optional
        Override default household users.
    fixture_overrides : dict, optional
        Fixture key → Fixture to override defaults (for what-if).
    garden_time : int, optional
        Override garden watering time (minutes since midnight).
    leak_gpm : float
        Continuous leak rate in GPM (0 = no leak).
    callback : callable, optional
        Called each minute with (minute, state) for live UI updates.
    """
    rng = np.random.default_rng(seed)
    state = SimState()

    # Generate stochastic events for the day
    events = generate_all_events(rng, users, fixture_overrides, garden_time)
    event_map = _build_active_map(events)

    # Track active continuous fixtures: key → {end_minute, flow_gpm, fixture_key}
    active: dict[str, dict] = {}
    fixture_counter = 0  # unique ID for concurrent same-fixture uses

    for minute in range(MINUTES_PER_DAY):
        # ── Activate new events this minute ──────────────────────────
        if minute in event_map:
            for ev in event_map[minute]:
                fkey = ev["fixture_key"]
                fixture: Fixture = ev["fixture"]
                dur = ev["duration_min"]

                if fixture.is_instantaneous:
                    # Toilet flush — immediate water use
                    gals = fixture.water_per_use(0)
                    state.cumulative_gallons += gals
                    state.fixture_gallons[fkey] += gals
                    state.events_log.append({
                        "minute": minute,
                        "type": "flush",
                        "fixture": fkey,
                        "gallons": round(gals, 3),
                        "user": ev["user"],
                    })
                else:
                    # Continuous fixture — add to active set
                    uid = f"{fkey}_{fixture_counter}"
                    fixture_counter += 1
                    end_min = minute + int(round(dur))
                    active[uid] = {
                        "end_minute": min(end_min, MINUTES_PER_DAY),
                        "flow_gpm": fixture.flow_gpm,
                        "fixture_key": fkey,
                    }
                    state.events_log.append({
                        "minute": minute,
                        "type": "on",
                        "fixture": fkey,
                        "duration": round(dur, 1),
                        "user": ev["user"],
                    })

        # ── Compute flow this minute ─────────────────────────────────
        flow = leak_gpm  # continuous leak always flows
        if leak_gpm > 0:
            state.fixture_gallons["leak"] += leak_gpm

        expired = []
        for uid, info in active.items():
            if minute < info["end_minute"]:
                flow += info["flow_gpm"]
                state.fixture_gallons[info["fixture_key"]] += info["flow_gpm"]
            else:
                expired.append(uid)

        for uid in expired:
            del active[uid]

        state.flow_gpm = round(flow, 3)
        state.cumulative_gallons += flow  # 1 minute of flow at GPM = GPM gallons
        state.cumulative_cost = compute_cost_for_gallons(
            state.cumulative_gallons * 30  # project daily to monthly for pricing
        )

        # Record minute snapshot
        state.minute_log.append({
            "minute": minute,
            "hour": minute / 60,
            "time_str": f"{minute // 60:02d}:{minute % 60:02d}",
            "flow_gpm": state.flow_gpm,
            "cumulative_gallons": round(state.cumulative_gallons, 3),
            "cumulative_m3": round(gallons_to_m3(state.cumulative_gallons), 4),
            "projected_monthly_cost": round(state.cumulative_cost, 2),
        })

        if callback:
            callback(minute, state)

    # ── Leak detection ───────────────────────────────────────────────
    flow_series = [r["flow_gpm"] for r in state.minute_log]
    state.alerts = check_for_leaks(flow_series)

    return state


def run_replications(
    n: int = 30,
    base_seed: int = 1000,
    **sim_kwargs,
) -> list[SimState]:
    """Run n independent replications with different seeds."""
    results = []
    for i in range(n):
        s = run_single_day(seed=base_seed + i, **sim_kwargs)
        results.append(s)
    return results


def states_to_dataframe(states: list[SimState]) -> pd.DataFrame:
    """Convert replication results to a summary DataFrame."""
    rows = []
    for i, s in enumerate(states):
        total_gal = s.cumulative_gallons
        rows.append({
            "replication": i + 1,
            "total_gallons": round(total_gal, 2),
            "total_m3": round(gallons_to_m3(total_gal), 4),
            "projected_monthly_cost": round(s.cumulative_cost, 2),
            **{f"{k}_gallons": round(v, 2) for k, v in s.fixture_gallons.items()},
            "n_alerts": len(s.alerts),
        })
    return pd.DataFrame(rows)
