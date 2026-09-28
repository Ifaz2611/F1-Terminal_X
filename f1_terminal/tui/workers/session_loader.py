"""Async FastF1 session loader for the TUI (P2-9).

All ``fastf1`` calls must run inside a Textual worker — never on the UI thread.
When Textual is unavailable (CI / --demo) the synchronous helpers below are used.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from f1_terminal.config import get_logger
from f1_terminal.core.errors import F1DataError, SessionNotHeldError

logger = get_logger(__name__)


@dataclass
class LoadRequest:
    year: int
    track: Any
    session_code: str


@dataclass
class LoadResult:
    ok: bool
    wrapper: Any = None
    error: str = ""


def load_session_sync(year: int, track: Any, session_code: str) -> LoadResult:
    """Blocking load used by workers and by --demo fallback."""
    from f1_terminal.core.session import load_session

    try:
        wrapper = load_session(year, track, session_code)
        return LoadResult(ok=True, wrapper=wrapper)
    except SessionNotHeldError as e:
        return LoadResult(ok=False, error=str(e))
    except F1DataError as e:
        return LoadResult(ok=False, error=str(e))
    except Exception as e:  # pragma: no cover - defensive
        return LoadResult(ok=False, error=f"{type(e).__name__}: {e}")


def load_demo_session() -> LoadResult:
    """Load bundled offline fixture as a SessionWrapper-like object.

    Used by ``f1-tui --demo`` and docs recording — no network required.
    """
    import pandas as pd

    from f1_terminal.core.session import SessionWrapper

    sample = pd.read_csv("data/telemetry_sample.csv")
    # Minimal laps frame so plotting + tables have something to show
    laps = pd.DataFrame(
        {
            "Driver": ["VER", "HAM"],
            "LapNumber": [1, 1],
            "LapTime": pd.to_timedelta(["90.123s", "91.456s"]),
            "Sector1Time": pd.to_timedelta(["30s", "30.5s"]),
            "Sector2Time": pd.to_timedelta(["30s", "30.5s"]),
            "Sector3Time": pd.to_timedelta(["30.123s", "30.956s"]),
            "Compound": ["SOFT", "MEDIUM"],
            "PitInTime": [pd.NaT, pd.NaT],
            "PitOutTime": [pd.NaT, pd.NaT],
        }
    )
    # Attach pick_* helpers like conftest
    def _pick_drivers(code):
        codes = code if isinstance(code, list) else [code]
        return laps[laps["Driver"].isin(codes)]

    def _pick_driver(code):
        return laps[laps["Driver"] == code]

    laps.pick_drivers = _pick_drivers  # type: ignore[attr-defined]
    laps.pick_driver = _pick_driver  # type: ignore[attr-defined]

    class _DemoSession:
        drivers = ["VER", "HAM"]

        def get_driver(self, code: str):
            colors = {"VER": "0600EF", "HAM": "00D2BE"}
            return {"TeamColor": colors.get(code, "FFFFFF"), "TeamName": f"Team {code}"}

    # Demo telemetry is exposed via wrapper.session._demo_telemetry (see below).

    # We expose telemetry via a helper on the wrapper for demo widgets
    wrapper = SessionWrapper(
        session=_DemoSession(),
        laps=laps,
        drivers=["VER", "HAM"],
        year=2023,
        track="Monza",
        session_code="Q",
        identifier="Monza",
        event_name="Italian Grand Prix (demo)",
    )
    # stash sample for widgets
    wrapper.session._demo_telemetry = sample  # type: ignore[attr-defined]
    return LoadResult(ok=True, wrapper=wrapper)


def get_demo_telemetry(wrapper: Any, driver: str):
    """Return demo telemetry DataFrame for a driver."""
    import pandas as pd

    tel = getattr(getattr(wrapper, "session", None), "_demo_telemetry", None)
    if tel is not None:
        return tel.copy()
    try:
        return pd.read_csv("data/telemetry_sample.csv")
    except Exception:
        return pd.DataFrame(
            {"X": [0, 1], "Y": [0, 1], "Speed": [200, 210], "Distance": [0, 10]}
        )


async def run_in_textual_worker(
    app: Any, year: int, track: Any, session_code: str, on_done: Callable[[LoadResult], None]
) -> None:
    """Schedule ``load_session_sync`` in ``app.run_worker`` (non-blocking).

    Falls back to direct call when Textual workers are unavailable.
    """
    try:
        worker = app.run_worker(load_session_sync(year, track, session_code), exclusive=True)
        result = await worker.wait()
        on_done(result if isinstance(result, LoadResult) else LoadResult(ok=False, error=str(result)))
    except Exception:
        # Non-textual environment: run synchronously
        on_done(load_session_sync(year, track, session_code))


def friendly_error_message(year: int, track: Any, session_code: str, error: str) -> str:
    return (
        f"{year} {track} {session_code} not yet held or unavailable. "
        f"({error}) [Retry with cached data or --demo]"
    )
