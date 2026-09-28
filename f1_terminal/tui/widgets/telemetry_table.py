"""Telemetry-table widget helpers (P2-8).

Replaces printed lap summary with a sortable table model.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def build_lap_table_rows(wrapper: Any) -> pd.DataFrame:
    """Return sortable lap-summary DataFrame: Driver | Team | LapTime | S1 | S2 | S3."""
    from f1_terminal.core.telemetry import get_fastest_lap

    rows: list[dict] = []
    for drv in getattr(wrapper, "drivers", []):
        try:
            fastest = get_fastest_lap(wrapper, drv)
        except Exception:
            # Demo wrapper without per-driver telemetry: use laps frame directly
            try:
                dl = wrapper.laps[wrapper.laps["Driver"] == drv].iloc[0]
                fastest = dl
            except Exception:
                continue
        try:
            team = "Unknown"
            try:
                info = wrapper.session.get_driver(drv)
                team = info.get("TeamName", "Unknown") if hasattr(info, "get") else getattr(info, "TeamName", "Unknown")
            except Exception:
                pass

            def _fmt(v):
                try:
                    if pd.isna(v):
                        return "N/A"
                    if hasattr(v, "total_seconds"):
                        s = float(v.total_seconds())
                        return f"{int(s // 60)}:{s % 60:06.3f}"
                    return str(v)
                except Exception:
                    return str(v)

            rows.append(
                {
                    "Driver": drv,
                    "Team": team,
                    "LapTime": _fmt(fastest.get("LapTime")),
                    "S1": _fmt(fastest.get("Sector1Time")),
                    "S2": _fmt(fastest.get("Sector2Time")),
                    "S3": _fmt(fastest.get("Sector3Time")),
                    "_sort": _sort_key(fastest.get("LapTime")),
                }
            )
        except Exception:
            continue
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("_sort").drop(columns=["_sort"])
    return df


def _sort_key(v) -> float:
    try:
        if pd.isna(v):
            return float("inf")
        if hasattr(v, "total_seconds"):
            return float(v.total_seconds())
        return float(v)
    except Exception:
        return float("inf")


def render_ascii(wrapper: Any) -> str:
    df = build_lap_table_rows(wrapper)
    if df.empty:
        return "No lap data"
    return df.to_string(index=False)
