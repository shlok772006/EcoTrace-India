"""Flask application for EcoTrace India.

Defines all page routes, REST API endpoints, security
hooks, rate limiting, and error handlers.  Deployed on
Render with Gunicorn (see ``Procfile``).

Configuration is loaded from :pymod:`config` and
validation constants from :pymod:`constants`.
"""

import datetime
import logging
import uuid
from typing import Any

import bleach
from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from calculator import (
    calculate_eco_score,
    calculate_footprint,
    calculate_tree_offset,
    get_benchmarks,
    load_emission_factors,
)
from config import Config
from constants import (
    DEFAULT_PORT,
    INPUT_LIMITS,
    MAX_CHAT_MESSAGE_LENGTH,
    VALID_CITY_TIERS,
    VALID_DIET_TYPES,
)
from exceptions import (
    CalculationError,
    GeminiAPIError,
    ValidationError,
)
from gemini_client import (
    get_action_plan,
    get_chat_response,
    get_insights,
    ping,
)

# ---------------------------------------------------------------
# Application factory & logging
# ---------------------------------------------------------------

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(
    "Application starting — using standard Python "
    "logging"
)

# Eagerly load emission factors before the first request
load_emission_factors()
logger.info("Emission factors loaded")

# ---------------------------------------------------------------
# Security & performance hooks
# ---------------------------------------------------------------


@app.before_request
def add_request_id() -> None:
    """Attach a unique ID to every request for tracing.

    The ID is stored in ``request.environ['REQUEST_ID']``
    and can be included in log messages for end-to-end
    traceability.
    """
    request.environ["REQUEST_ID"] = str(uuid.uuid4())


@app.after_request
def add_security_headers(
    response: Response,
) -> Response:
    """Inject security headers into every response.

    Adds Content-Security-Policy, X-Content-Type-Options,
    and X-Frame-Options headers.

    Args:
        response: The outgoing Flask response object.

    Returns:
        The response with additional security headers.
    """
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' "
        "https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' "
        "https://fonts.googleapis.com; "
        "font-src 'self' "
        "https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    )
    response.headers[
        "Content-Security-Policy"
    ] = csp
    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=31536000; includeSubDomains"
    return response


# ---------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[Config.RATE_LIMIT_DEFAULT],
    storage_uri=Config.RATE_LIMIT_STORAGE_URI,
)

# ---------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------


def _sanitize_string(value: Any) -> str:
    """Strip all HTML tags from a value using Bleach.

    Args:
        value: The raw input (may be any type).

    Returns:
        A plain-text string with all HTML removed.
    """
    if not isinstance(value, str):
        return str(value)
    return bleach.clean(value, tags=[], strip=True)


