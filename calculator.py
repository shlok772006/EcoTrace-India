"""
calculator.py — EcoTrace India
Pure calculation logic with India-specific emission factors.
No Flask dependency — this module is imported by app.py.
"""

import json
import os
from typing import Any


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

_FACTORS_CACHE: dict[str, Any] | None = None


def load_emission_factors() -> dict[str, Any]:
    """Load emission factors from data/emission_factors.json.

    Values are cached after the first call so the file is read only once.
    """
    global _FACTORS_CACHE
    if _FACTORS_CACHE is None:
        factors_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "data", "emission_factors.json"
        )
        with open(factors_path, "r", encoding="utf-8") as f:
            _FACTORS_CACHE = json.load(f)
    return _FACTORS_CACHE


# ---------------------------------------------------------------------------
# Carbon footprint calculation
# ---------------------------------------------------------------------------

def calculate_footprint(user_data: dict[str, Any]) -> dict[str, Any]:
    """Calculate annual carbon footprint from monthly user inputs.

    All numeric inputs are *monthly* values. They are multiplied by 12 to get
    annual figures.  Diet factors are already annual in the data file.

    Returns a dict with:
        total          – grand total in tonnes CO2e/year
        breakdown      – dict with energy/transport/diet/waste in tonnes
        largest_category – name of the highest-emitting category

    Formula source: DATA_MODEL.md § CalculationFormulas
    """
    factors = load_emission_factors()
    energy_f = factors["energy"]
    transport_f = factors["transport"]
    diet_f = factors["diet"]
    waste_f = factors["waste"]

    # --- ENERGY ---
    electricity_annual: float = (
        float(user_data.get("electricity_kwh", 0)) * 12
        * energy_f["electricity_kwh"]
    ) / 1000  # kg → tonnes

    lpg_annual: float = (
        float(user_data.get("lpg_cylinders", 0)) * 12
        * energy_f["lpg_per_cylinder"]
    ) / 1000

    energy_total: float = electricity_annual + lpg_annual

    # --- TRANSPORT ---
    transport_total: float = (
        (float(user_data.get("petrol_car_km", 0)) * transport_f["petrol_car_per_km"] * 12)
        + (float(user_data.get("two_wheeler_km", 0)) * transport_f["two_wheeler_per_km"] * 12)
        + (float(user_data.get("train_km", 0)) * transport_f["train_per_km"] * 12)
        + (float(user_data.get("flight_km", 0)) * transport_f["domestic_flight_per_km"] * 12)
    ) / 1000

    # --- DIET ---
    diet_type: str = user_data.get("diet_type", "vegetarian")
    diet_total: float = diet_f.get(diet_type, diet_f["vegetarian"]) / 1000  # already annual

    # --- WASTE ---
    waste_kg_annual: float = float(user_data.get("waste_kg", 0)) * 12
    waste_total: float = (waste_kg_annual * waste_f["landfill_per_kg"]) / 1000
    if user_data.get("recycles"):
        waste_total *= (1 - waste_f["recycled_reduction"])
    if user_data.get("composts"):
        waste_total *= (1 - waste_f["composting_reduction"])

    grand_total: float = energy_total + transport_total + diet_total + waste_total

    # Determine largest category using an explicit dict
    # (fixes the locals()-in-lambda issue from DATA_MODEL.md)
    category_totals = {
        "energy": energy_total,
        "transport": transport_total,
        "diet": diet_total,
        "waste": waste_total,
    }
    largest_category: str = max(category_totals, key=lambda k: category_totals[k])

    return {
        "total": round(grand_total, 2),
        "breakdown": {
            "energy": round(energy_total, 2),
            "transport": round(transport_total, 2),
            "diet": round(diet_total, 2),
            "waste": round(waste_total, 2),
        },
        "largest_category": largest_category,
    }


# ---------------------------------------------------------------------------
# Eco Score
# ---------------------------------------------------------------------------

def calculate_eco_score(total_tonnes: float) -> dict[str, str]:
    """Grade the user's footprint relative to India urban average (5.0 t).

    Returns a dict with grade, label, and color.
    Formula source: DATA_MODEL.md § Eco Score Formula
    """
    factors = load_emission_factors()
    urban_avg: float = factors["benchmarks"]["india_urban_average"]
    ratio: float = total_tonnes / urban_avg if urban_avg else 1.0

    if ratio <= 0.4:
        return {"grade": "A+", "label": "Climate Hero 🌟", "color": "#00C853"}
    elif ratio <= 0.6:
        return {"grade": "A", "label": "Eco Champion 🌿", "color": "#43A047"}
    elif ratio <= 0.8:
        return {"grade": "B", "label": "Green Thinker 🍃", "color": "#7CB342"}
    elif ratio <= 1.0:
        return {"grade": "C", "label": "Average Impact 🌍", "color": "#FDD835"}
    elif ratio <= 1.4:
        return {"grade": "D", "label": "Above Average ⚠️", "color": "#FB8C00"}
    else:
        return {"grade": "F", "label": "High Impact 🔴", "color": "#E53935"}


# ---------------------------------------------------------------------------
# Tree / offset equivalents
# ---------------------------------------------------------------------------

def calculate_tree_offset(total_tonnes: float) -> dict[str, float | int]:
    """How many trees / solar panels / car-km to offset the footprint.

    Formula source: DATA_MODEL.md § Tree Offset Formula
    """
    factors = load_emission_factors()
    offsets = factors["offsets"]

    trees_needed: float = total_tonnes / offsets["tree_absorption_per_year"]
    equivalent_car_km: float = total_tonnes * 5848  # km at 171 g/km
    solar_panels_kw: float = total_tonnes / offsets["solar_panel_saving_per_kw"]

    return {
        "trees_needed": round(trees_needed),
        "equivalent_car_km": round(equivalent_car_km),
        "solar_panels_kw": round(solar_panels_kw, 1),
    }


# ---------------------------------------------------------------------------
# Benchmark data helper
# ---------------------------------------------------------------------------

def get_benchmarks() -> dict[str, float]:
    """Return benchmark values for the results page comparison."""
    factors = load_emission_factors()
    b = factors["benchmarks"]
    return {
        "india_national": b["india_national_average"],
        "india_urban": b["india_urban_average"],
        "global": b["global_average"],
        "target_2050": b["global_target_2050"],
    }
