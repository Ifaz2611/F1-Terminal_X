"""
I/O helpers — satisfies README ``f1_terminal.io:load_session_data``.

Provides ``load_session_data(year, track, session, source=..., path=...)``
that loads from FastF1 (default) or from CSV/Parquet files.  For offline use
the bundled ``data/telemetry_sample.csv`` is used when FastF1 is unavailable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import pandas as pd

from f1_terminal.config import get_logger, settings
from f1_terminal.core.errors import F1DataError, SessionNotHeldError

logger = get_logger(__name__)

Source = Literal["fastf1", "csv", "parquet", "auto"]


def _sample_csv_path() -> Path:
    return (Path(__file__).parent.parent.parent / "data" / "telemetry_sample.csv").resolve()


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise F1DataError(f"CSV not found: {path}")
    logger.info("Loading telemetry CSV: %s", path)
    return pd.read_csv(path)


def _load_from_fastf1(year: int, track: str | int, session_code: str) -> pd.DataFrame:
    """Try to load via FastF1 and return a telemetry/laps DataFrame."""
    try:
        import fastf1  # type: ignore[import-not-found]
    except ImportError as e:
        raise F1DataError("fastf1 not installed; use source='csv'") from e

    # Resolve track identifier via canonical tracks when int given
    identifier: str | int = track
    if isinstance(track, int):
        try:
            from f1_terminal.tracks import get_track

            identifier = get_track(track).fastf1_name
        except Exception:
            pass
    elif isinstance(track, str) and track.isdigit():
        try:
            from f1_terminal.tracks import get_track

            identifier = get_track(int(track)).fastf1_name
        except Exception:
            pass

    logger.info("Loading session via FastF1: %s %s %s", year, identifier, session_code)
    try:
        # Use unified cache
        cache_dir = settings.cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            fastf1.Cache.set_cache_directory(str(cache_dir))
        except AttributeError:
            fastf1.Cache.enable_cache(str(cache_dir))  # type: ignore[attr-defined]
    except Exception:
        pass

    try:
        sess = fastf1.get_session(year, str(identifier), session_code)
        sess.load(telemetry=True, laps=True, weather=False)
    except Exception as e:
        # Map DataNotLoadedError -> SessionNotHeldError
        msg = str(e)
        if "DataNotLoadedError" in type(e).__name__ or "has not" in msg.lower():
            raise SessionNotHeldError(f"Session {year} {identifier} {session_code} not available: {e}") from e
        raise F1DataError(f"Failed to load session {year} {identifier} {session_code}: {e}") from e

    # Return laps DataFrame if available, else try fastest telemetry
    if hasattr(sess, "laps") and sess.laps is not None and not sess.laps.empty:
        return sess.laps.copy()
    raise F1DataError("No lap data returned from FastF1")


def load_session_data(
    year: int,
    track: str | int,
    session: str = "R",
    source: Source = "auto",
    path: Optional[str | Path] = None,
) -> pd.DataFrame:
    """Load session data from FastF1 or local files.

    Args:
        year: Season year (e.g. 2023).
        track: Track name, fastf1_name, or round number.
        session: Session code (FP1, FP2, FP3, Q, R, S, SQ).
        source: ``"fastf1"`` | ``"csv"`` | ``"parquet"`` | ``"auto"``.
                ``auto`` tries FastF1 first, falls back to sample CSV.
        path: Explicit file path for csv/parquet sources.

    Returns:
        DataFrame — either laps (FastF1) or telemetry sample (CSV).

    Example:
        >>> from f1_terminal.io import load_session_data
        >>> df = load_session_data(2023, "Monza", "Q")
        >>> df = load_session_data(2023, "Monza", "Q", source="csv", path="data/telemetry_sample.csv")
    """
    if path is not None:
        p = Path(path)
        if p.suffix.lower() == ".parquet":
            logger.info("Loading parquet: %s", p)
            return pd.read_parquet(p)
        return _load_csv(p)

    if source == "csv":
        return _load_csv(_sample_csv_path())
    if source == "parquet":
        p = _sample_csv_path().with_suffix(".parquet")
        if p.exists():
            return pd.read_parquet(p)
        raise F1DataError(f"Parquet not found: {p}")
    if source == "fastf1":
        return _load_from_fastf1(year, track, session)

    # auto
    try:
        return _load_from_fastf1(year, track, session)
    except Exception as e:
        logger.warning("FastF1 load failed (%s), falling back to sample CSV", e)
        sample = _sample_csv_path()
        if sample.exists():
            return _load_csv(sample)
        raise
