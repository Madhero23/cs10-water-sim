"""
report.py – Multi-Replication Statistics & Report Builder
Computes summary statistics across 30 replications and generates
structured report content for the dashboard.
"""

import pandas as pd
import numpy as np
from scipy import stats

from simulation import SimState, states_to_dataframe
from pricing import compute_monthly_bill, gallons_to_m3


def compute_statistics(df: pd.DataFrame) -> dict:
    """
    Compute key statistics from a replication summary DataFrame.

    Returns dict with mean, std, CI, min, max for gallons and cost.
    """
    n = len(df)
    t_crit = stats.t.ppf(0.975, df=n - 1) if n > 1 else 0

    def _stats(col):
        mean = df[col].mean()
        std = df[col].std()
        ci = t_crit * std / (n ** 0.5) if n > 1 else 0
        return {
            "mean": round(mean, 2),
            "std": round(std, 2),
            "ci_95": round(ci, 2),
            "min": round(df[col].min(), 2),
            "max": round(df[col].max(), 2),
            "ci_lower": round(mean - ci, 2),
            "ci_upper": round(mean + ci, 2),
        }

    return {
        "n_replications": n,
        "daily_gallons": _stats("total_gallons"),
        "daily_m3": _stats("total_m3"),
        "monthly_cost": _stats("projected_monthly_cost"),
    }


def compute_fixture_breakdown(df: pd.DataFrame) -> dict:
    """
    Compute average per-fixture contribution from replications.
    Returns dict of fixture → {mean_gallons, percentage}.
    """
    fixture_cols = [c for c in df.columns if c.endswith("_gallons") and c != "total_gallons"]
    total = sum(df[c].mean() for c in fixture_cols)

    breakdown = {}
    for col in fixture_cols:
        key = col.replace("_gallons", "")
        mean_gal = df[col].mean()
        pct = (mean_gal / total * 100) if total > 0 else 0
        breakdown[key] = {
            "mean_gallons": round(mean_gal, 2),
            "percentage": round(pct, 1),
        }
    return breakdown


def generate_bill_summary(mean_daily_gallons: float, days: int = 30) -> dict:
    """Generate a monthly bill summary from average daily usage."""
    monthly_gallons = mean_daily_gallons * days
    return compute_monthly_bill(monthly_gallons)


def generate_report_text(
    statistics: dict,
    fixture_breakdown: dict,
    bill_summary: dict,
    alerts_summary: dict | None = None,
) -> str:
    """Generate markdown-formatted simulation report text."""
    s = statistics
    gal = s["daily_gallons"]
    cost = s["monthly_cost"]

    report = f"""# Single Household Water Usage Simulation Report

## 1. Problem Statement

This simulation models the daily water consumption of a 4-member Filipino household
in Davao City. It aims to quantify per-fixture water usage, estimate monthly water
bills under the Davao City Water District (DCWD) tiered pricing structure, and
evaluate the impact of conservation strategies on household water costs.

## 2. Model Description

- **Type:** Hybrid Discrete-Event Simulation (DES) + Stochastic Modeling
- **Duration:** 24-hour daily cycle (1,440 one-minute time steps)
- **Replications:** {s['n_replications']} independent runs
- **Household:** 4 users (2 parents, 2 children)
- **Fixtures:** Shower, Faucet, Toilet, Washing Machine, Dishwasher, Garden/Irrigation
- **Pricing:** DCWD tiered residential rates

User behavior is modeled stochastically with activity windows based on typical
Filipino household routines (morning rush, midday, evening).

## 3. Results Summary

### Daily Water Usage
- **Mean:** {gal['mean']} gallons/day (± {gal['ci_95']} gallons, 95% CI)
- **Range:** {gal['min']} – {gal['max']} gallons/day
- **Std Dev:** {gal['std']} gallons

### Monthly Projected Cost
- **Mean:** ₱{cost['mean']} (± ₱{cost['ci_95']}, 95% CI)
- **Range:** ₱{cost['min']} – ₱{cost['max']}

### Per-Fixture Contribution
"""
    for key, data in fixture_breakdown.items():
        name = key.replace("_", " ").title()
        report += f"- **{name}:** {data['mean_gallons']} gal/day ({data['percentage']}%)\n"

    report += f"""
### Monthly Bill Breakdown
- **Total Usage:** {bill_summary['total_gallons']} gallons ({bill_summary['total_m3']} m³)
- **Total Cost:** ₱{bill_summary['total_cost_php']}
"""
    for tier in bill_summary["tier_breakdown"]:
        report += f"  - {tier['tier_label']}: {tier['m3']} m³ → ₱{tier['cost']}\n"

    if alerts_summary:
        report += f"""
### Leak / Anomaly Detection
- **Total Alerts:** {alerts_summary.get('total', 0)}
- **High Severity:** {alerts_summary.get('high', 0)}
- **Medium Severity:** {alerts_summary.get('medium', 0)}
"""

    report += """
## 4. Recommendations

1. **Install low-flow showerheads** (1.8 GPM) to reduce shower water by ~28%.
2. **Shorten shower times** by 2 minutes per user to save ~20 gallons/day.
3. **Shift garden watering** to early morning to reduce evaporation losses.
4. **Fix any detected leaks** promptly — a 0.1 GPM drip wastes ~144 gallons/day (4,320 gal/month).
5. **Monitor overnight usage** as an early indicator of hidden leaks.

---
*Generated by Single Household Water Usage Simulation | CSE 10/L Modeling & Simulation*
"""
    return report
