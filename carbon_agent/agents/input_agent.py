"""
Agent 1: Input / Intent Agent.
Interprets natural language queries, extracts lifestyle activities and quantities into structured JSON,
detects missing context, and formulates clarification questions without hallucinating data.
"""
import re
from typing import Dict, Any, List, Tuple


class InputIntentAgent:
    """
    Parses unstructured text into normalized activity attributes.
    Supports deterministic pattern extraction with intent recognition.
    """

    def __init__(self):
        self.name = "Input / Intent Agent"

    def parse_user_text(self, text: str) -> Dict[str, Any]:
        """
        Main entry point: Converts unstructured user narrative into structured activity JSON.
        """
        if not text or not text.strip():
            return {
                "structured_data": {},
                "detected_intents": [],
                "missing_information": ["No activity details provided."],
                "clarification_questions": ["Could you describe your daily commute, monthly electricity units, and dietary habits?"]
            }

        text_lower = text.lower()
        extracted: Dict[str, Any] = {}
        detected_intents: List[str] = []
        missing_info: List[str] = []
        clarifications: List[str] = []

        # 1. Transportation Extraction
        transport_extracted = {}
        # Petrol car
        petrol_car_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?|kilo\s*meters?).*?\b(?:petrol\s*car|gasoline\s*car|car\s*petrol|in\s*my\s*petrol\s*car)\b|\b(?:petrol\s*car|gasoline\s*car)\b.*?(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?)', text_lower)
        # Generic car if not specified
        generic_car_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?).*?\b(?:car|drive|driving)\b|\b(?:car|drive|driving)\b.*?(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?)', text_lower)
        # Diesel car
        diesel_car_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?).*?\b(?:diesel\s*car|diesel)\b|\b(?:diesel\s*car)\b.*?(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?)', text_lower)
        # Bike / motorcycle / 2-wheeler
        bike_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?).*?\b(?:bike|motorcycle|scooter|two\s*wheeler|2\s*wheeler|bullet)\b|\b(?:bike|motorcycle|scooter|two\s*wheeler|2\s*wheeler|bullet)\b.*?(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?)', text_lower)
        # Electric vehicle / EV
        ev_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?).*?\b(?:ev|electric\s*car|electric\s*vehicle)\b|\b(?:ev|electric\s*car)\b.*?(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?)', text_lower)
        # Bus
        bus_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?).*?\b(?:bus|public\s*bus)\b|\b(?:bus|public\s*bus)\b.*?(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?)', text_lower)
        # Train / Metro
        train_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?).*?\b(?:train|metro|railway|local\s*train)\b|\b(?:train|metro)\b.*?(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?)', text_lower)
        # Flight
        flight_dom_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:km|kms|kilometers?).*?\b(?:domestic\s*flight|flights?)\b|\b(?:flight|flights?)\b.*?(\d+(?:\.\d+)?)\s*(?:km|kms)', text_lower)

        # Detect frequency (daily, monthly, weekly)
        is_daily_commute = bool(re.search(r'\b(?:daily|every\s*day|per\s*day|a\s*day|day)\b', text_lower))
        is_monthly_commute = bool(re.search(r'\b(?:monthly|every\s*month|per\s*month|a\s*month)\b', text_lower))
        is_weekly_commute = bool(re.search(r'\b(?:weekly|every\s*week|per\s*week|a\s*week)\b', text_lower))

        freq_mult = 1.0
        if is_daily_commute:
            freq_mult = 30.4167
        elif is_weekly_commute:
            freq_mult = 4.345

        def _get_val(match):
            if not match:
                return None
            val_str = match.group(1) if match.group(1) is not None else match.group(2)
            try:
                return float(val_str)
            except Exception:
                return None

        if diesel_car_match:
            km = _get_val(diesel_car_match)
            if km is not None:
                transport_extracted["diesel_car_km"] = round(km * freq_mult, 2)
                transport_extracted["reported_frequency"] = "daily" if is_daily_commute else ("weekly" if is_weekly_commute else "monthly")
                detected_intents.append("transport_diesel_car")
        elif petrol_car_match:
            km = _get_val(petrol_car_match)
            if km is not None:
                transport_extracted["petrol_car_km"] = round(km * freq_mult, 2)
                transport_extracted["reported_frequency"] = "daily" if is_daily_commute else ("weekly" if is_weekly_commute else "monthly")
                detected_intents.append("transport_petrol_car")
        elif generic_car_match and not ev_match:
            km = _get_val(generic_car_match)
            if km is not None:
                # Default generic car to petrol car
                transport_extracted["petrol_car_km"] = round(km * freq_mult, 2)
                transport_extracted["reported_frequency"] = "daily" if is_daily_commute else ("weekly" if is_weekly_commute else "monthly")
                detected_intents.append("transport_car")

        if bike_match:
            km = _get_val(bike_match)
            if km is not None:
                transport_extracted["motorcycle_km"] = round(km * freq_mult, 2)
                detected_intents.append("transport_motorcycle")

        if ev_match:
            km = _get_val(ev_match)
            if km is not None:
                transport_extracted["electric_car_km"] = round(km * freq_mult, 2)
                detected_intents.append("transport_electric_vehicle")

        if bus_match:
            km = _get_val(bus_match)
            if km is not None:
                transport_extracted["bus_km"] = round(km * freq_mult, 2)
                detected_intents.append("transport_bus")

        if train_match:
            km = _get_val(train_match)
            if km is not None:
                transport_extracted["train_km"] = round(km * freq_mult, 2)
                detected_intents.append("transport_train")

        if flight_dom_match:
            km = _get_val(flight_dom_match)
            if km is not None:
                transport_extracted["flight_domestic_km"] = round(km, 2)
                detected_intents.append("transport_flight")

        if transport_extracted:
            extracted["transportation"] = transport_extracted
        else:
            missing_info.append("Transportation details not specified.")

        # 2. Electricity Extraction
        elec_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:units|kwh|kilowatt\s*hours?)\b|\b(?:electricity|power|units)\b.*?(\d+(?:\.\d+)?)\s*(?:units|kwh)?', text_lower)
        solar_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:units|kwh)?\s*(?:solar|rooftop\s*solar)\b|\b(?:solar)\b.*?(\d+(?:\.\d+)?)\s*(?:units|kwh)?', text_lower)

        elec_extracted = {}
        if elec_match:
            kwh = _get_val(elec_match)
            if kwh is not None:
                elec_extracted["consumption_kwh"] = kwh
                detected_intents.append("electricity_consumption")

        if solar_match:
            s_kwh = _get_val(solar_match)
            if s_kwh is not None:
                elec_extracted["solar_kwh"] = s_kwh
                detected_intents.append("solar_generation")

        if elec_extracted:
            extracted["electricity"] = elec_extracted
        else:
            missing_info.append("Electricity usage not detected.")
            clarifications.append("How many units (kWh) of electricity do you typically consume per month?")

        # 3. Household Fuel Extraction
        fuel_extracted = {}
        lpg_cyl_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:cylinders?|lpg\s*cylinders?)\b|\b(?:lpg|cylinder)\b.*?(\d+(?:\.\d+)?)\s*(?:cylinders?|per\s*month)?', text_lower)
        lpg_kg_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|kilograms?)\s*(?:of\s*)?lpg\b', text_lower)
        png_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:scm|m3|cubic\s*meters?).*?\b(?:png|piped\s*gas|natural\s*gas)\b|\b(?:png|piped\s*gas)\b.*?(\d+(?:\.\d+)?)', text_lower)

        if lpg_cyl_match:
            cyls = _get_val(lpg_cyl_match)
            if cyls is not None:
                fuel_extracted["lpg_cylinders"] = cyls
                fuel_extracted["lpg_kg"] = round(cyls * 14.2, 2)
                detected_intents.append("fuel_lpg_cylinder")
        elif lpg_kg_match:
            kg = _get_val(lpg_kg_match)
            if kg is not None:
                fuel_extracted["lpg_kg"] = kg
                detected_intents.append("fuel_lpg_kg")

        if png_match:
            scm = _get_val(png_match)
            if scm is not None:
                fuel_extracted["natural_gas_scm"] = scm
                detected_intents.append("fuel_natural_gas")

        if fuel_extracted:
            extracted["household_fuel"] = fuel_extracted

        # 4. Food & Diet Extraction
        food_extracted = {}
        if re.search(r'\b(?:vegan|plant\s*based)\b', text_lower):
            food_extracted["diet_type"] = "vegan"
            detected_intents.append("diet_vegan")
        elif re.search(r'\b(?:heavy\s*meat|lot\s*of\s*meat|daily\s*meat|beef|pork)\b', text_lower):
            food_extracted["diet_type"] = "heavy_meat"
            detected_intents.append("diet_heavy_meat")
        elif re.search(r'\b(?:non[- ]?veg|chicken|meat|medium\s*meat|omnivore)\b', text_lower):
            food_extracted["diet_type"] = "medium_meat"
            detected_intents.append("diet_medium_meat")
        elif re.search(r'\b(?:pescatarian|fish|seafood)\b', text_lower):
            food_extracted["diet_type"] = "pescatarian"
            detected_intents.append("diet_pescatarian")
        elif re.search(r'\b(?:vegetarian|veg)\b', text_lower):
            food_extracted["diet_type"] = "vegetarian"
            detected_intents.append("diet_vegetarian")
        else:
            missing_info.append("Diet type not mentioned (defaulting to vegetarian or ask user).")

        if food_extracted:
            extracted["food"] = food_extracted

        # 5. Waste Extraction
        waste_extracted = {}
        waste_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|kilos?)\s*(?:of\s*)?(?:waste|garbage|trash)\b|\b(?:waste|garbage)\b.*?(\d+(?:\.\d+)?)\s*(?:kg|kilos?)', text_lower)
        recycle_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:recycled?|recycling)\b|\b(?:recycled?|recycling)\b.*?(\d+(?:\.\d+)?)\s*%', text_lower)
        compost_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:compost(?:ed|ing)?)\b|\b(?:compost(?:ed|ing)?)\b.*?(\d+(?:\.\d+)?)\s*%', text_lower)

        if waste_match:
            w_kg = _get_val(waste_match)
            if w_kg is not None:
                # If stated as weekly waste, convert to monthly
                if bool(re.search(r'\b(?:per\s*week|a\s*week|weekly)\b', text_lower)):
                    waste_extracted["waste_kg"] = round(w_kg * 4.345, 2)
                else:
                    waste_extracted["waste_kg"] = w_kg
                detected_intents.append("waste_generation")

        if recycle_match:
            r_pct = _get_val(recycle_match)
            if r_pct is not None:
                waste_extracted["recycling_pct"] = min(100.0, r_pct)

        if compost_match:
            c_pct = _get_val(compost_match)
            if c_pct is not None:
                waste_extracted["composting_pct"] = min(100.0, c_pct)

        if waste_extracted:
            extracted["waste"] = waste_extracted

        # 6. Reduction Target Intent
        target_match = re.search(r'reduce.*?(?:by\s*)?(\d+(?:\.\d+)?)\s*%', text_lower)
        if target_match:
            target_pct = float(target_match.group(1))
            detected_intents.append("goal_target_reduction")
            extracted["reduction_target_pct"] = target_pct

        return {
            "structured_data": extracted,
            "detected_intents": detected_intents,
            "missing_information": missing_info,
            "clarification_questions": clarifications
        }
