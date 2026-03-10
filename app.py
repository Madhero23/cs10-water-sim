"""
app.py – Dash Interactive Dashboard
Single Household Water Usage Simulation
CSE 10/L – Modeling and Simulation | University of Mindanao
"""

import dash
from dash import html, dcc, Input, Output, State, callback, no_update
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import json

from simulation import run_single_day, run_replications, states_to_dataframe, SimState
from fixtures import FIXTURE_LIBRARY
from pricing import compute_monthly_bill, gallons_to_m3
from leak_detector import LeakAlert
from what_if import SCENARIOS, run_all_scenarios, compare_to_baseline
from report import (
    compute_statistics, compute_fixture_breakdown,
    generate_bill_summary, generate_report_text,
)


# ── Plotly Theme ─────────────────────────────────────────────────────────────

PLOT_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#94a3b8", size=12),
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            zerolinecolor="rgba(255,255,255,0.06)",
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            zerolinecolor="rgba(255,255,255,0.06)",
        ),
        colorway=[
            "#38bdf8", "#22d3ee", "#34d399", "#a78bfa",
            "#fbbf24", "#fb7185", "#fb923c",
        ],
    )
)

FIXTURE_COLORS = {
    "shower": "#38bdf8",
    "faucet": "#22d3ee",
    "toilet": "#a78bfa",
    "washing_machine": "#fbbf24",
    "dishwasher": "#fb923c",
    "garden": "#34d399",
    "leak": "#fb7185",
}

FIXTURE_LABELS = {
    "shower": "Shower",
    "faucet": "Faucet",
    "toilet": "Toilet",
    "washing_machine": "Washing Machine",
    "dishwasher": "Dishwasher",
    "garden": "Garden / Irrigation",
    "leak": "Leak",
}


# ── Dash App ─────────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__,
    title="Water Usage Simulation",
    update_title=None,
    suppress_callback_exceptions=True,
)

