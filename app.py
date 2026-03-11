"""
app.py – Dash Interactive Dashboard (v2)
Single Household Water Usage Simulation
CSE 10/L – Modeling and Simulation | University of Mindanao

Features:
  - Duration selector (Hours / Days / Weeks)
  - 4 tabs: Live Overview, Usage Charts, Utilization, Summary Report
  - 6 fixture consumption cards with live progress bars
  - Statistical baseline leak detection with 3 conditions
  - Simulate Leak button
  - All units in Liters (L) and Philippine Peso (₱)
"""

import dash
from dash import html, dcc, Input, Output, State, callback, no_update, ALL, ctx
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import json

from simulation import run_single_day, run_replications, states_to_dataframe, SimState
from fixtures import FIXTURE_LIBRARY, FIXTURE_KEYS, FIXTURE_COLORS, FIXTURE_LABELS, FIXTURE_ICONS
from pricing import (
    compute_cost, compute_bill_summary, compute_tiered_cost,
    compute_flat_cost, PRICING_SCHEMES,
)
from leak_detector import (
    detect_leaks, compute_baseline, inject_leak, get_leak_status,
    LeakAlert, BaselineProfile,
)
from what_if import SCENARIOS, run_all_scenarios, compare_to_baseline
from report import (
    compute_statistics, compute_fixture_breakdown, compute_utilization,
    generate_bill_summary, generate_report_text, generate_recommendations,
)


# ── Plotly Theme ─────────────────────────────────────────────────────────────

PLOT_BG = "rgba(0,0,0,0)"
PLOT_FONT = dict(family="Inter, sans-serif", color="#94a3b8", size=12)
GRID_COLOR = "rgba(255,255,255,0.04)"
ZERO_COLOR = "rgba(255,255,255,0.06)"

def make_layout(**overrides):
    """Create a Plotly layout dict with theme defaults and safe overrides."""
    base = dict(
        paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
        font=PLOT_FONT,
        margin=dict(l=50, r=20, t=40, b=50),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=ZERO_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=ZERO_COLOR),
        colorway=["#3B82F6", "#06B6D4", "#A855F7", "#F97316", "#EC4899", "#22C55E", "#EF4444"],
    )
    base.update(overrides)
    return base


# ── Dash App ─────────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__, title="Water Usage Simulation",
    update_title=None, suppress_callback_exceptions=True,
)

app.index_string = '''<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <meta name="description" content="Single Household Water Usage Simulation – CSE 10/L">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
    {%app_entry%}
    <footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>'''


# ── Layout Helpers ───────────────────────────────────────────────────────────

def metric_card(id_prefix, label, icon, color_class="blue"):
    return html.Div(className="card metric-card span-3", children=[
        html.Div(icon, className="card-title-icon", style={"fontSize": "24px"}),
        html.Div(id=f"{id_prefix}-value", className=f"metric-value {color_class}", children="—"),
        html.Div(id=f"{id_prefix}-unit", className="metric-unit"),
        html.Div(label, className="metric-label"),
    ])


def empty_fig():
    fig = go.Figure()
    fig.update_layout(**make_layout(height=300))
    return fig


# ── App Layout ───────────────────────────────────────────────────────────────

