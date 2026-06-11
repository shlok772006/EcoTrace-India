"""Gemini API client for EcoTrace India.

Handles all interactions with the Google Gemini generative-AI
model.  The API key is read **exclusively** from the
``GEMINI_API_KEY`` environment variable — it is never hard-coded.

Prompt templates follow ``PROMPT_STRATEGY.md`` exactly.  Each
public function returns a deterministic fallback when the API is
unreachable, so the front-end always has something to display.
"""

import json
import logging
from typing import Any

from google import genai

from config import Config
from constants import CHAT_HISTORY_WINDOW
from exceptions import GeminiAPIError

__all__ = [
    "ping",
    "get_insights",
    "get_action_plan",
    "get_chat_response",
    "get_progress_message",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Gemini initialisation
# ---------------------------------------------------------------

_CLIENT: genai.Client | None = None
_MODEL_NAME: str = "gemini-2.5-flash"


def _get_client() -> genai.Client:
    """Lazily initialise and return the Gemini client.

    The API key is sourced from :pyattr:`Config.GEMINI_API_KEY`.

    Returns:
        A configured ``genai.Client`` instance.

    Raises:
        GeminiAPIError: If the API key is missing.
    """
    global _CLIENT  # noqa: PLW0603
    if _CLIENT is None:
        api_key: str | None = Config.GEMINI_API_KEY
        if not api_key:
            raise GeminiAPIError(
                "GEMINI_API_KEY environment variable is "
                "not set. Set it before starting the "
                "application."
            )
        _CLIENT = genai.Client(api_key=api_key)
        logger.info(
            "Gemini client initialised (using %s)",
            _MODEL_NAME,
        )
    return _CLIENT


def ping() -> bool:
    """Check Gemini API connectivity.

    Sends a trivial generation request to verify that the
    API key is valid and the service is reachable.

    Returns:
        ``True`` if the API responded, ``False`` otherwise.
    """
    try:
        client = _get_client()
        response = client.models.generate_content(
            model=_MODEL_NAME,
            contents="Respond with 'ok'",
        )
        return bool(response.text)
    except Exception as exc:
        logger.error("Gemini API ping failed: %s", exc)
        return False


# ---------------------------------------------------------------
# Prompts — from PROMPT_STRATEGY.md
# ---------------------------------------------------------------

BASE_SYSTEM_PROMPT: str = (
    "You are EcoBot, a friendly, practical, and "
    "encouraging carbon footprint advisor specialized "
    "in the Indian context.\n\n"
    "Your purpose: Help Indian individuals understand "
    "and reduce their carbon footprint through simple, "
    "achievable, budget-friendly actions.\n\n"
    "Your knowledge base:\n"
    "- India-specific emission factors "
    "(India grid: 0.75 kg CO2/kWh)\n"
    "- Indian transportation patterns "
    "(two-wheelers, auto-rickshaws, Indian Railways)\n"
    "- Indian dietary habits "
    "(vegetarian/non-vegetarian split, "
    "regional cuisines)\n"
    "- Indian government sustainability schemes "
    "(Solar Rooftop, PM e-DRIVE, UJALA LED scheme, "
    "Green India Mission)\n"
    "- Indian climate context "
    "(monsoon patterns, urban heat islands, "
    "air quality)\n\n"
    "Always:\n"
    "- Give advice that is practical for an average "
    "Indian household\n"
    "- Suggest free or low-cost actions first before "
    "expensive alternatives\n"
    "- Use Indian examples, units, and references "
    "(rupees, km, kg LPG cylinders)\n"
    "- Be warm and encouraging — every action matters\n"
    "- Respond in: {language}\n"
    "- Keep responses under 200 words unless the user "
    "asks for more detail\n\n"
    "Never:\n"
    "- Fabricate emission statistics or make up numbers\n"
    "- Give advice that requires expensive purchases as "
    "the only option\n"
    "- Express opinions on political parties or climate "
    "policy\n"
    "- Answer questions completely unrelated to "
    "sustainability and carbon footprints\n"
    "- Be preachy or make the user feel guilty"
)


INSIGHTS_PROMPT: str = (
    "You are EcoBot, an Indian carbon footprint "
    "advisor.\n\n"
    "A user has just calculated their carbon footprint. "
    "Here is their data:\n\n"
    "Total footprint: {total} tonnes CO2e per year\n"
    "Breakdown:\n"
    "- Energy (electricity + LPG): {energy} tonnes "
    "({energy_pct}% of total)\n"
    "- Transport: {transport} tonnes "
    "({transport_pct}% of total)\n"
    "- Diet: {diet} tonnes ({diet_pct}% of total)\n"
    "- Waste: {waste} tonnes ({waste_pct}% of total)\n\n"
    "Biggest emission source: {largest_category}\n"
    "City tier: {city_tier}\n"
    "India urban average: 5.0 tonnes/year\n"
    "India national average: 2.19 tonnes/year\n\n"
    "Generate EXACTLY 3 personalized carbon reduction "
    "tips targeting this specific user's data. Focus on "
    "their biggest emission source first.\n\n"
    "Respond in: {language}\n\n"
    "Return ONLY valid JSON in this exact format "
    "(no markdown, no extra text):\n"
    '{{\n'
    '  "insights": [\n'
    '    {{\n'
    '      "tip": "specific actionable tip",\n'
    '      "co2_saved_kg": 150,\n'
    '      "difficulty": "easy",\n'
    '      "category": "energy",\n'
    '      "india_context": "one sentence making this '
    'relevant to India specifically"\n'
    '    }},\n'
    '    {{\n'
    '      "tip": "specific actionable tip",\n'
    '      "co2_saved_kg": 300,\n'
    '      "difficulty": "medium",\n'
    '      "category": "transport",\n'
    '      "india_context": "one sentence making this '
    'relevant to India specifically"\n'
    '    }},\n'
    '    {{\n'
    '      "tip": "specific actionable tip",\n'
    '      "co2_saved_kg": 200,\n'
    '      "difficulty": "hard",\n'
    '      "category": "diet",\n'
    '      "india_context": "one sentence making this '
    'relevant to India specifically"\n'
    '    }}\n'
    '  ],\n'
    '  "motivational_message": '
    '"One warm, encouraging sentence personalized '
    'to their score"\n'
    '}}'
)


ACTION_PLAN_PROMPT: str = (
    "You are EcoBot, an Indian carbon footprint "
    "advisor.\n\n"
    "Generate a practical 30-day carbon reduction "
    "action plan for this user:\n\n"
    "Their footprint: {total} tonnes CO2e/year\n"
    "Biggest source: {largest_category}\n"
    "Top areas to improve: {top_categories}\n"
    "City tier: {city_tier}\n"
    "Language: {language}\n\n"
    "The plan should start with the easiest, "
    "highest-impact actions in Week 1 and gradually "
    "introduce more challenging changes.\n\n"
    "Rules:\n"
    "- All actions must be achievable for an average "
    "Indian household\n"
    "- Prioritize free or low-cost actions\n"
    "- Include specific Indian products, apps, or "
    "schemes where relevant (e.g. KSRTC bus pass, "
    "BESCOM green tariff, Zomato plant-based "
    "options)\n"
    "- Each action should take less than 30 minutes "
    "to implement\n\n"
    "Return ONLY valid JSON (no markdown):\n"
    '{{\n'
    '  "estimated_annual_saving_tonnes": 0.8,\n'
    '  "weeks": [\n'
    '    {{\n'
    '      "week": 1,\n'
    '      "theme": "Quick Wins",\n'
    '      "actions": [\n'
    '        {{\n'
    '          "day_range": "Day 1-2",\n'
    '          "action": "specific action",\n'
    '          "impact": "saves X kg CO2/month",\n'
    '          "time_needed": "10 minutes"\n'
    '        }}\n'
    '      ]\n'
    '    }},\n'
    '    {{"week": 2, "theme": "...", '
    '"actions": [...]}},\n'
    '    {{"week": 3, "theme": "...", '
    '"actions": [...]}},\n'
    '    {{"week": 4, "theme": "...", '
    '"actions": [...]}}\n'
    '  ]\n'
    '}}'
)


CHAT_PROMPT: str = (
    "You are EcoBot, a friendly Indian carbon "
    "footprint and sustainability advisor.\n\n"
    "{base_system_prompt}\n\n"
    "The user is chatting with you on EcoTrace India, "
    "a carbon footprint tracking app. They may ask "
    "about:\n"
    "- Their specific footprint results\n"
    "- How to reduce emissions in specific areas\n"
    "- Climate change facts relevant to India\n"
    "- How Indian government schemes can help reduce "
    "their footprint\n"
    "- General sustainability questions\n\n"
    "If the user has calculated their footprint, their "
    "data is:\n"
    "{user_footprint_summary}\n\n"
    "Keep responses conversational, warm, and under "
    "150 words.\n"
    "Suggest relevant features of the EcoTrace app "
    'when appropriate (e.g. "You can track this in '
    'the Monthly Tracker →").'
)


PROGRESS_PROMPT: str = (
    "You are EcoBot, an Indian carbon footprint "
    "advisor.\n\n"
    "A user has logged their carbon footprint for "
    "this month.\n\n"
    "Previous month: {prev_total} tonnes\n"
    "This month: {current_total} tonnes\n"
    "Change: {change_pct}% {increase_or_decrease}\n"
    "Their biggest category this month: "
    "{largest_category}\n\n"
    "Write ONE short, warm, encouraging message "
    "(max 50 words) in {language}.\n"
    "If they improved: celebrate specifically what "
    "likely caused the improvement.\n"
    "If they got worse: be gentle, acknowledge life "
    "gets busy, suggest one easy fix.\n"
    "Never be preachy. Sound like a supportive friend, "
    "not a lecturer.\n"
    "Return only the message text, no JSON."
)


# ---------------------------------------------------------------
# Helper — safe JSON parse
# ---------------------------------------------------------------


def _parse_json_response(
    text: str,
) -> dict[str, Any] | None:
    """Extract valid JSON from a Gemini response string.

    Handles the common case where the model wraps its
    JSON output in markdown code fences.

    Args:
        text: Raw text returned by ``response.text``.

    Returns:
        Parsed dictionary, or ``None`` if parsing fails.
    """
    cleaned: str = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [
            line
            for line in lines
            if not line.strip().startswith("```")
        ]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error(
            "Failed to parse Gemini JSON response: %s",
            exc,
        )
        logger.debug("Raw response: %s", text[:500])
        return None


# ---------------------------------------------------------------
# Public API
# ---------------------------------------------------------------


def get_insights(
    footprint_data: dict[str, Any],
    language: str = "English",
) -> dict[str, Any]:
    """Generate 3 personalised reduction tips via Gemini.

    Args:
        footprint_data: Full result from
            ``calculate_footprint()`` — must contain
            ``total``, ``breakdown``, and
            ``largest_category``.
        language: Response language (default English).

    Returns:
        Dictionary with ``insights`` list and
        ``motivational_message``, or a static fallback.

    Raises:
        GeminiAPIError: Propagated only if the client
            cannot be initialised; transient call errors
            are caught and produce a fallback instead.
    """
    client = _get_client()

    total: float = footprint_data["total"]
    breakdown: dict[str, float] = footprint_data[
        "breakdown"
    ]

    def _pct(value: float) -> int:
        return round((value / total) * 100) if total else 0

    city_tier: str = footprint_data.get(
        "city_tier", "metro"
    )

    prompt: str = INSIGHTS_PROMPT.format(
        total=total,
        energy=breakdown["energy"],
        energy_pct=_pct(breakdown["energy"]),
        transport=breakdown["transport"],
        transport_pct=_pct(breakdown["transport"]),
        diet=breakdown["diet"],
        diet_pct=_pct(breakdown["diet"]),
        waste=breakdown["waste"],
        waste_pct=_pct(breakdown["waste"]),
        largest_category=footprint_data[
            "largest_category"
        ],
        city_tier=city_tier,
        language=language,
    )

    try:
        logger.info(
            "Requesting Gemini insights for "
            "footprint %.2f tonnes",
            total,
        )
        response = client.models.generate_content(
            model=_MODEL_NAME,
            contents=[
                BASE_SYSTEM_PROMPT.format(
                    language=language
                ),
                prompt,
            ],
        )
        parsed = _parse_json_response(response.text)
        if parsed and "insights" in parsed:
            logger.info(
                "Gemini insights generated successfully"
            )
            return parsed
        logger.warning(
            "Gemini returned unparseable insights"
        )
        return _fallback_insights(footprint_data)
    except GeminiAPIError:
        raise
    except Exception as exc:
        logger.error(
            "Gemini API error in get_insights: %s", exc
        )
        return _fallback_insights(footprint_data)


def get_action_plan(
    footprint_data: dict[str, Any],
    language: str = "English",
) -> dict[str, Any]:
    """Generate a 30-day action plan via Gemini.

    Args:
        footprint_data: Full result from
            ``calculate_footprint()``.
        language: Response language (default English).

    Returns:
        Dictionary with ``estimated_annual_saving_tonnes``
        and ``weeks`` list, or a static fallback.
    """
    client = _get_client()

    breakdown: dict[str, float] = footprint_data[
        "breakdown"
    ]
    sorted_cats = sorted(
        breakdown.items(),
        key=lambda x: x[1],
        reverse=True,
    )
    top_categories: str = ", ".join(
        c[0] for c in sorted_cats[:2]
    )

    prompt: str = ACTION_PLAN_PROMPT.format(
        total=footprint_data["total"],
        largest_category=footprint_data[
            "largest_category"
        ],
        top_categories=top_categories,
        city_tier=footprint_data.get(
            "city_tier", "metro"
        ),
        language=language,
    )

    try:
        logger.info(
            "Requesting Gemini action plan for "
            "footprint %.2f tonnes",
            footprint_data["total"],
        )
        response = client.models.generate_content(
            model=_MODEL_NAME,
            contents=[
                BASE_SYSTEM_PROMPT.format(
                    language=language
                ),
                prompt,
            ],
        )
        parsed = _parse_json_response(response.text)
        if parsed and "weeks" in parsed:
            logger.info(
                "Gemini action plan generated "
                "successfully"
            )
            return parsed
        logger.warning(
            "Gemini returned unparseable action plan"
        )
        return _fallback_action_plan(footprint_data)
    except GeminiAPIError:
        raise
    except Exception as exc:
        logger.error(
            "Gemini API error in get_action_plan: %s",
            exc,
        )
        return _fallback_action_plan(footprint_data)


def get_chat_response(
    message: str,
    chat_history: list[dict[str, str]],
    footprint_data: dict[str, Any] | None = None,
    language: str = "English",
) -> str:
    """Get a conversational response from Gemini.

    Args:
        message: The user's latest message.
        chat_history: Prior messages, each a dict with
            ``role`` (``"user"`` / ``"bot"``) and
            ``text``.
        footprint_data: Optional footprint result to
            give the model user-specific context.
        language: Response language.

    Returns:
        Response text from Gemini, or a fallback string.
    """
    client = _get_client()

    if footprint_data and "total" in footprint_data:
        bd = footprint_data["breakdown"]
        summary: str = (
            f"Total: {footprint_data['total']} "
            f"tonnes/year. "
            f"Breakdown: Energy {bd['energy']}t, "
            f"Transport {bd['transport']}t, "
            f"Diet {bd['diet']}t, "
            f"Waste {bd['waste']}t. "
            f"Biggest source: "
            f"{footprint_data['largest_category']}."
        )
    else:
        summary = (
            "The user has not calculated their "
            "footprint yet."
        )

    system_prompt: str = CHAT_PROMPT.format(
        base_system_prompt=BASE_SYSTEM_PROMPT.format(
            language=language
        ),
        user_footprint_summary=summary,
    )

    contents: list[str] = [system_prompt]
    recent = chat_history[-CHAT_HISTORY_WINDOW:]
    for entry in recent:
        role = (
            "User"
            if entry.get("role") == "user"
            else "EcoBot"
        )
        contents.append(
            f"{role}: {entry.get('text', '')}"
        )
    contents.append(f"User: {message}")

    try:
        logger.info("Requesting Gemini chat response")
        response = client.models.generate_content(
            model=_MODEL_NAME,
            contents=contents,
        )
        logger.info(
            "Gemini chat response generated "
            "successfully"
        )
        return response.text.strip()
    except GeminiAPIError:
        raise
    except Exception as exc:
        logger.error(
            "Gemini API error in get_chat_response: %s",
            exc,
        )
        return _fallback_chat_response()


def get_progress_message(
    prev_total: float,
    current_total: float,
    largest_category: str,
    language: str = "English",
) -> str:
    """Generate a motivational message for progress.

    Args:
        prev_total: Previous month's total (tonnes).
        current_total: Current month's total (tonnes).
        largest_category: Biggest emission category
            this month.
        language: Response language.

    Returns:
        A short motivational message string.
    """
    client = _get_client()

    change_pct: float = (
        round(
            (
                (current_total - prev_total)
                / prev_total
            )
            * 100,
            1,
        )
        if prev_total > 0
        else 0.0
    )
    increase_or_decrease: str = (
        "decrease"
        if current_total < prev_total
        else "increase"
    )

    prompt: str = PROGRESS_PROMPT.format(
        prev_total=prev_total,
        current_total=current_total,
        change_pct=abs(change_pct),
        increase_or_decrease=increase_or_decrease,
        largest_category=largest_category,
        language=language,
    )

    try:
        logger.info(
            "Requesting Gemini progress message"
        )
        response = client.models.generate_content(
            model=_MODEL_NAME,
            contents=[
                BASE_SYSTEM_PROMPT.format(
                    language=language
                ),
                prompt,
            ],
        )
        logger.info(
            "Gemini progress message generated "
            "successfully"
        )
        return response.text.strip()
    except GeminiAPIError:
        raise
    except Exception as exc:
        logger.error(
            "Gemini API error in "
            "get_progress_message: %s",
            exc,
        )
        return _fallback_progress_message(
            prev_total, current_total
        )


# ---------------------------------------------------------------
# Fallbacks — used when Gemini is unavailable
# ---------------------------------------------------------------


def _fallback_insights(
    footprint_data: dict[str, Any],
) -> dict[str, Any]:
    """Return static tips when the AI is unavailable.

    Args:
        footprint_data: The user's footprint result.

    Returns:
        Dictionary matching the ``insights`` schema.
    """
    largest: str = footprint_data.get(
        "largest_category", "energy"
    )

    tips: dict[str, dict[str, Any]] = {
        "energy": {
            "tip": (
                "Switch to LED bulbs and 5-star "
                "rated appliances"
            ),
            "co2_saved_kg": 120,
            "difficulty": "easy",
            "category": "energy",
            "india_context": (
                "The UJALA scheme offers LED bulbs "
                "at subsidised rates across India."
            ),
        },
        "transport": {
            "tip": (
                "Use public transport or carpool "
                "for your daily commute"
            ),
            "co2_saved_kg": 250,
            "difficulty": "medium",
            "category": "transport",
            "india_context": (
                "Indian Railways is one of the "
                "greenest transport options at just "
                "0.011 kg CO2/km."
            ),
        },
        "diet": {
            "tip": "Try two meat-free days per week",
            "co2_saved_kg": 200,
            "difficulty": "easy",
            "category": "diet",
            "india_context": (
                "India has one of the world's "
                "richest vegetarian culinary "
                "traditions to explore."
            ),
        },
        "waste": {
            "tip": (
                "Start segregating and composting "
                "wet waste at home"
            ),
            "co2_saved_kg": 80,
            "difficulty": "easy",
            "category": "waste",
            "india_context": (
                "Many Indian cities now provide "
                "composting bins under Swachh "
                "Bharat Mission."
            ),
        },
    }

    categories: list[str] = [
        "energy",
        "transport",
        "diet",
        "waste",
    ]
    categories.remove(largest)
    ordered: list[str] = [largest] + categories[:2]

    return {
        "insights": [tips[c] for c in ordered],
        "motivational_message": (
            "Every step you take towards reducing "
            "your footprint makes a difference. "
            "Keep going! 🌱"
        ),
    }


def _fallback_action_plan(
    footprint_data: dict[str, Any],
) -> dict[str, Any]:
    """Return a static action plan when Gemini is down.

    Args:
        footprint_data: The user's footprint result.

    Returns:
        Dictionary matching the ``action_plan`` schema.
    """
    return {
        "estimated_annual_saving_tonnes": 0.5,
        "weeks": [
            {
                "week": 1,
                "theme": "Quick Wins",
                "actions": [
                    {
                        "day_range": "Day 1-2",
                        "action": (
                            "Switch off appliances "
                            "at the wall when not "
                            "in use"
                        ),
                        "impact": (
                            "saves 5 kg CO2/month"
                        ),
                        "time_needed": "5 minutes",
                    },
                    {
                        "day_range": "Day 3-4",
                        "action": (
                            "Replace one light bulb "
                            "with an LED"
                        ),
                        "impact": (
                            "saves 3 kg CO2/month"
                        ),
                        "time_needed": "10 minutes",
                    },
                    {
                        "day_range": "Day 5-7",
                        "action": (
                            "Set AC to 24°C instead "
                            "of lower"
                        ),
                        "impact": (
                            "saves 8 kg CO2/month"
                        ),
                        "time_needed": "1 minute",
                    },
                ],
            },
            {
                "week": 2,
                "theme": "Transport Changes",
                "actions": [
                    {
                        "day_range": "Day 8-10",
                        "action": (
                            "Use public transport "
                            "for one trip you "
                            "normally drive"
                        ),
                        "impact": (
                            "saves 4 kg CO2/month"
                        ),
                        "time_needed": "15 minutes",
                    },
                    {
                        "day_range": "Day 11-14",
                        "action": (
                            "Combine errands into "
                            "one trip to reduce "
                            "driving"
                        ),
                        "impact": (
                            "saves 3 kg CO2/month"
                        ),
                        "time_needed": "10 minutes",
                    },
                ],
            },
            {
                "week": 3,
                "theme": "Food & Diet",
                "actions": [
                    {
                        "day_range": "Day 15-18",
                        "action": (
                            "Try two meat-free days "
                            "this week"
                        ),
                        "impact": (
                            "saves 6 kg CO2/month"
                        ),
                        "time_needed": "0 minutes",
                    },
                    {
                        "day_range": "Day 19-21",
                        "action": (
                            "Buy local seasonal "
                            "produce from your "
                            "nearest market"
                        ),
                        "impact": (
                            "saves 2 kg CO2/month"
                        ),
                        "time_needed": "20 minutes",
                    },
                ],
            },
            {
                "week": 4,
                "theme": "Waste & Habits",
                "actions": [
                    {
                        "day_range": "Day 22-25",
                        "action": (
                            "Start segregating wet "
                            "and dry waste at home"
                        ),
                        "impact": (
                            "saves 3 kg CO2/month"
                        ),
                        "time_needed": "10 minutes",
                    },
                    {
                        "day_range": "Day 26-28",
                        "action": (
                            "Carry a reusable bag "
                            "and water bottle "
                            "everywhere"
                        ),
                        "impact": (
                            "saves 1 kg CO2/month"
                        ),
                        "time_needed": "5 minutes",
                    },
                    {
                        "day_range": "Day 29-30",
                        "action": (
                            "Review your month and "
                            "set goals for next "
                            "month"
                        ),
                        "impact": "builds habit",
                        "time_needed": "15 minutes",
                    },
                ],
            },
        ],
    }


def _fallback_chat_response() -> str:
    """Return a static chat message when Gemini is down.

    Returns:
        A helpful fallback string.
    """
    return (
        "I'm having trouble connecting right now, "
        "but here's a quick tip: switching to LED "
        "bulbs is one of the easiest ways to reduce "
        "your carbon footprint. The UJALA scheme "
        "offers them at subsidised rates! 🌱 "
        "Please try again in a moment."
    )


def _fallback_progress_message(
    prev_total: float,
    current_total: float,
) -> str:
    """Return a static progress message.

    Args:
        prev_total: Previous month's total (tonnes).
        current_total: Current month's total (tonnes).

    Returns:
        An encouraging message string.
    """
    if current_total < prev_total:
        return (
            "Great progress! Your footprint is "
            "heading in the right direction. "
            "Keep it up! 🌱"
        )
    if current_total > prev_total:
        return (
            "Life gets busy sometimes — don't "
            "worry! Try one small change this "
            "week, like switching off standby "
            "appliances. 💪"
        )
    return (
        "Staying steady is still a win! Look for "
        "one new way to reduce your impact this "
        "month. 🌍"
    )
