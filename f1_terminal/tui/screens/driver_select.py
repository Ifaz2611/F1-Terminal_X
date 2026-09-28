"""Driver-select screen model (P2-5). Replaces driver input() loops."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DriverRow:
    code: str
    team: str
    color: str
    lap_time: str
    selected: bool = False


def _fmt_lap(v) -> str:
    try:
        import pandas as pd

        if pd.isna(v):
            return "N/A"
        if hasattr(v, "total_seconds"):
            s = float(v.total_seconds())
            return f"{int(s // 60)}:{s % 60:06.3f}"
        return str(v)
    except Exception:
        return str(v)


def driver_rows(wrapper: Any) -> list[DriverRow]:
    """Build rows with team color chips + fastest lap; sorted by lap time."""
    from f1_terminal.core.telemetry import get_fastest_lap

    rows: list[DriverRow] = []
    for drv in getattr(wrapper, "drivers", []):
        team, color, lap = "Unknown", "#E10600", "N/A"
        try:
            info = wrapper.session.get_driver(drv)
            team = info.get("TeamName", team) if hasattr(info, "get") else getattr(info, "TeamName", team)
            c = info.get("TeamColor", None) if hasattr(info, "get") else getattr(info, "TeamColor", None)
            if c:
                color = f"#{str(c).lstrip('#')}"
        except Exception:
            pass
        try:
            fastest = get_fastest_lap(wrapper, drv)
            lap = _fmt_lap(fastest.get("LapTime"))
            sort = fastest.get("LapTime").total_seconds() if hasattr(fastest.get("LapTime"), "total_seconds") else float("inf")
        except Exception:
            sort = float("inf")
        rows.append(DriverRow(code=drv, team=team, color=color, lap_time=lap))
        rows[-1].__dict__["_sort"] = sort
    rows.sort(key=lambda r: getattr(r, "_sort", float("inf")))
    return rows


def toggle_selection(selected: set[str], code: str) -> set[str]:
    """Space toggles; returns new set."""
    out = set(selected)
    if code in out:
        out.discard(code)
    else:
        out.add(code)
    return out


def select_all(wrapper: Any) -> set[str]:
    return set(getattr(wrapper, "drivers", []))
