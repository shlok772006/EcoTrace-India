"""
app.py — EcoTrace India
Flask application with all routes and API endpoints.
Deployed on Render with gunicorn.
"""

import datetime
import logging
import os
from typing import Any

import bleach
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from calculator import (
    calculate_eco_score,
    calculate_footprint,
    calculate_tree_offset,
    get_benchmarks,
)
from gemini_client import get_action_plan, get_chat_response, get_insights

# ---------------------------------------------------------------------------
# Environment & logging setup
# ---------------------------------------------------------------------------

load_dotenv()  # Load .env for local development

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Application starting — using standard Python logging")

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per minute"],
    storage_uri="memory://",
)

# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------

VALID_DIET_TYPES = {"vegan", "vegetarian", "non_vegetarian", "heavy_meat"}
VALID_CITY_TIERS = {"metro", "tier_2", "rural"}


def _sanitize_string(value: Any) -> str:
    """Sanitise a string input with bleach."""
    if not isinstance(value, str):
        return str(value)
    return bleach.clean(value, tags=[], strip=True)


def _validate_calculate_input(data: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """Validate and sanitise calculator form input.

    Returns (cleaned_data, None) on success, or (None, error_message) on failure.
    """
    if not data:
        return None, "Request body is empty"

    cleaned: dict[str, Any] = {}

    # Numeric fields — clamp to reasonable ranges
    numeric_fields = {
        "electricity_kwh": (0, 10000),
        "lpg_cylinders": (0, 50),
        "petrol_car_km": (0, 50000),
        "two_wheeler_km": (0, 50000),
        "train_km": (0, 50000),
        "flight_km": (0, 100000),
        "waste_kg": (0, 5000),
    }
    for field, (min_val, max_val) in numeric_fields.items():
        try:
            val = float(data.get(field, 0))
            cleaned[field] = max(min_val, min(val, max_val))
        except (TypeError, ValueError):
            cleaned[field] = 0

    # Diet type
    diet_type = _sanitize_string(data.get("diet_type", "vegetarian"))
    if diet_type not in VALID_DIET_TYPES:
        return None, f"Invalid diet_type: {diet_type}. Must be one of {VALID_DIET_TYPES}"
    cleaned["diet_type"] = diet_type

    # Boolean fields
    cleaned["recycles"] = bool(data.get("recycles", False))
    cleaned["composts"] = bool(data.get("composts", False))

    # City tier
    city_tier = _sanitize_string(data.get("city_tier", "metro"))
    if city_tier not in VALID_CITY_TIERS:
        city_tier = "metro"
    cleaned["city_tier"] = city_tier

    # Language
    cleaned["language"] = _sanitize_string(data.get("language", "English"))

    return cleaned, None


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.route("/")
def index() -> str:
    """Landing page."""
    return render_template("index.html")


@app.route("/calculator")
def calculator_page() -> str:
    """Carbon calculator form page."""
    return render_template("calculator.html")


@app.route("/results")
def results_page() -> str:
    """Results display page."""
    return render_template("results.html")


@app.route("/action-plan")
def action_plan_page() -> str:
    """30-day action plan page (Sprint 2)."""
    return render_template("action_plan.html")


@app.route("/tracker")
def tracker_page() -> str:
    """Monthly progress tracker page (Sprint 2)."""
    return render_template("tracker.html")


@app.route("/chat")
def chat_page() -> str:
    """AI chat assistant page (Sprint 2)."""
    return render_template("chat.html")


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------

@app.route("/api/calculate", methods=["POST"])
@limiter.limit("60 per minute")
def api_calculate() -> tuple:
    """Calculate carbon footprint from user inputs.

    Input:  JSON body matching DataSchema from DATA_MODEL.md.
    Output: Full result with total, breakdown, eco_score, benchmarks, tree_offset.
    """
    data = request.get_json(silent=True)
    cleaned, error = _validate_calculate_input(data)
    if error:
        logger.warning("Invalid calculate input: %s", error)
        return jsonify({"error": error}), 400

    try:
        # Core calculation
        result = calculate_footprint(cleaned)

        # Enrich with eco score, benchmarks, and tree offset
        result["eco_score"] = calculate_eco_score(result["total"])
        result["benchmarks"] = get_benchmarks()
        result["tree_offset"] = calculate_tree_offset(result["total"])

        # Pass through city_tier and language for subsequent API calls
        result["city_tier"] = cleaned["city_tier"]
        result["language"] = cleaned["language"]

        logger.info(
            "Footprint calculated: %.2f tonnes (largest: %s)",
            result["total"],
            result["largest_category"],
        )
        return jsonify(result), 200

    except Exception as e:
        logger.error("Calculation error: %s", e, exc_info=True)
        return jsonify({"error": "Calculation failed. Please try again."}), 500


@app.route("/api/insights", methods=["POST"])
@limiter.limit("20 per minute")
def api_insights() -> tuple:
    """Generate AI-powered reduction insights.

    Input:  Full footprint result from /api/calculate + language.
    Output: 3 personalized tips from Gemini.
    """
    data = request.get_json(silent=True)
    if not data or "total" not in data:
        return jsonify({"error": "Missing footprint data. Calculate first."}), 400

    language = _sanitize_string(data.get("language", "English"))

    try:
        insights = get_insights(data, language)
        logger.info("Insights generated for footprint %.2f tonnes", data["total"])
        return jsonify(insights), 200
    except Exception as e:
        logger.error("Insights error: %s", e, exc_info=True)
        return jsonify({"error": "Failed to generate insights. Please try again."}), 500


@app.route("/api/action-plan", methods=["POST"])
@limiter.limit("20 per minute")
def api_action_plan() -> tuple:
    """Generate a 30-day action plan.

    Input:  Full footprint result from /api/calculate + language.
    Output: Structured 4-week action plan from Gemini.
    """
    data = request.get_json(silent=True)
    if not data or "total" not in data:
        return jsonify({"error": "Missing footprint data. Calculate first."}), 400

    language = _sanitize_string(data.get("language", "English"))

    try:
        plan = get_action_plan(data, language)
        logger.info("Action plan generated for footprint %.2f tonnes", data["total"])
        return jsonify(plan), 200
    except Exception as e:
        logger.error("Action plan error: %s", e, exc_info=True)
        return jsonify({"error": "Failed to generate action plan. Please try again."}), 500


@app.route("/api/chat", methods=["POST"])
@limiter.limit("30 per minute")
def api_chat() -> tuple:
    """Chat with EcoBot.

    Input:  message, chat_history (list), language, optional footprint_data.
    Output: AI response text.
    """
    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return jsonify({"error": "Message is required."}), 400

    message = _sanitize_string(data["message"])
    if not message or len(message) > 1000:
        return jsonify({"error": "Message must be between 1 and 1000 characters."}), 400

    chat_history = data.get("chat_history", [])
    footprint_data = data.get("footprint_data", None)
    language = _sanitize_string(data.get("language", "English"))

    try:
        response_text = get_chat_response(message, chat_history, footprint_data, language)
        logger.info("Chat response generated")
        return jsonify({"response": response_text}), 200
    except Exception as e:
        logger.error("Chat error: %s", e, exc_info=True)
        return jsonify({"error": "Failed to get response. Please try again."}), 500


@app.route("/health", methods=["GET"])
def health_check() -> tuple:
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "services": ["gemini-api", "render"],
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }), 200


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e: Exception) -> tuple:
    """Handle 404 errors."""
    if request.path.startswith("/api/"):
        return jsonify({"error": "Endpoint not found"}), 404
    return render_template("index.html"), 404


@app.errorhandler(500)
def server_error(e: Exception) -> tuple:
    """Handle 500 errors."""
    logger.error("Internal server error: %s", e)
    if request.path.startswith("/api/"):
        return jsonify({"error": "Internal server error"}), 500
    return render_template("index.html"), 500


@app.errorhandler(429)
def rate_limit_exceeded(e: Exception) -> tuple:
    """Handle rate limit errors."""
    return jsonify({"error": "Rate limit exceeded. Please wait and try again."}), 429


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
