"""
Legacy shim — F1_Main_py.schedule_driver

Deprecated: use f1_terminal.core.session.get_schedule + load_session.
Will be removed in v2.0.
"""

from __future__ import annotations

import warnings

from f1_terminal.core.errors import F1DataError, SessionNotHeldError  # noqa: F401
from f1_terminal.core.session import SessionWrapper, get_schedule, load_session  # noqa: F401

warnings.warn(
    "F1_Main_py.schedule_driver is deprecated; use f1_terminal.core.session. Will be removed in v2.0",
    DeprecationWarning,
    stacklevel=2,
)

def show_schedule() -> None:  # keep API
    from f1_terminal.cli.main import schedule as _sched

    return _sched(year=2026)  # type: ignore[call-arg]

def show_driver_lineup() -> None:
    from f1_terminal.cli.main import driver as _drv

    return _drv(year=2026, round=1)  # type: ignore[call-arg]

def main(argv=None):  # type: ignore[no-redef]

    # Delegate to unified CLI: f1 schedule / f1 driver
    from f1_terminal.cli.main import app

    if argv is not None:
        return app(argv)
    # No argv -> interactive fallback from f1_terminal.cli.interactive
    from f1_terminal.cli.interactive import interactive_flow

    return interactive_flow()
