"""Smoke tests for plotting with mocked data (Agg backend, no plt.show)."""

import matplotlib

matplotlib.use("Agg")
from unittest.mock import MagicMock

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from f1_terminal.tracks import TRACKS


@pytest.fixture(autouse=True)
def no_show(monkeypatch):
    monkeypatch.setattr(plt, "show", lambda *a, **k: None)


def _make_session_with_laps():
    laps = pd.DataFrame(
        {
            "Driver": ["VER", "HAM", "VER", "HAM"],
            "LapTime": pd.to_timedelta(["90s", "91s", "89.5s", "90.5s"]),
            "LapNumber": [1, 1, 2, 2],
            "Sector1Time": pd.to_timedelta(["30s"] * 4),
            "Sector2Time": pd.to_timedelta(["30s"] * 4),
            "Sector3Time": pd.to_timedelta(["30s"] * 4),
            "PitInTime": [pd.NaT] * 4,
            "PitOutTime": [pd.NaT] * 4,
        }
    )

    # Mock fastest lap telemetry
    def make_tel():
        tel = pd.DataFrame(
            {
                "X": [0, 10, 20, 30],
                "Y": [0, 10, 20, 15],
                "Speed": [200, 210, 220, 230],
                "Throttle": [100, 100, 80, 100],
                "Brake": [0, 0, 1, 0],
                "nGear": [3, 4, 5, 6],
                "DRS": [0, 1, 1, 0],
                "Distance": [0, 10, 20, 30],
            }
        )
        tel.add_distance = lambda: tel  # type: ignore[attr-defined]
        return tel

    # Attach pick helpers

    def _pick_drivers(code):
        if isinstance(code, list):
            return laps[laps["Driver"].isin(code)]
        res = laps[laps["Driver"] == code].copy()
        # attach pick_fastest to filtered df
        def pick_fastest():
            if res.empty:
                return None
            row = res.loc[res["LapTime"].idxmin()].copy()
            row.get_telemetry = lambda: make_tel()  # type: ignore[attr-defined]
            return row

        res.pick_fastest = pick_fastest  # type: ignore[attr-defined]
        return res

    def _pick_driver(code):
        return _pick_drivers(code)

    laps.pick_drivers = _pick_drivers  # type: ignore[attr-defined]
    laps.pick_driver = _pick_driver  # type: ignore[attr-defined]

    # Global pick_fastest for whole laps (used by some code paths)
    session = MagicMock()
    session.laps = laps
    session.drivers = ["VER", "HAM"]
    session.get_driver.return_value = {"TeamColor": "FF0000", "TeamName": "Test"}

    return session


def test_track_visualizer_creates_figures():
    from f1_terminal.f1_advanced_visualizer import TrackVisualizer

    session = _make_session_with_laps()
    track = TRACKS[8]  # Austria
    viz = TrackVisualizer(session, 2024, track)

    # Each plot should not raise and should create a Figure (via plt.gcf or returning None but not error)
    # The current viz methods call plt.show (mocked) and close via plt; we check no exception

    viz.plot_fastest_laps_track()
    fig = plt.gcf()
    assert fig is not None
    plt.close("all")

    viz.plot_speed_comparison(["VER"])
    plt.close("all")

    viz.plot_sector_analysis()
    plt.close("all")

    viz.plot_race_pace()
    plt.close("all")


def test_core_io_csv():
    from f1_terminal.core.io import load_session_data

    df = load_session_data(2023, "Monza", "Q", source="csv")
    assert not df.empty
    assert "X" in df.columns or "Speed" in df.columns


def test_core_transforms_prepare_trace(mock_session):
    # Build session with attachable fastest
    import pandas as pd

    from f1_terminal.core.transforms import prepare_telemetry_trace

    mock_session.laps.copy()

    # Create a mock fastest lap row with get_telemetry
    def _mk_tel():
        tel = pd.DataFrame(
            {
                "X": [0, 1, 2],
                "Y": [0, 1, 2],
                "Speed": [100, 150, 200],
                "Throttle": [100, 100, 100],
                "Brake": [0, 0, 0],
                "nGear": [3, 4, 5],
                "DRS": [0, 0, 1],
            }
        )
        tel.add_distance = lambda: tel.assign(Distance=[0, 10, 20])  # type: ignore[attr-defined]
        return tel

    # Patch pick_fastest to return row with get_telemetry
    class FakeRow(pd.Series):
        pass

    # Instead, rely on mock_session's existing driver data; test fallback path
    # directly test with sample CSV via io fallback is covered above
    # Here ensure error for missing driver
    from f1_terminal.core.errors import DriverNotFoundError

    with pytest.raises(DriverNotFoundError):
        prepare_telemetry_trace(mock_session, "XYZ")


def test_core_features_engineer(mock_session):
    from f1_terminal.core.features import engineer_lap_features

    df = engineer_lap_features(mock_session, drivers=["VER", "HAM"])
    assert not df.empty
    assert "Driver" in df.columns
    assert "LapTime_s" in df.columns
    assert "AvgSpeed" in df.columns
