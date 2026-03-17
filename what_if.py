"""
what_if.py – Conservation Scenario Projector (Liters / LPM)
Aligned with CSE 10/L Project Guide scenarios.
"""

import numpy as np
import pandas as pd
from typing import Optional

from simulation import run_replications, states_to_dataframe


# ── Scenario Definitions (per project guide) ────────────────────────────────

SCENARIOS = {
    "baseline": {
        "label": "📊 Baseline (Normal Usage)",
        "description": "Standard flow rates and typical behavioral patterns.",
        "fixture_overrides": None,
        "garden_time": None,
        "leak_gpm": 0.0,
    },
    "low_flow": {
        "label": "💧 Low-Flow Fixtures",
        "description": "Low-flow showerhead (12→7 LPM), faucet aerator (5→3 LPM), dual-flush toilet (8→5 LPM).",
        "fixture_overrides": {
            "shower": {"flow_lpm": 7.0, "flow_min": 5.0, "flow_max": 7.0},
            "faucet": {"flow_lpm": 3.0, "flow_min": 2.0, "flow_max": 3.0},
            "toilet": {"flow_lpm": 5.0, "flow_min": 4.0, "flow_max": 5.0},
        },
        "garden_time": None,
        "leak_gpm": 0.0,
    },
    "behavior_mod": {
        "label": "🧘 Behavior Modification",
        "description": "Shorter showers (−3 min), full loads only, garden shifted to 5-7 AM.",
        "fixture_overrides": {
            "shower": {"duration_mean": 8.0, "duration_std": 1.5},  # -3 min
        },
        "garden_time": 360,   # 6:00 AM
        "leak_gpm": 0.0,
    },
    "leak_test": {
        "label": "🔍 Leak Detection Test",
        "description": "Simulated leak at 0.5-2.0 LPM during idle hours.",
        "fixture_overrides": None,
        "garden_time": None,
        "leak_gpm": 1.0,
    },
    "combined": {
        "label": "🌟 Combined Conservation",
        "description": "Low-flow fixtures + behavior changes + off-peak garden.",
        "fixture_overrides": {
            "shower": {"flow_lpm": 7.0, "flow_min": 5.0, "flow_max": 7.0,
                       "duration_mean": 8.0, "duration_std": 1.5},
            "faucet": {"flow_lpm": 3.0, "flow_min": 2.0, "flow_max": 3.0},
            "toilet": {"flow_lpm": 5.0, "flow_min": 4.0, "flow_max": 5.0},
        },
        "garden_time": 360,
        "leak_gpm": 0.0,
    },
}


def run_all_scenarios(
    n_replications: int = 10,
    base_seed: int = 1000,
    pricing_scheme: str = "flat",
    num_users: int = 4,
) -> dict:
    """Run all scenarios and return {key: DataFrame}."""
    results = {}
    for key, sc in SCENARIOS.items():
        states = run_replications(
            n=n_replications,
            base_seed=base_seed,
            fixture_overrides=sc["fixture_overrides"],
            garden_time=sc["garden_time"],
            leak_gpm=sc["leak_gpm"],
            pricing_scheme=pricing_scheme,
            num_users=num_users,
        )
        results[key] = states_to_dataframe(states)
    return results


def compare_to_baseline(results: dict) -> pd.DataFrame:
    """Build a comparison table relative to baseline."""
    rows = []
    baseline_df = results.get("baseline")
    if baseline_df is None:
        return pd.DataFrame()

    bl_daily = baseline_df["total_liters"].mean()
    bl_cost = baseline_df["total_cost"].mean()

    for key, df in results.items():
        sc = SCENARIOS[key]
        daily = df["total_liters"].mean()
        cost = df["total_cost"].mean()
        monthly_l = daily * 30
        monthly_cost = cost * 30
        bl_monthly_l = bl_daily * 30
        bl_monthly_cost = bl_cost * 30

        rows.append({
            "Scenario": sc["label"],
            "Daily Liters": round(daily, 1),
            "Monthly Liters": round(monthly_l, 0),
            "Monthly Cost (₱)": round(monthly_cost, 2),
            "Monthly Savings (L)": round(bl_monthly_l - monthly_l, 0),
            "Monthly Savings (₱)": round(bl_monthly_cost - monthly_cost, 2),
        })

    return pd.DataFrame(rows)
