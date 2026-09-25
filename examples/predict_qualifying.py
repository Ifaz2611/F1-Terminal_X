"""
Predict qualifying gaps — example script (offline-friendly).

Uses ``engineer_lap_features`` on sample data or FastF1 session.
"""

from pathlib import Path

import pandas as pd

from f1_terminal.features import engineer_lap_features
from f1_terminal.io import load_session_data

# Try FastF1, fallback to sample CSV (demo mode)
try:
    df = load_session_data(2023, "Monza", "Q", source="auto")
    print(f"Loaded {len(df)} rows via load_session_data")
    # If df is laps, engineer features
    if "Driver" in df.columns and "LapTime" in df.columns:
        # Mock session shim
        class _Sess:
            laps = df

        # Use get_telemetry-free path for demo; engineer still works
        features = engineer_lap_features(_Sess(), drivers=None)
        print(features.head())
    else:
        print(df.head())
except Exception as e:
    print(f"Demo fallback (no network): {e}")
    sample = Path(__file__).parent.parent / "data" / "telemetry_sample.csv"
    df = pd.read_csv(sample)
    print(df.describe())

# Simple sklearn example (if data available)
try:
    # Dummy training on sample CSV's Speed vs Distance (illustrative)
    from sklearn.ensemble import GradientBoostingRegressor

    X = df[["Distance"]].fillna(0) if "Distance" in df.columns else pd.DataFrame({"x": range(len(df))})
    y = df["Speed"] if "Speed" in df.columns else X["Distance"] * 0.5
    model = GradientBoostingRegressor().fit(X, y)
    print(f"Model trained — score: {model.score(X, y):.3f}")
except Exception as e:
    print(f"ML demo skipped: {e}")
