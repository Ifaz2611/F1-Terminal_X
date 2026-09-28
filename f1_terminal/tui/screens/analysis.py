"""Analysis screen model (P2-6). Replaces display_analysis_menu()."""

from __future__ import annotations

TABS = ["Track Map", "Speed Trace", "Throttle/Brake", "Sectors", "Race Pace", "All"]
TAB_KEYS = {"1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5}


def tab_for_key(key: str) -> int | None:
    return TAB_KEYS.get(key)
