"""
leak_detector.py – Statistical Baseline Leak Detection
Implements 3 trigger conditions per CSE 10/L project guide.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np


@dataclass
class LeakAlert:
    """A single leak / anomaly alert."""
    alert_type: str       # "leak", "anomaly", "warning"
    severity: str         # "high", "medium", "low"
    minute: int
    time_str: str
    description: str
    flow_lpm: float = 0.0
    fixture: str = ""
    duration_min: float = 0.0
    estimated_waste_liters: float = 0.0


@dataclass
class BaselineProfile:
    """Statistical baseline from historical runs."""
    historical_avg_daily: float = 0.0
    hourly_baseline: dict = field(default_factory=lambda: {h: 0.0 for h in range(24)})
    per_fixture_baseline: dict = field(default_factory=dict)
    std_daily: float = 0.0
    n_runs: int = 0


def compute_baseline(replication_states) -> BaselineProfile:
    """Compute baseline profile from a list of SimState objects."""
    from fixtures import FIXTURE_KEYS

    baseline = BaselineProfile()
    n = len(replication_states)
    if n == 0:
        return baseline

    baseline.n_runs = n
    daily_totals = []

    hourly_sums = {h: 0.0 for h in range(24)}
    fixture_sums = {k: 0.0 for k in FIXTURE_KEYS}

    for state in replication_states:
        daily_totals.append(state.cumulative_liters)

        for h in range(24):
            if h in state.hourly_liters:
                hourly_sums[h] += state.hourly_liters[h]

        for k in FIXTURE_KEYS:
            fixture_sums[k] += state.fixture_liters.get(k, 0)

    baseline.historical_avg_daily = round(np.mean(daily_totals), 2)
    baseline.std_daily = round(np.std(daily_totals), 2)
    baseline.hourly_baseline = {h: round(v / n, 2) for h, v in hourly_sums.items()}
    baseline.per_fixture_baseline = {k: round(v / n, 2) for k, v in fixture_sums.items()}

    return baseline


def detect_leaks(
    state,
    baseline: Optional[BaselineProfile] = None,
) -> List[LeakAlert]:
    """
    Analyze simulation state for leaks using 3 conditions:
    1. Overnight continuous flow (23:00-05:00)
    2. Daily usage > baseline × 1.5
    3. Single fixture active > 30 min without user event
    """
    alerts = []
    minute_log = state.minute_log
    events = state.events

    # Build event time lookup
    event_minutes = set()
    for ev in events:
        for t in range(int(ev["minute"]), int(ev["minute"] + ev["duration"])):
            event_minutes.add(t)

    # ── CONDITION 1: Overnight continuous flow ──────────────────────────────
    overnight_consecutive = 0
    overnight_start = None

    for entry in minute_log:
        m = entry["minute"]
        day_hour = m % 1440 // 60

        # Overnight = 23:00-05:00
        is_overnight = day_hour >= 23 or day_hour < 5

        if is_overnight and entry["flow_lpm"] > 0.5:
            if m not in event_minutes:
                if overnight_start is None:
                    overnight_start = m
                overnight_consecutive += 1

                if overnight_consecutive >= 30:
                    h = m // 60 % 24
                    time_str = f"{h:02d}:{m % 60:02d}"
                    waste = entry["flow_lpm"] * overnight_consecutive
                    alerts.append(LeakAlert(
                        alert_type="leak",
                        severity="high",
                        minute=m,
                        time_str=time_str,
                        description=(
                            f"⚠️ LEAK DETECTED — Continuous flow of "
                            f"{entry['flow_lpm']:.1f} LPM during idle hours. "
                            f"Duration: {overnight_consecutive} min. "
                            f"Est. waste: {waste:.1f} L"
                        ),
                        flow_lpm=entry["flow_lpm"],
                        duration_min=overnight_consecutive,
                        estimated_waste_liters=waste,
                    ))
                    overnight_consecutive = 0
                    overnight_start = None
        else:
            overnight_consecutive = 0
            overnight_start = None

    # ── CONDITION 2: Overuse anomaly ────────────────────────────────────────
    if baseline and baseline.historical_avg_daily > 0:
        threshold = baseline.historical_avg_daily * 1.5
        if state.cumulative_liters > threshold:
            deviation = (
                (state.cumulative_liters - baseline.historical_avg_daily)
                / baseline.historical_avg_daily * 100
            )
            alerts.append(LeakAlert(
                alert_type="anomaly",
                severity="medium",
                minute=state.total_minutes - 1,
                time_str="End of Day",
                description=(
                    f"Daily usage ({state.cumulative_liters:.1f} L) exceeds "
                    f"150% of baseline ({baseline.historical_avg_daily:.1f} L). "
                    f"Deviation: +{deviation:.1f}%"
                ),
                flow_lpm=0,
            ))

    # ── CONDITION 3: Sustained unexpected fixture flow ──────────────────────
    # Track continuous per-fixture active minutes without user events
    fixture_run = {}
    for entry in minute_log:
        m = entry["minute"]
        if m in event_minutes:
            # Normal user event, reset
            fixture_run.clear()
            continue

        if entry["flow_lpm"] > 0.5:
            fk = "unknown"
            # Try to identify which fixture
            for ev in events:
                if ev["minute"] <= m < ev["minute"] + ev["duration"]:
                    fk = ev["fixture"]
                    break

            if fk not in fixture_run:
                fixture_run[fk] = {"start": m, "count": 0, "flow": entry["flow_lpm"]}
            fixture_run[fk]["count"] += 1
            fixture_run[fk]["flow"] = max(fixture_run[fk]["flow"], entry["flow_lpm"])

            if fixture_run[fk]["count"] >= 30:
                h = m // 60 % 24
                time_str = f"{h:02d}:{m % 60:02d}"
                waste = fixture_run[fk]["flow"] * fixture_run[fk]["count"]
                alerts.append(LeakAlert(
                    alert_type="warning",
                    severity="medium",
                    minute=m,
                    time_str=time_str,
                    description=(
                        f"Fixture '{fk}' active for {fixture_run[fk]['count']} min "
                        f"without user event — possible leak. "
                        f"Flow: {fixture_run[fk]['flow']:.1f} LPM"
                    ),
                    flow_lpm=fixture_run[fk]["flow"],
                    fixture=fk,
                    duration_min=fixture_run[fk]["count"],
                    estimated_waste_liters=waste,
                ))
                fixture_run.pop(fk)

    return alerts


def inject_leak(
    seed: int = 99,
    onset_range_1: tuple = (0, 300),     # 00:00-05:00
    onset_range_2: tuple = (600, 840),   # 10:00-14:00
    rate_range: tuple = (0.5, 2.0),
) -> dict:
    """Generate random leak parameters for testing."""
    rng = np.random.default_rng(seed)

    onset = int(rng.choice([
        rng.integers(onset_range_1[0], onset_range_1[1]),
        rng.integers(onset_range_2[0], onset_range_2[1]),
    ]))
    rate = round(rng.uniform(rate_range[0], rate_range[1]), 2)
    fixture = rng.choice(["toilet", "faucet", "pipe"])

    return {
        "onset_minute": onset,
        "rate_lpm": rate,
        "source_fixture": str(fixture),
        "onset_time": f"{onset // 60:02d}:{onset % 60:02d}",
    }


def get_leak_status(alerts: List[LeakAlert]) -> dict:
    """Get overall leak status indicator."""
    if any(a.severity == "high" for a in alerts):
        return {"status": "leak", "label": "🔴 LEAK ALERT", "color": "#EF4444"}
    elif any(a.severity == "medium" for a in alerts):
        return {"status": "anomaly", "label": "🟡 ANOMALY", "color": "#F59E0B"}
    return {"status": "ok", "label": "🟢 NO LEAKS DETECTED", "color": "#22C55E"}
