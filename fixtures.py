"""
fixtures.py – Fixture Library (Liters / LPM)
All flow rates in Liters Per Minute, durations in minutes.
Based on CSE 10/L Water Usage Simulation Project Guide.
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import copy


# Background drip leak rate (continuous, always active)
BACKGROUND_DRIP_LPM = 0.02


@dataclass
class Fixture:
    """A single water fixture."""
    name: str
    flow_lpm: float               # liters per minute while active
    lpf: Optional[float] = None   # liters per flush (toilet only)
    is_instantaneous: bool = False
    duration_mean: float = 0.0
    duration_std: float = 0.0
    duration_min: float = 0.0
    duration_max: float = 0.0
    dist_type: str = "normal"     # "normal", "uniform", "fixed", "poisson"
    icon: str = "💧"
    color: str = "#38bdf8"

    # Range for stochastic flow rate sampling
    flow_min: float = 0.0
    flow_max: float = 0.0

    def sample_flow(self, rng: np.random.Generator) -> float:
        """Sample a flow rate from the fixture's range."""
        if self.flow_min > 0 and self.flow_max > 0:
            return rng.uniform(self.flow_min, self.flow_max)
        return self.flow_lpm

    def sample_duration(self, rng: np.random.Generator) -> float:
        """Sample a usage duration in minutes."""
        if self.is_instantaneous:
            return 1.0  # toilet flush ~1 min
        if self.dist_type == "normal":
            dur = rng.normal(self.duration_mean, self.duration_std)
            return max(1.0, dur)
        elif self.dist_type == "uniform":
            return rng.uniform(self.duration_min, self.duration_max)
        elif self.dist_type == "fixed":
            return self.duration_mean
        return self.duration_mean

    def water_per_use(self, flow: float, duration_minutes: float) -> float:
        """Liters consumed for a single use."""
        if self.is_instantaneous:
            return flow * duration_minutes  # flush: LPM × ~1 min
        return flow * duration_minutes


# ── Default Fixture Library (CSE 10/L Guide Specs) ──────────────────────────

FIXTURE_LIBRARY: dict[str, Fixture] = {
    "shower": Fixture(
        name="Shower",
        flow_lpm=10.0,
        flow_min=8.0, flow_max=12.0,
        duration_mean=11.0, duration_std=2.0,
        dist_type="normal",
        icon="🚿", color="#3B82F6",
    ),
    "faucet": Fixture(
        name="Faucet",
        flow_lpm=4.0,
        flow_min=3.0, flow_max=5.0,
        duration_min=0.5, duration_max=3.0,
        dist_type="uniform",
        icon="🚰", color="#06B6D4",
    ),
    "toilet": Fixture(
        name="Toilet",
        flow_lpm=7.0,
        flow_min=6.0, flow_max=8.0,
        is_instantaneous=True,
        icon="🚽", color="#A855F7",
    ),
    "washing_machine": Fixture(
        name="Washing Machine",
        flow_lpm=10.0,
        flow_min=8.0, flow_max=12.0,
        duration_min=45.0, duration_max=90.0,
        dist_type="uniform",
        icon="🫧", color="#F97316",
    ),
    "dishwasher": Fixture(
        name="Dishwasher",
        flow_lpm=7.5,
        flow_min=6.0, flow_max=9.0,
        duration_min=45.0, duration_max=90.0,
        dist_type="uniform",
        icon="🍽️", color="#EC4899",
    ),
    "garden": Fixture(
        name="Garden Hose",
        flow_lpm=17.5,
        flow_min=15.0, flow_max=20.0,
        duration_min=10.0, duration_max=30.0,
        dist_type="uniform",
        icon="🌿", color="#22C55E",
    ),
}

FIXTURE_KEYS = list(FIXTURE_LIBRARY.keys())

FIXTURE_COLORS = {k: f.color for k, f in FIXTURE_LIBRARY.items()}
FIXTURE_COLORS["leak"] = "#EF4444"
FIXTURE_COLORS["drip"] = "#F59E0B"

FIXTURE_LABELS = {k: f.name for k, f in FIXTURE_LIBRARY.items()}
FIXTURE_LABELS["leak"] = "Leak"
FIXTURE_LABELS["drip"] = "Background Drip"

FIXTURE_ICONS = {k: f.icon for k, f in FIXTURE_LIBRARY.items()}
FIXTURE_ICONS["leak"] = "💧"
FIXTURE_ICONS["drip"] = "💦"


def get_fixture(name: str) -> Fixture:
    """Retrieve a copy of a fixture from the library."""
    return copy.deepcopy(FIXTURE_LIBRARY[name])


def get_modified_fixture(name: str, **overrides) -> Fixture:
    """Get a fixture with modified attributes (for what-if scenarios)."""
    f = copy.deepcopy(FIXTURE_LIBRARY[name])
    for k, v in overrides.items():
        setattr(f, k, v)
    return f
