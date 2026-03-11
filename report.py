"""
report.py – Multi-Replication Statistics & Report Builder (Liters / ₱)
"""

import pandas as pd
import numpy as np
from scipy import stats as sp_stats
from fixtures import FIXTURE_KEYS, FIXTURE_LABELS, FIXTURE_ICONS
from pricing import compute_cost, compute_bill_summary


def compute_statistics(df: pd.DataFrame) -> dict:
    """Compute summary statistics across replications."""
    n = len(df)
    result = {}

    for col, label in [("total_liters", "daily_liters"), ("total_cost", "daily_cost")]:
        values = df[col].values
        mean_v = round(float(np.mean(values)), 2)
        std_v = round(float(np.std(values, ddof=1)), 2)
        if n > 1:
            ci = sp_stats.t.interval(0.95, df=n - 1, loc=mean_v, scale=std_v / np.sqrt(n))
            ci_lower = round(ci[0], 2)
            ci_upper = round(ci[1], 2)
        else:
            ci_lower = ci_upper = mean_v

        result[label] = {
            "mean": mean_v,
            "std": std_v,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "min": round(float(values.min()), 2),
            "max": round(float(values.max()), 2),
        }

    return result


def compute_fixture_breakdown(df: pd.DataFrame) -> list[dict]:
    """Compute per-fixture average breakdown."""
    total_liters = df["total_liters"].mean()
    breakdown = []

    for k in FIXTURE_KEYS:
        col_l = f"{k}_liters"
        col_u = f"{k}_uses"
        col_a = f"{k}_active_min"

        if col_l not in df.columns:
            continue

        avg_liters = round(df[col_l].mean(), 2)
        avg_uses = round(df[col_u].mean(), 1) if col_u in df.columns else 0
        avg_active = round(df[col_a].mean(), 1) if col_a in df.columns else 0
        pct = round(avg_liters / total_liters * 100, 1) if total_liters > 0 else 0
        avg_per_use = round(avg_liters / avg_uses, 1) if avg_uses > 0 else 0

        breakdown.append({
            "fixture_key": k,
            "name": FIXTURE_LABELS.get(k, k),
            "icon": FIXTURE_ICONS.get(k, "💧"),
            "avg_liters": avg_liters,
            "avg_uses": avg_uses,
            "avg_per_use": avg_per_use,
            "avg_active_min": avg_active,
            "pct_of_total": pct,
        })

    breakdown.sort(key=lambda x: x["avg_liters"], reverse=True)
    return breakdown


def compute_utilization(df: pd.DataFrame, total_minutes: int = 1380) -> list[dict]:
    """Compute fixture utilization as % of total simulation time."""
    util = []
    for k in FIXTURE_KEYS:
        col = f"{k}_active_min"
        if col not in df.columns:
            continue
        avg_active = df[col].mean()
        pct = round(avg_active / total_minutes * 100, 1) if total_minutes > 0 else 0

        color = "#22C55E"       # green
        if pct > 60:
            color = "#EF4444"   # red
        elif pct > 30:
            color = "#F59E0B"   # yellow

        util.append({
            "fixture_key": k,
            "name": FIXTURE_LABELS.get(k, k),
            "icon": FIXTURE_ICONS.get(k, "💧"),
            "active_min": round(avg_active, 1),
            "utilization_pct": pct,
            "color": color,
        })

    util.sort(key=lambda x: x["utilization_pct"], reverse=True)
    return util


