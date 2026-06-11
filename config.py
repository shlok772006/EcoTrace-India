"""Application configuration for EcoTrace India.

Centralises all environment-variable reading and Flask
configuration so that ``app.py`` never calls
``os.environ`` directly.
"""

__all__ = ["Config"]

import os
from typing import Final

from dotenv import load_dotenv

# Load .env for local development (no-op in production)
load_dotenv()


class Config:
    """Flask and application configuration.

    Attributes:
        GEMINI_API_KEY: Google Gemini API key (required).
        PORT: HTTP port for the development server.
        DEBUG: Whether Flask runs in debug mode.
        TESTING: Flag for the test suite.
        RATE_LIMIT_DEFAULT: Default rate-limit string.
        RATE_LIMIT_STORAGE_URI: Backend for flask-limiter.
    """

    GEMINI_API_KEY: Final[str | None] = os.environ.get(
        "GEMINI_API_KEY"
    )

    PORT: Final[int] = int(os.environ.get("PORT", "5000"))

    DEBUG: Final[bool] = (
        os.environ.get("FLASK_DEBUG", "0") == "1"
    )

    TESTING: Final[bool] = False

    # Rate limiting
    RATE_LIMIT_DEFAULT: Final[str] = "200 per minute"
    RATE_LIMIT_STORAGE_URI: Final[str] = "memory://"
