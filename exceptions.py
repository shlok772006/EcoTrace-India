"""Custom exception hierarchy for EcoTrace India.

Provides domain-specific exceptions so that calling code can
distinguish between calculation failures, Gemini API problems,
and input-validation errors without relying on bare ``Exception``
catches.
"""

__all__ = [
    "EcoTraceError",
    "CalculationError",
    "GeminiAPIError",
    "ValidationError",
]


class EcoTraceError(Exception):
    """Base exception for all EcoTrace India errors.

    All custom exceptions inherit from this class so callers
    can catch the entire family with a single ``except``.
    """


class CalculationError(EcoTraceError):
    """Raised when the carbon-footprint calculation fails.

    Examples include missing emission-factor data or unexpected
    numeric overflow during the formula evaluation.
    """


class GeminiAPIError(EcoTraceError):
    """Raised when a Gemini API call fails or returns bad data.

    Wraps transport errors, authentication failures, and
    unparseable responses from the Gemini model.
    """


class ValidationError(EcoTraceError):
    """Raised when user input fails validation.

    Includes invalid diet types, out-of-range numeric fields,
    or malformed request bodies.
    """
