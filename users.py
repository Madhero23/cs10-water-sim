"""
users.py – Household User Behavior Module (LPM / Liters)
Generates stochastic daily schedules for 4 household members.
Uses Poisson for toilet flushes, exponential inter-event times.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Tuple, List

from fixtures import Fixture, get_fixture


# ── Time-window helpers ─────────────────────────────────────────────────────

def hm(h: int, m: int = 0) -> int:
    return h * 60 + m

MORNING_WINDOW = (hm(5, 30), hm(9, 0))
MIDDAY_WINDOW  = (hm(11, 0), hm(14, 0))
EVENING_WINDOW = (hm(17, 0), hm(21, 0))


@dataclass
class UserProfile:
    name: str
    showers_per_day: int = 1
    faucet_uses: Tuple[int, int] = (5, 8)
    toilet_flush_lambda: float = 6.0      # Poisson λ
    preferred_shower_window: Tuple[int, int] = MORNING_WINDOW
    preferred_faucet_windows: List[Tuple[int, int]] = field(
        default_factory=lambda: [MORNING_WINDOW, MIDDAY_WINDOW, EVENING_WINDOW]
    )
    preferred_toilet_windows: List[Tuple[int, int]] = field(
        default_factory=lambda: [MORNING_WINDOW, MIDDAY_WINDOW, EVENING_WINDOW]
    )


DEFAULT_USERS = [
    UserProfile(name="U1 (Parent A)", preferred_shower_window=MORNING_WINDOW),
    UserProfile(name="U2 (Parent B)", preferred_shower_window=MORNING_WINDOW),
    UserProfile(name="U3 (Child A)",  preferred_shower_window=EVENING_WINDOW),
    UserProfile(name="U4 (Child B)",  preferred_shower_window=EVENING_WINDOW),
]

LAUNDRY_DEFAULT_TIME = hm(9, 0)
DISHWASHER_DEFAULT_TIME = hm(20, 0)
GARDEN_DEFAULT_TIME = hm(18, 0)


def _random_time_in_window(rng: np.random.Generator, window: Tuple[int, int]) -> int:
    return int(rng.integers(window[0], window[1]))


def generate_user_events(
    user: UserProfile,
    rng: np.random.Generator,
    fixture_overrides: dict | None = None,
    day_offset: int = 0,
) -> list[dict]:
    """Generate fixture events for one user for one day."""
    events = []
    fixtures = fixture_overrides or {}
    offset = day_offset * 1440

    def _get(key):
        return fixtures.get(key, get_fixture(key))

    # Shower (1 per day)
    for _ in range(user.showers_per_day):
        f = _get("shower")
        minute = _random_time_in_window(rng, user.preferred_shower_window) + offset
        flow = f.sample_flow(rng)
        dur = f.sample_duration(rng)
        events.append({
            "minute": minute, "fixture_key": "shower", "fixture": f,
            "flow_lpm": flow, "duration_min": dur, "user": user.name,
        })

    # Faucet uses (5-8 per day)
    n_faucet = int(rng.integers(user.faucet_uses[0], user.faucet_uses[1] + 1))
    for _ in range(n_faucet):
        f = _get("faucet")
        window = user.preferred_faucet_windows[
            int(rng.integers(0, len(user.preferred_faucet_windows)))
        ]
        minute = _random_time_in_window(rng, window) + offset
        flow = f.sample_flow(rng)
        dur = f.sample_duration(rng)
        events.append({
            "minute": minute, "fixture_key": "faucet", "fixture": f,
            "flow_lpm": flow, "duration_min": dur, "user": user.name,
        })

    # Toilet flushes (Poisson distributed)
    n_toilet = int(rng.poisson(user.toilet_flush_lambda))
    n_toilet = max(1, min(n_toilet, 15))
    for _ in range(n_toilet):
        f = _get("toilet")
        window = user.preferred_toilet_windows[
            int(rng.integers(0, len(user.preferred_toilet_windows)))
        ]
        minute = _random_time_in_window(rng, window) + offset
        flow = f.sample_flow(rng)
        events.append({
            "minute": minute, "fixture_key": "toilet", "fixture": f,
            "flow_lpm": flow, "duration_min": 1.0, "user": user.name,
        })

    return events


def generate_shared_events(
    rng: np.random.Generator,
    fixture_overrides: dict | None = None,
    garden_time: int | None = None,
    day_offset: int = 0,
) -> list[dict]:
    """Generate shared appliance events for one day."""
    events = []
    fixtures = fixture_overrides or {}
    offset = day_offset * 1440

    def _get(key):
        return fixtures.get(key, get_fixture(key))

    # Washing machine (0 or 1 per day, 70% chance)
    if rng.random() < 0.7:
        f = _get("washing_machine")
        start = LAUNDRY_DEFAULT_TIME + int(rng.integers(-30, 31)) + offset
        flow = f.sample_flow(rng)
        dur = f.sample_duration(rng)
        events.append({
            "minute": start, "fixture_key": "washing_machine", "fixture": f,
            "flow_lpm": flow, "duration_min": dur, "user": "Shared",
        })

    # Dishwasher (0 or 1 per day, 60% chance)
    if rng.random() < 0.6:
        f = _get("dishwasher")
        start = DISHWASHER_DEFAULT_TIME + int(rng.integers(-15, 16)) + offset
        flow = f.sample_flow(rng)
        dur = f.sample_duration(rng)
        events.append({
            "minute": start, "fixture_key": "dishwasher", "fixture": f,
            "flow_lpm": flow, "duration_min": dur, "user": "Shared",
        })

    # Garden hose (0 or 1 per day, 50% chance)
    if rng.random() < 0.5:
        f = _get("garden")
        g_time = garden_time if garden_time is not None else GARDEN_DEFAULT_TIME
        start = g_time + int(rng.integers(-10, 11)) + offset
        flow = f.sample_flow(rng)
        dur = f.sample_duration(rng)
        events.append({
            "minute": start, "fixture_key": "garden", "fixture": f,
            "flow_lpm": flow, "duration_min": dur, "user": "Shared",
        })

    return events


def generate_all_events(
    rng: np.random.Generator,
    users: list[UserProfile] | None = None,
    fixture_overrides: dict | None = None,
    garden_time: int | None = None,
    num_days: int = 1,
) -> list[dict]:
    """Generate all fixture events for num_days days."""
    users = users or DEFAULT_USERS
    all_events = []

    for day in range(num_days):
        for user in users:
            all_events.extend(
                generate_user_events(user, rng, fixture_overrides, day)
            )
        all_events.extend(
            generate_shared_events(rng, fixture_overrides, garden_time, day)
        )

    all_events.sort(key=lambda e: e["minute"])
    return all_events
