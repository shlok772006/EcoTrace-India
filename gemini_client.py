"""
gemini_client.py — EcoTrace India
All Gemini API calls and prompt building.
Reads GEMINI_API_KEY from environment variable ONLY — never hardcoded.
"""

import json
import logging
import os
from typing import Any

import google.generativeai as genai


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Gemini initialisation
# ---------------------------------------------------------------------------

_MODEL = None


def _get_model() -> genai.GenerativeModel:
    """Lazily initialise and return the Gemini model.

    The API key is read from the GEMINI_API_KEY environment variable.
    """
    global _MODEL
    if _MODEL is None:
        api_key: str | None = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set. "
                "Set it before starting the application."
            )
        genai.configure(api_key=api_key)
        _MODEL = genai.GenerativeModel("gemini-1.5-flash")
        logger.info("Gemini model initialised (gemini-1.5-flash)")
    return _MODEL


# ---------------------------------------------------------------------------
# Prompts — from PROMPT_STRATEGY.md
# ---------------------------------------------------------------------------

BASE_SYSTEM_PROMPT = """You are EcoBot, a friendly, practical, and encouraging carbon footprint
advisor specialized in the Indian context.

Your purpose: Help Indian individuals understand and reduce their carbon
footprint through simple, achievable, budget-friendly actions.

Your knowledge base:
- India-specific emission factors (India grid: 0.75 kg CO2/kWh)
- Indian transportation patterns (two-wheelers, auto-rickshaws, Indian Railways)
- Indian dietary habits (vegetarian/non-vegetarian split, regional cuisines)
- Indian government sustainability schemes (Solar Rooftop, PM e-DRIVE,
  UJALA LED scheme, Green India Mission)
- Indian climate context (monsoon patterns, urban heat islands, air quality)

Always:
- Give advice that is practical for an average Indian household
- Suggest free or low-cost actions first before expensive alternatives
- Use Indian examples, units, and references (rupees, km, kg LPG cylinders)
- Be warm and encouraging — every action matters
- Respond in: {language}
- Keep responses under 200 words unless the user asks for more detail

Never:
- Fabricate emission statistics or make up numbers
- Give advice that requires expensive purchases as the only option
- Express opinions on political parties or climate policy
- Answer questions completely unrelated to sustainability and carbon footprints
- Be preachy or make the user feel guilty"""


INSIGHTS_PROMPT = """You are EcoBot, an Indian carbon footprint advisor.

A user has just calculated their carbon footprint. Here is their data:

Total footprint: {total} tonnes CO2e per year
Breakdown:
- Energy (electricity + LPG): {energy} tonnes ({energy_pct}% of total)
- Transport: {transport} tonnes ({transport_pct}% of total)
- Diet: {diet} tonnes ({diet_pct}% of total)
- Waste: {waste} tonnes ({waste_pct}% of total)

Biggest emission source: {largest_category}
City tier: {city_tier}
India urban average: 5.0 tonnes/year
India national average: 2.19 tonnes/year

Generate EXACTLY 3 personalized carbon reduction tips targeting this
specific user's data. Focus on their biggest emission source first.

Respond in: {language}

Return ONLY valid JSON in this exact format (no markdown, no extra text):
{{
  "insights": [
    {{
      "tip": "specific actionable tip",
      "co2_saved_kg": 150,
      "difficulty": "easy",
      "category": "energy",
      "india_context": "one sentence making this relevant to India specifically"
    }},
    {{
      "tip": "specific actionable tip",
      "co2_saved_kg": 300,
      "difficulty": "medium",
      "category": "transport",
      "india_context": "one sentence making this relevant to India specifically"
    }},
    {{
      "tip": "specific actionable tip",
      "co2_saved_kg": 200,
      "difficulty": "hard",
      "category": "diet",
      "india_context": "one sentence making this relevant to India specifically"
    }}
  ],
  "motivational_message": "One warm, encouraging sentence personalized to their score"
}}"""


# ---------------------------------------------------------------------------
# Helper — safe JSON parse
# ---------------------------------------------------------------------------

