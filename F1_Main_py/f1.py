"""
Legacy shim — F1_Main_py.f1

Deprecated: use ``f1_terminal.core`` and ``f1_terminal.cli``.
Kept for backward compat; will be removed in v2.0.

This file re-exports core helpers so old imports still work.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "F1_Main_py.f1 is deprecated; use f1_terminal.core / f1 CLI. Will be removed in v2.0",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export core for backward compat
from f1_terminal.core.colors import get_team_color  # noqa: F401
from f1_terminal.core.errors import (  # noqa: F401
    DriverNotFoundError,
    F1DataError,
    SessionNotHeldError,
    TelemetryNotAvailableError,
)
from f1_terminal.core.session import SessionWrapper, get_schedule, load_session  # noqa: F401
from f1_terminal.core.telemetry import get_driver_telemetry, get_fastest_lap, get_telemetry  # noqa: F401

# Thin wrapper entry point — delegates to new core-powered visualizer
try:
    from f1_terminal.f1_advanced_visualizer import TrackVisualizer  # noqa: F401

    def main(argv=None):  # type: ignore[no-redef]
        from f1_terminal.f1_advanced_visualizer import main as _main

        return _main(argv)
except Exception:

    def main(argv=None):  # type: ignore[no-redef]
        from f1_terminal.cli.main import app as _app

        return _app(["telemetry"] + (argv or []))
