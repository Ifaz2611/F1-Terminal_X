"""Speed-trace widget helpers (P2-8)."""

from __future__ import annotations

import pandas as pd


def make_figure(telemetry: pd.DataFrame, color: str = "#E10600"):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from f1_terminal.config import FIGURE_DPI
    from f1_terminal.core.plotting import plot_speed_trace

    fig, ax = plt.subplots(figsize=(12, 4), dpi=FIGURE_DPI)
    plot_speed_trace(ax, telemetry, color=color)
    ax.set_title("Speed Trace", fontsize=12, fontweight="bold")
    fig.tight_layout()
    return fig


def render_ascii(telemetry: pd.DataFrame, driver: str = "DRV") -> str:
    from f1_terminal.tui.ascii import speed_plotext, telemetry_summary_text

    try:
        art = speed_plotext(telemetry, title=f"Speed — {driver}")
        summary = telemetry_summary_text(telemetry, driver)
        return f"{art}\n{summary}"
    except Exception as e:
        return f"{driver}: render failed ({e})"
