"""Telemetry helpers — Phase 1 core.

Pure wrappers around FastF1 fastest-lap + telemetry fetching.
Handles pick_drivers/pick_driver fallback, missing telemetry, add_distance().
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from f1_terminal.config import get_logger
from f1_terminal.core.errors import DriverNotFoundError, TelemetryNotAvailableError

logger = get_logger(__name__)


def _resolve_driver_laps(laps: pd.DataFrame, code: str) -> pd.DataFrame:
    if laps is None or getattr(laps, "empty", False):
        return laps
    for method in ("pick_drivers", "pick_driver"):
        try:
            fn = getattr(laps, method, None)
            if fn is None:
                continue
            for arg in (code, [code]):
                try:
                    result = fn(arg)  # type: ignore[operator]
                    if result is not None and not getattr(result, "empty", True):
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
    return laps.iloc[0:0]


def get_fastest_lap(session: Any, driver_code: str) -> pd.Series:
    """Return fastest lap Series for driver.

    Args:
        session: SessionWrapper or raw fastf1 Session.
        driver_code: e.g. "VER"

    Returns:
        Series (fastest lap row) with get_telemetry method.

    Raises:
        DriverNotFoundError, TelemetryNotAvailableError
    """
    # Unwrap SessionWrapper
    laps = getattr(session, "laps", None)
    if laps is None:
        # maybe session is directly laps DataFrame? fallback
        laps = getattr(getattr(session, "session", None), "laps", None)
    if laps is None:
        raise TelemetryNotAvailableError("Session has no laps")

    dlaps = _resolve_driver_laps(laps, driver_code)
    if dlaps is None or getattr(dlaps, "empty", False):
        raise DriverNotFoundError(f"Driver {driver_code} not found")

    # Try pick_fastest on driver laps
    fastest = None
    try:
        fastest = dlaps.pick_fastest()  # type: ignore[attr-defined]
    except Exception:
        fastest = None

    if fastest is None:
        # Fallback: smallest LapTime
        try:
            valid = dlaps.dropna(subset=["LapTime"]) if "LapTime" in dlaps.columns else dlaps
            if not valid.empty:
                fastest = valid.loc[valid["LapTime"].idxmin()]  # type: ignore[index]
            else:
                fastest = dlaps.iloc[0]  # type: ignore[call-overload]
        except Exception as e:
            raise TelemetryNotAvailableError(f"No valid fastest lap for {driver_code}: {e}") from e

    if fastest is None or (hasattr(fastest, "empty") and fastest.empty):  # type: ignore[union-attr]
        raise TelemetryNotAvailableError(f"No lap for driver {driver_code}")

    # Validate LapTime present
    try:
        if pd.isna(fastest.get("LapTime")):  # type: ignore[union-attr]
            raise TelemetryNotAvailableError(f"Driver {driver_code} has no valid LapTime")
    except TelemetryNotAvailableError:
        raise
    except Exception:
        pass

    return fastest  # type: ignore[return-value]


def get_telemetry(fastest_lap: pd.Series) -> pd.DataFrame:
    """Return telemetry DataFrame for a fastest_lap Series.

    Ensures Distance column exists (via add_distance or euclidean fallback).
    Raises TelemetryNotAvailableError if unavailable.
    """
    telemetry: Any = None
    if hasattr(fastest_lap, "get_telemetry"):
        try:
            telemetry = fastest_lap.get_telemetry()  # type: ignore[operator]
        except Exception as e:
            raise TelemetryNotAvailableError(f"get_telemetry failed: {e}") from e

    if telemetry is None or getattr(telemetry, "empty", False):
        raise TelemetryNotAvailableError("Telemetry empty or unavailable")

    # Ensure Distance
    if "Distance" not in telemetry.columns:
        try:
            telemetry = telemetry.add_distance()  # type: ignore[attr-defined]
        except Exception:
            if {"X", "Y"}.issubset(set(telemetry.columns)):
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

    # Normalize Brake bool -> int
    if "Brake" in telemetry.columns:
        try:
            if telemetry["Brake"].dtype == bool:
                telemetry = telemetry.copy()
                telemetry["Brake"] = telemetry["Brake"].astype(int)
        except Exception:
            pass

    return telemetry  # type: ignore[return-value]


def get_driver_telemetry(session: Any, driver_code: str) -> tuple[pd.Series, pd.DataFrame]:
    """Combine get_fastest_lap + get_telemetry.

    Returns:
        (fastest_lap_series, telemetry_df)

    Raises:
        DriverNotFoundError, TelemetryNotAvailableError
    """
    fastest = get_fastest_lap(session, driver_code)
    telemetry = get_telemetry(fastest)
    logger.info("Got telemetry for %s: %s rows", driver_code, len(telemetry))
    return fastest, telemetry