def _parse_json_response(text: str) -> dict[str, Any] | None:
    """Try to extract valid JSON from Gemini's response.

    Handles cases where the model wraps JSON in markdown code fences.
    """
    cleaned = text.strip()
    # Strip markdown code fences if present
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line (```json) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Gemini JSON response: %s", e)
        logger.debug("Raw response: %s", text[:500])
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_insights(footprint_data: dict[str, Any], language: str = "English") -> dict[str, Any]:
    """Generate 3 personalized reduction tips using Gemini.

    Args:
        footprint_data: Full result from calculate_footprint() — must contain
                        total, breakdown, and largest_category.
        language: Response language (default English).

    Returns:
        Dict with 'insights' list and 'motivational_message', or an error dict.
    """
    model = _get_model()

    total = footprint_data["total"]
    breakdown = footprint_data["breakdown"]

    # Calculate percentages
    energy_pct = round((breakdown["energy"] / total) * 100) if total > 0 else 0
    transport_pct = round((breakdown["transport"] / total) * 100) if total > 0 else 0
    diet_pct = round((breakdown["diet"] / total) * 100) if total > 0 else 0
    waste_pct = round((breakdown["waste"] / total) * 100) if total > 0 else 0

    city_tier = footprint_data.get("city_tier", "metro")

    prompt = INSIGHTS_PROMPT.format(
        total=total,
        energy=breakdown["energy"],
        energy_pct=energy_pct,
        transport=breakdown["transport"],
        transport_pct=transport_pct,
        diet=breakdown["diet"],
        diet_pct=diet_pct,
        waste=breakdown["waste"],
        waste_pct=waste_pct,
        largest_category=footprint_data["largest_category"],
        city_tier=city_tier,
        language=language,
    )

    try:
        logger.info("Requesting Gemini insights for footprint %.2f tonnes", total)
        response = model.generate_content(
            [BASE_SYSTEM_PROMPT.format(language=language), prompt]
        )
        parsed = _parse_json_response(response.text)
        if parsed and "insights" in parsed:
            logger.info("Gemini insights generated successfully")
            return parsed
        else:
            logger.warning("Gemini returned unparseable insights response")
            return _fallback_insights(footprint_data)
    except Exception as e:
        logger.error("Gemini API error in get_insights: %s", e)
        return _fallback_insights(footprint_data)


# ---------------------------------------------------------------------------
# Fallback — used when Gemini is unavailable or returns invalid JSON
# ---------------------------------------------------------------------------

def _fallback_insights(footprint_data: dict[str, Any]) -> dict[str, Any]:
    """Provide sensible static tips when the AI is unavailable."""
    largest = footprint_data.get("largest_category", "energy")

    tips_by_category = {
        "energy": {
            "tip": "Switch to LED bulbs and 5-star rated appliances",
            "co2_saved_kg": 120,
            "difficulty": "easy",
            "category": "energy",
            "india_context": "The UJALA scheme offers LED bulbs at subsidised rates across India.",
        },
        "transport": {
            "tip": "Use public transport or carpool for your daily commute",
            "co2_saved_kg": 250,
            "difficulty": "medium",
            "category": "transport",
            "india_context": "Indian Railways is one of the greenest transport options at just 0.011 kg CO2/km.",
        },
        "diet": {
            "tip": "Try two meat-free days per week",
            "co2_saved_kg": 200,
            "difficulty": "easy",
            "category": "diet",
            "india_context": "India has one of the world's richest vegetarian culinary traditions to explore.",
        },
        "waste": {
            "tip": "Start segregating and composting wet waste at home",
            "co2_saved_kg": 80,
            "difficulty": "easy",
            "category": "waste",
            "india_context": "Many Indian cities now provide composting bins under Swachh Bharat Mission.",
        },
    }

    # Build 3 tips: start with largest category
    categories = ["energy", "transport", "diet", "waste"]
    categories.remove(largest)
    ordered = [largest] + categories[:2]

    return {
        "insights": [tips_by_category[c] for c in ordered],
        "motivational_message": "Every step you take towards reducing your footprint makes a difference. Keep going! 🌱",
    }
