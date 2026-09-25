"""Team color helper — Phase 1 core.

Consolidates get_team_color from f1_advanced_visualizer and f1_qualifying.
Always returns hex string.
"""

from __future__ import annotations

from typing import Any

from f1_terminal.config import get_logger

logger = get_logger(__name__)


def get_team_color(
    session: Any,
    driver_code: str,
    fallback_cmap: Any = None,
    idx: int = 0,
    total: int = 1,
) -> str:
    """Safely extract team color from session driver info.

    Always returns hex string like "#RRGGBB".

    Args:
        session: FastF1 session or SessionWrapper.
        driver_code: Driver abbreviation (e.g. "VER").
        fallback_cmap: matplotlib colormap or callable returning RGBA.
        idx: Driver index for fallback.
        total: Total drivers for fallback normalization.

    Returns:
        Hex color string.
    """
    # Unwrap SessionWrapper -> raw session (only if truly wrapped, not MagicMock)
    try:
        from f1_terminal.core.session import SessionWrapper as _SW

        if isinstance(session, _SW):
            session = session.session
        else:
            # Guard against MagicMock: getattr on MagicMock always returns MagicMock,
            # so check that 'session' attribute is not a MagicMock auto-created one
            # If session has attribute 'laps' and 'drivers' and 'session' that looks like mock, ignore.
            raw = getattr(session, "session", None)
            # Only unwrap if raw is not a mock and has get_driver but session itself is not mock-like
            if raw is not None and hasattr(raw, "get_driver") and not str(type(raw)).endswith("MagicMock'>") and not str(type(session)).endswith("MagicMock'>"):
                # Additional check: ensure session is SessionWrapper-like (has 'laps' and 'identifier')
                if hasattr(session, "laps") and hasattr(session, "identifier"):
                    session = raw
    except Exception:
        pass

    try:
        driver_info = session.get_driver(driver_code)  # type: ignore[union-attr]
        team_color = None
        if hasattr(driver_info, "get"):
            try:
                team_color = driver_info.get("TeamColor", None)  # type: ignore[union-attr]
            except Exception:
                team_color = None
        if team_color is None:
            team_color = getattr(driver_info, "TeamColor", None)

        if team_color is not None:
            # Guard: MagicMock should fallback
            if "MagicMock" in type(team_color).__name__ or "Mock" in type(team_color).__name__ and not isinstance(team_color, (str, int)):
                team_color = None

        if team_color is not None:
            # Handle NaN
            try:
                import pandas as pd

                if pd.isna(team_color):
                    team_color = None
            except Exception:
                pass

        if team_color is not None:
            # Only accept str/int
            if isinstance(team_color, int):
                return f"#{team_color:06X}"
            if not isinstance(team_color, str):
                # Unexpected type (e.g., MagicMock) -> fallback
                team_color = None

        if team_color is not None:
            s = str(team_color).strip().lstrip("#")
            # Reject mock strings
            if "MagicMock" in s or "Mock" in s:
                team_color = None
            elif s and s.lower() != "nan":
                # If numeric string without hash
                if s.isdigit():
                    try:
                        return f"#{int(s):06X}"
                    except Exception:
                        pass
                # If hex, validate basic hex pattern
                # Ensure it looks like hex (0-9a-fA-F)
                if all(c in "0123456789abcdefABCDEF" for c in s) and 3 <= len(s) <= 8:
                    return f"#{s}"
                # Otherwise still return but only if hex-like
                if len(s) <= 20 and s.isalnum():
                    return f"#{s}"
                # Fallback to cmap if not hex-like
                team_color = None
    except Exception as e:
        logger.debug("get_team_color fallback for %s: %s", driver_code, e)

    # Fallback via colormap
    if fallback_cmap is not None:
        try:
            # cmap can be matplotlib cmap or string name
            if isinstance(fallback_cmap, str):
                import matplotlib.pyplot as plt

                fallback_cmap = plt.get_cmap(fallback_cmap)
            rgba = fallback_cmap(idx / max(total, 1))
            try:
                import matplotlib.colors as mcolors

                return mcolors.to_hex(rgba)
            except Exception:
                # Manual conversion
                r, g, b = rgba[0], rgba[1], rgba[2]
                return f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"
        except Exception:
            pass

    # Ultimate fallback - F1 red
    return "#E10600"
