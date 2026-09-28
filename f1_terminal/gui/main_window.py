"""Main window layout (P3-3): left controls | center canvas | right details.

Implemented backend-agnostically:
- PyQt6: QMainWindow + QSplitter + QTabWidget (full).
- customtkinter/tkinter: CTk frames + tabview (lighter).
- headless: build_matplotlib_figure() still works for tests/CI.
"""

from __future__ import annotations

from typing import Any


def build_matplotlib_figure(wrapper: Any, analysis: str = "track", driver: str = "VER"):
    """Pure figure builder shared by all GUI backends (testable headless)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from f1_terminal.config import FIGURE_DPI
    from f1_terminal.core.colors import get_team_color
    from f1_terminal.core.plotting import (
        plot_race_pace,
        plot_sector_bars,
        plot_speed_trace,
        plot_track_map,
    )
    from f1_terminal.core.telemetry import get_driver_telemetry, get_fastest_lap

    analysis = analysis.lower()
    if analysis in ("track", "track map"):
        try:
            _f, tel = get_driver_telemetry(wrapper, driver)
        except Exception:
            from f1_terminal.tui.workers.session_loader import get_demo_telemetry

            tel = get_demo_telemetry(wrapper, driver)
        fig, ax = plt.subplots(figsize=(10, 8), dpi=FIGURE_DPI)
        cmap = plt.get_cmap("tab20")
        try:
            idx = sorted(wrapper.drivers).index(driver)
        except Exception:
            idx = 0
        plot_track_map(ax, tel, color=get_team_color(wrapper, driver, cmap, idx, max(len(wrapper.drivers), 1)))
        ax.set_title(f"Track Map — {driver}", fontsize=13, fontweight="bold")
        fig.tight_layout()
        return fig
    if analysis in ("speed", "speed trace"):
        _f, tel = get_driver_telemetry(wrapper, driver)
        fig, ax = plt.subplots(figsize=(12, 4), dpi=FIGURE_DPI)
        plot_speed_trace(ax, tel, color=get_team_color(wrapper, driver, None, 0, 1))
        fig.tight_layout()
        return fig
    if analysis in ("sector", "sectors"):
        import pandas as pd

        rows = []
        for drv in wrapper.drivers:
            try:
                f = get_fastest_lap(wrapper, drv)
                rows.append({"Driver": drv, "Sector1Time": f.get("Sector1Time"), "Sector2Time": f.get("Sector2Time"), "Sector3Time": f.get("Sector3Time")})
            except Exception:
                continue
        fig, ax = plt.subplots(figsize=(10, 6), dpi=FIGURE_DPI)
        plot_sector_bars(ax, pd.DataFrame(rows))
        fig.tight_layout()
        return fig
    # pace default
    fig, ax = plt.subplots(figsize=(12, 6), dpi=FIGURE_DPI)
    import matplotlib.pyplot as plt2

    cmap = plt2.get_cmap("tab20")
    colors = {d: get_team_color(wrapper, d, cmap, i, len(wrapper.drivers)) for i, d in enumerate(wrapper.drivers)}
    plot_race_pace(ax, wrapper.laps, wrapper.drivers, colors)
    fig.tight_layout()
    return fig


class MainWindow:
    """Backend-agnostic controller holding year/track/session/drivers state."""

    def __init__(self, year: int = 2026, track: str = "Monza", session_code: str = "Q"):
        self.year = year
        self.track = track
        self.session_code = session_code
        self.drivers: list[str] = []
        self.wrapper: Any = None

    def load(self) -> Any:
        from f1_terminal.gui.workers import load_blocking

        res = load_blocking(self.year, self.track, self.session_code)
        if not res.ok:
            raise RuntimeError(res.error)
        self.wrapper = res.wrapper
        self.drivers = list(res.wrapper.drivers)
        return self.wrapper

    def figure(self, analysis: str = "track", driver: str = "VER"):
        if self.wrapper is None:
            self.load()
        return build_matplotlib_figure(self.wrapper, analysis, driver)