app.layout = html.Div(id="app-container", children=[

    # Data stores
    dcc.Store(id="sim-data-store"),
    dcc.Store(id="baseline-store"),
    dcc.Store(id="active-tab", data="tab-live"),

    # ── Header ───────────────────────────────────────────────────
    html.Div(className="header", children=[
        html.Div(className="header-left", children=[
            html.Span("💧", className="header-icon"),
            html.Div([
                html.Div("Single Household Water Usage Simulation", className="header-title"),
                html.Div("CSE 10/L – Modeling & Simulation | University of Mindanao", className="header-subtitle"),
            ]),
        ]),
        html.Div(className="header-right", children=[
            html.Div(id="sim-clock", className="sim-clock", children="00:00"),
            html.Div(id="sim-status", className="status-badge ready", children=[
                html.Span(className="status-dot"),
                html.Span("Ready"),
            ]),
        ]),
    ]),

    # ── Controls Bar ─────────────────────────────────────────────
    html.Div(className="controls-bar", children=[

        # Duration selector
        html.Div(className="duration-group", children=[
            html.Span("Duration:", className="duration-label"),
            html.Div(id="duration-toggles", className="toggle-group", children=[
                html.Button("Hours", id="btn-hours", className="toggle-btn active", n_clicks=0),
                html.Button("Days", id="btn-days", className="toggle-btn", n_clicks=0),
                html.Button("Weeks", id="btn-weeks", className="toggle-btn", n_clicks=0),
            ]),
            dcc.Input(
                id="duration-value", type="number", value=24, min=1, max=72,
                style={
                    "width": "70px", "padding": "6px 10px",
                    "backgroundColor": "rgba(255,255,255,0.06)",
                    "color": "#f1f5f9", "border": "1px solid rgba(255,255,255,0.08)",
                    "borderRadius": "8px", "fontSize": "13px", "fontFamily": "Inter",
                },
            ),
            html.Span(id="duration-unit-label", className="duration-label", children="hours"),
        ]),

        html.Div(className="controls-separator"),

        # Pricing scheme
        dcc.Dropdown(
            id="pricing-dropdown",
            options=[{"label": v["label"], "value": k} for k, v in PRICING_SCHEMES.items()],
            value="flat", clearable=False, className="dropdown-scenario",
            style={
                "width": "220px", "backgroundColor": "rgba(255,255,255,0.06)",
                "color": "#f1f5f9", "border": "1px solid rgba(255,255,255,0.08)",
                "borderRadius": "8px",
            },
        ),

        html.Div(className="controls-separator"),

        # Scenario
        dcc.Dropdown(
            id="scenario-dropdown",
            options=[{"label": sc["label"], "value": k} for k, sc in SCENARIOS.items()],
            value="baseline", clearable=False, className="dropdown-scenario",
            style={
                "width": "260px", "backgroundColor": "rgba(255,255,255,0.06)",
                "color": "#f1f5f9", "border": "1px solid rgba(255,255,255,0.08)",
                "borderRadius": "8px",
            },
        ),

        html.Div(className="controls-separator"),

        # Buttons
        html.Button("▶  Run", id="btn-run", className="btn btn-primary", n_clicks=0),
        html.Button("📊  30 Replications", id="btn-replicate", className="btn btn-secondary", n_clicks=0),
        html.Button("🔄  Compare All", id="btn-compare", className="btn btn-secondary", n_clicks=0),
        html.Button("💧  Simulate Leak", id="btn-leak", className="btn btn-danger", n_clicks=0),
        html.Button("⏹  Reset", id="btn-reset", className="btn btn-reset", n_clicks=0),
    ]),

    # ── Tab Bar ──────────────────────────────────────────────────
    html.Div(className="tab-bar", children=[
        html.Button("📊 Live Overview", id="tab-btn-live", className="tab-btn active", n_clicks=0),
        html.Button("📈 Usage Charts", id="tab-btn-charts", className="tab-btn", n_clicks=0),
        html.Button("⚙️ Utilization", id="tab-btn-util", className="tab-btn", n_clicks=0),
        html.Button("📋 Summary Report", id="tab-btn-report", className="tab-btn", n_clicks=0),
    ]),

    # ══════════════════════════════════════════════════════════════
    #  TAB 1 — Live Overview
    # ══════════════════════════════════════════════════════════════
    html.Div(id="tab-live", className="tab-content active", children=[
        html.Div(className="dashboard-grid", children=[
            # Metric cards
            metric_card("flow", "Current Flow Rate", "🌊", "cyan"),
            metric_card("cumulative", "Cumulative Usage", "📊", "blue"),
            metric_card("cost", "Daily Cost", "💰", "emerald"),
            metric_card("alerts-count", "Active Alerts", "⚠️", "amber"),

            # Fixture cards + Donut chart
            html.Div(className="card span-8", children=[
                html.Div(className="card-header", children=[
                    html.Div(className="card-title", children=[
                        html.Span("🏠", className="card-title-icon"),
                        "Fixture Water Consumption Breakdown",
                    ]),
                ]),
                html.Div(id="fixture-cards-panel"),
            ]),
            html.Div(className="card span-4", children=[
                html.Div(className="card-header", children=[
                    html.Div(className="card-title", children=[
                        html.Span("🍩", className="card-title-icon"),
                        "Fixture Share",
                    ]),
                ]),
                dcc.Graph(id="fixture-pie", config={"displayModeBar": False},
                          style={"height": "380px"}, figure=empty_fig()),
            ]),

            # Leak alerts
            html.Div(className="card span-12", children=[
                html.Div(id="leak-status-display"),
                html.Div(className="card-header", children=[
                    html.Div(className="card-title", children=[
                        html.Span("🚨", className="card-title-icon"),
                        "Leak & Anomaly Alerts",
                    ]),
                ]),
                html.Div(id="alerts-panel", children=[
                    html.Div(className="no-alerts", children=[
                        html.Span("✓", className="check-icon"),
                        "Run simulation to check for anomalies",
                    ]),
                ]),
            ]),
        ]),
    ]),

    # ══════════════════════════════════════════════════════════════
    #  TAB 2 — Usage Charts
    # ══════════════════════════════════════════════════════════════
    html.Div(id="tab-charts", className="tab-content", children=[
        html.Div(className="dashboard-grid", children=[
            # Horizontal bar chart
            html.Div(className="card span-12", children=[
                html.Div(className="card-header", children=[
                    html.Div(className="card-title", children=[
                        html.Span("📊", className="card-title-icon"),
                        "Ranked Fixture Usage",
                    ]),
                ]),
                dcc.Graph(id="hbar-chart", config={"displayModeBar": False},
                          style={"height": "350px"}, figure=empty_fig()),
            ]),

            # 24-hour stacked timeline
            html.Div(className="card span-12", children=[
                html.Div(className="card-header", children=[
                    html.Div(className="card-title", children=[
                        html.Span("📈", className="card-title-icon"),
                        "24-Hour Flow Timeline by Fixture",
                    ]),
                ]),
                dcc.Graph(id="timeline-chart", config={"displayModeBar": False},
                          style={"height": "400px"}, figure=empty_fig()),
            ]),

            # What-if comparison
            html.Div(className="card span-8", children=[
                html.Div(className="card-header", children=[
                    html.Div(className="card-title", children=[
                        html.Span("🔬", className="card-title-icon"),
                        "What-If Scenario Comparison",
                    ]),
                ]),
                html.Div(id="whatif-content", children=[
                    html.Div(className="loading-overlay", children=[
                        html.Div("Click 'Compare All' to run projections.",
                                 className="loading-text"),
                    ]),
                ]),
            ]),
            html.Div(className="card span-4", children=[
                html.Div(className="card-header", children=[
                    html.Div(className="card-title", children=[
                        html.Span("🧾", className="card-title-icon"),
                        "Bill Summary",
                    ]),
                ]),
                html.Div(id="bill-content", children=[
                    html.Div(className="loading-overlay", children=[
                        html.Div("Run simulation to see bill.",
                                 className="loading-text"),
                    ]),
                ]),
            ]),

            # Savings bar chart
            html.Div(className="card span-12", children=[
                html.Div(className="card-header", children=[
                    html.Div(className="card-title", children=[
                        html.Span("📉", className="card-title-icon"),
                        "Scenario Savings Comparison",
                    ]),
                ]),
                dcc.Graph(id="savings-chart", config={"displayModeBar": False},
                          style={"height": "350px"}, figure=empty_fig()),
            ]),
        ]),
    ]),

    # ══════════════════════════════════════════════════════════════
    #  TAB 3 — Utilization
    # ══════════════════════════════════════════════════════════════
    html.Div(id="tab-util", className="tab-content", children=[
        html.Div(className="dashboard-grid", children=[
            html.Div(className="card span-12", children=[
                html.Div(className="card-header", children=[
                    html.Div(className="card-title", children=[
                        html.Span("⚙️", className="card-title-icon"),
                        "Fixture Utilization (Server Utilization)",
                    ]),
                ]),
                html.Div(id="utilization-panel", children=[
                    html.Div(className="loading-overlay", children=[
                        html.Div("Run 30 Replications to see utilization metrics.",
                                 className="loading-text"),
                    ]),
                ]),
            ]),
            html.Div(className="card span-12", children=[
                html.Div(className="card-header", children=[
                    html.Div(className="card-title", children=[
                        html.Span("📊", className="card-title-icon"),
                        "Baseline Monitor",
                    ]),
                ]),
                html.Div(id="baseline-monitor"),
                dcc.Graph(id="baseline-chart", config={"displayModeBar": False},
                          style={"height": "350px"}, figure=empty_fig()),
            ]),

            # Replication statistics
            html.Div(className="card span-12", children=[
                html.Div(className="card-header", children=[
                    html.Div(className="card-title", children=[
                        html.Span("📊", className="card-title-icon"),
                        "Replication Statistics (30 Runs)",
                    ]),
                ]),
                html.Div(id="replication-content", children=[
                    html.Div(className="loading-overlay", children=[
                        html.Div("Click '30 Replications' to generate statistics.",
                                 className="loading-text"),
                    ]),
                ]),
            ]),
        ]),
    ]),

    # ══════════════════════════════════════════════════════════════
    #  TAB 4 — Summary Report
    # ══════════════════════════════════════════════════════════════
    html.Div(id="tab-report", className="tab-content", children=[
        html.Div(className="dashboard-grid", children=[
            # Summary table
            html.Div(className="card span-12", children=[
                html.Div(className="card-header", children=[
                    html.Div(className="card-title", children=[
                        html.Span("📋", className="card-title-icon"),
                        "Post-Simulation Summary",
                    ]),
                ]),
                html.Div(id="summary-table-content", children=[
                    html.Div(className="loading-overlay", children=[
                        html.Div("Run 30 Replications to generate summary.",
                                 className="loading-text"),
                    ]),
                ]),
            ]),

            # Full report
            html.Div(className="card span-12", children=[
                html.Div(className="card-header", children=[
                    html.Div(className="card-title", children=[
                        html.Span("📝", className="card-title-icon"),
                        "Full Simulation Report",
                    ]),
                ]),
                html.Div(id="report-content", className="report-content", children=[
                    html.Div(className="loading-overlay", children=[
                        html.Div("Run 30 replications to generate the full report.",
                                 className="loading-text"),
                    ]),
                ]),
            ]),
        ]),
    ]),
])


