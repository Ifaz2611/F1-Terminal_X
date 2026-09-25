"""
Legacy shim — F1_Main_py.driver

Deprecated: use f1_terminal.core. Will be removed in v2.0.
Re-exports core helpers so old code keeps working.
"""

from __future__ import annotations

import warnings

from f1_terminal.core.colors import get_team_color  # noqa: F401
from f1_terminal.core.errors import (  # noqa: F401
    DriverNotFoundError,
    F1DataError,
    TelemetryNotAvailableError,
)
from f1_terminal.core.session import SessionWrapper, get_schedule, load_session  # noqa: F401
from f1_terminal.core.telemetry import (  # noqa: F401
    get_driver_telemetry,
    get_fastest_lap,
    get_telemetry,
)

warnings.warn(
    "F1_Main_py.driver is deprecated; use f1_terminal.core. Will be removed in v2.0",
    DeprecationWarning,
    stacklevel=2,
)

# Keep legacy helpers for backward compat (used by old tests if any)
def _get_driver_field(driver, key: str, default: str = "Unknown") -> str:  # noqa: D401
    for accessor in (
        lambda d, k: d[k] if k in d else None,
        lambda d, k: d.get(k, None) if hasattr(d, "get") else None,
        lambda d, k: getattr(d, k, None),
    ):
        try:
            val = accessor(driver, key)
            if val is not None and str(val) != "nan" and str(val).strip():
                return str(val)
        except Exception:
            continue
    return default

def _resolve_driver_laps(target_laps, code):  # noqa: ANN001
    import pandas as pd  # noqa: F401

    # delegate to core helper
    try:
        from f1_terminal.core.session import _get_driver_laps_fallback as _g
        return _g(target_laps, code)
    except Exception:
        return target_laps[target_laps["Driver"] == code] if "Driver" in target_laps.columns else target_laps

def main(argv=None):  # type: ignore[no-redef]
    """Legacy driver analyzer entry — delegates to new CLI."""

    # For backward compat, run the old interactive driver analyzer if no argv
    # Otherwise delegate to CLI driver command
    if argv is None:
        # Old driver.py had a rich interactive menu; now just call CLI schedule+driver flow
        # Preserve minimal behavior: show help
        print("F1_Main_py.driver: use 'f1 driver --help' (core-powered). Delegating...")
        try:
            from f1_terminal.cli.main import app
            return app(["driver", "--help"])
        except Exception:
            return None
    # argv provided
    from f1_terminal.cli.main import app
    return app(["driver"] + (argv if isinstance(argv, list) else []))
