"""
Tab 1: Carbon Calculator Tab.
Provides structured activity inputs, optional natural language extraction via Input Agent,
and deterministic calculation output with category breakdown.
"""
import gradio as gr
from typing import Dict, Any, Tuple
from carbon_agent.agents.input_agent import InputIntentAgent
from carbon_agent.agents.validation_agent import ValidationAgent
from carbon_agent.tools.carbon_calculator import calculate_carbon_footprint

input_agent = InputIntentAgent()
validation_agent = ValidationAgent()


def render_calculator_tab(state: gr.State):
    """Render Gradio components for the Carbon Calculator tab."""
    gr.Markdown("### 🧮 Personal Carbon Footprint Accounting")
    gr.Markdown("Enter your monthly activities below, or type a natural-language description for the **Input / Intent Agent** to parse.")

    # 1. Natural Language Extraction Section
    with gr.Accordion("🤖 Optional: Natural Language Input (Input / Intent Agent)", open=True):
        with gr.Row():
            nl_input = gr.Textbox(
                label="Describe your lifestyle in plain English:",
                placeholder="e.g., I drive my petrol car 25 km daily, use 180 units of electricity, consume 1 LPG cylinder every two months, eat vegetarian food, and recycle 20% of waste.",
                lines=2,
                scale=4
            )
            parse_btn = gr.Button("🔍 Parse with Agent", variant="secondary", scale=1)
        nl_feedback = gr.Markdown(visible=False)

    # 2. Structured Inputs
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Accordion("🚗 Transportation (km / month)", open=True):
                petrol_km = gr.Number(label="Petrol Car (km/mo)", value=350, minimum=0)
                diesel_km = gr.Number(label="Diesel Car (km/mo)", value=0, minimum=0)
                motorcycle_km = gr.Number(label="Motorcycle / 2-Wheeler (km/mo)", value=120, minimum=0)
                ev_km = gr.Number(label="Electric Car / EV (km/mo)", value=0, minimum=0)
                bus_km = gr.Number(label="City Bus (km/mo)", value=50, minimum=0)
                train_km = gr.Number(label="Train / Metro (km/mo)", value=80, minimum=0)
                flights_km = gr.Number(label="Domestic Flights (km/mo)", value=0, minimum=0)

        with gr.Column(scale=1):
            with gr.Accordion("⚡ Electricity & Energy", open=True):
                electricity_kwh = gr.Number(label="Grid Electricity (kWh / Units per month)", value=180, minimum=0)
                solar_kwh = gr.Number(label="Rooftop Solar Offset (kWh generated/month)", value=0, minimum=0)

            with gr.Accordion("🔥 Household Cooking Fuel", open=True):
                lpg_cylinders = gr.Number(label="LPG Cylinders per Month (14.2 kg standard)", value=1.0, minimum=0, step=0.1)
                natural_gas_scm = gr.Number(label="Piped Natural Gas (SCM / m³ per month)", value=0, minimum=0)

            with gr.Accordion("🥗 Food & Waste", open=True):
                diet_choice = gr.Dropdown(
                    label="Primary Dietary Pattern",
                    choices=[
                        ("Heavy Meat (>100g/day)", "heavy_meat"),
                        ("Medium Meat (50-100g/day)", "medium_meat"),
                        ("Pescatarian (Fish & Dairy)", "pescatarian"),
                        ("Vegetarian (Lacto-Ovo)", "vegetarian"),
                        ("Vegan (100% Plant-Based)", "vegan")
                    ],
                    value="vegetarian"
                )
                waste_kg = gr.Number(label="Municipal Solid Waste (kg / month)", value=35, minimum=0)
                recycling_pct = gr.Slider(label="Dry Waste Recycled (%)", minimum=0, maximum=100, value=20, step=5)
                composting_pct = gr.Slider(label="Organic Waste Composted (%)", minimum=0, maximum=100, value=10, step=5)

    calculate_btn = gr.Button("⚡ Calculate Carbon Footprint", variant="primary", size="lg")

    # 3. Calculation Results Display
    with gr.Row():
        with gr.Column(scale=1):
            kpi_monthly = gr.Markdown("### Monthly CO₂e\n## -- kg")
        with gr.Column(scale=1):
            kpi_annual = gr.Markdown("### Annualized CO₂e\n## -- tonnes")
        with gr.Column(scale=1):
            kpi_hotspot = gr.Markdown("### Primary Hotspot\n## --")

    breakdown_display = gr.Markdown("")
    calc_notes_display = gr.Markdown("")

    # Callback: Natural Language Parsing
    def on_parse_nl(text, current_state):
        result = input_agent.parse_user_text(text)
        struct = result["structured_data"]
        
        # Prepare updates for UI input elements
        trans = struct.get("transportation", {})
        elec = struct.get("electricity", {})
        fuel = struct.get("household_fuel", {})
        food = struct.get("food", {})
        waste = struct.get("waste", {})

        p_km = trans.get("petrol_car_km", gr.update())
        d_km = trans.get("diesel_car_km", gr.update())
        m_km = trans.get("motorcycle_km", gr.update())
        e_km = trans.get("electric_car_km", gr.update())
        b_km = trans.get("bus_km", gr.update())
        t_km = trans.get("train_km", gr.update())
        f_km = trans.get("flight_domestic_km", gr.update())

        e_kwh = elec.get("consumption_kwh", gr.update())
        s_kwh = elec.get("solar_kwh", gr.update())

        lpg_cyl = fuel.get("lpg_cylinders", gr.update())
        gas = fuel.get("natural_gas_scm", gr.update())

        diet = food.get("diet_type", gr.update())

        w_kg = waste.get("waste_kg", gr.update())
        r_pct = waste.get("recycling_pct", gr.update())
        c_pct = waste.get("composting_pct", gr.update())

        msg = "✅ **Input / Intent Agent Extracted:**\n"
        if result["detected_intents"]:
            msg += f"- *Intents:* {', '.join(result['detected_intents'])}\n"
        if result["missing_information"]:
            msg += f"- *Unspecified Info:* {'; '.join(result['missing_information'])}\n"

        return (
            p_km, d_km, m_km, e_km, b_km, t_km, f_km,
            e_kwh, s_kwh, lpg_cyl, gas, diet,
            w_kg, r_pct, c_pct,
            gr.update(value=msg, visible=True)
        )

    parse_btn.click(
        fn=on_parse_nl,
        inputs=[nl_input, state],
        outputs=[
            petrol_km, diesel_km, motorcycle_km, ev_km, bus_km, train_km, flights_km,
            electricity_kwh, solar_kwh, lpg_cylinders, natural_gas_scm, diet_choice,
            waste_kg, recycling_pct, composting_pct,
            nl_feedback
        ]
    )

    # Callback: Calculate Carbon Footprint
    def on_calculate(
        p_km, d_km, m_km, ev_km, b_km, t_km, f_km,
        e_kwh, s_kwh, lpg_cyl, gas, diet,
        w_kg, r_pct, c_pct,
        current_state
    ):
        raw_data = {
            "transportation": {
                "petrol_car_km": p_km,
                "diesel_car_km": d_km,
                "motorcycle_km": m_km,
                "electric_car_km": ev_km,
                "bus_km": b_km,
                "train_km": t_km,
                "flight_domestic_km": f_km
            },
            "electricity": {
                "consumption_kwh": e_kwh,
                "solar_kwh": s_kwh
            },
            "household_fuel": {
                "lpg_cylinders": lpg_cyl,
                "natural_gas_scm": gas
            },
            "food": {
                "diet_type": diet
            },
            "waste": {
                "waste_kg": w_kg,
                "recycling_pct": r_pct,
                "composting_pct": c_pct
            }
        }

        # Validate with Validation Agent
        val_res = validation_agent.validate_and_normalize(raw_data)
        norm_data = val_res["normalized_data"]

        # Calculate deterministically
        results = calculate_carbon_footprint(norm_data)

        # Update central state dictionary
        current_state = current_state or {}
        current_state["raw_inputs"] = raw_data
        current_state["normalized_activity_data"] = norm_data
        current_state["carbon_results"] = results
        current_state["validation_status"] = val_res

        total_m = results["total_monthly_kg_co2e"]
        annual_t = results["annualized_kg_co2e"] / 1000.0

        cats = results["categories"]
        sorted_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)
        top_cat = sorted_cats[0][0].replace("_", " ").title() if sorted_cats else "None"

        kpi_m_val = f"### 📅 Monthly CO₂e\n# **{total_m:.1f} kg**"
        kpi_a_val = f"### 🌍 Annualized CO₂e\n# **{annual_t:.2f} tonnes**"
        kpi_h_val = f"### 🎯 Largest Hotspot\n# **{top_cat}**"

        # Table formatting
        table_md = "#### 📊 Category Breakdown Table\n\n"
        table_md += "| Category | Monthly CO₂e (kg) | Percentage Share (%) |\n"
        table_md += "| :--- | :---: | :---: |\n"
        for cat, val in cats.items():
            pct = results["breakdown_percentages"].get(cat, 0.0)
            table_md += f"| **{cat.replace('_', ' ').title()}** | {val:.2f} kg | {pct:.1f}% |\n"

        notes_md = "#### 📑 Certified Emission Accounting Notes\n"
        for note in results["calculation_notes"]:
            notes_md += f"- *{note}*\n"

        if val_res["warnings"]:
            notes_md += "\n> [!WARNING]\n"
            for w in val_res["warnings"]:
                notes_md += f"> - {w}\n"

        return (
            kpi_m_val, kpi_a_val, kpi_h_val,
            table_md, notes_md,
            current_state
        )

    calculate_btn.click(
        fn=on_calculate,
        inputs=[
            petrol_km, diesel_km, motorcycle_km, ev_km, bus_km, train_km, flights_km,
            electricity_kwh, solar_kwh, lpg_cylinders, natural_gas_scm, diet_choice,
            waste_kg, recycling_pct, composting_pct,
            state
        ],
        outputs=[
            kpi_monthly, kpi_annual, kpi_hotspot,
            breakdown_display, calc_notes_display,
            state
        ]
    )

    return calculate_btn
