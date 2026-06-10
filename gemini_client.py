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


ACTION_PLAN_PROMPT = """You are EcoBot, an Indian carbon footprint advisor.

Generate a practical 30-day carbon reduction action plan for this user:

Their footprint: {total} tonnes CO2e/year
Biggest source: {largest_category}
Top areas to improve: {top_categories}
City tier: {city_tier}
Language: {language}

The plan should start with the easiest, highest-impact actions in Week 1
and gradually introduce more challenging changes.

Rules:
- All actions must be achievable for an average Indian household
- Prioritize free or low-cost actions
- Include specific Indian products, apps, or schemes where relevant
  (e.g. KSRTC bus pass, BESCOM green tariff, Zomato plant-based options)
- Each action should take less than 30 minutes to implement

Return ONLY valid JSON (no markdown):
{{
  "estimated_annual_saving_tonnes": 0.8,
  "weeks": [
    {{
      "week": 1,
      "theme": "Quick Wins",
      "actions": [
        {{
          "day_range": "Day 1-2",
          "action": "specific action",
          "impact": "saves X kg CO2/month",
          "time_needed": "10 minutes"
        }}
      ]
    }},
    {{"week": 2, "theme": "...", "actions": [...]}},
    {{"week": 3, "theme": "...", "actions": [...]}},
    {{"week": 4, "theme": "...", "actions": [...]}}
  ]
}}"""


CHAT_PROMPT = """You are EcoBot, a friendly Indian carbon footprint and sustainability advisor.

{base_system_prompt}

The user is chatting with you on EcoTrace India, a carbon footprint
tracking app. They may ask about:
- Their specific footprint results
- How to reduce emissions in specific areas
- Climate change facts relevant to India
- How Indian government schemes can help reduce their footprint
- General sustainability questions

If the user has calculated their footprint, their data is:
{user_footprint_summary}

Keep responses conversational, warm, and under 150 words.
Suggest relevant features of the EcoTrace app when appropriate
(e.g. "You can track this in the Monthly Tracker →")."""


PROGRESS_PROMPT = """You are EcoBot, an Indian carbon footprint advisor.

A user has logged their carbon footprint for this month.

Previous month: {prev_total} tonnes
This month: {current_total} tonnes
Change: {change_pct}% {increase_or_decrease}
Their biggest category this month: {largest_category}

Write ONE short, warm, encouraging message (max 50 words) in {language}.
If they improved: celebrate specifically what likely caused the improvement.
If they got worse: be gentle, acknowledge life gets busy, suggest one easy fix.
Never be preachy. Sound like a supportive friend, not a lecturer.
Return only the message text, no JSON."""



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


def get_action_plan(footprint_data: dict[str, Any], language: str = "English") -> dict[str, Any]:
    """Generate a 30-day action plan using Gemini.

    Args:
        footprint_data: Full result from calculate_footprint().
        language: Response language (default English).

    Returns:
        Dict with 'estimated_annual_saving_tonnes' and 'weeks' list, or fallback.
    """
    model = _get_model()

    breakdown = footprint_data["breakdown"]
    # Sort categories by emission value descending
    sorted_cats = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
    top_categories = ", ".join([c[0] for c in sorted_cats[:2]])

    prompt = ACTION_PLAN_PROMPT.format(
        total=footprint_data["total"],
        largest_category=footprint_data["largest_category"],
        top_categories=top_categories,
        city_tier=footprint_data.get("city_tier", "metro"),
        language=language,
    )

    try:
        logger.info("Requesting Gemini action plan for footprint %.2f tonnes", footprint_data["total"])
        response = model.generate_content(
            [BASE_SYSTEM_PROMPT.format(language=language), prompt]
        )
        parsed = _parse_json_response(response.text)
        if parsed and "weeks" in parsed:
            logger.info("Gemini action plan generated successfully")
            return parsed
        else:
            logger.warning("Gemini returned unparseable action plan response")
            return _fallback_action_plan(footprint_data)
    except Exception as e:
        logger.error("Gemini API error in get_action_plan: %s", e)
        return _fallback_action_plan(footprint_data)


def get_chat_response(
    message: str,
    chat_history: list[dict[str, str]],
    footprint_data: dict[str, Any] | None = None,
    language: str = "English",
) -> str:
    """Get a chat response from Gemini.

    Args:
        message: The user's message.
        chat_history: List of prior messages [{"role": "user"/"bot", "text": "..."}].
        footprint_data: Optional footprint result for context.
        language: Response language.

    Returns:
        Response text from Gemini, or a fallback string.
    """
    model = _get_model()

    # Build footprint summary for context
    if footprint_data and "total" in footprint_data:
        summary = (
            f"Total: {footprint_data['total']} tonnes/year. "
            f"Breakdown: Energy {footprint_data['breakdown']['energy']}t, "
            f"Transport {footprint_data['breakdown']['transport']}t, "
            f"Diet {footprint_data['breakdown']['diet']}t, "
            f"Waste {footprint_data['breakdown']['waste']}t. "
            f"Biggest source: {footprint_data['largest_category']}."
        )
    else:
        summary = "The user has not calculated their footprint yet."

    system_prompt = CHAT_PROMPT.format(
        base_system_prompt=BASE_SYSTEM_PROMPT.format(language=language),
        user_footprint_summary=summary,
    )

    # Build conversation for Gemini
    contents = [system_prompt]
    for entry in chat_history[-10:]:  # Keep last 10 messages for context
        role = "User" if entry.get("role") == "user" else "EcoBot"
        contents.append(f"{role}: {entry.get('text', '')}")
    contents.append(f"User: {message}")

    try:
        logger.info("Requesting Gemini chat response")
        response = model.generate_content(contents)
        logger.info("Gemini chat response generated successfully")
        return response.text.strip()
    except Exception as e:
        logger.error("Gemini API error in get_chat_response: %s", e)
        return _fallback_chat_response()


