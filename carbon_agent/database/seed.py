"""
Database seeder for certified emission factors, standard reduction actions, and default profile.
"""
import csv
from pathlib import Path
from carbon_agent.config.settings import DATA_DIR
from carbon_agent.database.database import get_db, init_db
from carbon_agent.database.models import EmissionFactor, ReductionAction, UserProfile

STANDARD_REDUCTION_ACTIONS = [
    {
        "action_id": "carpool_commute",
        "category": "transportation",
        "title": "Carpooling / Ride-Sharing for Commute",
        "description": "Share private car commute with 1-2 colleagues or neighbours 3 days per week.",
        "formula_type": "pct_reduction",
        "default_reduction_pct": 30.0,
        "difficulty": "Easy",
        "cost_tier": "Free",
        "assumptions": "Cuts solo personal car commute distance by approximately 30% through shared occupancy."
    },
    {
        "action_id": "modal_shift_metro_bus",
        "category": "transportation",
        "title": "Modal Shift to Metro / Rapid Bus Transit",
        "description": "Replace 40% of car or motorcycle commute trips with electric metro or municipal bus.",
        "formula_type": "modal_shift",
        "default_reduction_pct": 40.0,
        "difficulty": "Medium",
        "cost_tier": "Low",
        "assumptions": "Swaps high-intensity private vehicle km with lower emission factor mass transit (0.035-0.089 kg CO2e/pkm)."
    },
    {
        "action_id": "ev_transition",
        "category": "transportation",
        "title": "Transition to Electric 2-Wheeler / EV",
        "description": "Replace internal combustion vehicle with an energy-efficient electric vehicle.",
        "formula_type": "pct_reduction",
        "default_reduction_pct": 60.0,
        "difficulty": "Hard",
        "cost_tier": "Investment",
        "assumptions": "Electric drive efficiency yields net 60% emission reduction even on current grid mix."
    },
    {
        "action_id": "ac_thermostat_24c",
        "category": "energy",
        "title": "Calibrate Air Conditioning to 24°C - 26°C",
        "description": "Set AC thermostats to Bureau of Energy Efficiency (BEE) recommended 24°C rather than 18°-20°C.",
        "formula_type": "pct_reduction",
        "default_reduction_pct": 18.0,
        "difficulty": "Easy",
        "cost_tier": "Free",
        "assumptions": "Each 1°C increase in AC setpoint saves approximately 6% of cooling electricity."
    },
    {
        "action_id": "led_efficient_appliances",
        "category": "energy",
        "title": "Upgrade Lighting to 5-Star LEDs & Smart Strips",
        "description": "Eliminate vampire phantom loads and replace inefficient CFL/incandescent bulbs with 5-star LEDs.",
        "formula_type": "pct_reduction",
        "default_reduction_pct": 12.0,
        "difficulty": "Easy",
        "cost_tier": "Low",
        "assumptions": "LEDs consume 75% less energy than conventional lighting, cutting lighting load by ~12%."
    },
    {
        "action_id": "rooftop_solar_pv",
        "category": "energy",
        "title": "Install Rooftop Solar PV Net-Metering",
        "description": "Install a 2-3 kW residential rooftop solar system to supply clean energy and export surplus.",
        "formula_type": "pct_reduction",
        "default_reduction_pct": 65.0,
        "difficulty": "Hard",
        "cost_tier": "Investment",
        "assumptions": "Rooftop solar lifecycle emissions (0.04 kg CO2e/kWh) displace grid power (0.82 kg CO2e/kWh) by 65%."
    },
    {
        "action_id": "dietary_flexitarian_shift",
        "category": "food",
        "title": "Adopt 2-3 Plant-Based Days per Week (Meatless Days)",
        "description": "Substitute meat-heavy meals with legume and vegetable-rich whole foods 3 days per week.",
        "formula_type": "diet_shift",
        "default_reduction_pct": 25.0,
        "difficulty": "Medium",
        "cost_tier": "Free",
        "assumptions": "Transitioning partially from heavy/medium meat towards vegetarian reduces food footprint by ~25%."
    },
    {
        "action_id": "food_waste_prevention",
        "category": "food",
        "title": "Meal Planning & Food Waste Elimination",
        "description": "Plan weekly grocery purchases carefully and utilize leftovers to minimize spoiled food.",
        "formula_type": "pct_reduction",
        "default_reduction_pct": 15.0,
        "difficulty": "Easy",
        "cost_tier": "Free",
        "assumptions": "Average households waste 15-20% of purchased food; careful planning directly cuts food production footprint."
    },
    {
        "action_id": "dry_waste_segregation_recycling",
        "category": "waste",
        "title": "100% Dry Waste Segregation & Recycling",
        "description": "Clean and segregate plastics, paper, cardboard, and metals for recycling streams.",
        "formula_type": "pct_reduction",
        "default_reduction_pct": 45.0,
        "difficulty": "Easy",
        "cost_tier": "Free",
        "assumptions": "Diverts 40-50% of landfill volume and credits avoided primary production emissions."
    },
    {
        "action_id": "home_composting_wet_waste",
        "category": "waste",
        "title": "Decentralized Wet Organic Waste Composting",
        "description": "Compost kitchen peels, coffee grounds, and garden trimmings in a balcony or backyard composter.",
        "formula_type": "pct_reduction",
        "default_reduction_pct": 40.0,
        "difficulty": "Medium",
        "cost_tier": "Low",
        "assumptions": "Aerobic composting prevents anaerobic decomposition and methane generation in open dumpsites."
    }
]


def seed_emission_factors(session):
    """Load emission factors from CSV if not already present."""
    csv_file = DATA_DIR / "emission_factors.csv"
    if not csv_file.exists():
        print(f"Warning: Emission factors CSV not found at {csv_file}")
        return

    with open(csv_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing = session.query(EmissionFactor).filter_by(activity=row["activity"]).first()
            if not existing:
                factor = EmissionFactor(
                    category=row["category"].strip(),
                    activity=row["activity"].strip(),
                    unit=row["unit"].strip(),
                    emission_factor=float(row["emission_factor"]),
                    factor_unit=row["factor_unit"].strip(),
                    region=row["region"].strip(),
                    source=row["source"].strip(),
                    reference_year=int(row["reference_year"]),
                    notes=row.get("notes", "").strip()
                )
                session.add(factor)
        session.flush()


def seed_reduction_actions(session):
    """Seed catalog of domain-validated emission reduction actions."""
    for action_data in STANDARD_REDUCTION_ACTIONS:
        existing = session.query(ReductionAction).filter_by(action_id=action_data["action_id"]).first()
        if not existing:
            action = ReductionAction(**action_data)
            session.add(action)
    session.flush()


def seed_default_user(session):
    """Ensure a default user profile exists for session persistence."""
    default_user = session.query(UserProfile).filter_by(username="default_user").first()
    if not default_user:
        user = UserProfile(
            username="default_user",
            region="India",
            target_reduction_pct=20.0
        )
        session.add(user)
        session.flush()


def seed_all():
    """Initialize tables and run all seeders."""
    init_db()
    with get_db() as session:
        seed_emission_factors(session)
        seed_reduction_actions(session)
        seed_default_user(session)
    print("Database initialization and seeding completed successfully.")


if __name__ == "__main__":
    seed_all()
