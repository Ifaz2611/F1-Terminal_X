"""Session loading engine — Phase 1 core.

Provides ``get_schedule``, ``load_session``, and ``SessionWrapper``.

Goals:
- Decouple data/plot from I/O so CLI and TUI share one engine.
- Pure data loading with retry, friendly errors, offline fallback.
- No ``input()`` or ``plt.show()`` calls.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Optional

import pandas as pd

from f1_terminal.config import get_logger, settings
from f1_terminal.core.errors import DriverNotFoundError, F1DataError, SessionNotHeldError

logger = get_logger(__name__)


def _resolve_identifier(track: Any) -> str:
    """Resolve Track|int|str to fastf1 identifier string."""
    # Track dataclass
    try:
        if hasattr(track, "fastf1_name"):
            return str(track.fastf1_name)  # type: ignore[union-attr]
    except Exception:
        pass
    # int round number
    if isinstance(track, int):
        try:
            from f1_terminal.tracks import get_track

            return get_track(track).fastf1_name
        except Exception:
            return str(track)
    # digit string
    if isinstance(track, str) and track.isdigit():
        try:
            from f1_terminal.tracks import get_track

            return get_track(int(track)).fastf1_name
        except Exception:
            pass
    return str(track)


def _setup_cache() -> None:
    try:
        import fastf1  # type: ignore[import-not-found]

        cache_dir = settings.cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            fastf1.Cache.set_cache_directory(str(cache_dir))
        except AttributeError:
            fastf1.Cache.enable_cache(str(cache_dir))  # type: ignore[attr-defined]
    except Exception:
        pass


@lru_cache(maxsize=32)
def get_schedule(year: int) -> pd.DataFrame:
    """Return event schedule for a year.

    Cached in-memory. Handles incomplete 2026 schedule gracefully:
    filters out rows with NaT EventDate? Returns what fastf1 gives.
    On failure raises F1DataError -> caller can show friendly msg.

    Args:
        year: Season year (e.g. 2023).

    Returns:
        DataFrame from fastf1.get_event_schedule.
    """
    _setup_cache()
    logger.info("Loading schedule for year %s", year)
    try:
        import fastf1  # type: ignore[import-not-found]

        schedule = fastf1.get_event_schedule(year)
        # fastf1 3.8+ returns DataFrame with EventDate; handle incomplete 2026
        # Ensure copy so caller can mutate safely
        if schedule is None or schedule.empty:
            logger.warning("Schedule empty for year %s", year)
            return schedule if schedule is not None else pd.DataFrame()
        return schedule.copy()
    except Exception as e:
        # If offline and cache exists, try to return last cached? fastf1 handles cache internally
        # For offline fallback, try to synthesize from TRACKS if year==default and cache missing
        msg = str(e).lower()
        if "schedule" in msg or "not" in msg:
            logger.warning("Schedule load failed for %s: %s", year, e)
        raise F1DataError(f"Failed to load schedule for {year}: {e}") from e


def _get_driver_laps_fallback(laps: pd.DataFrame, code: str) -> pd.DataFrame:
    """Fallback driver laps resolution (pick_drivers/pick_driver/manual)."""
    if laps is None or laps.empty:
        return laps if laps is not None else pd.DataFrame()
    for method in ("pick_drivers", "pick_driver"):
        try:
            fn = getattr(laps, method, None)
            if fn is None:
                continue
            for arg in (code, [code]):
                try:
                    result = fn(arg)  # type: ignore[operator]
                    if result is not None and getattr(result, "empty", True) is not False:
                        # check not empty
                        try:
                            if not result.empty:  # type: ignore[union-attr]
                                return result
                        except Exception:
                            return result
                except Exception:
                    continue
        except Exception:
            continue
    try:
        if "Driver" in laps.columns:
            return laps[laps["Driver"] == code]
    except Exception:
        pass
    return laps.iloc[0:0].copy()


@dataclass
class SessionWrapper:
    """Thin wrapper around a fastf1 Session.

    Attributes:
        session: Raw fastf1 Session object.
        laps: DataFrame of laps (session.laps).
        drivers: List of driver codes.
        year: Season year.
        track: Original track identifier (string or Track).
        session_code: Session string (R, Q, FP1, etc.).
    """

    session: Any
    laps: pd.DataFrame
    drivers: list[str]
    year: int
    track: Any
    session_code: str
    identifier: str = ""
    event_name: str = ""

    def get_driver_laps(self, code: str) -> pd.DataFrame:
        """Return laps for a driver code, with fallback handling.

        Raises DriverNotFoundError if no laps.
        """
        result = _get_driver_laps_fallback(self.laps, code)
        if result is None or getattr(result, "empty", False):
            raise DriverNotFoundError(f"Driver {code} not found")
        return result


def load_session(
    year: int,
    track: Any,
    session_code: str,
    *,
    telemetry: bool = True,
    laps: bool = True,
    weather: bool = False,
    retries: int = 3,
    backoff: float = 1.0,
) -> SessionWrapper:
    """Load a session via FastF1 with retry and friendly errors.

    Args:
        year: Season year.
        track: Track name, fastf1_name, round number (int), or Track.
        session_code: Session code (FP1, FP2, FP3, Q, R, S, SQ).
        telemetry: Load telemetry.
        laps: Load laps.
        weather: Load weather.
        retries: Number of attempts.
        backoff: Base backoff seconds (exponential).

    Returns:
        SessionWrapper.

    Raises:
        SessionNotHeldError: If session hasn't occurred or data unavailable.
        F1DataError: For other failures.
    """
    _setup_cache()
    identifier = _resolve_identifier(track)
    logger.info("Loading session %s %s %s (telemetry=%s)", year, identifier, session_code, telemetry)

    last_exc: Optional[Exception] = None

    for attempt in range(1, retries + 1):
        try:
            import fastf1  # type: ignore[import-not-found]

            sess = fastf1.get_session(year, identifier, session_code)
            # Load with provided flags
            sess.load(telemetry=telemetry, laps=laps, weather=weather)

            laps_df = getattr(sess, "laps", None)
            if laps_df is None:
                laps_df = pd.DataFrame()
            # Defensive copy
            try:
                laps_df = laps_df.copy() if hasattr(laps_df, "copy") else pd.DataFrame(laps_df)
            except Exception:
                pass

            drivers: list[str] = []
            try:
                raw_drivers = getattr(sess, "drivers", []) or []
                drivers = [str(d) for d in raw_drivers]
            except Exception:
                try:
                    drivers = sorted(laps_df["Driver"].dropna().unique().tolist()) if "Driver" in laps_df.columns else []
                except Exception:
                    drivers = []

            # Event name for display
            event_name = identifier
            try:
                ev = getattr(sess, "event", None)
                if ev is not None:
                    if isinstance(ev, dict):
                        event_name = ev.get("EventName", identifier)
                    elif hasattr(ev, "get"):
                        event_name = ev.get("EventName", identifier)  # type: ignore[union-attr]
                    else:
                        event_name = getattr(ev, "EventName", identifier)
                else:
                    event_name = getattr(sess, "event_name", identifier)
            except Exception:
                pass

            return SessionWrapper(
                session=sess,
                laps=laps_df,
                drivers=drivers,
                year=year,
                track=track,
                session_code=session_code,
                identifier=identifier,
                event_name=str(event_name),
            )

        except Exception as e:
            last_exc = e
            type_name = type(e).__name__
            msg = str(e).lower()

            # Detect not-held / not-yet cases -> SessionNotHeldError immediately (still retry? friendly msg)
            is_not_held = (
                "DataNotLoadedError" in type_name
                or "not" in msg and ("held" in msg or "yet" in msg or "occurred" in msg or "not available" in msg)
                or "no data" in msg
            )
            if is_not_held:
                # Don't retry endlessly for future sessions; but still honor retries for transient?
                # Immediately raise with friendly msg
                raise SessionNotHeldError(
                    f"Session {year} {identifier} {session_code} not yet held or data unavailable: {e}"
                ) from e

            # For other errors, retry with backoff
            if attempt < retries:
                sleep_s = backoff * (2 ** (attempt - 1))
                logger.warning("Session load attempt %s/%s failed (%s), retrying in %.1fs", attempt, retries, e, sleep_s)
                try:
                    time.sleep(sleep_s)
                except Exception:
                    pass
                continue
            # Final failure
            break

    # If we reach here, all retries exhausted
    # Check cache offline fallback: if cache dir has any files for this session, try to load without network?
    # FastF1 already uses cache; if we failed due to network, error would have happened in sess.load()
    # Provide generic F1DataError
    if last_exc is not None:
        raise F1DataError(f"Failed to load session {year} {identifier} {session_code}: {last_exc}") from last_exc
    raise F1DataError(f"Failed to load session {year} {identifier} {session_code}: unknown error")
