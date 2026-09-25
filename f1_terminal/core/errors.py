"""Core error hierarchy for F1 Terminal X."""

from __future__ import annotations


class F1DataError(Exception):
    """Base for data-related errors."""

    exit_code: int = 1


class SessionNotHeldError(F1DataError):
    """Session has not yet occurred or data unavailable."""


class DriverNotFoundError(F1DataError):
    """Driver not found in session."""


class TelemetryNotAvailableError(F1DataError):
    """Telemetry unavailable for lap/driver."""


class CacheError(F1DataError):
    """Cache read/write failure."""
