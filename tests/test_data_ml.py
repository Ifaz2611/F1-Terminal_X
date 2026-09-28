"""Cache/datasource/ML smoke tests (offline)."""

from __future__ import annotations

import pandas as pd


def test_cache_status_clear(tmp_path, monkeypatch):
    from f1_terminal.config import settings

    monkeypatch.setattr(settings, "cache_dir", tmp_path / "cache")
    from f1_terminal.core import cache as cache_mod

    info = cache_mod.cache_status()
    assert "cache_dir" in info
    assert cache_mod.clear_cache() == 0


def test_csv_source():
    from f1_terminal.core.datasource import get_source

    src = get_source("csv")
    w = src.load_session(2023, "Monza", "Q")
    assert "VER" in w.drivers


def test_ml_train_predict():
    from f1_terminal.ml import predict, train

    # Build minimal features frame directly (avoid telemetry fetch)
    df = pd.DataFrame(
        {
            "Driver": ["VER", "HAM", "LEC", "VER", "HAM", "LEC"],
            "LapNumber": [1, 1, 1, 2, 2, 2],
            "LapTime_s": [90.0, 91.0, 92.0, 89.5, 90.5, 91.5],
            "S1_s": [30.0, 30.5, 31.0, 29.8, 30.2, 30.8],
            "S2_s": [30.0, 30.5, 31.0, 30.0, 30.3, 30.5],
            "S3_s": [30.0, 30.0, 30.0, 29.7, 30.0, 30.2],
            "AvgSpeed": [220, 218, 215, 222, 219, 216],
            "MaxSpeed": [330, 328, 325, 332, 329, 326],
            "BrakingCount": [5, 5, 6, 5, 5, 6],
            "Throttle95p": [100, 100, 99, 100, 100, 99],
            "GearShifts": [20, 20, 21, 20, 20, 21],
            "DRSPct": [30.0, 28.0, 25.0, 31.0, 29.0, 26.0],
            "Compound": ["SOFT"] * 6,
            "TrackTemp": [40.0] * 6,
            "AirTemp": [25.0] * 6,
        }
    )
    pipe = train(df)
    preds = predict(pipe, df)
    assert len(preds) == len(df)


def test_engineer_features_empty():
    from f1_terminal.core.features import engineer_lap_features

    class S:
        laps = pd.DataFrame()

    out = engineer_lap_features(S())
    assert out.empty or list(out.columns)
