# DATA_MODEL.md — EcoTrace India
### Emission Factors, Calculation Formulas & Benchmark Values
> This is the single source of truth for all numbers in the app.
> Anti-Gravity must use ONLY these values. Never invent emission factors.

---

## <EmissionFactors>

### Energy
```python
ENERGY_FACTORS = {
    # India national grid average: 0.75 kg CO2 per kWh
    # Source: Central Electricity Authority, India (2023)
    "electricity_kwh": 0.75,          # kg CO2 per kWh consumed

    # LPG: 1 standard cylinder = 14.2 kg LPG
    # Source: Ministry of Petroleum, India
    "lpg_per_cylinder": 37.68,        # kg CO2 per 14.2kg cylinder (2.654 kg CO2/kg LPG)

    # PNG (Piped Natural Gas)
    "png_per_scm": 2.0,               # kg CO2 per standard cubic metre
}
```

### Transport
```python
TRANSPORT_FACTORS = {
    # Source: Ministry of Road Transport & Highways + IPCC guidelines
    "petrol_car_per_km": 0.171,       # kg CO2 per km (average Indian petrol car)
    "diesel_car_per_km": 0.141,       # kg CO2 per km (average Indian diesel car)
    "two_wheeler_per_km": 0.089,      # kg CO2 per km (average Indian two-wheeler)
    "auto_rickshaw_per_km": 0.072,    # kg CO2 per km (CNG auto)
    "bus_per_km": 0.089,              # kg CO2 per km per passenger (city bus)
    "metro_per_km": 0.031,            # kg CO2 per km per passenger (Indian metro)
    "train_per_km": 0.011,            # kg CO2 per km per passenger (Indian Railways)
    "domestic_flight_per_km": 0.255,  # kg CO2 per km per passenger (short haul)
    "cab_per_km": 0.171,              # kg CO2 per km (treat as petrol car)
}
```

### Diet
```python
DIET_FACTORS = {
    # Annual dietary emissions - Source: Oxford University food study + India adjustments
    "vegan": 1500,                    # kg CO2e per year
    "vegetarian": 1700,               # kg CO2e per year
    "non_vegetarian": 2500,           # kg CO2e per year (avg 3-4 times/week meat)
    "heavy_meat": 3300,               # kg CO2e per year (daily meat consumption)
}
```

### Waste
```python
WASTE_FACTORS = {
    # Source: CPCB India waste emission guidelines
    "landfill_per_kg": 0.5,           # kg CO2e per kg waste sent to landfill
    "recycled_reduction": 0.3,        # 30% reduction if recycling regularly
    "composting_reduction": 0.4,      # 40% reduction if composting wet waste
}
```

</EmissionFactors>

---

## <BenchmarkValues>

```python
INDIA_BENCHMARKS = {
    # Source: World Bank / EDGAR 2024 data
    "india_national_average": 2.19,   # tonnes CO2 per person per year (2024)
    "india_urban_average": 5.0,       # tonnes CO2 per person per year
    "india_rural_average": 1.2,       # tonnes CO2 per person per year
    "global_average": 4.7,            # tonnes CO2 per person per year
    "global_target_2050": 2.0,        # tonnes CO2 per person per year (Paris Agreement)
    "usa_average": 14.4,              # tonnes CO2 per person per year
    "china_average": 8.0,             # tonnes CO2 per person per year
    "eu_average": 6.4,                # tonnes CO2 per person per year
}

OFFSET_VALUES = {
    # Source: Various forestry studies
    "tree_absorption_per_year": 0.025,   # tonnes CO2 per mature tree per year
    "solar_panel_saving_per_kw": 1.5,    # tonnes CO2 saved per kW installed per year
}
```

</BenchmarkValues>

---

## <CalculationFormulas>

