"""
f1_terminal.core — shared engine (Phase 0 stubs + Phase 1 full).
"""

from f1_terminal.core.colors import get_team_color
from f1_terminal.core.errors import (
    CacheError,
    DriverNotFoundError,
    F1DataError,
    SessionNotHeldError,
    TelemetryNotAvailableError,
)
from f1_terminal.core.features import engineer_lap_features
from f1_terminal.core.io import load_session_data
from f1_terminal.core.session import SessionWrapper, get_schedule, load_session
from f1_terminal.core.telemetry import get_driver_telemetry, get_fastest_lap, get_telemetry
from f1_terminal.core.transforms import prepare_telemetry_trace

try:
    from f1_terminal.tracks import TRACKS, Track, all_tracks, get_track
except ImportError:
    TRACKS = {}  # type: ignore[assignment]

# Re-export plotting pure functions for convenience (optional import)
try:
    from f1_terminal.core.plotting import (
        plot_gear_map,
        plot_race_pace,
        plot_sector_bars,
        plot_speed_trace,
        plot_throttle_brake,
        plot_tire_strategy,
        plot_track_map,
    )
except Exception:
    pass

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
    "SessionWrapper",
    "get_schedule",
    "load_session",
    "get_fastest_lap",
    "get_telemetry",
    "get_driver_telemetry",
    "get_team_color",
    "plot_track_map",
    "plot_speed_trace",
    "plot_throttle_brake",
    "plot_gear_map",
    "plot_sector_bars",
    "plot_race_pace",
    "plot_tire_strategy",
]
