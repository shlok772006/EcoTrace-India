"""Constants for EcoTrace India carbon footprint calculations.

Centralises all magic numbers, thresholds, and named constants
used across the calculator and grading modules.  Every value is
sourced from ``DATA_MODEL.md`` and must not be changed without
updating that document first.

Note
----
Emission factors loaded from ``data/emission_factors.json`` at
run-time are intentionally **not** duplicated here.  Only values
that were previously hard-coded inline belong in this module.
"""

__all__ = [
    "MONTHS_PER_YEAR",
    "KG_PER_TONNE",
    "CAR_KM_PER_TONNE_CO2",
    "ECO_GRADE_A_PLUS_MAX",
    "ECO_GRADE_A_MAX",
    "ECO_GRADE_B_MAX",
    "ECO_GRADE_C_MAX",
    "ECO_GRADE_D_MAX",
    "ECO_GRADES",
    "INPUT_LIMITS",
    "VALID_DIET_TYPES",
    "VALID_CITY_TIERS",
    "MAX_CHAT_MESSAGE_LENGTH",
    "CHAT_HISTORY_WINDOW",
    "DEFAULT_PORT",
]

from typing import Final

# ------------------------------------------------------------------
# Annualisation
# ------------------------------------------------------------------

MONTHS_PER_YEAR: Final[int] = 12
"""Multiplier to convert monthly user inputs to annual values."""

KG_PER_TONNE: Final[float] = 1000.0
"""Kilograms in one metric tonne (used for kg → tonne conversion)."""

# ------------------------------------------------------------------
# Transport — equivalent car km per tonne CO2
# ------------------------------------------------------------------

CAR_KM_PER_TONNE_CO2: Final[float] = 5848.0
"""Equivalent petrol-car km that emit 1 tonne CO2 (at 171 g/km)."""

# ------------------------------------------------------------------
# Eco-Score grading thresholds (ratio to urban average)
# ------------------------------------------------------------------

ECO_GRADE_A_PLUS_MAX: Final[float] = 0.4
ECO_GRADE_A_MAX: Final[float] = 0.6
ECO_GRADE_B_MAX: Final[float] = 0.8
ECO_GRADE_C_MAX: Final[float] = 1.0
ECO_GRADE_D_MAX: Final[float] = 1.4

# ------------------------------------------------------------------
# Eco-Score labels and colours
# ------------------------------------------------------------------

ECO_GRADES: Final[list[dict[str, str]]] = [
    {
        "grade": "A+",
        "label": "Climate Hero 🌟",
        "color": "#00C853",
    },
    {
        "grade": "A",
        "label": "Eco Champion 🌿",
        "color": "#43A047",
    },
    {
        "grade": "B",
        "label": "Green Thinker 🍃",
        "color": "#7CB342",
    },
    {
        "grade": "C",
        "label": "Average Impact 🌍",
        "color": "#FDD835",
    },
    {
        "grade": "D",
        "label": "Above Average ⚠️",
        "color": "#FB8C00",
    },
    {
        "grade": "F",
        "label": "High Impact 🔴",
        "color": "#E53935",
    },
]

# ------------------------------------------------------------------
# Input-validation limits (monthly values)
# ------------------------------------------------------------------

INPUT_LIMITS: Final[dict[str, tuple[float, float]]] = {
    "electricity_kwh": (0, 10_000),
    "lpg_cylinders": (0, 50),
    "petrol_car_km": (0, 50_000),
    "two_wheeler_km": (0, 50_000),
    "train_km": (0, 50_000),
    "flight_km": (0, 100_000),
    "waste_kg": (0, 5_000),
}

VALID_DIET_TYPES: Final[frozenset[str]] = frozenset(
    {"vegan", "vegetarian", "non_vegetarian", "heavy_meat"}
)

VALID_CITY_TIERS: Final[frozenset[str]] = frozenset(
    {"metro", "tier_2", "rural"}
)

# ------------------------------------------------------------------
# Chat / prompt limits
# ------------------------------------------------------------------

MAX_CHAT_MESSAGE_LENGTH: Final[int] = 1000
CHAT_HISTORY_WINDOW: Final[int] = 10
"""Number of recent chat messages to include as context."""

# ------------------------------------------------------------------
# Default server port
# ------------------------------------------------------------------

DEFAULT_PORT: Final[int] = 5000