### Total Annual Carbon Footprint
```python
def calculate_footprint(user_data: dict) -> dict:
    """
    All inputs are monthly figures. Multiply by 12 for annual.
    Returns breakdown by category and total in tonnes CO2e/year.
    """

    # --- ENERGY ---
    electricity_annual = (user_data["electricity_kwh"] * 12
                          * ENERGY_FACTORS["electricity_kwh"]) / 1000  # convert kg to tonnes

    lpg_annual = (user_data["lpg_cylinders"] * 12
                  * ENERGY_FACTORS["lpg_per_cylinder"]) / 1000

    energy_total = electricity_annual + lpg_annual

    # --- TRANSPORT ---
    transport_total = (
        (user_data["petrol_car_km"] * TRANSPORT_FACTORS["petrol_car_per_km"] * 12)
      + (user_data["two_wheeler_km"] * TRANSPORT_FACTORS["two_wheeler_per_km"] * 12)
      + (user_data["train_km"] * TRANSPORT_FACTORS["train_per_km"] * 12)
      + (user_data["flight_km"] * TRANSPORT_FACTORS["domestic_flight_per_km"] * 12)
    ) / 1000

    # --- DIET ---
    diet_total = DIET_FACTORS[user_data["diet_type"]] / 1000  # already annual

    # --- WASTE ---
    waste_kg_annual = user_data["waste_kg"] * 12
    waste_total = (waste_kg_annual * WASTE_FACTORS["landfill_per_kg"]) / 1000
    if user_data.get("recycles"):
        waste_total *= (1 - WASTE_FACTORS["recycled_reduction"])
    if user_data.get("composts"):
        waste_total *= (1 - WASTE_FACTORS["composting_reduction"])

    grand_total = energy_total + transport_total + diet_total + waste_total

    return {
        "total": round(grand_total, 2),
        "breakdown": {
            "energy": round(energy_total, 2),
            "transport": round(transport_total, 2),
            "diet": round(diet_total, 2),
            "waste": round(waste_total, 2),
        },
        "largest_category": max(
            ["energy", "transport", "diet", "waste"],
            key=lambda x: locals()[f"{x}_total"]
        )
    }
```

### Eco Score Formula
```python
def calculate_eco_score(total_tonnes: float) -> dict:
    """
    Score relative to India urban average (5.0 tonnes).
    A+ = hero, F = high impact.
    """
    urban_avg = INDIA_BENCHMARKS["india_urban_average"]
    ratio = total_tonnes / urban_avg

    if ratio <= 0.4:
        return {"grade": "A+", "label": "Climate Hero 🌟", "color": "#00C853"}
    elif ratio <= 0.6:
        return {"grade": "A",  "label": "Eco Champion 🌿", "color": "#43A047"}
    elif ratio <= 0.8:
        return {"grade": "B",  "label": "Green Thinker 🍃", "color": "#7CB342"}
    elif ratio <= 1.0:
        return {"grade": "C",  "label": "Average Impact 🌍", "color": "#FDD835"}
    elif ratio <= 1.4:
        return {"grade": "D",  "label": "Above Average ⚠️", "color": "#FB8C00"}
    else:
        return {"grade": "F",  "label": "High Impact 🔴", "color": "#E53935"}
```

### Tree Offset Formula
```python
def calculate_tree_offset(total_tonnes: float) -> dict:
    trees_needed = total_tonnes / OFFSET_VALUES["tree_absorption_per_year"]
    years_to_offset = 1  # if you plant that many trees
    return {
        "trees_needed": round(trees_needed),
        "equivalent_car_km": round(total_tonnes * 5848),  # km at 171g/km
        "solar_panels_kw": round(total_tonnes / OFFSET_VALUES["solar_panel_saving_per_kw"], 1)
    }
```

</CalculationFormulas>

---

## <DataSchema>

### Calculator Input (from form)
```json
{
  "electricity_kwh": 150,
  "lpg_cylinders": 1.5,
  "petrol_car_km": 500,
  "two_wheeler_km": 200,
  "train_km": 100,
  "flight_km": 0,
  "diet_type": "non_vegetarian",
  "waste_kg": 20,
  "recycles": true,
  "composts": false,
  "city_tier": "metro",
  "language": "English"
}
```

### Calculator Output (to frontend + Gemini)
```json
{
  "total": 4.82,
  "breakdown": {
    "energy": 1.62,
    "transport": 1.21,
    "diet": 2.50,
    "waste": 0.09
  },
  "largest_category": "diet",
  "eco_score": {"grade": "C", "label": "Average Impact 🌍", "color": "#FDD835"},
  "benchmarks": {
    "india_national": 2.19,
    "india_urban": 5.0,
    "global": 4.7,
    "target_2050": 2.0
  },
  "tree_offset": {
    "trees_needed": 193,
    "equivalent_car_km": 28167,
    "solar_panels_kw": 3.2
  }
}
```

### Monthly Progress Entry (localStorage)
```json
{
  "month": "2025-05",
  "total": 4.82,
  "breakdown": {"energy": 1.62, "transport": 1.21, "diet": 2.50, "waste": 0.09}
}
```

</DataSchema>
