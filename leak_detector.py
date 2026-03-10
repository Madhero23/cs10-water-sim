"""
leak_detector.py – Anomaly & Leak Detection
Analyzes per-minute flow data to detect leaks and unusual patterns.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class LeakAlert:
    """A single leak / anomaly alert."""
    alert_type: str       # "continuous_flow", "spike", "overnight"
    severity: str         # "low", "medium", "high"
    minute: int           # minute when detected
    time_str: str         # human-readable time
    description: str
    flow_gpm: float = 0.0


def _minute_to_str(m: int) -> str:
    return f"{m // 60:02d}:{m % 60:02d}"


def check_for_leaks(
    flow_series: list[float],
    quiet_start: int = 23 * 60,    # 11:00 PM
    quiet_end: int = 5 * 60,       # 5:00 AM
    continuous_threshold: int = 30, # minutes of continuous flow
    spike_multiplier: float = 2.0,
    rolling_window: int = 60,
) -> List[LeakAlert]:
    """
    Analyze a 1,440-element flow series and return alerts.

    Detection rules:
    1. Continuous overnight flow — any flow > 0 for continuous_threshold+
       minutes during quiet hours.
    2. Sudden spike — current flow > spike_multiplier × rolling average.
    """
    alerts: List[LeakAlert] = []
    n = len(flow_series)

    # ── Rule 1: Continuous overnight flow ────────────────────────────
    consecutive = 0
    alert_raised_overnight = False
    for m in range(n):
        is_quiet = m >= quiet_start or m < quiet_end
        if is_quiet and flow_series[m] > 0.01:
            consecutive += 1
            if consecutive >= continuous_threshold and not alert_raised_overnight:
                alerts.append(LeakAlert(
                    alert_type="overnight",
                    severity="high",
                    minute=m,
                    time_str=_minute_to_str(m),
                    description=(
                        f"Continuous water flow detected for {consecutive} minutes "
                        f"during quiet hours (11 PM – 5 AM). "
                        f"Possible leak or running fixture."
                    ),
                    flow_gpm=flow_series[m],
                ))
                alert_raised_overnight = True
        else:
            consecutive = 0

    # ── Rule 2: Sudden spikes ─────────────────────────────────────────
    for m in range(rolling_window, n):
        window = flow_series[max(0, m - rolling_window):m]
        avg = sum(window) / len(window) if window else 0
        if avg > 0.1 and flow_series[m] > spike_multiplier * avg:
            # Avoid duplicate alerts within 10 minutes
            if not any(
                a.alert_type == "spike" and abs(a.minute - m) < 10
                for a in alerts
            ):
                alerts.append(LeakAlert(
                    alert_type="spike",
                    severity="medium",
                    minute=m,
                    time_str=_minute_to_str(m),
                    description=(
                        f"Flow spike detected at {_minute_to_str(m)}: "
                        f"{flow_series[m]:.1f} GPM vs rolling avg {avg:.1f} GPM "
                        f"({flow_series[m]/avg:.1f}× above average)."
                    ),
                    flow_gpm=flow_series[m],
                ))

    # ── Rule 3: Continuous flow during any unoccupied period ─────────
    # Check for long stretches of low but non-zero flow (drip leak)
    drip_consecutive = 0
    drip_alerted = False
    for m in range(n):
        if 0 < flow_series[m] <= 0.2:
            drip_consecutive += 1
            if drip_consecutive >= 120 and not drip_alerted:  # 2+ hours of drip
                alerts.append(LeakAlert(
                    alert_type="continuous_flow",
                    severity="medium",
                    minute=m,
                    time_str=_minute_to_str(m),
                    description=(
                        f"Low continuous flow (~{flow_series[m]:.2f} GPM) detected "
                        f"for {drip_consecutive} consecutive minutes. "
                        f"Possible drip leak."
                    ),
                    flow_gpm=flow_series[m],
                ))
                drip_alerted = True
        else:
            drip_consecutive = 0

    # Sort by minute
    alerts.sort(key=lambda a: a.minute)
    return alerts
