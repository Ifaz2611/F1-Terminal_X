"""Plotting pure-function tests (Agg backend, mocked DataFrames)."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def _tel(n=30):

    x = list(range(n))
    return pd.DataFrame(
        {
            "X": x,
            "Y": [i * 0.5 for i in x],
            "Speed": [200 + i for i in x],
            "Throttle": [100] * n,
            "Brake": [0] * n,
            "nGear": [3 + (i // 5) for i in x],
            "DRS": [1 if i > 10 else 0 for i in x],
            "Distance": [i * 10 for i in x],
        }
    )


def test_plot_track_map():
    from f1_terminal.core.plotting import plot_track_map

    fig, ax = plt.subplots()
    plot_track_map(ax, _tel())
    assert len(ax.collections) > 0 or len(ax.lines) > 0
    plt.close(fig)


def test_plot_track_map_empty():
    from f1_terminal.core.plotting import plot_track_map

    fig, ax = plt.subplots()
    plot_track_map(ax, pd.DataFrame())
    plt.close(fig)


def test_plot_speed_trace():
    from f1_terminal.core.plotting import plot_speed_trace

    fig, ax = plt.subplots()
    plot_speed_trace(ax, _tel())
    assert len(ax.lines) > 0
    plt.close(fig)


def test_plot_throttle_brake_gear():
    from f1_terminal.core.plotting import plot_gear_map, plot_throttle_brake

    fig, ax = plt.subplots()
    plot_throttle_brake(ax, _tel())
    plt.close(fig)
    fig, ax = plt.subplots()
    plot_gear_map(ax, _tel())
    plt.close(fig)


def test_plot_sector_pace_tire(mock_session):
    from f1_terminal.core.plotting import plot_race_pace, plot_sector_bars, plot_tire_strategy

    sector_df = pd.DataFrame(
        {
            "Driver": ["VER", "HAM"],
            "Sector1Time": [30.0, 30.5],
            "Sector2Time": [30.0, 30.5],
            "Sector3Time": [30.1, 30.4],
        }
    )
    fig, ax = plt.subplots()
    plot_sector_bars(ax, sector_df)
    assert len(ax.patches) > 0
    plt.close(fig)

    fig, ax = plt.subplots()
    plot_race_pace(ax, mock_session.laps, ["VER", "HAM"], {"VER": "#0600EF", "HAM": "#00D2BE"})
    plt.close(fig)

    fig, ax = plt.subplots()
    plot_tire_strategy(ax, mock_session.laps, ["VER", "HAM"])
    plt.close(fig)
