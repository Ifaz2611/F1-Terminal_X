"""Session engine tests (mocked fastf1, no network)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from f1_terminal.core.errors import F1DataError, SessionNotHeldError


def _fake_session():
    sess = MagicMock()
    laps = pd.DataFrame(
        {
            "Driver": ["VER", "HAM"],
            "LapNumber": [1, 1],
            "LapTime": pd.to_timedelta(["90s", "91s"]),
            "PitInTime": [pd.NaT, pd.NaT],
            "PitOutTime": [pd.NaT, pd.NaT],
        }
    )
    sess.laps = laps
    sess.drivers = ["VER", "HAM"]
    sess.event = {"EventName": "Test GP"}
    return sess


def test_load_session_ok():
    from f1_terminal.core.session import load_session

    with patch("fastf1.get_session", return_value=_fake_session()) as gs:
        fake = _fake_session()
        # get_session returns object with .load
        sess_obj = MagicMock()
        sess_obj.laps = fake.laps
        sess_obj.drivers = ["VER", "HAM"]
        sess_obj.event = {"EventName": "Test GP"}
        gs.return_value = sess_obj
        w = load_session(2023, "Monza", "Q")
        assert w.drivers == ["VER", "HAM"]
        assert len(w.laps) == 2


def test_load_session_not_held():
    from f1_terminal.core.session import load_session

    class DataNotLoadedError(Exception):
        pass

    with patch("fastf1.get_session", side_effect=DataNotLoadedError("no data")):
        # patch type name check via message fallback
        with patch("fastf1.get_session", side_effect=Exception("Session has not yet occurred")):
            with pytest.raises((SessionNotHeldError, F1DataError)):
                load_session(2026, "Abu Dhabi", "R", retries=1, backoff=0)


def test_get_schedule_mocked():
    from f1_terminal.core.session import get_schedule

    get_schedule.cache_clear()
    df = pd.DataFrame({"RoundNumber": [1], "EventName": ["Bahrain GP"], "EventDate": pd.to_datetime(["2023-03-05"])})
    with patch("fastf1.get_event_schedule", return_value=df):
        out = get_schedule(2023)
        assert not out.empty
    get_schedule.cache_clear()
