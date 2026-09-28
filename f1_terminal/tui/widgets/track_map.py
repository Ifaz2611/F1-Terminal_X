"""Track-map widget helpers (P2-8)."""

from __future__ import annotations

from typing import Any

import pandas as pd


def make_figure(telemetry: pd.DataFrame, color: str = "#E10600"):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from f1_terminal.config import FIGURE_DPI
    from f1_terminal.core.plotting import plot_track_map

    fig, ax = plt.subplots(figsize=(10, 8), dpi=FIGURE_DPI)
    plot_track_map(ax, telemetry, color=color)
    ax.set_title("Track Map", fontsize=12, fontweight="bold")
    fig.tight_layout()
    return fig


def render_ascii(telemetry: pd.DataFrame, track: str = "Track") -> str:
    from f1_terminal.tui.ascii import track_summary_text

    return track_summary_text(telemetry, track)


def textual_widget(*args: Any, **kwargs: Any):
    """Return a Textual Static widget when textual is installed, else None."""
    try:
        from textual.widgets import Static

        return Static(render_ascii(kwargs.get("telemetry"), kwargs.get("track", "Track")))
    except Exception:
        return None
