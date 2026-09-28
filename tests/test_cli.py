"""CLI tests via typer CliRunner (mocked sessions, no network)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
from typer.testing import CliRunner

from f1_terminal.cli.main import app

runner = CliRunner()


def test_f1_help():
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    assert "advanced" in r.output or "Usage" in r.output


def test_f1_version():
    r = runner.invoke(app, ["--version"])
    assert r.exit_code == 0


def _mock_wrapper():
    sess = MagicMock()
    sess.drivers = ["VER", "HAM"]
    laps = pd.DataFrame(
        {
            "Driver": ["VER", "HAM"],
            "LapNumber": [1, 1],
            "LapTime": pd.to_timedelta(["90s", "91s"]),
            "Sector1Time": pd.to_timedelta(["30s", "30.5s"]),
            "Sector2Time": pd.to_timedelta(["30s", "30.5s"]),
            "Sector3Time": pd.to_timedelta(["30s", "30.5s"]),
            "Compound": ["SOFT", "MEDIUM"],
            "PitInTime": [pd.NaT, pd.NaT],
            "PitOutTime": [pd.NaT, pd.NaT],
        }
    )
    w = MagicMock()
    w.drivers = ["VER", "HAM"]
    w.laps = laps
    w.session = sess
    w.track = "Monza"
    return w


def test_schedule_mocked():
    with patch("f1_terminal.core.session.get_schedule") as gs:
        gs.return_value = pd.DataFrame(
            {"RoundNumber": [1], "Country": ["Bahrain"], "Location": ["Sakhir"], "EventName": ["Bahrain GP"]}
        )
        r = runner.invoke(app, ["schedule", "--year", "2023"])
        assert r.exit_code == 0
        assert "Bahrain" in r.output


def test_cache_status():
    r = runner.invoke(app, ["cache", "--status"])
    assert r.exit_code == 0
    assert "cache_dir" in r.output


def test_config_list():
    r = runner.invoke(app, ["config", "--list"])
    assert r.exit_code == 0
    assert "cache_dir" in r.output


def test_compare_mocked():
    from f1_terminal.core import telemetry as tel_mod

    w = _mock_wrapper()
    tel = pd.DataFrame({"X": [0, 1], "Y": [0, 1], "Speed": [200, 210], "Distance": [0, 10], "DRS": [0, 0], "nGear": [3, 4]})
    fastest = pd.Series({"LapTime": pd.to_timedelta("90s")})
    with patch("f1_terminal.core.session.load_session", return_value=w):
        with patch.object(tel_mod, "get_driver_telemetry", return_value=(fastest, tel)):
            r = runner.invoke(app, ["compare", "--year", "2023", "--track", "Monza", "--drivers", "VER,HAM", "--no-show"])
            assert r.exit_code == 0