def get_progress_message(
    prev_total: float,
    current_total: float,
    largest_category: str,
    language: str = "English",
) -> str:
    """Generate a motivational message for monthly progress.

    Args:
        prev_total: Previous month's total in tonnes.
        current_total: Current month's total in tonnes.
        largest_category: Biggest emission category this month.
        language: Response language.

    Returns:
        A short motivational message string.
    """
    model = _get_model()

    change_pct = round(((current_total - prev_total) / prev_total) * 100, 1) if prev_total > 0 else 0
    increase_or_decrease = "decrease" if current_total < prev_total else "increase"

    prompt = PROGRESS_PROMPT.format(
        prev_total=prev_total,
        current_total=current_total,
        change_pct=abs(change_pct),
        increase_or_decrease=increase_or_decrease,
        largest_category=largest_category,
        language=language,
    )

    try:
        logger.info("Requesting Gemini progress message")
        response = model.generate_content(
            [BASE_SYSTEM_PROMPT.format(language=language), prompt]
        )
        logger.info("Gemini progress message generated successfully")
        return response.text.strip()
    except Exception as e:
        logger.error("Gemini API error in get_progress_message: %s", e)
        return _fallback_progress_message(prev_total, current_total)


# ---------------------------------------------------------------------------
# Fallbacks — used when Gemini is unavailable or returns invalid JSON
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


def _fallback_action_plan(footprint_data: dict[str, Any]) -> dict[str, Any]:
    """Provide a static action plan when Gemini is unavailable."""
    largest = footprint_data.get("largest_category", "energy")
    return {
        "estimated_annual_saving_tonnes": 0.5,
        "weeks": [
            {
                "week": 1,
                "theme": "Quick Wins",
                "actions": [
                    {"day_range": "Day 1-2", "action": "Switch off appliances at the wall when not in use", "impact": "saves 5 kg CO2/month", "time_needed": "5 minutes"},
                    {"day_range": "Day 3-4", "action": "Replace one light bulb with an LED", "impact": "saves 3 kg CO2/month", "time_needed": "10 minutes"},
                    {"day_range": "Day 5-7", "action": "Set AC to 24°C instead of lower", "impact": "saves 8 kg CO2/month", "time_needed": "1 minute"},
                ],
            },
            {
                "week": 2,
                "theme": "Transport Changes",
                "actions": [
                    {"day_range": "Day 8-10", "action": "Use public transport for one trip you normally drive", "impact": "saves 4 kg CO2/month", "time_needed": "15 minutes"},
                    {"day_range": "Day 11-14", "action": "Combine errands into one trip to reduce driving", "impact": "saves 3 kg CO2/month", "time_needed": "10 minutes"},
                ],
            },
            {
                "week": 3,
                "theme": "Food & Diet",
                "actions": [
                    {"day_range": "Day 15-18", "action": "Try two meat-free days this week", "impact": "saves 6 kg CO2/month", "time_needed": "0 minutes"},
                    {"day_range": "Day 19-21", "action": "Buy local seasonal produce from your nearest market", "impact": "saves 2 kg CO2/month", "time_needed": "20 minutes"},
                ],
            },
            {
                "week": 4,
                "theme": "Waste & Habits",
                "actions": [
                    {"day_range": "Day 22-25", "action": "Start segregating wet and dry waste at home", "impact": "saves 3 kg CO2/month", "time_needed": "10 minutes"},
                    {"day_range": "Day 26-28", "action": "Carry a reusable bag and water bottle everywhere", "impact": "saves 1 kg CO2/month", "time_needed": "5 minutes"},
                    {"day_range": "Day 29-30", "action": "Review your month and set goals for next month", "impact": "builds habit", "time_needed": "15 minutes"},
                ],
            },
        ],
    }


def _fallback_chat_response() -> str:
    """Provide a fallback chat response when Gemini is unavailable."""
    return (
        "I'm having trouble connecting right now, but here's a quick tip: "
        "switching to LED bulbs is one of the easiest ways to reduce your "
        "carbon footprint. The UJALA scheme offers them at subsidised rates! 🌱 "
        "Please try again in a moment."
    )


def _fallback_progress_message(prev_total: float, current_total: float) -> str:
    """Provide a static progress message when Gemini is unavailable."""
    if current_total < prev_total:
        return "Great progress! Your footprint is heading in the right direction. Keep it up! 🌱"
    elif current_total > prev_total:
        return "Life gets busy sometimes — don't worry! Try one small change this week, like switching off standby appliances. 💪"
    else:
        return "Staying steady is still a win! Look for one new way to reduce your impact this month. 🌍"
