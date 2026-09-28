"""Sector-bars widget helpers (P2-8)."""

from __future__ import annotations

import pandas as pd


def make_figure(sector_df: pd.DataFrame):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from f1_terminal.config import FIGURE_DPI
    from f1_terminal.core.plotting import plot_sector_bars

    fig, ax = plt.subplots(figsize=(10, max(4, len(sector_df) * 0.5)), dpi=FIGURE_DPI)
    plot_sector_bars(ax, sector_df)
    ax.set_title("Sector Analysis", fontsize=12, fontweight="bold")
    fig.tight_layout()
    return fig


def render_ascii(sector_df: pd.DataFrame) -> str:
    if sector_df is None or sector_df.empty:
        return "No sector data"
    try:
        cols = [c for c in ["Driver", "Sector1Time", "Sector2Time", "Sector3Time"] if c in sector_df.columns]
        return sector_df[cols].to_string(index=False) if cols else sector_df.to_string(index=False)
    except Exception as e:
        return f"Sector render failed: {e}"
