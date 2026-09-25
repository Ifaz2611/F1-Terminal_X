"""
f1_terminal.core — shared engine (Phase 0 stubs + Phase 1 full).
"""

from f1_terminal.core.errors import (
    CacheError,
    DriverNotFoundError,
    F1DataError,
    SessionNotHeldError,
    TelemetryNotAvailableError,
)
from f1_terminal.core.features import engineer_lap_features
from f1_terminal.core.io import load_session_data
from f1_terminal.core.transforms import prepare_telemetry_trace

try:
    from f1_terminal.tracks import TRACKS, Track, all_tracks, get_track
except ImportError:
    TRACKS = {}  # type: ignore[assignment]

__all__ = [
    "F1DataError",
    "SessionNotHeldError",
    "DriverNotFoundError",
    "TelemetryNotAvailableError",
    "CacheError",
    "load_session_data",
    "prepare_telemetry_trace",
    "engineer_lap_features",
    "TRACKS",
    "Track",
    "get_track",
    "all_tracks",
]
