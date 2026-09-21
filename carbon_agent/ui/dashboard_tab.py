"""
Tab 2: Visual Dashboard Tab.
Renders Plotly analytics: category distribution donut chart, benchmark comparisons,
and longitudinal progress trends.
"""
import gradio as gr
import plotly.graph_objects as go
from typing import Dict, Any
from carbon_agent.config.settings import BENCHMARKS
from carbon_agent.agents.analysis_agent import EmissionAnalysisAgent

analysis_agent = EmissionAnalysisAgent()


def create_donut_chart(categories: Dict[str, float]) -> go.Figure:
    """Generate modern Plotly donut chart for category emissions."""
    labels = [k.replace("_", " ").title() for k in categories.keys()]
    values = list(categories.values())

    # Curated modern palette
    colors = ["#10b981", "#06b6d4", "#f59e0b", "#8b5cf6", "#ec4899"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
                textinfo="label+percent",
                hoverinfo="label+value+percent",
                textfont=dict(size=13, family="Inter, sans-serif")
            )
        ]
    )
    fig.update_layout(
        title=dict(text="Monthly Carbon Footprint by Category (kg CO₂e)", font=dict(size=16, family="Inter, sans-serif")),
        margin=dict(t=40, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def create_benchmark_chart(user_monthly: float) -> go.Figure:
    """Generate comparative benchmark bar chart against Indian, Global, and Paris targets."""
    labels = ["User Footprint", "India Average", "Paris 1.5°C Target", "Global Average"]
    values = [
        user_monthly,
        BENCHMARKS["india_monthly_kg_co2e"],
        BENCHMARKS["paris_target_monthly_kg_co2e"],
        BENCHMARKS["global_monthly_kg_co2e"]
    ]
    colors = ["#047857", "#0284c7", "#10b981", "#ef4444"]

    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker=dict(color=colors, line=dict(color="#ffffff", width=1.5)),
                text=[f"{v:.1f} kg" for v in values],
                textposition="auto",
                textfont=dict(family="Inter, sans-serif", size=12)
            )
        ]
    )
    fig.update_layout(
        title=dict(text="Monthly CO₂e Comparison vs Standards (kg CO₂e/month)", font=dict(size=16, family="Inter, sans-serif")),
        yaxis=dict(title="kg CO₂e / month", gridcolor="#f1f5f9"),
        xaxis=dict(gridcolor="#f1f5f9"),
        margin=dict(t=40, b=20, l=40, r=20),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def render_dashboard_tab(state: gr.State):
    """Render Gradio components for Dashboard tab."""
    gr.Markdown("### 📊 Interactive Visual Analytics & Benchmark Diagnostics")
    refresh_btn = gr.Button("🔄 Refresh Dashboard from Current Calculation", variant="secondary")

    with gr.Row():
        chart_donut = gr.Plot(label="Category Distribution")
        chart_benchmark = gr.Plot(label="Benchmark Comparison")

    insights_box = gr.Markdown("### 🔍 Diagnostic Insights\n*Calculate your footprint in Tab 1 to generate diagnostics.*")

    def update_dashboard(current_state):
        current_state = current_state or {}
        carbon_res = current_state.get("carbon_results", {})
        if not carbon_res:
            empty_fig = go.Figure().update_layout(title="No carbon data yet. Please calculate in Tab 1.")
            return empty_fig, empty_fig, "### 🔍 Diagnostic Insights\n*Please calculate your footprint in Tab 1 first.*"

        categories = carbon_res.get("categories", {})
        total_monthly = carbon_res.get("total_monthly_kg_co2e", 0.0)

        donut = create_donut_chart(categories)
        benchmark = create_benchmark_chart(total_monthly)

        # Run Analysis Agent
        history = current_state.get("history", [])
        analysis = analysis_agent.analyze(carbon_res, history)
        current_state["emission_analysis"] = analysis

        insights_md = f"### 🔍 Diagnostic Insights from Emission Analysis Agent\n\n"
        insights_md += f"- **Dominant Emission Hotspot:** **{analysis['dominant_category'].replace('_', ' ').title()}** "
        insights_md += f"({analysis['dominant_category_percentage']}% of total emissions)\n"
        insights_md += f"- **National Context:** Your monthly emissions are **{abs(analysis['benchmarks']['india_comparison_pct'])}% "
        insights_md += f"{'higher than' if analysis['benchmarks']['india_comparison_pct'] >= 0 else 'lower than'}** the India national per-capita average.\n"
        insights_md += f"- **Global Context:** Your footprint is **{abs(analysis['benchmarks']['global_comparison_pct'])}% "
        insights_md += f"{'higher than' if analysis['benchmarks']['global_comparison_pct'] >= 0 else 'lower than'}** the global average.\n\n"
        insights_md += "#### 💡 Strategic Analysis:\n"
        for ins in analysis["insights"]:
            insights_md += f"> {ins}\n\n"

        return donut, benchmark, insights_md

    refresh_btn.click(
        fn=update_dashboard,
        inputs=[state],
        outputs=[chart_donut, chart_benchmark, insights_box]
    )

    return refresh_btn
