"""
users.py – Household User Behavior Module
Generates stochastic daily schedules for 4 household members.
Each user is modeled as a SimPy process that triggers fixture events.
"""

import simpy
import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple

from fixtures import Fixture, get_fixture


# ── Time-window helpers (minutes since midnight) ────────────────────────────

def hm(h: int, m: int = 0) -> int:
    """Convert hour:minute to minutes since midnight."""
    return h * 60 + m


# Peak activity windows (Filipino household patterns)
MORNING_WINDOW = (hm(5, 30), hm(7, 30))   # 5:30 – 7:30 AM
MIDDAY_WINDOW  = (hm(11, 0), hm(13, 0))   # 11:00 AM – 1:00 PM
EVENING_WINDOW = (hm(17, 0), hm(21, 0))   # 5:00 – 9:00 PM


@dataclass
class UserProfile:
    """Describes a household member's daily behaviour parameters."""
    name: str
    showers_per_day: int = 1
    faucet_uses: Tuple[int, int] = (5, 8)    # uniform range
    toilet_flushes: Tuple[int, int] = (4, 6)
    preferred_shower_window: Tuple[int, int] = MORNING_WINDOW
    preferred_faucet_windows: List[Tuple[int, int]] = field(
        default_factory=lambda: [MORNING_WINDOW, MIDDAY_WINDOW, EVENING_WINDOW]
    )
    preferred_toilet_windows: List[Tuple[int, int]] = field(
        default_factory=lambda: [MORNING_WINDOW, MIDDAY_WINDOW, EVENING_WINDOW]
    )


# Default 4-member household
DEFAULT_USERS = [
    UserProfile(name="Parent A", preferred_shower_window=MORNING_WINDOW),
    UserProfile(name="Parent B", preferred_shower_window=MORNING_WINDOW),
    UserProfile(name="Child A",  preferred_shower_window=EVENING_WINDOW),
    UserProfile(name="Child B",  preferred_shower_window=EVENING_WINDOW),
]


# ── Shared Appliance Schedules ──────────────────────────────────────────────

LAUNDRY_DEFAULT_TIME = hm(9, 0)     # 9:00 AM
DISHWASHER_DEFAULT_TIME = hm(20, 0) # 8:00 PM
GARDEN_DEFAULT_TIME = hm(18, 0)     # 6:00 PM


# ── Schedule Generator ──────────────────────────────────────────────────────

def _random_time_in_window(rng: np.random.Generator, window: Tuple[int, int]) -> int:
    """Pick a random minute within a time window."""
    return int(rng.integers(window[0], window[1]))


def generate_user_events(
    user: UserProfile,
    rng: np.random.Generator,
    fixture_overrides: dict | None = None,
) -> list[dict]:
    """
    Generate a list of fixture-use events for one user for one day.
    Returns list of dicts: {minute, fixture_key, fixture, duration_min, user_name}
    """
    events = []
    fixtures = fixture_overrides or {}

    def _get(key):
        return fixtures.get(key, get_fixture(key))

    # Shower
    for _ in range(user.showers_per_day):
        f = _get("shower")
        minute = _random_time_in_window(rng, user.preferred_shower_window)
        dur = f.sample_duration(rng)
        events.append({
            "minute": minute,
            "fixture_key": "shower",
            "fixture": f,
            "duration_min": dur,
            "user": user.name,
        })

    # Faucet uses
    n_faucet = int(rng.integers(user.faucet_uses[0], user.faucet_uses[1] + 1))
    for _ in range(n_faucet):
        f = _get("faucet")
        window = user.preferred_faucet_windows[
            int(rng.integers(0, len(user.preferred_faucet_windows)))
        ]
        minute = _random_time_in_window(rng, window)
        dur = f.sample_duration(rng)
        events.append({
            "minute": minute,
            "fixture_key": "faucet",
            "fixture": f,
            "duration_min": dur,
            "user": user.name,
        })

    # Toilet flushes
    n_toilet = int(rng.integers(user.toilet_flushes[0], user.toilet_flushes[1] + 1))
    for _ in range(n_toilet):
        f = _get("toilet")
        window = user.preferred_toilet_windows[
            int(rng.integers(0, len(user.preferred_toilet_windows)))
        ]
        minute = _random_time_in_window(rng, window)
        events.append({
            "minute": minute,
            "fixture_key": "toilet",
            "fixture": f,
            "duration_min": 0.0,
            "user": user.name,
        })

    return events


def generate_shared_events(
    rng: np.random.Generator,
    fixture_overrides: dict | None = None,
    garden_time: int | None = None,
) -> list[dict]:
    """
    Generate shared appliance events (laundry, dishwasher, garden).
    """
    events = []
    fixtures = fixture_overrides or {}

    def _get(key):
        return fixtures.get(key, get_fixture(key))

    # Washing machine – 1 cycle per day
    f = _get("washing_machine")
    laundry_start = LAUNDRY_DEFAULT_TIME + int(rng.integers(-30, 31))
    events.append({
        "minute": laundry_start,
        "fixture_key": "washing_machine",
        "fixture": f,
        "duration_min": f.sample_duration(rng),
        "user": "Shared",
    })

    # Dishwasher – 1 cycle per day
    f = _get("dishwasher")
    dw_start = DISHWASHER_DEFAULT_TIME + int(rng.integers(-15, 16))
    events.append({
        "minute": dw_start,
        "fixture_key": "dishwasher",
        "fixture": f,
        "duration_min": f.sample_duration(rng),
        "user": "Shared",
    })

    # Garden / Irrigation – 1 session per day
    f = _get("garden")
    g_time = garden_time if garden_time is not None else GARDEN_DEFAULT_TIME
    g_start = g_time + int(rng.integers(-10, 11))
    events.append({
        "minute": g_start,
        "fixture_key": "garden",
        "fixture": f,
        "duration_min": f.sample_duration(rng),
        "user": "Shared",
    })

    return events


def generate_all_events(
    rng: np.random.Generator,
    users: list[UserProfile] | None = None,
    fixture_overrides: dict | None = None,
    garden_time: int | None = None,
) -> list[dict]:
    """
    Generate all fixture events for one 24-hour day.
    Returns sorted list of event dicts.
    """
    users = users or DEFAULT_USERS
    all_events = []

    for user in users:
        all_events.extend(generate_user_events(user, rng, fixture_overrides))

    all_events.extend(generate_shared_events(rng, fixture_overrides, garden_time))

    # Sort by minute
    all_events.sort(key=lambda e: e["minute"])
    return all_events
