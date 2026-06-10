import json
import pytest
from app import app
from calculator import load_emission_factors

@pytest.fixture
def client():
    # Load emission factors before testing
    load_emission_factors()
    
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    """Test that the health endpoint returns expected JSON."""
    response = client.get('/health')
    assert response.status_code in [200, 503]
    data = json.loads(response.data)
    assert "status" in data
    assert "services" in data

def test_calculate_valid_input(client):
    """Test calculation with normal data."""
    valid_data = {
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
        "language": "English"
    }
    response = client.post('/api/calculate', json=valid_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "total" in data
    assert "breakdown" in data
    assert "eco_score" in data
    assert "benchmarks" in data

def test_calculate_all_zeros(client):
    """Test calculation with zero usage."""
    zero_data = {
        "electricity_kwh": 0,
        "lpg_cylinders": 0,
        "petrol_car_km": 0,
        "two_wheeler_km": 0,
        "train_km": 0,
        "flight_km": 0,
        "diet_type": "vegan",
        "waste_kg": 0,
        "recycles": True,
        "composts": True,
        "city_tier": "rural",
        "language": "English"
    }
    response = client.post('/api/calculate', json=zero_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["total"] > 0  # Still > 0 because diet always has a baseline (1500 kg for vegan = 1.5t)
    assert data["breakdown"]["energy"] == 0

def test_calculate_maximum_values(client):
    """Test calculation with unusually high numbers."""
    max_data = {
        "electricity_kwh": 99999,
        "lpg_cylinders": 999,
        "petrol_car_km": 99999,
        "two_wheeler_km": 99999,
        "train_km": 99999,
        "flight_km": 99999,
        "diet_type": "heavy_meat",
        "waste_kg": 9999,
        "recycles": False,
        "composts": False,
        "city_tier": "metro",
        "language": "English"
    }
    response = client.post('/api/calculate', json=max_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["total"] > 500  # Clamped values still result in a very high footprint

def test_calculate_missing_fields(client):
    """Test calculation with missing required fields defaults gracefully."""
    missing_data = {
        "electricity_kwh": 100
        # Missing almost everything
    }
    response = client.post('/api/calculate', json=missing_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["breakdown"]["transport"] == 0

def test_calculate_invalid_diet(client):
    """Test calculation with an invalid diet type."""
    invalid_data = {
        "electricity_kwh": 100,
        "lpg_cylinders": 1,
        "petrol_car_km": 500,
        "two_wheeler_km": 100,
        "train_km": 50,
        "flight_km": 0,
        "diet_type": "alien_food",
        "waste_kg": 15,
        "recycles": True,
        "composts": False,
        "city_tier": "metro",
        "language": "English"
    }
    response = client.post('/api/calculate', json=invalid_data)
    assert response.status_code == 400
    assert b"Invalid diet_type" in response.data

def test_xss_sanitization(client):
    """Test that bleach sanitizes malicious inputs in text fields."""
    xss_data = {
        "electricity_kwh": 100,
        "lpg_cylinders": 1,
        "petrol_car_km": 500,
        "two_wheeler_km": 100,
        "train_km": 50,
        "flight_km": 0,
        "diet_type": "vegan",
        "waste_kg": 15,
        "recycles": True,
        "composts": False,
        "city_tier": "metro",
        "language": "<script>alert('xss')</script>English"
    }
    response = client.post('/api/calculate', json=xss_data)
    # The API should just bleach the string and proceed, or reject it.
    # App logic sanitizes "language" so it shouldn't contain the script tag.
    assert response.status_code == 200
    data = json.loads(response.data)
    # Language is passed through in the result
    assert "<script>" not in data.get("language", "")
