"""Shared fixtures for tests (mocked fastf1, no network)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest


@pytest.fixture
def mock_session() -> MagicMock:
    """Return a mocked FastF1 session with laps and get_driver."""
    # Build minimal laps DataFrame with required columns
    laps_data = {
        "Driver": ["VER", "HAM", "LEC", "VER", "HAM"],
        "LapNumber": [1, 1, 1, 2, 2],
        "LapTime": pd.to_timedelta(["90.123s", "91.456s", "92s", "89.5s", "90.8s"]),
        "Sector1Time": pd.to_timedelta(["30s", "30.5s", "31s", "29.5s", "30s"]),
        "Sector2Time": pd.to_timedelta(["30s", "30.5s", "31s", "30s", "30.2s"]),
        "Sector3Time": pd.to_timedelta(["30.1s", "30.4s", "30s", "30s", "30.6s"]),
        "Compound": ["SOFT", "MEDIUM", "SOFT", "SOFT", "MEDIUM"],
        "PitInTime": [pd.NaT] * 5,
        "PitOutTime": [pd.NaT] * 5,
        "TrackStatus": ["1"] * 5,
    }
    laps = pd.DataFrame(laps_data)

    # Add fastf1-like helpers to DataFrame
    def _pick_drivers(code):
        if isinstance(code, list):
            return laps[laps["Driver"].isin(code)]
        return laps[laps["Driver"] == code]

    def _pick_driver(code):
        return laps[laps["Driver"] == code]

    def _pick_fastest_for_driver(code: str):
        dl = laps[laps["Driver"] == code]
        if dl.empty:
            return None
        # Return Series with get_telemetry
        fastest = dl.loc[dl["LapTime"].idxmin()]

        # Attach get_telemetry method via custom Series subclass trick: monkey-patch
        fastest = fastest.copy()

        def get_telemetry():
            # Return telemetry DataFrame with required columns

            n = 20
            tel = pd.DataFrame(
                {
                    "X": range(n),
                    "Y": range(n),
                    "Speed": [200 + i for i in range(n)],
                    "Throttle": [100] * n,
                    "Brake": [0] * n,
                    "nGear": [4] * n,
                    "DRS": [0] * n,
                    "Distance": [i * 10 for i in range(n)],
                }
            )
            # Add add_distance for compatibility
            def add_distance():
                return tel

            tel.add_distance = add_distance  # type: ignore[attr-defined]
            return tel

        fastest.get_telemetry = get_telemetry  # type: ignore[attr-defined]
        return fastest

    # Make laps support pick_* methods
    laps.pick_drivers = _pick_drivers  # type: ignore[attr-defined]
    laps.pick_driver = _pick_driver  # type: ignore[attr-defined]

    # Mock session
    session = MagicMock()
    session.laps = laps
    session.drivers = ["VER", "HAM", "LEC"]

    def _get_driver(code: str):
        colors = {"VER": "0600EF", "HAM": "00D2BE", "LEC": "DC0000"}
        return {"TeamColor": colors.get(code, "FFFFFF"), "TeamName": f"Team {code}", "BroadcastName": code}

    session.get_driver.side_effect = _get_driver

    # Also mock pick_fastest on driver slices via DataFrame monkey? We'll handle in telemetry tests directly
    # Provide helper for tests
    session._pick_fastest_for_driver = _pick_fastest_for_driver  # type: ignore[attr-defined]

    return session


@pytest.fixture
def sample_telemetry() -> pd.DataFrame:
    """Sample telemetry DataFrame (matches data/telemetry_sample.csv)."""
    import pandas as pd

    return pd.read_csv("data/telemetry_sample.csv")