app.index_string = '''<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <meta name="description" content="Single Household Water Usage Simulation – CSE 10/L Modeling & Simulation">
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


# ── App Layout ───────────────────────────────────────────────────────────────

app.layout = html.Div(id="app-container", children=[

    # Hidden data stores
    dcc.Store(id="sim-data-store"),
    dcc.Store(id="scenario-results-store"),
    dcc.Store(id="replication-data-store"),

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
        dcc.Loading(id="loading-run", type="circle", color="#38bdf8", children=[
            html.Button("▶  Run Simulation", id="btn-run", className="btn btn-primary", n_clicks=0),
        ]),
        dcc.Loading(id="loading-rep", type="circle", color="#22d3ee", children=[
            html.Button("📊  Run 30 Replications", id="btn-replicate", className="btn btn-secondary", n_clicks=0),
        ]),
        html.Div(className="controls-separator"),
        dcc.Dropdown(
            id="scenario-dropdown",
            options=[
                {"label": sc["label"], "value": key}
                for key, sc in SCENARIOS.items()
            ],
            value="baseline",
            clearable=False,
            className="dropdown-scenario",
            style={
                "width": "280px",
                "backgroundColor": "rgba(255,255,255,0.06)",
                "color": "#f1f5f9",
                "border": "1px solid rgba(255,255,255,0.08)",
                "borderRadius": "8px",
            },
        ),
        dcc.Loading(id="loading-compare", type="circle", color="#a78bfa", children=[
            html.Button("🔄  Compare All Scenarios", id="btn-compare", className="btn btn-secondary", n_clicks=0),
        ]),
    ]),

    # ── Dashboard Grid ───────────────────────────────────────────
    html.Div(className="dashboard-grid", children=[

        # Row 1: Metric cards
        metric_card("flow", "Current Flow Rate", "🌊", "cyan"),
        metric_card("cumulative", "Cumulative Usage", "📊", "blue"),
        metric_card("cost", "Projected Monthly Cost", "💰", "emerald"),
        metric_card("alerts-count", "Active Alerts", "⚠️", "amber"),

        # Row 2: Timeline + Fixture breakdown
        html.Div(className="card span-8", children=[
            html.Div(className="card-header", children=[
                html.Div(className="card-title", children=[
                    html.Span("📈", className="card-title-icon"),
                    "24-Hour Flow Timeline",
                ]),
            ]),
            dcc.Graph(id="timeline-chart", config={"displayModeBar": False},
                      style={"height": "320px"}),
        ]),
        html.Div(className="card span-4", children=[
            html.Div(className="card-header", children=[
                html.Div(className="card-title", children=[
                    html.Span("🍩", className="card-title-icon"),
                    "Fixture Breakdown",
                ]),
            ]),
            dcc.Graph(id="fixture-pie", config={"displayModeBar": False},
                      style={"height": "320px"}),
        ]),

        # Row 3: Replication stats + Leak alerts
        html.Div(className="card span-7", children=[
            html.Div(className="card-header", children=[
                html.Div(className="card-title", children=[
                    html.Span("📊", className="card-title-icon"),
                    "Replication Statistics (30 Runs)",
                ]),
            ]),
            html.Div(id="replication-content", children=[
                html.Div(className="loading-overlay", children=[
                    html.Div("Click 'Run 30 Replications' to generate statistics.",
                             className="loading-text"),
                ]),
            ]),
        ]),
        html.Div(className="card span-5", children=[
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

        # Row 4: What-If Comparison + Monthly Bill
        html.Div(className="card span-8", children=[
            html.Div(className="card-header", children=[
                html.Div(className="card-title", children=[
                    html.Span("🔬", className="card-title-icon"),
                    "What-If Scenario Comparison",
                ]),
            ]),
            html.Div(id="whatif-content", children=[
                html.Div(className="loading-overlay", children=[
                    html.Div("Click 'Compare All Scenarios' to run projections.",
                             className="loading-text"),
                ]),
            ]),
        ]),
        html.Div(className="card span-4", children=[
            html.Div(className="card-header", children=[
                html.Div(className="card-title", children=[
                    html.Span("🧾", className="card-title-icon"),
                    "Monthly Bill Summary",
                ]),
            ]),
            html.Div(id="bill-content", children=[
                html.Div(className="loading-overlay", children=[
                    html.Div("Run simulation to see bill breakdown.",
                             className="loading-text"),
                ]),
            ]),
        ]),

        # Row 5: What-If bar chart
        html.Div(className="card span-12", children=[
            html.Div(className="card-header", children=[
                html.Div(className="card-title", children=[
                    html.Span("📉", className="card-title-icon"),
                    "Scenario Savings Comparison",
                ]),
            ]),
            dcc.Graph(id="savings-chart", config={"displayModeBar": False},
                      style={"height": "350px"}),
        ]),

        # Row 6: Full Report
        html.Div(className="card span-12", children=[
            html.Div(className="card-header", children=[
                html.Div(className="card-title", children=[
                    html.Span("📝", className="card-title-icon"),
                    "Simulation Report",
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
])


# ── Callbacks ────────────────────────────────────────────────────────────────

@app.callback(
    [
        Output("sim-data-store", "data"),
        Output("sim-status", "children"),
        Output("sim-status", "className"),
        Output("sim-clock", "children"),
    ],
    Input("btn-run", "n_clicks"),
    State("scenario-dropdown", "value"),
    prevent_initial_call=True,
)
def run_simulation(n_clicks, scenario_key):
    """Run a single 24-hour simulation."""
    if not n_clicks:
        return no_update, no_update, no_update, no_update

    sc = SCENARIOS[scenario_key]
    kwargs = {}
    if sc["fixture_overrides"]:
        kwargs["fixture_overrides"] = sc["fixture_overrides"]
    if sc["garden_time"] is not None:
        kwargs["garden_time"] = sc["garden_time"]
    if sc["leak_gpm"]:
        kwargs["leak_gpm"] = sc["leak_gpm"]

    state = run_single_day(seed=42, **kwargs)

    # Serialize state for store
    data = {
        "minute_log": state.minute_log,
        "fixture_gallons": state.fixture_gallons,
        "cumulative_gallons": state.cumulative_gallons,
        "cumulative_cost": state.cumulative_cost,
        "flow_gpm": state.flow_gpm,
        "alerts": [
            {
                "alert_type": a.alert_type,
                "severity": a.severity,
                "minute": a.minute,
                "time_str": a.time_str,
                "description": a.description,
                "flow_gpm": a.flow_gpm,
            }
            for a in state.alerts
        ],
        "scenario": scenario_key,
    }

    status = [html.Span(className="status-dot"), html.Span("Complete")]
    return data, status, "status-badge complete", "23:59"


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
        Output("timeline-chart", "figure"),
        Output("fixture-pie", "figure"),
        Output("alerts-panel", "children"),
        Output("bill-content", "children"),
    ],
    Input("sim-data-store", "data"),
    prevent_initial_call=True,
)
def update_dashboard(data):
    """Update all dashboard panels from simulation data."""
    if not data:
        return [no_update] * 12

    minute_log = data["minute_log"]
    fixture_gallons = data["fixture_gallons"]
    alerts = data["alerts"]

    last = minute_log[-1]

    # Metric cards
    flow_val = f"{last['flow_gpm']:.1f}"
    flow_unit = "GPM"
    cum_val = f"{last['cumulative_gallons']:.0f}"
    cum_unit = f"gallons ({last['cumulative_m3']:.2f} m³)"
    cost_val = f"₱{last['projected_monthly_cost']:,.2f}"
    cost_unit = "projected monthly"
    alert_val = str(len(alerts))
    alert_unit = "high" if any(a["severity"] == "high" for a in alerts) else "normal"

    # Timeline chart
    df = pd.DataFrame(minute_log)
    timeline_fig = go.Figure()
    timeline_fig.add_trace(go.Scatter(
        x=df["hour"],
        y=df["flow_gpm"],
        fill="tozeroy",
        fillcolor="rgba(56, 189, 248, 0.1)",
        line=dict(color="#38bdf8", width=2),
        name="Flow Rate (GPM)",
        hovertemplate="Time: %{x:.1f}h<br>Flow: %{y:.2f} GPM<extra></extra>",
    ))
    timeline_fig.update_layout(
        **PLOT_TEMPLATE["layout"],
        xaxis_title="Hour of Day",
        yaxis_title="Flow Rate (GPM)",
        showlegend=False,
        xaxis=dict(
            **PLOT_TEMPLATE["layout"]["xaxis"],
            range=[0, 24],
            dtick=3,
        ),
    )

    # Fixture pie chart
    pie_labels = []
    pie_values = []
    pie_colors = []
    for key, gal in fixture_gallons.items():
        if gal > 0.01:
            pie_labels.append(FIXTURE_LABELS.get(key, key))
            pie_values.append(round(gal, 2))
            pie_colors.append(FIXTURE_COLORS.get(key, "#666"))

    pie_fig = go.Figure()
    pie_fig.add_trace(go.Pie(
        labels=pie_labels,
        values=pie_values,
        marker=dict(colors=pie_colors),
        hole=0.55,
        textinfo="percent+label",
        textfont=dict(size=11, color="#f1f5f9"),
        hovertemplate="%{label}<br>%{value:.1f} gal (%{percent})<extra></extra>",
    ))
    pie_fig.update_layout(
        **PLOT_TEMPLATE["layout"],
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
    )

    # Alerts panel
    if alerts:
        alert_items = []
        for a in alerts:
            alert_items.append(
                html.Div(className=f"alert-item {a['severity']}", children=[
                    html.Div(a["time_str"], className="alert-time"),
                    html.Div(a["description"], className="alert-text"),
                ])
            )
        alerts_panel = html.Div(className="alert-list", children=alert_items)
    else:
        alerts_panel = html.Div(className="no-alerts", children=[
            html.Span("✓", className="check-icon"),
            "No anomalies detected. System normal.",
        ])

    # Bill summary
    daily_gal = last["cumulative_gallons"]
    bill = compute_monthly_bill(daily_gal * 30)
    bill_rows = []
    for tier in bill["tier_breakdown"]:
        bill_rows.append(html.Tr([
            html.Td(tier["tier_label"]),
            html.Td(f'{tier["m3"]} m³'),
            html.Td(f'₱{tier["rate"]}' if tier["rate"] != "flat" else "Flat"),
            html.Td(f'₱{tier["cost"]:,.2f}'),
        ]))
    bill_rows.append(html.Tr([
        html.Td("Total", colSpan=3, style={"fontWeight": "700"}),
        html.Td(f'₱{bill["total_cost_php"]:,.2f}', style={"fontWeight": "700"}),
    ]))

    bill_content = html.Table(className="bill-table", children=[
        html.Thead(html.Tr([
            html.Th("Tier"),
            html.Th("Volume"),
            html.Th("Rate"),
            html.Th("Cost"),
        ])),
        html.Tbody(bill_rows),
    ])

    return (
        flow_val, flow_unit,
        cum_val, cum_unit,
        cost_val, cost_unit,
        alert_val, alert_unit,
        timeline_fig, pie_fig,
        alerts_panel, bill_content,
    )


@app.callback(
    [
        Output("replication-content", "children"),
        Output("report-content", "children"),
    ],
    Input("btn-replicate", "n_clicks"),
    State("scenario-dropdown", "value"),
    prevent_initial_call=True,
)
def run_replications_cb(n_clicks, scenario_key):
    """Run 30 replications, display statistics AND generate report in one pass."""
    if not n_clicks:
        return no_update, no_update

    sc = SCENARIOS[scenario_key]
    kwargs = {}
    if sc["fixture_overrides"]:
        kwargs["fixture_overrides"] = sc["fixture_overrides"]
    if sc["garden_time"] is not None:
        kwargs["garden_time"] = sc["garden_time"]
    if sc["leak_gpm"]:
        kwargs["leak_gpm"] = sc["leak_gpm"]

    states = run_replications(n=30, base_seed=1000, **kwargs)
    df = states_to_dataframe(states)
    stats = compute_statistics(df)
    fixture_bk = compute_fixture_breakdown(df)
    bill = generate_bill_summary(stats["daily_gallons"]["mean"])

    # ── Stats table ──────────────────────────────────────────────
    gal = stats["daily_gallons"]
    cost = stats["monthly_cost"]

    stats_table = html.Table(className="bill-table", children=[
        html.Thead(html.Tr([
            html.Th("Metric"),
            html.Th("Mean"),
            html.Th("Std Dev"),
            html.Th("95% CI"),
            html.Th("Min"),
            html.Th("Max"),
        ])),
        html.Tbody([
            html.Tr([
                html.Td("Daily Gallons"),
                html.Td(f'{gal["mean"]}'),
                html.Td(f'{gal["std"]}'),
                html.Td(f'{gal["ci_lower"]} – {gal["ci_upper"]}'),
                html.Td(f'{gal["min"]}'),
                html.Td(f'{gal["max"]}'),
            ]),
            html.Tr([
                html.Td("Monthly Cost (₱)"),
                html.Td(f'₱{cost["mean"]}'),
                html.Td(f'₱{cost["std"]}'),
                html.Td(f'₱{cost["ci_lower"]} – ₱{cost["ci_upper"]}'),
                html.Td(f'₱{cost["min"]}'),
                html.Td(f'₱{cost["max"]}'),
            ]),
        ]),
    ])

    # Replication bar chart
    rep_fig = go.Figure()
    rep_fig.add_trace(go.Bar(
        x=df["replication"],
        y=df["total_gallons"],
        marker=dict(
            color=df["total_gallons"],
            colorscale=[[0, "#22d3ee"], [1, "#38bdf8"]],
        ),
        hovertemplate="Rep %{x}<br>%{y:.1f} gallons<extra></extra>",
    ))
    rep_fig.add_hline(
        y=gal["mean"], line_dash="dash",
        line_color="#fbbf24", line_width=2,
        annotation_text=f'Mean: {gal["mean"]} gal',
        annotation_font_color="#fbbf24",
    )
    rep_fig.update_layout(
        **PLOT_TEMPLATE["layout"],
        xaxis_title="Replication #",
        yaxis_title="Total Daily Gallons",
        showlegend=False,
        height=280,
    )

    rep_content = html.Div([
        stats_table,
        html.Div(style={"height": "16px"}),
        dcc.Graph(figure=rep_fig, config={"displayModeBar": False}),
    ])

    # ── Report ───────────────────────────────────────────────────
    alert_counts = {"total": 0, "high": 0, "medium": 0}
    for s in states:
        alert_counts["total"] += len(s.alerts)
        for a in s.alerts:
            if a.severity == "high":
                alert_counts["high"] += 1
            elif a.severity == "medium":
                alert_counts["medium"] += 1

    report_md = generate_report_text(stats, fixture_bk, bill, alert_counts)
    report_content = dcc.Markdown(report_md, style={"lineHeight": "1.8"})

    return rep_content, report_content


@app.callback(
    [
        Output("whatif-content", "children"),
        Output("savings-chart", "figure"),
    ],
    Input("btn-compare", "n_clicks"),
    prevent_initial_call=True,
)
def compare_scenarios_cb(n_clicks):
    """Run all what-if scenarios and display comparison."""
    if not n_clicks:
        return no_update, no_update

    results = run_all_scenarios(n_replications=10, base_seed=1000)
    comparison_df = compare_to_baseline(results)

    # Comparison table
    table_rows = []
    for _, row in comparison_df.iterrows():
        savings_gal = row["Monthly Savings (gal)"]
        savings_cost = row["Monthly Savings (₱)"]

        gal_class = "positive" if savings_gal > 0 else ("negative" if savings_gal < 0 else "")
        cost_class = "positive" if savings_cost > 0 else ("negative" if savings_cost < 0 else "")

        gal_display = f"+{savings_gal:.0f}" if savings_gal > 0 else f"{savings_gal:.0f}"
        cost_display = f"+₱{savings_cost:.2f}" if savings_cost > 0 else f"₱{savings_cost:.2f}"

        table_rows.append(html.Tr([
            html.Td(row["Scenario"]),
            html.Td(f'{row["Daily Gallons"]:.1f}'),
            html.Td(f'{row["Monthly Gallons"]:.0f}'),
            html.Td(f'₱{row["Monthly Cost (₱)"]:.2f}'),
            html.Td(gal_display, className=gal_class),
            html.Td(cost_display, className=cost_class),
        ]))

    whatif_table = html.Table(className="comparison-table", children=[
        html.Thead(html.Tr([
            html.Th("Scenario"),
            html.Th("Daily (gal)"),
            html.Th("Monthly (gal)"),
            html.Th("Monthly Cost"),
            html.Th("Gal Saved/Mo"),
            html.Th("₱ Saved/Mo"),
        ])),
        html.Tbody(table_rows),
    ])

    # Savings bar chart
    scenarios = comparison_df["Scenario"].tolist()
    gal_savings = comparison_df["Monthly Savings (gal)"].tolist()
    cost_savings = comparison_df["Monthly Savings (₱)"].tolist()

    savings_fig = go.Figure()
    savings_fig.add_trace(go.Bar(
        name="Gallons Saved / Month",
        x=scenarios,
        y=gal_savings,
        marker_color=["#34d399" if v >= 0 else "#fb7185" for v in gal_savings],
        yaxis="y",
        hovertemplate="%{x}<br>%{y:.0f} gal<extra></extra>",
    ))
    savings_fig.add_trace(go.Bar(
        name="₱ Saved / Month",
        x=scenarios,
        y=cost_savings,
        marker_color=["#38bdf8" if v >= 0 else "#fbbf24" for v in cost_savings],
        yaxis="y2",
        hovertemplate="%{x}<br>₱%{y:.2f}<extra></extra>",
    ))
    savings_fig.update_layout(
        **PLOT_TEMPLATE["layout"],
        barmode="group",
        yaxis=dict(
            title="Gallons Saved",
            **PLOT_TEMPLATE["layout"]["yaxis"],
        ),
        yaxis2=dict(
            title="₱ Saved",
            overlaying="y",
            side="right",
            gridcolor="rgba(255,255,255,0.04)",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11),
        ),
        height=320,
    )

    return whatif_table, savings_fig


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  💧 Single Household Water Usage Simulation")
    print("  CSE 10/L – Modeling & Simulation")
    print("  University of Mindanao")
    print("=" * 60)
    print("\n  Dashboard running at: http://127.0.0.1:8050\n")
    app.run(debug=False, host="127.0.0.1", port=8050)