# ══════════════════════════════════════════════════════════════════════════════
#  CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════


# ── Tab switching ────────────────────────────────────────────────────────────

@app.callback(
    [
        Output("tab-live", "className"),
        Output("tab-charts", "className"),
        Output("tab-util", "className"),
        Output("tab-report", "className"),
        Output("tab-btn-live", "className"),
        Output("tab-btn-charts", "className"),
        Output("tab-btn-util", "className"),
        Output("tab-btn-report", "className"),
    ],
    [
        Input("tab-btn-live", "n_clicks"),
        Input("tab-btn-charts", "n_clicks"),
        Input("tab-btn-util", "n_clicks"),
        Input("tab-btn-report", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def switch_tab(n1, n2, n3, n4):
    triggered = ctx.triggered_id
    tabs = {
        "tab-btn-live": 0, "tab-btn-charts": 1,
        "tab-btn-util": 2, "tab-btn-report": 3,
    }
    active = tabs.get(triggered, 0)
    tab_classes = ["tab-content"] * 4
    btn_classes = ["tab-btn"] * 4
    tab_classes[active] = "tab-content active"
    btn_classes[active] = "tab-btn active"
    return (*tab_classes, *btn_classes)


# ── Duration toggle ──────────────────────────────────────────────────────────

@app.callback(
    [
        Output("btn-hours", "className"),
        Output("btn-days", "className"),
        Output("btn-weeks", "className"),
        Output("duration-value", "max"),
        Output("duration-value", "value"),
        Output("duration-unit-label", "children"),
    ],
    [
        Input("btn-hours", "n_clicks"),
        Input("btn-days", "n_clicks"),
        Input("btn-weeks", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def toggle_duration(h, d, w):
    triggered = ctx.triggered_id
    classes = ["toggle-btn"] * 3
    if triggered == "btn-hours":
        classes[0] = "toggle-btn active"
        return (*classes, 72, 24, "hours")
    elif triggered == "btn-days":
        classes[1] = "toggle-btn active"
        return (*classes, 30, 7, "days")
    elif triggered == "btn-weeks":
        classes[2] = "toggle-btn active"
        return (*classes, 4, 2, "weeks")
    classes[0] = "toggle-btn active"
    return (*classes, 72, 24, "hours")


# ── Reset ────────────────────────────────────────────────────────────────────

@app.callback(
    [
        Output("sim-data-store", "data", allow_duplicate=True),
        Output("sim-status", "children", allow_duplicate=True),
        Output("sim-status", "className", allow_duplicate=True),
        Output("sim-clock", "children", allow_duplicate=True),
    ],
    Input("btn-reset", "n_clicks"),
    prevent_initial_call=True,
)
def reset_dashboard(n):
    if not n:
        return no_update, no_update, no_update, no_update
    status = [html.Span(className="status-dot"), html.Span("Ready")]
    return None, status, "status-badge ready", "00:00"


# ── Run Simulation ───────────────────────────────────────────────────────────

def _get_duration(dur_val, unit_label):
    """Convert duration value + unit to total minutes."""
    val = dur_val or 24
    if unit_label == "days":
        return int(val * 1440)
    elif unit_label == "weeks":
        return int(val * 7 * 1440)
    return int(val * 60)  # hours


def _get_scenario_kwargs(scenario_key):
    """Extract simulation kwargs from scenario."""
    sc = SCENARIOS[scenario_key]
    kwargs = {}
    if sc["fixture_overrides"]:
        kwargs["fixture_overrides"] = sc["fixture_overrides"]
    if sc["garden_time"] is not None:
        kwargs["garden_time"] = sc["garden_time"]
    if sc["leak_gpm"]:
        kwargs["leak_gpm"] = sc["leak_gpm"]
    return kwargs


@app.callback(
    [
        Output("sim-data-store", "data"),
        Output("sim-status", "children"),
        Output("sim-status", "className"),
        Output("sim-clock", "children"),
    ],
    Input("btn-run", "n_clicks"),
    [
        State("scenario-dropdown", "value"),
        State("pricing-dropdown", "value"),
        State("duration-value", "value"),
        State("duration-unit-label", "children"),
    ],
    prevent_initial_call=True,
)
def run_simulation(n_clicks, scenario_key, pricing, dur_val, unit_label):
    if not n_clicks:
        return no_update, no_update, no_update, no_update

    total_min = _get_duration(dur_val, unit_label)
    num_days = max(1, total_min // 1440)
    kwargs = _get_scenario_kwargs(scenario_key)

    state = run_single_day(
        seed=42, duration_minutes=total_min,
        warmup_minutes=60, pricing_scheme=pricing,
        num_days=num_days, **kwargs,
    )

    # Run leak detection
    alerts = detect_leaks(state)
    state.alerts = alerts

    # Serialize
    data = {
        "minute_log": state.minute_log,
        "fixture_liters": state.fixture_liters,
        "fixture_uses": state.fixture_uses,
        "fixture_active_minutes": state.fixture_active_minutes,
        "cumulative_liters": state.cumulative_liters,
        "cumulative_cost": state.cumulative_cost,
        "peak_flow_lpm": state.peak_flow_lpm,
        "hourly_liters": state.hourly_liters,
        "hourly_fixture_liters": state.hourly_fixture_liters,
        "drip_liters": state.drip_liters,
        "leak_liters": state.leak_liters,
        "total_minutes": state.total_minutes,
        "pricing_scheme": pricing,
        "alerts": [
            {
                "alert_type": a.alert_type, "severity": a.severity,
                "minute": a.minute, "time_str": a.time_str,
                "description": a.description, "flow_lpm": a.flow_lpm,
                "fixture": a.fixture, "duration_min": a.duration_min,
                "estimated_waste_liters": a.estimated_waste_liters,
            }
            for a in alerts
        ],
        "scenario": scenario_key,
    }

    end_h = total_min // 60
    clock = f"{end_h:02d}:00" if num_days <= 1 else f"Day {num_days}"
    status = [html.Span(className="status-dot"), html.Span("Complete")]
    return data, status, "status-badge complete", clock


# ── Simulate Leak ────────────────────────────────────────────────────────────

@app.callback(
    [
        Output("sim-data-store", "data", allow_duplicate=True),
        Output("sim-status", "children", allow_duplicate=True),
        Output("sim-status", "className", allow_duplicate=True),
        Output("sim-clock", "children", allow_duplicate=True),
    ],
    Input("btn-leak", "n_clicks"),
    [
        State("pricing-dropdown", "value"),
        State("duration-value", "value"),
        State("duration-unit-label", "children"),
    ],
    prevent_initial_call=True,
)
def simulate_leak(n_clicks, pricing, dur_val, unit_label):
    if not n_clicks:
        return no_update, no_update, no_update, no_update

    leak_params = inject_leak(seed=n_clicks)
    total_min = _get_duration(dur_val, unit_label)
    num_days = max(1, total_min // 1440)

    state = run_single_day(
        seed=42, duration_minutes=total_min,
        warmup_minutes=60, pricing_scheme=pricing,
        num_days=num_days,
        leak_gpm=leak_params["rate_lpm"],
        leak_onset=leak_params["onset_minute"],
    )

    alerts = detect_leaks(state)
    state.alerts = alerts

    data = {
        "minute_log": state.minute_log,
        "fixture_liters": state.fixture_liters,
        "fixture_uses": state.fixture_uses,
        "fixture_active_minutes": state.fixture_active_minutes,
        "cumulative_liters": state.cumulative_liters,
        "cumulative_cost": state.cumulative_cost,
        "peak_flow_lpm": state.peak_flow_lpm,
        "hourly_liters": state.hourly_liters,
        "hourly_fixture_liters": state.hourly_fixture_liters,
        "drip_liters": state.drip_liters,
        "leak_liters": state.leak_liters,
        "total_minutes": state.total_minutes,
        "pricing_scheme": pricing,
        "alerts": [
            {
                "alert_type": a.alert_type, "severity": a.severity,
                "minute": a.minute, "time_str": a.time_str,
                "description": a.description, "flow_lpm": a.flow_lpm,
                "fixture": a.fixture, "duration_min": a.duration_min,
                "estimated_waste_liters": a.estimated_waste_liters,
            }
            for a in alerts
        ],
        "scenario": "leak_test",
        "leak_params": leak_params,
    }

    status = [html.Span(className="status-dot"), html.Span("Leak Detected")]

    return data, status, "status-badge leak-detected", f"Leak @ {leak_params['onset_time']}"


# ── Update Tab 1: Live Overview ──────────────────────────────────────────────

@app.callback(
    [
        Output("flow-value", "children"),
        Output("flow-unit", "children"),
        Output("cumulative-value", "children"),
        Output("cumulative-unit", "children"),
        Output("cost-value", "children"),
        Output("cost-unit", "children"),
        Output("alerts-count-value", "children"),
        Output("alerts-count-unit", "children"),
        Output("fixture-cards-panel", "children"),
        Output("fixture-pie", "figure"),
        Output("alerts-panel", "children"),
        Output("leak-status-display", "children"),
        Output("bill-content", "children"),
        Output("timeline-chart", "figure"),
        Output("hbar-chart", "figure"),
    ],
    Input("sim-data-store", "data"),
    prevent_initial_call=True,
)
def update_dashboard(data):
    if not data:
        return [no_update] * 15

    fixture_liters = data["fixture_liters"]
    fixture_uses = data["fixture_uses"]
    fixture_active = data.get("fixture_active_minutes", {})
    alerts = data["alerts"]
    total_liters = data["cumulative_liters"]
    total_cost = data["cumulative_cost"]
    peak_flow = data["peak_flow_lpm"]
    hourly_liters = data.get("hourly_liters", {})
    hourly_fixture = data.get("hourly_fixture_liters", {})
    minute_log = data["minute_log"]

    # ── Metric cards ─────────────────────────────────────────────
    flow_val = f"{peak_flow:.1f}"
    flow_unit = "LPM (peak)"
    cum_val = f"{total_liters:.1f}"
    cum_unit = "liters"
    cost_val = f"₱{total_cost:.4f}"
    cost_unit = f"{data.get('pricing_scheme', 'flat')} rate"
    alert_val = str(len(alerts))
    alert_unit = "⚠️ alerts" if alerts else "none"

    # ── Fixture cards ────────────────────────────────────────────
    max_liters = max(fixture_liters.values()) if fixture_liters else 1
    cards = []
    for fk in FIXTURE_KEYS:
        liters = fixture_liters.get(fk, 0)
        uses = fixture_uses.get(fk, 0)
        active_min = fixture_active.get(fk, 0)
        pct = round(liters / total_liters * 100, 1) if total_liters > 0 else 0
        avg_per_use = round(liters / uses, 1) if uses > 0 else 0
        bar_pct = min(100, round(liters / max_liters * 100)) if max_liters > 0 else 0
        cost_fix = liters * 0.004  # flat rate approx

        # Status color
        status_cls = "status-green"
        if pct > 40:
            status_cls = "status-red"
        elif pct > 25:
            status_cls = "status-yellow"

        is_top = liters == max_liters and liters > 0
        card_cls = f"fixture-card {status_cls}"
        if is_top:
            card_cls += " top-consumer"

        color = FIXTURE_COLORS.get(fk, "#38bdf8")

        cards.append(html.Div(className=card_cls, children=[
            html.Div(className="fixture-card-header", children=[
                html.Div(className="fixture-card-name", children=[
                    html.Span(FIXTURE_ICONS.get(fk, "💧")),
                    FIXTURE_LABELS.get(fk, fk),
                ]),
                html.Div(f"{pct}%", className="fixture-card-pct",
                         style={"color": color}),
            ]),
            html.Div(className="fixture-progress", children=[
                html.Div(className="fixture-progress-fill",
                         style={"width": f"{bar_pct}%", "background": color}),
            ]),
            html.Div(f"{liters:.1f} L consumed", style={"fontSize": "14px", "fontWeight": "700", "color": "#f1f5f9"}),
            html.Div(className="fixture-card-stats", children=[
                html.Div(className="fixture-stat", children=[
                    html.Span(f"{uses}", className="fixture-stat-val"), " activations",
                ]),
                html.Div(className="fixture-stat", children=[
                    "Avg: ", html.Span(f"{avg_per_use} L", className="fixture-stat-val"),
                ]),
                html.Div(className="fixture-stat", children=[
                    "Cost: ", html.Span(f"₱{cost_fix:.2f}", className="fixture-stat-val"),
                ]),
                html.Div(className="fixture-stat", children=[
                    html.Span("🟢" if status_cls == "status-green" else ("🟡" if status_cls == "status-yellow" else "🔴")),
                    " Normal" if status_cls == "status-green" else (" High" if status_cls == "status-yellow" else " Overuse"),
                ]),
            ]),
        ]))

    fixture_cards = html.Div(className="fixture-grid", children=cards)

    # ── Donut chart ──────────────────────────────────────────────
    pie_labels, pie_values, pie_colors = [], [], []
    for fk in FIXTURE_KEYS:
        v = fixture_liters.get(fk, 0)
        if v > 0.1:
            pie_labels.append(FIXTURE_LABELS.get(fk, fk))
            pie_values.append(round(v, 1))
            pie_colors.append(FIXTURE_COLORS.get(fk, "#666"))

    pie_fig = go.Figure(go.Pie(
        labels=pie_labels, values=pie_values,
        marker=dict(colors=pie_colors), hole=0.55,
        textinfo="percent+label",
        textfont=dict(size=11, color="#f1f5f9"),
        hovertemplate="%{label}<br>%{value:.1f} L (%{percent})<extra></extra>",
    ))
    pie_fig.update_layout(**make_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10), height=380,
        annotations=[dict(
            text=f"<b>{total_liters:.0f} L</b><br>₱{total_cost:.2f}",
            x=0.5, y=0.5, font_size=16, font_color="#f1f5f9",
            showarrow=False,
        )],
    ))

    # ── Alerts panel ─────────────────────────────────────────────
    if alerts:
        alert_items = [
            html.Div(className=f"alert-item {a['severity']}", children=[
                html.Div(a["time_str"], className="alert-time"),
                html.Div(a["description"], className="alert-text"),
            ])
            for a in alerts
        ]
        alerts_panel = html.Div(className="alert-list", children=alert_items)
    else:
        alerts_panel = html.Div(className="no-alerts", children=[
            html.Span("✓", className="check-icon"),
            "No anomalies detected. System normal.",
        ])

    # Leak status
    has_high = any(a["severity"] == "high" for a in alerts)
    has_med = any(a["severity"] == "medium" for a in alerts)
    if has_high:
        leak_cls = "leak-status-panel leak-status-leak"
        leak_text = f"🔴 LEAK ALERT — {len(alerts)} alert(s) detected. Investigate immediately."
    elif has_med:
        leak_cls = "leak-status-panel leak-status-anomaly"
        leak_text = f"🟡 ANOMALY — Usage above normal baseline ({len(alerts)} alert(s))."
    else:
        leak_cls = "leak-status-panel leak-status-ok"
        leak_text = "🟢 NO LEAKS DETECTED — System operating normally."

    leak_status = html.Div(className=leak_cls, children=[leak_text])

    # ── Bill content ─────────────────────────────────────────────
    bill = compute_bill_summary(total_liters, data.get("pricing_scheme", "flat"))
    bill_content = html.Div([
        html.Div(f"Total: {total_liters:.1f} L", style={"fontSize": "14px", "fontWeight": "700", "color": "#f1f5f9", "marginBottom": "8px"}),
        html.Div(f"Scheme: {bill.get('scheme', 'Flat Rate')}", style={"fontSize": "12px", "color": "#94a3b8", "marginBottom": "8px"}),
        html.Div(f"₱{bill['total_cost_php']:.4f}", style={"fontSize": "24px", "fontWeight": "800", "color": "#34d399"}),
        html.Div(f"Monthly est: ₱{bill['total_cost_php'] * 30:.2f}", style={"fontSize": "12px", "color": "#64748b", "marginTop": "4px"}),
    ])

    # ── Timeline chart ───────────────────────────────────────────
    # Determine hourly keys (handle only 24h of data for display)
    display_hours = min(24, max(int(k) for k in hourly_liters.keys()) + 1) if hourly_liters else 24

    timeline_fig = go.Figure()
    for fk in FIXTURE_KEYS:
        y_vals = []
        for h in range(display_hours):
            hk = str(h) if str(h) in hourly_fixture.get(str(0), {}) else h
            val = 0
            h_key = str(h)
            if h_key in hourly_fixture:
                val = hourly_fixture[h_key].get(fk, 0)
            elif h in hourly_fixture:
                val = hourly_fixture[h].get(fk, 0)
            y_vals.append(round(val, 1))

        timeline_fig.add_trace(go.Bar(
            name=FIXTURE_LABELS.get(fk, fk),
            x=list(range(display_hours)),
            y=y_vals,
            marker_color=FIXTURE_COLORS.get(fk, "#666"),
            hovertemplate=f"{FIXTURE_LABELS.get(fk, fk)}<br>" + "Hour %{x}: %{y:.1f} L<extra></extra>",
        ))

    # Add overnight alert zone
    timeline_fig.add_vrect(x0=23, x1=24, fillcolor="rgba(239,68,68,0.05)", line_width=0,
                           annotation_text="Overnight", annotation_position="top left",
                           annotation_font_color="#EF4444")
    timeline_fig.add_vrect(x0=0, x1=5, fillcolor="rgba(239,68,68,0.05)", line_width=0)
    # Peak zones
    timeline_fig.add_vrect(x0=6, x1=9, fillcolor="rgba(56,189,248,0.03)", line_width=0,
                           annotation_text="AM Peak", annotation_position="top left",
                           annotation_font_color="#38bdf8")
    timeline_fig.add_vrect(x0=18, x1=21, fillcolor="rgba(251,191,36,0.03)", line_width=0,
                           annotation_text="PM Peak", annotation_position="top left",
                           annotation_font_color="#fbbf24")

    timeline_fig.update_layout(**make_layout(
        barmode="stack",
        xaxis_title="Hour of Day",
        yaxis_title="Liters",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
        height=400,
    ))

    # ── Horizontal bar chart ─────────────────────────────────────
    sorted_fixtures = sorted(
        [(fk, fixture_liters.get(fk, 0)) for fk in FIXTURE_KEYS],
        key=lambda x: x[1],
    )
    hbar_fig = go.Figure()
    hbar_fig.add_trace(go.Bar(
        y=[FIXTURE_LABELS.get(fk, fk) for fk, _ in sorted_fixtures],
        x=[v for _, v in sorted_fixtures],
        orientation="h",
        marker_color=[FIXTURE_COLORS.get(fk, "#666") for fk, _ in sorted_fixtures],
        text=[f"{v:.1f} L" for _, v in sorted_fixtures],
        textposition="outside",
        textfont=dict(color="#94a3b8", size=12),
        hovertemplate="%{y}<br>%{x:.1f} L<extra></extra>",
    ))
    hbar_fig.update_layout(**make_layout(
        showlegend=False, height=350,
        xaxis_title="Liters", yaxis_title="",
    ))

    return (
        flow_val, flow_unit, cum_val, cum_unit,
        cost_val, cost_unit, alert_val, alert_unit,
        fixture_cards, pie_fig, alerts_panel, leak_status,
        bill_content, timeline_fig, hbar_fig,
    )


# ── Run 30 Replications ─────────────────────────────────────────────────────

@app.callback(
    [
        Output("replication-content", "children"),
        Output("report-content", "children"),
        Output("summary-table-content", "children"),
        Output("utilization-panel", "children"),
        Output("baseline-chart", "figure"),
        Output("baseline-monitor", "children"),
        Output("baseline-store", "data"),
    ],
    Input("btn-replicate", "n_clicks"),
    [
        State("scenario-dropdown", "value"),
        State("pricing-dropdown", "value"),
    ],
    prevent_initial_call=True,
)
def run_replications_cb(n_clicks, scenario_key, pricing):
    if not n_clicks:
        return [no_update] * 7

    kwargs = _get_scenario_kwargs(scenario_key)

    states = run_replications(
        n=30, base_seed=1000,
        pricing_scheme=pricing, **kwargs,
    )
    df = states_to_dataframe(states)
    stats = compute_statistics(df)
    fixture_bk = compute_fixture_breakdown(df)
    util_data = compute_utilization(df)
    bill = generate_bill_summary(stats["daily_liters"]["mean"], pricing)
    recs = generate_recommendations(fixture_bk)

    # Baseline
    baseline = compute_baseline(states)

    gal = stats["daily_liters"]
    cost = stats["daily_cost"]

    # ── Stats table ──────────────────────────────────────────────
    stats_table = html.Table(className="bill-table", children=[
        html.Thead(html.Tr([
            html.Th("Metric"), html.Th("Mean"), html.Th("Std Dev"),
            html.Th("95% CI"), html.Th("Min"), html.Th("Max"),
        ])),
        html.Tbody([
            html.Tr([
                html.Td("Daily Liters"),
                html.Td(f'{gal["mean"]}'),
                html.Td(f'{gal["std"]}'),
                html.Td(f'{gal["ci_lower"]} – {gal["ci_upper"]}'),
                html.Td(f'{gal["min"]}'), html.Td(f'{gal["max"]}'),
            ]),
            html.Tr([
                html.Td("Daily Cost (₱)"),
                html.Td(f'₱{cost["mean"]}'),
                html.Td(f'₱{cost["std"]}'),
                html.Td(f'₱{cost["ci_lower"]} – ₱{cost["ci_upper"]}'),
                html.Td(f'₱{cost["min"]}'), html.Td(f'₱{cost["max"]}'),
            ]),
        ]),
    ])

    rep_fig = go.Figure()
    rep_fig.add_trace(go.Bar(
        x=df["replication"], y=df["total_liters"],
        marker=dict(color=df["total_liters"], colorscale=[[0, "#22d3ee"], [1, "#38bdf8"]]),
        hovertemplate="Rep %{x}<br>%{y:.1f} L<extra></extra>",
    ))
    rep_fig.add_hline(y=gal["mean"], line_dash="dash", line_color="#fbbf24", line_width=2,
                      annotation_text=f'Mean: {gal["mean"]} L', annotation_font_color="#fbbf24")
    rep_fig.update_layout(**make_layout(
        xaxis_title="Replication #",
        yaxis_title="Total Daily Liters", showlegend=False, height=280,
    ))

    rep_content = html.Div([stats_table, html.Div(style={"height": "16px"}),
                            dcc.Graph(figure=rep_fig, config={"displayModeBar": False})])

    # ── Report ───────────────────────────────────────────────────
    alert_counts = {"total": 0, "high": 0, "medium": 0}
    for s in states:
        s_alerts = detect_leaks(s)
        alert_counts["total"] += len(s_alerts)
        for a in s_alerts:
            if a.severity == "high":
                alert_counts["high"] += 1
            elif a.severity == "medium":
                alert_counts["medium"] += 1

    report_md = generate_report_text(stats, fixture_bk, bill, alert_counts, recs)
    report_content = dcc.Markdown(report_md, style={"lineHeight": "1.8"})

    # ── Summary table ────────────────────────────────────────────
    summary_rows = []
    total_l = 0
    total_u = 0
    for fb in fixture_bk:
        status = "🟢 Normal"
        if fb["pct_of_total"] > 40:
            status = "🔴 High"
        elif fb["pct_of_total"] > 25:
            status = "🟡 Elevated"
        cost_f = fb["avg_liters"] * 0.004
        summary_rows.append(html.Tr([
            html.Td(f'{fb["icon"]} {fb["name"]}'),
            html.Td(f'{fb["avg_liters"]:.1f} L'),
            html.Td(f'{fb["avg_uses"]:.0f}'),
            html.Td(f'{fb["avg_per_use"]:.1f} L'),
            html.Td(f'{fb["pct_of_total"]}%'),
            html.Td(f'₱{cost_f:.4f}'),
            html.Td(status),
        ]))
        total_l += fb["avg_liters"]
        total_u += fb["avg_uses"]

    summary_rows.append(html.Tr([
        html.Td("TOTAL", style={"fontWeight": "700"}),
        html.Td(f'{total_l:.1f} L', style={"fontWeight": "700"}),
        html.Td(f'{total_u:.0f}', style={"fontWeight": "700"}),
        html.Td("—"), html.Td("100%"),
        html.Td(f'₱{total_l * 0.004:.4f}', style={"fontWeight": "700"}),
        html.Td(""),
    ]))

    summary_table = html.Div([
        html.Table(className="summary-table", children=[
            html.Thead(html.Tr([
                html.Th("Fixture"), html.Th("Total Liters"), html.Th("# Uses"),
                html.Th("Avg L/Use"), html.Th("% of Total"), html.Th("Cost (₱)"),
                html.Th("Status"),
            ])),
            html.Tbody(summary_rows),
        ]),
        html.Div(className="recommendation-list", children=[
            html.Div(className="recommendation-item", children=[r])
            for r in recs
        ]),
    ])

    # ── Utilization gauges ───────────────────────────────────────
    gauge_cards = []
    for u in util_data:
        gauge_cards.append(html.Div(className="gauge-card", children=[
            html.Div(f"{u['icon']} {u['name']}", className="gauge-fixture-name"),
            html.Div(className="gauge-bar-container", children=[
                html.Div(className="gauge-bar-fill",
                         style={"width": f"{min(100, u['utilization_pct'])}%",
                                "background": u['color']}),
            ]),
            html.Div(f"{u['utilization_pct']}%", className="gauge-pct",
                      style={"color": u['color']}),
            html.Div(f"{u['active_min']:.0f} min active / {1380} min total", className="gauge-label"),
        ]))

    util_panel = html.Div(className="utilization-grid", children=gauge_cards)

    # ── Baseline chart ───────────────────────────────────────────
    baseline_x = list(range(24))
    baseline_y = [baseline.hourly_baseline.get(h, 0) for h in range(24)]

    bl_fig = go.Figure()
    bl_fig.add_trace(go.Scatter(
        x=baseline_x, y=baseline_y,
        fill="tozeroy", fillcolor="rgba(148,163,184,0.08)",
        line=dict(color="#64748b", width=2, dash="dash"),
        name="Baseline (avg)",
        hovertemplate="Hour %{x}<br>%{y:.1f} L<extra></extra>",
    ))
    # Overnight alert zone
    bl_fig.add_vrect(x0=23, x1=24, fillcolor="rgba(239,68,68,0.08)", line_width=0)
    bl_fig.add_vrect(x0=0, x1=5, fillcolor="rgba(239,68,68,0.08)", line_width=0,
                     annotation_text="🔴 Alert Zone (> 0.5 LPM = leak)",
                     annotation_position="top left", annotation_font_color="#EF4444",
                     annotation_font_size=10)
    bl_fig.update_layout(**make_layout(
        xaxis_title="Hour of Day", yaxis_title="Liters",
        showlegend=True, height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    ))

    baseline_monitor = html.Div(className="baseline-deviation", children=[
        f"Baseline: {baseline.historical_avg_daily:.1f} L/day | "
        f"Std Dev: ±{baseline.std_daily:.1f} L | "
        f"Anomaly Threshold: {baseline.historical_avg_daily * 1.5:.1f} L (150%)"
    ])

    # Store baseline
    bl_data = {
        "avg_daily": baseline.historical_avg_daily,
        "std_daily": baseline.std_daily,
    }

    return (rep_content, report_content, summary_table, util_panel,
            bl_fig, baseline_monitor, bl_data)


# ── Compare All Scenarios ────────────────────────────────────────────────────

@app.callback(
    [
        Output("whatif-content", "children"),
        Output("savings-chart", "figure"),
    ],
    Input("btn-compare", "n_clicks"),
    State("pricing-dropdown", "value"),
    prevent_initial_call=True,
)
def compare_scenarios_cb(n_clicks, pricing):
    if not n_clicks:
        return no_update, no_update

    results = run_all_scenarios(n_replications=10, base_seed=1000, pricing_scheme=pricing)
    comparison_df = compare_to_baseline(results)

    table_rows = []
    for _, row in comparison_df.iterrows():
        sav_l = row["Monthly Savings (L)"]
        sav_c = row["Monthly Savings (₱)"]
        l_cls = "positive" if sav_l > 0 else ("negative" if sav_l < 0 else "")
        c_cls = "positive" if sav_c > 0 else ("negative" if sav_c < 0 else "")
        l_disp = f"+{sav_l:.0f}" if sav_l > 0 else f"{sav_l:.0f}"
        c_disp = f"+₱{sav_c:.2f}" if sav_c > 0 else f"₱{sav_c:.2f}"
        table_rows.append(html.Tr([
            html.Td(row["Scenario"]),
            html.Td(f'{row["Daily Liters"]:.1f}'),
            html.Td(f'{row["Monthly Liters"]:.0f}'),
            html.Td(f'₱{row["Monthly Cost (₱)"]:.2f}'),
            html.Td(l_disp, className=l_cls),
            html.Td(c_disp, className=c_cls),
        ]))

    whatif_table = html.Table(className="comparison-table", children=[
        html.Thead(html.Tr([
            html.Th("Scenario"), html.Th("Daily (L)"),
            html.Th("Monthly (L)"), html.Th("Monthly Cost"),
            html.Th("L Saved/Mo"), html.Th("₱ Saved/Mo"),
        ])),
        html.Tbody(table_rows),
    ])

    scenarios = comparison_df["Scenario"].tolist()
    l_sav = comparison_df["Monthly Savings (L)"].tolist()
    c_sav = comparison_df["Monthly Savings (₱)"].tolist()

    sav_fig = go.Figure()
    sav_fig.add_trace(go.Bar(
        name="Liters Saved / Month", x=scenarios, y=l_sav,
        marker_color=["#34d399" if v >= 0 else "#fb7185" for v in l_sav],
        hovertemplate="%{x}<br>%{y:.0f} L<extra></extra>",
    ))
    sav_fig.add_trace(go.Bar(
        name="₱ Saved / Month", x=scenarios, y=c_sav, yaxis="y2",
        marker_color=["#38bdf8" if v >= 0 else "#fbbf24" for v in c_sav],
        hovertemplate="%{x}<br>₱%{y:.2f}<extra></extra>",
    ))
    sav_fig.update_layout(**make_layout(
        barmode="group",
        yaxis=dict(title="Liters Saved", gridcolor=GRID_COLOR),
        yaxis2=dict(title="₱ Saved", overlaying="y", side="right", gridcolor=GRID_COLOR),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        height=320,
    ))

    return whatif_table, sav_fig


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  💧 Single Household Water Usage Simulation")
    print("  CSE 10/L – Modeling & Simulation")
    print("  University of Mindanao")
    print("=" * 60)
    print("\n  Dashboard running at: http://127.0.0.1:8050\n")
    app.run(debug=False, host="127.0.0.1", port=8050)