def generate_recommendations(breakdown: list[dict]) -> list[str]:
    """Auto-generate 3 actionable recommendations based on top consumers."""
    recs = []
    if len(breakdown) == 0:
        return recs

    top = breakdown[0]
    if top["fixture_key"] == "shower":
        recs.append(
            f"💡 Your SHOWER used {top['pct_of_total']}% of today's water "
            f"({top['avg_liters']:.1f} L). Reducing shower time by 3 minutes "
            f"per person saves ~{4 * 10 * 3:.0f} L/day and "
            f"₱{4 * 10 * 3 * 0.004:.2f}/day."
        )
    elif top["fixture_key"] == "garden":
        recs.append(
            f"💡 Your GARDEN HOSE used {top['pct_of_total']}% of today's water "
            f"({top['avg_liters']:.1f} L). Shift watering to 5–7 AM to avoid "
            f"peak-hour surcharges."
        )
    else:
        recs.append(
            f"💡 Your {top['name'].upper()} used {top['pct_of_total']}% of "
            f"today's water ({top['avg_liters']:.1f} L). Consider reducing "
            f"usage duration or installing a low-flow alternative."
        )

    # Second recommendation
    if len(breakdown) > 1:
        second = breakdown[1]
        if second["fixture_key"] == "garden":
            recs.append(
                f"💡 Your GARDEN HOSE used {second['pct_of_total']}% "
                f"({second['avg_liters']:.1f} L). Shift watering to early "
                f"morning (5–7 AM) to avoid peak-hour surcharges."
            )
        else:
            recs.append(
                f"💡 Your {second['name'].upper()} used {second['pct_of_total']}% "
                f"({second['avg_liters']:.1f} L). Consider installing low-flow "
                f"alternatives or reducing usage."
            )

    # General recommendation
    recs.append(
        "💡 Install low-flow showerheads (12→7 LPM) to cut shower usage by "
        "~42% with no change in behavior."
    )

    return recs[:3]


def generate_bill_summary(daily_liters: float, pricing_scheme: str = "flat") -> dict:
    """Generate monthly bill projection from daily average."""
    monthly = daily_liters * 30
    return compute_bill_summary(monthly, pricing_scheme)


def generate_report_text(
    stats: dict,
    fixture_breakdown: list[dict],
    bill: dict,
    alert_counts: dict,
    recommendations: list[str] | None = None,
) -> str:
    """Generate a markdown-formatted simulation report."""
    gl = stats["daily_liters"]
    gc = stats["daily_cost"]

    lines = [
        "## 📝 Simulation Report",
        "",
        "### Problem Statement",
        "This simulation models a **4-user household** water consumption system "
        "using Discrete-Event Simulation (DES) with stochastic user behavior, "
        "following CSE 10/L methodology.",
        "",
        "### Results Summary (30 Replications)",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Mean Daily Usage | **{gl['mean']} L** |",
        f"| Std Deviation | {gl['std']} L |",
        f"| 95% Confidence Interval | {gl['ci_lower']} – {gl['ci_upper']} L |",
        f"| Min / Max | {gl['min']} L – {gl['max']} L |",
        f"| Mean Daily Cost | ₱{gc['mean']} |",
        f"| Projected Monthly Cost | ₱{round(gc['mean'] * 30, 2)} |",
        "",
        "### Fixture Breakdown",
        "",
        "| Fixture | Liters | Uses | Avg/Use | % of Total |",
        "|---------|--------|------|---------|------------|",
    ]

    total_L = 0
    total_uses = 0
    for fb in fixture_breakdown:
        lines.append(
            f"| {fb['icon']} {fb['name']} | {fb['avg_liters']:.1f} L | "
            f"{fb['avg_uses']:.0f} | {fb['avg_per_use']:.1f} L | "
            f"{fb['pct_of_total']}% |"
        )
        total_L += fb["avg_liters"]
        total_uses += fb["avg_uses"]

    lines.append(f"| **TOTAL** | **{total_L:.1f} L** | **{total_uses:.0f}** | — | 100% |")
    lines.append("")

    # Alerts
    lines.append("### Leak & Anomaly Summary")
    lines.append(f"- Total alerts across 30 runs: **{alert_counts['total']}**")
    lines.append(f"- High severity: **{alert_counts['high']}**")
    lines.append(f"- Medium severity: **{alert_counts['medium']}**")
    lines.append("")

    # Recommendations
    if recommendations:
        lines.append("### Recommendations")
        lines.append("")
        for r in recommendations:
            lines.append(f"- {r}")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by CSE 10/L Water Usage Simulation — University of Mindanao*")

    return "\n".join(lines)
