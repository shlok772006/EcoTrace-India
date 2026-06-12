"""Carbon-footprint calculator for EcoTrace India.

Pure calculation logic with India-specific emission factors.
No Flask dependency — this module is imported by ``app.py``.

All formulas follow ``DATA_MODEL.md § CalculationFormulas``.
Emission factors are loaded at run-time from
``data/emission_factors.json`` and cached in-process.
"""

import json
import logging
import os
import threading
from typing import Any

from constants import (
    CAR_KM_PER_TONNE_CO2,
    ECO_GRADES,
    ECO_GRADE_A_MAX,
    ECO_GRADE_A_PLUS_MAX,
    ECO_GRADE_B_MAX,
    ECO_GRADE_C_MAX,
    ECO_GRADE_D_MAX,
    KG_PER_TONNE,
    MONTHS_PER_YEAR,
)
from exceptions import CalculationError

__all__ = [
    "load_emission_factors",
    "calculate_footprint",
    "calculate_eco_score",
    "calculate_tree_offset",
    "get_benchmarks",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------

_FACTORS_CACHE: dict[str, Any] | None = None
_FACTORS_LOCK = threading.Lock()


def load_emission_factors() -> dict[str, Any]:
    """Load emission factors from the JSON data file.

    Values are cached after the first call so the file is
    read only once per process lifetime.  Access is
    thread-safe (double-checked locking).

    Returns:
        A nested dictionary whose top-level keys are
        ``energy``, ``transport``, ``diet``, ``waste``,
        ``benchmarks``, and ``offsets``.

    Raises:
        CalculationError: If the data file cannot be found
            or contains invalid JSON.
    """
    global _FACTORS_CACHE  # noqa: PLW0603
    if _FACTORS_CACHE is None:
        with _FACTORS_LOCK:
            if _FACTORS_CACHE is None:
                factors_path = os.path.join(
                    os.path.dirname(
                        os.path.abspath(__file__)
                    ),
                    "data",
                    "emission_factors.json",
                )
                try:
                    with open(
                        factors_path,
                        "r",
                        encoding="utf-8",
                    ) as fh:
                        _FACTORS_CACHE = json.load(fh)
                except (
                    OSError,
                    json.JSONDecodeError,
                ) as exc:
                    raise CalculationError(
                        "Cannot load emission "
                        f"factors: {exc}"
                    ) from exc
    return _FACTORS_CACHE


# ---------------------------------------------------------------
# Carbon footprint calculation
# ---------------------------------------------------------------


def calculate_footprint(
    user_data: dict[str, Any],
) -> dict[str, Any]:
    """Calculate annual carbon footprint from monthly inputs.

    All numeric inputs are **monthly** values.  They are
    multiplied by 12 to obtain annual figures.  Diet factors
    in the data file are already annual.

    Args:
        user_data: Dictionary with keys such as
            ``electricity_kwh``, ``lpg_cylinders``,
            ``petrol_car_km``, ``diet_type``, etc.

    Returns:
        A dictionary containing:
        - ``total`` — grand total in tonnes CO₂e/year.
        - ``breakdown`` — dict with ``energy``,
          ``transport``, ``diet``, ``waste`` (all tonnes).
        - ``largest_category`` — name of the highest-
          emitting category.

    Raises:
        CalculationError: If emission factors have not been
            loaded or a required key is missing.
    """
    try:
        factors = load_emission_factors()
    except CalculationError:
        raise
    except Exception as exc:
        raise CalculationError(
            f"Unexpected factor-loading error: {exc}"
        ) from exc

    logger.info("Calculating footprint for user input")

    energy_f = factors["energy"]
    transport_f = factors["transport"]
    diet_f = factors["diet"]
    waste_f = factors["waste"]

    # --- ENERGY ---
    electricity_annual: float = (
        float(user_data.get("electricity_kwh", 0))
        * MONTHS_PER_YEAR
        * energy_f["electricity_kwh"]
    ) / KG_PER_TONNE

    lpg_annual: float = (
        float(user_data.get("lpg_cylinders", 0))
        * MONTHS_PER_YEAR
        * energy_f["lpg_per_cylinder"]
    ) / KG_PER_TONNE

    energy_total: float = electricity_annual + lpg_annual

    # --- TRANSPORT ---
    car_km = float(user_data.get("petrol_car_km", 0))
    bike_km = float(user_data.get("two_wheeler_km", 0))
    train_km = float(user_data.get("train_km", 0))
    flight_km = float(user_data.get("flight_km", 0))

    transport_total: float = (
        car_km * transport_f["petrol_car_per_km"]
        + bike_km * transport_f["two_wheeler_per_km"]
        + train_km * transport_f["train_per_km"]
        + flight_km * transport_f["domestic_flight_per_km"]
    ) * MONTHS_PER_YEAR / KG_PER_TONNE

    # --- DIET (already annual in the data file) ---
    diet_type: str = user_data.get(
        "diet_type", "vegetarian"
    )
    diet_total: float = (
        diet_f.get(diet_type, diet_f["vegetarian"])
        / KG_PER_TONNE
    )

    # --- WASTE ---
    waste_kg_annual: float = (
        float(user_data.get("waste_kg", 0))
        * MONTHS_PER_YEAR
    )
    waste_total: float = (
        waste_kg_annual * waste_f["landfill_per_kg"]
    ) / KG_PER_TONNE

    if user_data.get("recycles"):
        waste_total *= 1 - waste_f["recycled_reduction"]
    if user_data.get("composts"):
        waste_total *= 1 - waste_f["composting_reduction"]

    grand_total: float = (
        energy_total
        + transport_total
        + diet_total
        + waste_total
    )

    category_totals: dict[str, float] = {
        "energy": energy_total,
        "transport": transport_total,
        "diet": diet_total,
        "waste": waste_total,
    }
    largest_category: str = max(
        category_totals,
        key=lambda k: category_totals[k],
    )

    return {
        "total": round(grand_total, 2),
        "breakdown": {
            k: round(v, 2)
            for k, v in category_totals.items()
        },
        "largest_category": largest_category,
    }


# ---------------------------------------------------------------
# Eco Score
# ---------------------------------------------------------------


def calculate_eco_score(
    total_tonnes: float,
) -> dict[str, str]:
    """Grade the user relative to India urban average.

    Args:
        total_tonnes: The user's total annual footprint in
            metric tonnes CO₂e.

    Returns:
        A dictionary with ``grade``, ``label``, and
        ``color`` keys.
    """
    factors = load_emission_factors()
    urban_avg: float = factors["benchmarks"][
        "india_urban_average"
    ]
    ratio: float = (
        total_tonnes / urban_avg if urban_avg else 1.0
    )

    thresholds = [
        ECO_GRADE_A_PLUS_MAX,
        ECO_GRADE_A_MAX,
        ECO_GRADE_B_MAX,
        ECO_GRADE_C_MAX,
        ECO_GRADE_D_MAX,
    ]
    for threshold, grade_info in zip(
        thresholds, ECO_GRADES
    ):
        if ratio <= threshold:
            return dict(grade_info)

    # ratio > D_MAX → grade F
    return dict(ECO_GRADES[-1])


# ---------------------------------------------------------------
# Tree / offset equivalents
# ---------------------------------------------------------------


def calculate_tree_offset(
    total_tonnes: float,
) -> dict[str, float | int]:
    """Calculate nature-based offset equivalents.

    Args:
        total_tonnes: Annual footprint in tonnes CO₂e.

    Returns:
        Dictionary with ``trees_needed``,
        ``equivalent_car_km``, and ``solar_panels_kw``.
    """
    factors = load_emission_factors()
    offsets = factors["offsets"]

    trees_needed: float = (
        total_tonnes
        / offsets["tree_absorption_per_year"]
    )
    equivalent_car_km: float = (
        total_tonnes * CAR_KM_PER_TONNE_CO2
    )
    solar_panels_kw: float = (
        total_tonnes
        / offsets["solar_panel_saving_per_kw"]
    )

    return {
        "trees_needed": round(trees_needed),
        "equivalent_car_km": round(equivalent_car_km),
        "solar_panels_kw": round(solar_panels_kw, 1),
    }


# ---------------------------------------------------------------
# Benchmark data helper
# ---------------------------------------------------------------


def get_benchmarks() -> dict[str, float]:
    """Return benchmark values for the results page.

    Returns:
        Dictionary with ``india_national``,
        ``india_urban``, ``global``, and
        ``target_2050`` (all in tonnes CO₂e/year).
    """
    factors = load_emission_factors()
    bench = factors["benchmarks"]
    return {
        "india_national": bench["india_national_average"],
        "india_urban": bench["india_urban_average"],
        "global": bench["global_average"],
        "target_2050": bench["global_target_2050"],
    }
