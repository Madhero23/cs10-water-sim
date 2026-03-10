"""
pricing.py – Davao City Water District Tiered Pricing
Converts gallon usage to cubic meters and applies the DCWD rate schedule.
"""

GALLONS_PER_CUBIC_METER = 264.172

# Davao City Water District residential tiers
# Each tuple: (upper_bound_m3, rate_per_m3_php)
# The first tier is a flat minimum charge.
TIERS = [
    (10,  None),    # 0-10 m³  → flat ₱120.55
    (20,  18.85),   # 11-20 m³
    (30,  27.80),   # 21-30 m³
    (40,  37.90),   # 31-40 m³
    (None, 47.35),  # 41+  m³
]

MINIMUM_CHARGE_PHP = 120.55


def gallons_to_m3(gallons: float) -> float:
    """Convert gallons to cubic meters."""
    return gallons / GALLONS_PER_CUBIC_METER


def compute_monthly_bill(total_gallons: float) -> dict:
    """
    Compute the monthly water bill under DCWD tiered pricing.

    Returns a dict with:
        - total_gallons: input
        - total_m3: converted volume
        - tier_breakdown: list of {tier_label, m3, rate, cost}
        - total_cost_php: final bill in Philippine Pesos
    """
    total_m3 = gallons_to_m3(total_gallons)
    breakdown = []
    remaining = total_m3
    total_cost = 0.0
    prev_bound = 0

    for i, (upper, rate) in enumerate(TIERS):
        if remaining <= 0:
            break

        if upper is None:
            tier_m3 = remaining
        else:
            tier_m3 = min(remaining, upper - prev_bound)

        if i == 0:
            # First tier: flat minimum regardless of usage
            cost = MINIMUM_CHARGE_PHP
            label = f"0–{upper} m³ (minimum)"
        else:
            cost = tier_m3 * rate
            lower = prev_bound + 1
            label = f"{lower}–{upper} m³" if upper else f"{prev_bound + 1}+ m³"

        breakdown.append({
            "tier_label": label,
            "m3": round(tier_m3, 3),
            "rate": rate if rate else "flat",
            "cost": round(cost, 2),
        })
        total_cost += cost
        remaining -= tier_m3
        prev_bound = upper if upper else prev_bound

    return {
        "total_gallons": round(total_gallons, 2),
        "total_m3": round(total_m3, 3),
        "tier_breakdown": breakdown,
        "total_cost_php": round(total_cost, 2),
    }


def compute_cost_for_gallons(cumulative_gallons: float) -> float:
    """Quick helper — returns just the total ₱ cost."""
    return compute_monthly_bill(cumulative_gallons)["total_cost_php"]


def daily_cost(daily_gallons: float, days: int = 30) -> float:
    """Project a daily usage to a monthly bill."""
    return compute_cost_for_gallons(daily_gallons * days)
