"""
fixtures.py – Fixture Library
Defines all water-consuming fixtures in the household with
flow rates, per-use volumes, and stochastic duration samplers.
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class Fixture:
    """A single water fixture."""
    name: str
    flow_gpm: float                # gallons per minute while active
    gpf: Optional[float] = None    # gallons per flush (toilet only)
    is_instantaneous: bool = False  # True for toilet flush
    duration_mean: float = 0.0     # minutes (for normal dist)
    duration_std: float = 0.0
    duration_min: float = 0.0      # minutes (for uniform dist)
    duration_max: float = 0.0
    dist_type: str = "normal"      # "normal", "uniform", or "fixed"
    icon: str = "💧"

    def sample_duration(self, rng: np.random.Generator) -> float:
        """Sample a usage duration in minutes from the fixture's distribution."""
        if self.is_instantaneous:
            return 0.0  # toilet: single flush, no continuous flow
        if self.dist_type == "normal":
            dur = rng.normal(self.duration_mean, self.duration_std)
            return max(1.0, dur)  # at least 1 minute
        elif self.dist_type == "uniform":
            return rng.uniform(self.duration_min, self.duration_max)
        elif self.dist_type == "fixed":
            return self.duration_mean
        return self.duration_mean

    def water_per_use(self, duration_minutes: float) -> float:
        """Gallons consumed for a single use of the given duration."""
        if self.is_instantaneous:
            return self.gpf or 0.0
        return self.flow_gpm * duration_minutes


# ── Default Fixture Library ──────────────────────────────────────────────────

FIXTURE_LIBRARY: dict[str, Fixture] = {
    "shower": Fixture(
        name="Shower",
        flow_gpm=2.5,
        duration_mean=8.0,
        duration_std=2.0,
        dist_type="normal",
        icon="🚿",
    ),
    "faucet": Fixture(
        name="Faucet",
        flow_gpm=1.5,
        duration_mean=1.75,
        duration_std=0.0,
        duration_min=0.5,
        duration_max=3.0,
        dist_type="uniform",
        icon="🚰",
    ),
    "toilet": Fixture(
        name="Toilet",
        flow_gpm=0.0,
        gpf=1.6,
        is_instantaneous=True,
        icon="🚽",
    ),
    "washing_machine": Fixture(
        name="Washing Machine",
        flow_gpm=0.67,
        duration_mean=45.0,
        dist_type="fixed",
        icon="👕",
    ),
    "dishwasher": Fixture(
        name="Dishwasher",
        flow_gpm=1.5,
        duration_mean=60.0,
        dist_type="fixed",
        icon="🍽️",
    ),
    "garden": Fixture(
        name="Garden / Irrigation",
        flow_gpm=5.0,
        duration_min=15.0,
        duration_max=30.0,
        dist_type="uniform",
        icon="🌿",
    ),
}


def get_fixture(name: str) -> Fixture:
    """Retrieve a copy of a fixture from the library."""
    import copy
    return copy.deepcopy(FIXTURE_LIBRARY[name])


def get_modified_fixture(name: str, **overrides) -> Fixture:
    """Get a fixture with modified attributes (for what-if scenarios)."""
    import copy
    f = copy.deepcopy(FIXTURE_LIBRARY[name])
    for k, v in overrides.items():
        setattr(f, k, v)
    return f
