"""Telemetry + colors tests (mocked, Agg not needed)."""

from __future__ import annotations

import pandas as pd
import pytest

from f1_terminal.core.errors import DriverNotFoundError


def test_get_fastest_lap_mock(mock_session):
    from f1_terminal.core.telemetry import get_fastest_lap

    # mock_session fixture has laps but rows lack get_telemetry; fastest resolution uses LapTime
    fastest = get_fastest_lap(mock_session, "VER")
    assert fastest["Driver"] == "VER"


def test_get_fastest_lap_missing_driver(mock_session):
    from f1_terminal.core.telemetry import get_fastest_lap

    with pytest.raises(DriverNotFoundError):
        get_fastest_lap(mock_session, "XXX")


def test_get_telemetry_adds_distance():
    from f1_terminal.core.telemetry import get_telemetry

    lap = pd.Series({"LapTime": pd.to_timedelta("90s")})

    tel = pd.DataFrame({"X": [0, 3, 6], "Y": [0, 4, 8], "Speed": [200, 210, 220]})

    def _get():
        return tel

    lap.get_telemetry = _get  # type: ignore[attr-defined]
    out = get_telemetry(lap)
    assert "Distance" in out.columns
    assert len(out) == 3


def test_get_team_color_hex(mock_session):
    from f1_terminal.core.colors import get_team_color

    c = get_team_color(mock_session, "VER")
    assert isinstance(c, str) and c.startswith("#")
    c2 = get_team_color(mock_session, "UNKNOWN-DRIVER")
    assert c2.startswith("#")
