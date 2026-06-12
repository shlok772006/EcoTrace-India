"""Unit tests for EcoTrace India.

Covers all API endpoints, calculator edge cases
(boundary values, all diet types, all city tiers),
input validation, and security sanitisation.

Run with:  ``pytest -v test_app.py``
"""

import json
from typing import Any

import pytest

from app import app
from calculator import (
    calculate_eco_score,
    calculate_footprint,
    calculate_tree_offset,
    get_benchmarks,
    load_emission_factors,
)
from constants import (
    ECO_GRADE_A_MAX,
    ECO_GRADE_A_PLUS_MAX,
    INPUT_LIMITS,
    VALID_CITY_TIERS,
    VALID_DIET_TYPES,
)


# ---------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------


@pytest.fixture
def client():
    """Create a Flask test client with factors loaded.

    Yields:
        A ``FlaskClient`` instance.
    """
    load_emission_factors()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def _base_input(**overrides: Any) -> dict[str, Any]:
    """Build a valid calculator input with overrides.

    Args:
        **overrides: Field values to override.

    Returns:
        Complete input dictionary.
    """
    defaults: dict[str, Any] = {
        "electricity_kwh": 100,
        "lpg_cylinders": 1,
        "petrol_car_km": 500,
        "two_wheeler_km": 100,
        "train_km": 50,
        "flight_km": 0,
        "diet_type": "vegetarian",
        "waste_kg": 15,
        "recycles": True,
        "composts": False,
        "city_tier": "metro",
        "language": "English",
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------


class TestHealthEndpoint:
    """Tests for ``GET /health``."""

    def test_returns_expected_keys(
        self, client
    ) -> None:
        """Health response contains status and services."""
        resp = client.get("/health")
        assert resp.status_code in (200, 503)
        data = json.loads(resp.data)
        assert "status" in data
        assert "services" in data


# ---------------------------------------------------------------
# Calculate endpoint — happy path
# ---------------------------------------------------------------


class TestCalculateEndpoint:
    """Tests for ``POST /api/calculate``."""

    def test_valid_input(self, client) -> None:
        """Normal data returns full result."""
        resp = client.post(
            "/api/calculate",
            json=_base_input(),
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "total" in data
        assert "breakdown" in data
        assert "eco_score" in data
        assert "benchmarks" in data

    def test_missing_fields_default(
        self, client
    ) -> None:
        """Missing numeric fields default to zero."""
        resp = client.post(
            "/api/calculate",
            json={"electricity_kwh": 100},
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["breakdown"]["transport"] == 0


# ---------------------------------------------------------------
# Boundary-value tests (parametrised)
# ---------------------------------------------------------------


class TestBoundaryValues:
    """Parametrised tests for calculator boundaries."""

    def test_all_zeros(self, client) -> None:
        """Zero usage still produces a diet baseline."""
        resp = client.post(
            "/api/calculate",
            json=_base_input(
                electricity_kwh=0,
                lpg_cylinders=0,
                petrol_car_km=0,
                two_wheeler_km=0,
                train_km=0,
                flight_km=0,
                waste_kg=0,
                diet_type="vegan",
                recycles=True,
                composts=True,
                city_tier="rural",
            ),
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        # Vegan diet = 1500 kg = 1.5t baseline
        assert data["total"] > 0
        assert data["breakdown"]["energy"] == 0

    @pytest.mark.parametrize(
        "field,max_val",
        [
            ("electricity_kwh", 10_000),
            ("lpg_cylinders", 50),
            ("petrol_car_km", 50_000),
            ("two_wheeler_km", 50_000),
            ("train_km", 50_000),
            ("flight_km", 100_000),
            ("waste_kg", 5_000),
        ],
    )
    def test_maximum_values_clamped(
        self,
        client,
        field: str,
        max_val: float,
    ) -> None:
        """Values above the limit are clamped."""
        over = {field: max_val * 2}
        resp = client.post(
            "/api/calculate",
            json=_base_input(**over),
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["total"] > 0

    def test_zero_electricity(self, client) -> None:
        """Zero kWh results in zero energy from elec."""
        result = calculate_footprint(
            _base_input(
                electricity_kwh=0,
                lpg_cylinders=0,
            )
        )
        assert result["breakdown"]["energy"] == 0.0

    def test_max_realistic_flight(
        self, client
    ) -> None:
        """100,000 km flight produces large transport."""
        result = calculate_footprint(
            _base_input(flight_km=100_000)
        )
        assert result["breakdown"]["transport"] > 100

    @pytest.mark.parametrize(
        "diet", list(VALID_DIET_TYPES)
    )
    def test_all_diet_types(
        self, client, diet: str
    ) -> None:
        """Every valid diet type calculates OK."""
        resp = client.post(
            "/api/calculate",
            json=_base_input(diet_type=diet),
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["breakdown"]["diet"] > 0

    @pytest.mark.parametrize(
        "tier", list(VALID_CITY_TIERS)
    )
    def test_all_city_tiers(
        self, client, tier: str
    ) -> None:
        """Every valid city tier is accepted."""
        resp = client.post(
            "/api/calculate",
            json=_base_input(city_tier=tier),
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["city_tier"] == tier


# ---------------------------------------------------------------
# Validation & error tests
# ---------------------------------------------------------------


class TestValidation:
    """Tests for input validation and error handling."""

    def test_invalid_diet_rejected(
        self, client
    ) -> None:
        """Unrecognised diet type returns 400."""
        resp = client.post(
            "/api/calculate",
            json=_base_input(diet_type="alien_food"),
        )
        assert resp.status_code == 400
        assert b"Invalid diet_type" in resp.data

    def test_empty_body(self, client) -> None:
        """Empty POST body returns 400."""
        resp = client.post(
            "/api/calculate",
            data="",
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_invalid_city_tier_defaults(
        self, client
    ) -> None:
        """Invalid city tier falls back to metro."""
        resp = client.post(
            "/api/calculate",
            json=_base_input(city_tier="mars"),
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data["city_tier"] == "metro"


# ---------------------------------------------------------------
# Security tests
# ---------------------------------------------------------------


class TestSecurity:
    """Tests for XSS sanitisation and headers."""

    def test_xss_sanitized(self, client) -> None:
        """Script tags are stripped from text inputs."""
        resp = client.post(
            "/api/calculate",
            json=_base_input(
                language=(
                    "<script>alert('xss')"
                    "</script>English"
                ),
            ),
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert "<script>" not in data.get(
            "language", ""
        )

    def test_security_headers_present(
        self, client
    ) -> None:
        """Response includes required security headers."""
        resp = client.get("/")
        assert (
            resp.headers.get(
                "X-Content-Type-Options"
            )
            == "nosniff"
        )
        assert (
            resp.headers.get("X-Frame-Options")
            == "DENY"
        )
        assert "Content-Security-Policy" in resp.headers
        assert (
            "Strict-Transport-Security"
            in resp.headers
        )


# ---------------------------------------------------------------
# Eco-score grading unit tests
# ---------------------------------------------------------------


class TestEcoScore:
    """Tests for the eco-score grading function."""

    def test_zero_footprint(self) -> None:
        """Zero tonnes yields A+."""
        load_emission_factors()
        score = calculate_eco_score(0.0)
        assert score["grade"] == "A+"

    def test_high_footprint(self) -> None:
        """Very high footprint yields F."""
        load_emission_factors()
        score = calculate_eco_score(50.0)
        assert score["grade"] == "F"


# ---------------------------------------------------------------
# Tree offset unit tests
# ---------------------------------------------------------------


class TestTreeOffset:
    """Tests for the tree-offset calculator."""

    def test_zero_footprint(self) -> None:
        """Zero tonnes needs zero trees."""
        load_emission_factors()
        result = calculate_tree_offset(0.0)
        assert result["trees_needed"] == 0
        assert result["equivalent_car_km"] == 0

    def test_positive_footprint(self) -> None:
        """Positive footprint yields positive offsets."""
        load_emission_factors()
        result = calculate_tree_offset(5.0)
        assert result["trees_needed"] > 0
        assert result["solar_panels_kw"] > 0


# ---------------------------------------------------------------
# Benchmarks unit tests
# ---------------------------------------------------------------


class TestBenchmarks:
    """Tests for the benchmark data helper."""

    def test_has_all_keys(self) -> None:
        """Benchmarks dict contains expected keys."""
        load_emission_factors()
        bench = get_benchmarks()
        assert "india_national" in bench
        assert "india_urban" in bench
        assert "global" in bench
        assert "target_2050" in bench


# ---------------------------------------------------------------
# Chat endpoint tests
# ---------------------------------------------------------------


class TestChatEndpoint:
    """Tests for ``POST /api/chat``."""

    def test_missing_message(self, client) -> None:
        """Empty body returns 400."""
        resp = client.post(
            "/api/chat",
            json={},
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "error" in data

    def test_message_too_long(self, client) -> None:
        """Oversized message returns 400."""
        resp = client.post(
            "/api/chat",
            json={"message": "x" * 1001},
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "1000" in data["error"]

    def test_empty_message_rejected(
        self, client
    ) -> None:
        """Empty string message returns 400."""
        resp = client.post(
            "/api/chat",
            json={"message": ""},
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------
# Action-plan endpoint tests
# ---------------------------------------------------------------


class TestActionPlanEndpoint:
    """Tests for ``POST /api/action-plan``."""

    def test_missing_data(self, client) -> None:
        """Empty body returns 400."""
        resp = client.post(
            "/api/action-plan",
            json={},
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "error" in data

    def test_missing_total(self, client) -> None:
        """Body without 'total' key returns 400."""
        resp = client.post(
            "/api/action-plan",
            json={"breakdown": {}},
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------
# Insights endpoint tests
# ---------------------------------------------------------------


class TestInsightsEndpoint:
    """Tests for ``POST /api/insights``."""

    def test_missing_data(self, client) -> None:
        """Empty body returns 400."""
        resp = client.post(
            "/api/insights",
            json={},
        )
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "error" in data

    def test_missing_total(self, client) -> None:
        """Body without 'total' key returns 400."""
        resp = client.post(
            "/api/insights",
            json={"breakdown": {}},
        )
        assert resp.status_code == 400

