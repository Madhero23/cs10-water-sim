"""
pricing.py – Davao City Water District Pricing (₱ per Liter)
Three pricing schemes as per CSE 10/L Project Guide.
"""


# ── Pricing Schemes ─────────────────────────────────────────────────────────

PRICING_SCHEMES = {
    "flat": {
        "label": "Flat Rate (₱0.004/L)",
        "description": "Uniform rate applied to all consumption.",
    },
    "tiered": {
        "label": "Tiered Pricing",
        "description": "Rate increases as usage volume rises.",
    },
    "peak_hour": {
        "label": "Peak Hour Surcharge",
        "description": "Higher rate during peak hours (6-9 AM, 6-9 PM).",
    },
}

# Flat rate
FLAT_RATE = 0.004  # ₱ per liter

# Tiered rates
TIERS = [
    (500,  0.003),   # 0-500 L    → ₱0.003/L
    (1000, 0.005),   # 500-1000 L → ₱0.005/L
    (None, 0.007),   # >1000 L    → ₱0.007/L
]

# Peak hour rate
PEAK_RATE = 0.0045      # ₱/L during peak hours
OFF_PEAK_RATE = 0.003   # ₱/L during off-peak
PEAK_HOURS = set(range(6, 9 + 1)) | set(range(18, 21 + 1))  # 6-9 AM, 6-9 PM


def compute_flat_cost(total_liters: float) -> float:
    """Flat rate: ₱0.004 per liter."""
    return total_liters * FLAT_RATE


def compute_tiered_cost(total_liters: float) -> dict:
    """
    Tiered pricing: rate increases with volume.
    Returns dict with tier_breakdown and total_cost_php.
    """
    remaining = total_liters
    breakdown = []
    total_cost = 0.0
    prev_bound = 0

    for upper, rate in TIERS:
        if remaining <= 0:
            break
        if upper is None:
            tier_liters = remaining
            label = f"{prev_bound}+ L"
        else:
            tier_liters = min(remaining, upper - prev_bound)
            label = f"{prev_bound}–{upper} L"

        cost = tier_liters * rate
        breakdown.append({
            "tier_label": label,
            "liters": round(tier_liters, 2),
            "rate": rate,
            "cost": round(cost, 4),
        })
        total_cost += cost
        remaining -= tier_liters
        prev_bound = upper if upper else prev_bound

    return {
        "total_liters": round(total_liters, 2),
        "tier_breakdown": breakdown,
        "total_cost_php": round(total_cost, 4),
    }


def compute_peak_hour_cost(hourly_liters: dict) -> dict:
    """
    Peak hour pricing based on hour-by-hour consumption.
    hourly_liters: dict of {hour (0-23): liters}
    Returns breakdown by peak/off-peak.
    """
    peak_liters = 0.0
    offpeak_liters = 0.0

    for hour, liters in hourly_liters.items():
        h = int(hour)
        if h in PEAK_HOURS:
            peak_liters += liters
        else:
            offpeak_liters += liters

    peak_cost = peak_liters * PEAK_RATE
    offpeak_cost = offpeak_liters * OFF_PEAK_RATE
    total = peak_cost + offpeak_cost

    return {
        "peak_liters": round(peak_liters, 2),
        "peak_cost": round(peak_cost, 4),
        "offpeak_liters": round(offpeak_liters, 2),
        "offpeak_cost": round(offpeak_cost, 4),
        "total_cost_php": round(total, 4),
    }


def compute_cost(total_liters: float, scheme: str = "flat",
                 hourly_liters: dict | None = None) -> float:
    """Quick helper — returns just the total ₱ cost."""
    if scheme == "flat":
        return round(compute_flat_cost(total_liters), 4)
    elif scheme == "tiered":
        return compute_tiered_cost(total_liters)["total_cost_php"]
    elif scheme == "peak_hour" and hourly_liters:
        return compute_peak_hour_cost(hourly_liters)["total_cost_php"]
    return round(compute_flat_cost(total_liters), 4)


def compute_bill_summary(total_liters: float, scheme: str = "flat",
                         hourly_liters: dict | None = None) -> dict:
    """Generate a full bill summary for display."""
    if scheme == "tiered":
        result = compute_tiered_cost(total_liters)
        result["scheme"] = "Tiered Pricing"
        return result
    elif scheme == "peak_hour" and hourly_liters:
        result = compute_peak_hour_cost(hourly_liters)
        result["scheme"] = "Peak Hour Surcharge"
        result["total_liters"] = round(total_liters, 2)
        return result
    else:
        return {
            "scheme": "Flat Rate",
            "total_liters": round(total_liters, 2),
            "rate": FLAT_RATE,
            "total_cost_php": round(compute_flat_cost(total_liters), 4),
        }
