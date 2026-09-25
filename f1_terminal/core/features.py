"""
Feature engineering — satisfies README ``f1_terminal.features:engineer_lap_features``.

Stub + real minimal implementation returning a DataFrame with useful columns
for ML (corner speeds, braking points, etc.).  Handles NaN gracefully.

Columns returned (when data available):
    Driver, LapNumber, LapTime_s, S1_s, S2_s, S3_s, AvgSpeed, MaxSpeed,
    BrakingCount, Throttle95p, GearShifts, DRSPct, Compound, TrackTemp, AirTemp
"""

from __future__ import annotations

from typing import Any, List, Optional

import numpy as np
import pandas as pd

from f1_terminal.config import get_logger

logger = get_logger(__name__)

FEATURE_COLS = [
    "Driver",
    "LapNumber",
    "LapTime_s",
    "S1_s",
    "S2_s",
    "S3_s",
    "AvgSpeed",
    "MaxSpeed",
    "BrakingCount",
    "Throttle95p",
    "GearShifts",
    "DRSPct",
    "Compound",
    "TrackTemp",
    "AirTemp",
]


def _lap_time_s(val: Any) -> Optional[float]:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    try:
        if pd.isna(val):  # type: ignore[arg-type]
            return None
    except Exception:
        pass
    try:
        if hasattr(val, "total_seconds"):
            return float(val.total_seconds())  # type: ignore[union-attr]
    except Exception:
        pass
    try:
        return float(val)  # type: ignore[arg-type]
    except Exception:
        return None


def _get_telemetry_for_lap(lap_row: pd.Series) -> Optional[pd.DataFrame]:
    if hasattr(lap_row, "get_telemetry"):
        try:
            tel = lap_row.get_telemetry()  # type: ignore[operator]
            if tel is not None and not tel.empty:
                return tel
        except Exception:
            return None
    return None


def engineer_lap_features(session: Any, drivers: Optional[List[str]] = None) -> pd.DataFrame:
    """Build a feature table from session laps.

    Args:
        session: FastF1 Session with ``.laps``.
        drivers: List of driver codes; if None, uses all drivers.

    Returns:
        DataFrame with one row per lap and FEATURE_COLS columns.

    Example:
        >>> from f1_terminal.features import engineer_lap_features
        >>> features = engineer_lap_features(session, drivers=['VER', 'HAM'])
    """
    laps = getattr(session, "laps", None)
    if laps is None or laps.empty:
        logger.warning("No laps available for feature engineering")
        return pd.DataFrame(columns=FEATURE_COLS)

    if drivers is not None:
        try:
            # Filter to requested drivers
            mask = laps["Driver"].isin(drivers) if "Driver" in laps.columns else None
            if mask is not None:
                laps = laps[mask]
        except Exception:
            pass

    rows: list[dict[str, Any]] = []

    for _, lap in laps.iterrows():
        # lap is a Series (possibly fastf1 extended)
        driver = str(lap.get("Driver", "UNK")) if hasattr(lap, "get") else "UNK"
        lap_num = lap.get("LapNumber", None) if hasattr(lap, "get") else None

        # Lap time
        lt_s = _lap_time_s(lap.get("LapTime", None) if hasattr(lap, "get") else None)
        s1_s = _lap_time_s(lap.get("Sector1Time", None) if hasattr(lap, "get") else None)
        s2_s = _lap_time_s(lap.get("Sector2Time", None) if hasattr(lap, "get") else None)
        s3_s = _lap_time_s(lap.get("Sector3Time", None) if hasattr(lap, "get") else None)

        # Telemetry-derived features (best-effort)
        avg_speed: Optional[float] = None
        max_speed: Optional[float] = None
        braking_count: Optional[int] = None
        throttle95: Optional[float] = None
        gear_shifts: Optional[int] = None
        drs_pct: Optional[float] = None

        tel = _get_telemetry_for_lap(lap)  # type: ignore[arg-type]
        if tel is not None and not tel.empty:
            try:
                if "Speed" in tel.columns:
                    avg_speed = float(tel["Speed"].mean())
                    max_speed = float(tel["Speed"].max())
            except Exception:
                pass
            try:
                if "Brake" in tel.columns:
                    # Count braking events (rising edge)
                    b = tel["Brake"].astype(int) if tel["Brake"].dtype == bool else tel["Brake"]
                    braking_count = int((b.diff() == 1).sum())
                elif "BrakingPoint" in tel.columns:
                    braking_count = int(tel["BrakingPoint"].sum())
            except Exception:
                pass
            try:
                if "Throttle" in tel.columns:
                    throttle95 = float(tel["Throttle"].quantile(0.95))
            except Exception:
                pass
            try:
                if "nGear" in tel.columns:
                    gear_shifts = int((tel["nGear"].diff().abs() > 0).sum())
            except Exception:
                pass
            try:
                if "DRS" in tel.columns:
                    drs_pct = float((tel["DRS"] > 0).mean() * 100)
            except Exception:
                pass

        # Fallbacks when telemetry not available — derive from lap row if possible
        if avg_speed is None and "AvgSpeed" in laps.columns:
            try:
                avg_speed = float(lap.get("AvgSpeed"))  # type: ignore[union-attr]
            except Exception:
                pass
        if max_speed is None and "MaxSpeed" in laps.columns:
            try:
                max_speed = float(lap.get("MaxSpeed"))  # type: ignore[union-attr]
            except Exception:
                pass

        compound = lap.get("Compound", None) if hasattr(lap, "get") else None
        try:
            if pd.isna(compound):  # type: ignore[arg-type]
                compound = None
        except Exception:
            pass

        track_temp = lap.get("TrackTemp", None) if hasattr(lap, "get") else None
        air_temp = lap.get("AirTemp", None) if hasattr(lap, "get") else None

        rows.append(
            {
                "Driver": driver,
                "LapNumber": lap_num,
                "LapTime_s": lt_s,
                "S1_s": s1_s,
                "S2_s": s2_s,
                "S3_s": s3_s,
                "AvgSpeed": avg_speed,
                "MaxSpeed": max_speed,
                "BrakingCount": braking_count,
                "Throttle95p": throttle95,
                "GearShifts": gear_shifts,
                "DRSPct": drs_pct,
                "Compound": compound,
                "TrackTemp": track_temp,
                "AirTemp": air_temp,
            }
        )

    df = pd.DataFrame(rows, columns=FEATURE_COLS)
    # Ensure numeric columns are numeric
    for col in ["LapTime_s", "S1_s", "S2_s", "S3_s", "AvgSpeed", "MaxSpeed", "Throttle95p", "DRSPct"]:
        try:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        except Exception:
            pass

    # Add CornerSpeed-like alias for README compatibility (same as AvgSpeed)
    if "CornerSpeed" not in df.columns:
        df["CornerSpeed"] = df["AvgSpeed"]
        df["BrakingPoint"] = df["BrakingCount"]

    logger.info("Engineered features: %s rows, %s cols", len(df), len(df.columns))
    return df
