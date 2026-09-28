"""ASCII / terminal-safe rendering helpers (P2-7 baseline).

Uses ``plotext`` when available, otherwise plain-text summaries.
All functions work in ordinary terminals and CI — no Sixel/Kitty required.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from f1_terminal.config import get_logger

logger = get_logger(__name__)


def telemetry_summary_text(telemetry: pd.DataFrame, driver: str = "DRV") -> str:
    """Return a short terminal-safe summary for one telemetry trace."""
    if telemetry is None or telemetry.empty:
        return f"{driver}: no telemetry"
    lines = [f"Driver {driver} — {len(telemetry)} samples"]
    try:
        if "Speed" in telemetry.columns:
            lines.append(
                f"Speed: max {telemetry['Speed'].max():.1f} km/h, "
                f"avg {telemetry['Speed'].mean():.1f} km/h"
            )
    except Exception:
        pass
    try:
        if "Distance" in telemetry.columns:
            lines.append(f"Distance: {telemetry['Distance'].max():.0f} m")
    except Exception:
        pass
    try:
        if "nGear" in telemetry.columns:
            lines.append(f"Gears: {sorted(telemetry['nGear'].dropna().astype(int).unique().tolist())}")
    except Exception:
        pass
    try:
        if "DRS" in telemetry.columns:
            pct = float((telemetry["DRS"] > 0).mean() * 100)
            lines.append(f"DRS open: {pct:.1f}%")
    except Exception:
        pass
    return "\n".join(lines)


def track_summary_text(telemetry: pd.DataFrame, track: str = "Track") -> str:
    """Terminal-safe track-map substitute: bounding box + point count."""
    if telemetry is None or telemetry.empty or "X" not in telemetry.columns:
        return f"{track}: no position data"
    try:
        x0, x1 = float(telemetry["X"].min()), float(telemetry["X"].max())
        y0, y1 = float(telemetry["Y"].min()), float(telemetry["Y"].max())
        return (
            f"Track {track}: {len(telemetry)} pts | "
            f"X [{x0:.0f}, {x1:.0f}] Y [{y0:.0f}, {y1:.0f}]"
        )
    except Exception as e:
        return f"{track}: summary unavailable ({e})"


def speed_plotext(
    telemetry: pd.DataFrame,
    title: str = "Speed trace",
    width: int = 80,
    height: int = 20,
) -> str:
    """Render distance-vs-speed as plotext ASCII string.

    Falls back to :func:`telemetry_summary_text` when plotext is missing
    or data is incomplete, so ``--ascii`` never crashes in CI.
    """
    if telemetry is None or telemetry.empty:
        return f"{title}: no telemetry"
    if "Speed" not in telemetry.columns:
        return f"{title}: Speed unavailable"
    x = (
        telemetry["Distance"].tolist()
        if "Distance" in telemetry.columns
        else list(range(len(telemetry)))
    )
    y = telemetry["Speed"].ffill().fillna(0).tolist() if len(telemetry) else []
    try:
        import plotext as plt  # type: ignore[import-not-found]

        plt.clear_figure()
        plt.plot_size(width, height)
        plt.title(title)
        plt.xlabel("Distance (m)")
        plt.ylabel("Speed (km/h)")
        plt.plot(x, y)
        # build_string returns the canvas without printing
        canvas = plt.build_string() if hasattr(plt, "build_string") else plt.build()
        plt.clear_figure()
        return str(canvas)
    except ImportError:
        logger.debug("plotext not installed, using text fallback")
        return telemetry_summary_text(telemetry)
    except Exception as e:
        logger.warning("plotext render failed: %s", e)
        return telemetry_summary_text(telemetry)


def save_matplotlib_figure(fig: Any, track: str, session: str, driver: str = "") -> Path:
    """Save current matplotlib figure to ~/Downloads/f1_<track>_<session>_<driver>.png."""
    downloads = Path.home() / "Downloads"
    try:
        downloads.mkdir(parents=True, exist_ok=True)
    except Exception:
        downloads = Path.cwd()
    def _safe(s: object) -> str:
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in str(s))

    name = f"f1_{_safe(track)}_{_safe(session)}"
    if driver:
        name += f"_{_safe(driver)}"
    out = downloads / f"{name}.png"
    try:
        from f1_terminal.config import FIGURE_DPI

        fig.savefig(str(out), dpi=FIGURE_DPI, bbox_inches="tight")
    except Exception:
        fig.savefig(str(out), bbox_inches="tight")
    return out


def detect_image_protocol() -> Optional[str]:
    """Stretch-only helper: detect Sixel/Kitty support.

    Never blocks; returns None when unsupported (the normal case in CI).
    MVP must never require this.
    """
    import os

    term = os.environ.get("TERM", "")
    term_prog = os.environ.get("TERM_PROGRAM", "")
    if "kitty" in term_prog.lower() or "kitty" in term.lower():
        return "kitty"
    # Sixel detection is terminal-specific; report None by default.
    return None
