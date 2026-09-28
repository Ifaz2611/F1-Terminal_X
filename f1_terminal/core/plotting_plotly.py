"""Plotly renderer mirroring core/plotting.py (P3b-2).

Each function returns a plotly Figure for hover/zoom in Streamlit/Dash.
Falls back gracefully when plotly is missing (returns None).
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from f1_terminal.config import get_logger

logger = get_logger(__name__)


def _require_plotly():
    try:
        import plotly.graph_objects as go  # type: ignore[import-not-found]

        return go
    except ImportError as e:
        raise ImportError("plotly not installed; pip install plotly") from e


def plot_track_map_plotly(telemetry: pd.DataFrame, color: str = "#E10600"):
    go = _require_plotly()
    fig = go.Figure()
    if telemetry is None or telemetry.empty or "X" not in telemetry.columns:
        fig.add_annotation(text="No position data", showarrow=False)
        return fig
    tel = telemetry.dropna(subset=["X", "Y"])
    if "Speed" in tel.columns:
        fig.add_trace(go.Scatter(x=tel["X"], y=tel["Y"], mode="markers+lines", marker={"color": tel["Speed"], "colorscale": "Viridis", "showscale": True}, name="Track"))
    else:
        fig.add_trace(go.Scatter(x=tel["X"], y=tel["Y"], mode="lines", line={"color": color}, name="Track"))
    fig.update_layout(title="Track Map", yaxis_scaleanchor="x")
    return fig


def plot_speed_plotly(telemetry: pd.DataFrame, color: str = "#E10600"):
    go = _require_plotly()
    fig = go.Figure()
    if telemetry is None or telemetry.empty or "Speed" not in telemetry.columns:
        fig.add_annotation(text="No speed data", showarrow=False)
        return fig
    x = telemetry["Distance"] if "Distance" in telemetry.columns else range(len(telemetry))
    fig.add_trace(go.Scatter(x=x, y=telemetry["Speed"], mode="lines", line={"color": color}, name="Speed", hovertemplate="Dist %{x:.0f} m<br>Speed %{y:.1f} km/h"))
    fig.update_layout(title="Speed Trace", xaxis_title="Distance (m)", yaxis_title="Speed (km/h)")
    return fig


def plot_sectors_plotly(sector_df: pd.DataFrame):
    go = _require_plotly()
    fig = go.Figure()
    if sector_df is None or sector_df.empty:
        fig.add_annotation(text="No sector data", showarrow=False)
        return fig
    for col, color in (("Sector1Time", "#FF6B6B"), ("Sector2Time", "#4ECDC4"), ("Sector3Time", "#45B7D1")):
        if col in sector_df.columns:
            fig.add_trace(go.Bar(y=sector_df.get("Driver", range(len(sector_df))), x=sector_df[col], name=col, orientation="h", marker_color=color))
    fig.update_layout(title="Sector Times", barmode="stack")
    return fig


def plot_pace_plotly(laps: pd.DataFrame, drivers: Any = None):
    go = _require_plotly()
    fig = go.Figure()
    if laps is None or laps.empty:
        fig.add_annotation(text="No lap data", showarrow=False)
        return fig
    if drivers is None:
        try:
            drivers = sorted(laps["Driver"].dropna().unique().tolist())
        except Exception:
            drivers = []
    for drv in drivers or []:
        try:
            dl = laps[laps["Driver"] == drv]
            y = pd.to_timedelta(dl["LapTime"]).dt.total_seconds()
            fig.add_trace(go.Scatter(x=dl["LapNumber"], y=y, mode="lines+markers", name=drv))
        except Exception:
            continue
    fig.update_layout(title="Race Pace", xaxis_title="Lap", yaxis_title="Lap time (s)")
    return fig
