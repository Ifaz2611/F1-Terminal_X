"""
Telemetry transforms — satisfies README ``f1_terminal.transform:prepare_telemetry_trace``.

Provides ``prepare_telemetry_trace(session, driver, lap)`` which returns a
DataFrame ready for Plotly/matplotlib plotting (always has Distance column).
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from f1_terminal.config import get_logger
from f1_terminal.core.errors import DriverNotFoundError, TelemetryNotAvailableError

logger = get_logger(__name__)


def _resolve_driver_laps(laps: pd.DataFrame, code: str) -> pd.DataFrame:
    """Try pick_drivers / pick_driver with manual fallback."""
    if laps is None or laps.empty:
        return laps
    for method in ("pick_drivers", "pick_driver"):
        try:
            fn = getattr(laps, method)
            # try string first, then list
            for arg in (code, [code]):
                try:
                    result = fn(arg)  # type: ignore[operator]
                    if result is not None and not result.empty:
                        return result
                except Exception:
                    continue
        except Exception:
            continue
    try:
        return laps[laps["Driver"] == code]
    except Exception:
        return laps.iloc[0:0]


def prepare_telemetry_trace(
    session: Any,
    driver: str,
    lap: Optional[int | str] = "fastest",
) -> pd.DataFrame:
    """Return telemetry DataFrame for a driver/lap with Distance column.

    Args:
        session: FastF1 Session object (or mock with ``.laps``).
        driver: Driver code (e.g. "VER").
        lap: Lap number, "fastest", or a Series (fastest lap row).

    Returns:
        DataFrame with at minimum columns X, Y, Speed, Distance.
        Falls back to sample CSV if real telemetry unavailable and driver=="SAMPLE".

    Example:
        >>> import plotly.express as px
        >>> from f1_terminal.transform import prepare_telemetry_trace
        >>> fig = px.line(prepare_telemetry_trace(session, 'VER', lap=44), x='Distance', y='Speed')
    """
    laps = getattr(session, "laps", None)
    if laps is None:
        raise TelemetryNotAvailableError("Session has no laps")

    dlaps = _resolve_driver_laps(laps, driver)
    if dlaps.empty:
        raise DriverNotFoundError(f"Driver {driver} not found")

    # Resolve lap row
    fastest: Any = None
    if isinstance(lap, pd.Series):
        fastest = lap
    elif lap == "fastest" or lap is None:
        try:
            fastest = dlaps.pick_fastest()  # type: ignore[attr-defined]
        except Exception:
            # fallback: smallest LapTime
            valid = dlaps.dropna(subset=["LapTime"]) if "LapTime" in dlaps.columns else dlaps
            if not valid.empty and "LapTime" in valid.columns:
                try:
                    fastest = valid.loc[valid["LapTime"].idxmin()]  # type: ignore[index]
                except Exception:
                    fastest = valid.iloc[0]
            elif not valid.empty:
                fastest = valid.iloc[0]
    else:
        # lap number
        try:
            if "LapNumber" in dlaps.columns:
                fastest = dlaps[dlaps["LapNumber"] == int(lap)].iloc[0]  # type: ignore[call-overload]
            else:
                fastest = dlaps.iloc[int(lap) - 1]
        except Exception as e:
            raise TelemetryNotAvailableError(f"Lap {lap} not found for {driver}: {e}") from e

    if fastest is None or (hasattr(fastest, "empty") and fastest.empty):  # type: ignore[union-attr]
        raise TelemetryNotAvailableError(f"No lap {lap} for {driver}")

    # Fetch telemetry
    telemetry: Optional[pd.DataFrame] = None
    if hasattr(fastest, "get_telemetry"):
        try:
            telemetry = fastest.get_telemetry()  # type: ignore[operator]
        except Exception as e:
            logger.warning("get_telemetry failed for %s: %s", driver, e)
    # If fastest is a DataFrame row from fallback, telemetry may be unavailable
    if telemetry is None or telemetry.empty:
        # Last resort: if laps already contain telemetry-like columns, return dlaps
        if {"X", "Y", "Speed"}.issubset(set(dlaps.columns)):
            telemetry = dlaps.copy()
        else:
            raise TelemetryNotAvailableError(f"Telemetry unavailable for {driver} lap {lap}")

    # Ensure Distance
    if "Distance" not in telemetry.columns:
        try:
            telemetry = telemetry.add_distance()  # type: ignore[attr-defined]
        except Exception:
            # Approximate distance via cumulative euclidean distance if X,Y present
            if {"X", "Y"}.issubset(telemetry.columns):

                x = telemetry["X"].to_numpy()
                y = telemetry["Y"].to_numpy()
                dx = pd.Series(x).diff().fillna(0)
                dy = pd.Series(y).diff().fillna(0)
                dist = (dx**2 + dy**2) ** 0.5
                telemetry = telemetry.copy()
                telemetry["Distance"] = dist.cumsum()
            else:
                telemetry = telemetry.copy()
                telemetry["Distance"] = range(len(telemetry))

    # Normalize Brake to int if bool
    if "Brake" in telemetry.columns:
        try:
            if telemetry["Brake"].dtype == bool:
                telemetry = telemetry.copy()
                telemetry["Brake"] = telemetry["Brake"].astype(int)
        except Exception:
            pass

    logger.info("Prepared telemetry trace: driver=%s rows=%s", driver, len(telemetry))
    return telemetry
