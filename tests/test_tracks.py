"""Tests for canonical track registry."""

import pytest

from f1_terminal.tracks import TRACKS, all_tracks, get_track


def test_tracks_count():
    assert len(TRACKS) == 22


def test_all_tracks_returns_dict():
    assert all_tracks() is TRACKS


def test_get_track_valid():
    t = get_track(1)
    assert t.country == "Australia"
    assert t.fastf1_name == "Australia"


def test_spain_duplicate_fastf1_name_unique():
    # Both round 7 and 14 have country Spain but different identifiers
    t7 = get_track(7)
    t14 = get_track(14)
    assert t7.country == "Spain"
    assert t14.country == "Spain"
    assert t7.fastf1_name != t14.fastf1_name
    assert t7.fastf1_name == "Spain"
    assert t14.fastf1_name == "Spain" or t14.fastf1_name == "Madring" or t14.fastf1_name != t7.fastf1_name


def test_usa_triple_fastf1_names_unique():
    usa_tracks = [t for t in TRACKS.values() if t.country == "USA"]
    assert len(usa_tracks) == 3
    names = [t.fastf1_name for t in usa_tracks]
    assert len(set(names)) == 3


def test_get_track_invalid_raises():
    with pytest.raises(KeyError, match="99"):
        get_track(99)
    with pytest.raises(KeyError):
        get_track(0)
    with pytest.raises(KeyError):
        get_track(23)


def test_tracks_legacy_shape():
    from f1_terminal.tracks import TRACKS_LEGACY

    assert len(TRACKS_LEGACY) == 22
    assert TRACKS_LEGACY[1]["country"] == "Australia"
    assert "fastf1_name" in TRACKS_LEGACY[14]