def _validate_calculate_input(
    data: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate and sanitise calculator form input.

    Args:
        data: Raw JSON body from the request.

    Returns:
        A two-tuple ``(cleaned_data, error_message)``.
        On success ``error_message`` is ``None``; on
        failure ``cleaned_data`` is ``None``.

    Raises:
        ValidationError: If the diet type is not in
            the allowed set (caught by the caller).
    """
    if not data:
        return None, "Request body is empty"

    cleaned: dict[str, Any] = {}

    # Numeric fields — clamp to safe ranges
    for field, (lo, hi) in INPUT_LIMITS.items():
        try:
            val = float(data.get(field, 0))
            cleaned[field] = max(lo, min(val, hi))
        except (TypeError, ValueError):
            cleaned[field] = 0

    # Diet type
    diet = _sanitize_string(
        data.get("diet_type", "vegetarian")
    )
    if diet not in VALID_DIET_TYPES:
        return None, (
            f"Invalid diet_type: {diet}. "
            f"Must be one of {VALID_DIET_TYPES}"
        )
    cleaned["diet_type"] = diet

    # Boolean fields
    cleaned["recycles"] = bool(
        data.get("recycles", False)
    )
    cleaned["composts"] = bool(
        data.get("composts", False)
    )

    # City tier
    city_tier = _sanitize_string(
        data.get("city_tier", "metro")
    )
    if city_tier not in VALID_CITY_TIERS:
        city_tier = "metro"
    cleaned["city_tier"] = city_tier

    # Language
    cleaned["language"] = _sanitize_string(
        data.get("language", "English")
    )

    return cleaned, None


# ---------------------------------------------------------------
# Error-response helper (DRY)
# ---------------------------------------------------------------


def _error_response(
    msg: str,
    status: int = 500,
) -> tuple[Response, int]:
    """Build a standard JSON error response.

    Args:
        msg: User-facing error message.
        status: HTTP status code.

    Returns:
        A two-tuple ``(json_response, status_code)``.
    """
    return jsonify({"error": msg}), status


# ---------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------


@app.route("/")
def index() -> str:
    """Render the landing page.

    Returns:
        Rendered ``index.html`` template.
    """
    return render_template("index.html")


@app.route("/calculator")
def calculator_page() -> str:
    """Render the carbon calculator form page.

    Returns:
        Rendered ``calculator.html`` template.
    """
    return render_template("calculator.html")


@app.route("/results")
def results_page() -> str:
    """Render the results display page.

    Returns:
        Rendered ``results.html`` template.
    """
    return render_template("results.html")


@app.route("/action-plan")
def action_plan_page() -> str:
    """Render the 30-day action plan page.

    Returns:
        Rendered ``action_plan.html`` template.
    """
    return render_template("action_plan.html")


@app.route("/tracker")
def tracker_page() -> str:
    """Render the monthly progress tracker page.

    Returns:
        Rendered ``tracker.html`` template.
    """
    return render_template("tracker.html")


@app.route("/chat")
def chat_page() -> str:
    """Render the AI chat assistant page.

    Returns:
        Rendered ``chat.html`` template.
    """
    return render_template("chat.html")


# ---------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------


@app.route("/api/calculate", methods=["POST"])
@limiter.limit("60 per minute")
def api_calculate() -> tuple[Response, int]:
    """Calculate carbon footprint from user inputs.

    Expects a JSON body matching the DataSchema from
    ``DATA_MODEL.md``.

    Returns:
        JSON response with ``total``, ``breakdown``,
        ``eco_score``, ``benchmarks``, and
        ``tree_offset``.  HTTP 400 on invalid input,
        500 on server error.
    """
    data = request.get_json(silent=True)
    cleaned, error = _validate_calculate_input(data)
    if error:
        logger.warning(
            "Invalid calculate input: %s", error
        )
        return jsonify({"error": error}), 400

    try:
        result = calculate_footprint(cleaned)

        result["eco_score"] = calculate_eco_score(
            result["total"]
        )
        result["benchmarks"] = get_benchmarks()
        result["tree_offset"] = calculate_tree_offset(
            result["total"]
        )
        result["city_tier"] = cleaned["city_tier"]
        result["language"] = cleaned["language"]

        logger.info(
            "Footprint calculated: %.2f tonnes "
            "(largest: %s)",
            result["total"],
            result["largest_category"],
        )
        return jsonify(result), 200

    except Exception as exc:
        logger.error(
            "Calculation error: %s", exc, exc_info=True
        )
        return _error_response(
            "Calculation failed. Please try again."
        )


@app.route("/api/insights", methods=["POST"])
@limiter.limit("20 per minute")
def api_insights() -> tuple[Response, int]:
    """Generate AI-powered reduction insights.

    Expects the full footprint result from
    ``/api/calculate`` plus a ``language`` field.

    Returns:
        JSON with 3 personalised tips from Gemini.
        HTTP 400 if footprint data is missing,
        500 on Gemini failure.
    """
    data = request.get_json(silent=True)
    if not data or "total" not in data:
        return (
            jsonify(
                {
                    "error": (
                        "Missing footprint data. "
                        "Calculate first."
                    )
                }
            ),
            400,
        )

    language = _sanitize_string(
        data.get("language", "English")
    )

    try:
        insights = get_insights(data, language)
        logger.info(
            "Insights generated for footprint "
            "%.2f tonnes",
            data["total"],
        )
        return jsonify(insights), 200
    except Exception as exc:
        logger.error(
            "Insights error: %s", exc, exc_info=True
        )
        return _error_response(
            "Failed to generate insights. "
            "Please try again."
        )


@app.route("/api/action-plan", methods=["POST"])
@limiter.limit("20 per minute")
def api_action_plan() -> tuple[Response, int]:
    """Generate a 30-day action plan.

    Expects the full footprint result plus a
    ``language`` field.

    Returns:
        JSON with a structured 4-week plan from Gemini.
        HTTP 400 if data is missing, 500 on failure.
    """
    data = request.get_json(silent=True)
    if not data or "total" not in data:
        return (
            jsonify(
                {
                    "error": (
                        "Missing footprint data. "
                        "Calculate first."
                    )
                }
            ),
            400,
        )

    language = _sanitize_string(
        data.get("language", "English")
    )

    try:
        plan = get_action_plan(data, language)
        logger.info(
            "Action plan generated for footprint "
            "%.2f tonnes",
            data["total"],
        )
        return jsonify(plan), 200
    except Exception as exc:
        logger.error(
            "Action plan error: %s",
            exc,
            exc_info=True,
        )
        return _error_response(
            "Failed to generate action plan. "
            "Please try again."
        )


@app.route("/api/chat", methods=["POST"])
@limiter.limit("30 per minute")
def api_chat() -> tuple[Response, int]:
    """Chat with EcoBot.

    Expects ``message``, optional ``chat_history``,
    optional ``footprint_data``, and ``language``.

    Returns:
        JSON with ``response`` text.  HTTP 400 if
        message is missing or too long, 500 on failure.
    """
    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return (
            jsonify({"error": "Message is required."}),
            400,
        )

    message = _sanitize_string(data["message"])
    if (
        not message
        or len(message) > MAX_CHAT_MESSAGE_LENGTH
    ):
        return (
            jsonify(
                {
                    "error": (
                        "Message must be between 1 and "
                        f"{MAX_CHAT_MESSAGE_LENGTH} "
                        "characters."
                    )
                }
            ),
            400,
        )

    chat_history: list[dict[str, str]] = data.get(
        "chat_history", []
    )
    footprint_data: dict[str, Any] | None = data.get(
        "footprint_data"
    )
    language: str = _sanitize_string(
        data.get("language", "English")
    )

    try:
        response_text = get_chat_response(
            message,
            chat_history,
            footprint_data,
            language,
        )
        logger.info("Chat response generated")
        return (
            jsonify({"response": response_text}),
            200,
        )
    except Exception as exc:
        logger.error(
            "Chat error: %s", exc, exc_info=True
        )
        return _error_response(
            "Failed to get response. "
            "Please try again."
        )


@app.route("/health", methods=["GET"])
def health_check() -> tuple[Response, int]:
    """Health-check endpoint.

    Returns:
        JSON with ``status``, ``services``, and
        ``timestamp``.  HTTP 200 when healthy, 503
        when Gemini is unreachable.
    """
    gemini_ok: bool = ping()
    status = "healthy" if gemini_ok else "degraded"
    code = 200 if gemini_ok else 503

    return (
        jsonify(
            {
                "status": status,
                "services": {
                    "gemini-api": (
                        "healthy"
                        if gemini_ok
                        else "unhealthy"
                    ),
                    "render": "healthy",
                },
                "timestamp": (
                    datetime.datetime.now(
                        datetime.UTC
                    )
                    .isoformat()
                    .replace("+00:00", "Z")
                ),
            }
        ),
        code,
    )


# ---------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------


@app.errorhandler(404)
def not_found(
    exc: Exception,
) -> tuple[Response | str, int]:
    """Handle 404 Not Found errors.

    Args:
        exc: The exception raised by Flask.

    Returns:
        JSON for API routes, rendered landing page for
        browser requests.
    """
    if request.path.startswith("/api/"):
        return (
            jsonify({"error": "Endpoint not found"}),
            404,
        )
    return render_template("index.html"), 404


@app.errorhandler(500)
def server_error(
    exc: Exception,
) -> tuple[Response | str, int]:
    """Handle 500 Internal Server errors.

    Args:
        exc: The exception raised by Flask.

    Returns:
        JSON for API routes, rendered landing page for
        browser requests.
    """
    logger.error("Internal server error: %s", exc)
    if request.path.startswith("/api/"):
        return (
            jsonify(
                {"error": "Internal server error"}
            ),
            500,
        )
    return render_template("index.html"), 500


@app.errorhandler(429)
def rate_limit_exceeded(
    exc: Exception,
) -> tuple[Response, int]:
    """Handle 429 Too Many Requests errors.

    Args:
        exc: The rate-limit exception.

    Returns:
        JSON error with a retry message.
    """
    return (
        jsonify(
            {
                "error": (
                    "Rate limit exceeded. Please "
                    "wait and try again."
                )
            }
        ),
        429,
    )


# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG,
    )
