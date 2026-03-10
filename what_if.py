"""
what_if.py – Conservation Scenario Projector
Runs multiple simulation scenarios and compares water/cost savings to baseline.
"""

import numpy as np
import pandas as pd
from typing import Optional

from fixtures import get_fixture, get_modified_fixture
from users import DEFAULT_USERS, hm
from simulation import run_replications, states_to_dataframe


# ── Scenario Definitions ────────────────────────────────────────────────────

SCENARIOS = {
    "baseline": {
        "label": "Baseline (Normal Usage)",
        "description": "Normal household behavior with no conservation measures.",
        "fixture_overrides": None,
        "garden_time": None,
        "leak_gpm": 0.0,
        "user_mod": None,
    },
    "short_showers": {
        "label": "Short Showers (−2 min)",
        "description": "Each user reduces shower time by 2 minutes on average.",
        "fixture_overrides": {
            "shower": get_modified_fixture("shower", duration_mean=6.0),
        },
        "garden_time": None,
        "leak_gpm": 0.0,
        "user_mod": None,
    },
    "low_flow": {
        "label": "Low-Flow Fixtures (1.8 GPM)",
        "description": "Replace standard showerheads with 1.8 GPM low-flow models.",
        "fixture_overrides": {
            "shower": get_modified_fixture("shower", flow_gpm=1.8),
        },
        "garden_time": None,
        "leak_gpm": 0.0,
        "user_mod": None,
    },
    "leak_present": {
        "label": "Leak Present (0.1 GPM drip)",
        "description": "A 0.1 GPM continuous drip leak runs 24/7.",
        "fixture_overrides": None,
        "garden_time": None,
        "leak_gpm": 0.1,
        "user_mod": None,
    },
    "offpeak_irrigation": {
        "label": "Off-Peak Irrigation (5 AM)",
        "description": "Shift garden watering from evening to 5:00 AM.",
        "fixture_overrides": None,
        "garden_time": hm(5, 0),
        "leak_gpm": 0.0,
        "user_mod": None,
    },
}


def run_scenario(
    scenario_key: str,
    n_replications: int = 30,
    base_seed: int = 1000,
) -> dict:
    """
    Run a single scenario for n replications.

    Returns a dict with:
        - key, label, description
        - summary_df: per-replication summary DataFrame
        - mean_gallons, std_gallons, mean_cost, std_cost
        - ci_95_gallons, ci_95_cost  (95% confidence interval half-width)
    """
    sc = SCENARIOS[scenario_key]

    kwargs = {}
    if sc["fixture_overrides"]:
        kwargs["fixture_overrides"] = sc["fixture_overrides"]
    if sc["garden_time"] is not None:
        kwargs["garden_time"] = sc["garden_time"]
    if sc["leak_gpm"]:
        kwargs["leak_gpm"] = sc["leak_gpm"]

    states = run_replications(n=n_replications, base_seed=base_seed, **kwargs)
    df = states_to_dataframe(states)

    n = len(df)
    from scipy import stats
    t_crit = stats.t.ppf(0.975, df=n - 1) if n > 1 else 0

    mean_gal = df["total_gallons"].mean()
    std_gal = df["total_gallons"].std()
    mean_cost = df["projected_monthly_cost"].mean()
    std_cost = df["projected_monthly_cost"].std()

    ci_gal = t_crit * std_gal / (n ** 0.5) if n > 1 else 0
    ci_cost = t_crit * std_cost / (n ** 0.5) if n > 1 else 0

    return {
        "key": scenario_key,
        "label": sc["label"],
        "description": sc["description"],
        "summary_df": df,
        "mean_gallons": round(mean_gal, 2),
        "std_gallons": round(std_gal, 2),
        "mean_cost": round(mean_cost, 2),
        "std_cost": round(std_cost, 2),
        "ci_95_gallons": round(ci_gal, 2),
        "ci_95_cost": round(ci_cost, 2),
        "monthly_gallons": round(mean_gal * 30, 1),
        "monthly_cost": round(mean_cost, 2),
    }


def run_all_scenarios(
    n_replications: int = 30,
    base_seed: int = 1000,
) -> dict[str, dict]:
    """Run all scenarios and return results keyed by scenario name."""
    results = {}
    for key in SCENARIOS:
        results[key] = run_scenario(key, n_replications, base_seed)
    return results


def compare_to_baseline(all_results: dict[str, dict]) -> pd.DataFrame:
    """
    Build a comparison DataFrame showing savings vs baseline.
    """
    baseline = all_results["baseline"]
    rows = []

    for key, res in all_results.items():
        gal_saved = baseline["mean_gallons"] - res["mean_gallons"]
        cost_saved = baseline["mean_cost"] - res["mean_cost"]
        rows.append({
            "Scenario": res["label"],
            "Daily Gallons": res["mean_gallons"],
            "Daily Gallons ± CI": f'{res["mean_gallons"]} ± {res["ci_95_gallons"]}',
            "Monthly Gallons": res["monthly_gallons"],
            "Monthly Cost (₱)": res["monthly_cost"],
            "Monthly Cost ± CI": f'₱{res["mean_cost"]} ± ₱{res["ci_95_cost"]}',
            "Daily Savings (gal)": round(gal_saved, 2),
            "Monthly Savings (gal)": round(gal_saved * 30, 1),
            "Monthly Savings (₱)": round(cost_saved, 2),
        })

    return pd.DataFrame(rows)
