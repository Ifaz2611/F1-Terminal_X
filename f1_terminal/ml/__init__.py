"""ML pipeline — qualifying gap prediction (P4-4)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from f1_terminal.config import get_logger

logger = get_logger(__name__)

FEATURES = ["S1_s", "S2_s", "S3_s", "AvgSpeed", "MaxSpeed", "DRSPct", "Throttle95p"]
TARGET = "QualiGap_s"


def prepare_training_frame(features_df: pd.DataFrame) -> pd.DataFrame:
    """Add QualiGap_s target (gap to fastest LapTime_s) and drop NaNs."""
    df = features_df.copy()
    if "LapTime_s" not in df.columns:
        raise ValueError("features need LapTime_s")
    best = float(df["LapTime_s"].min())
    df[TARGET] = df["LapTime_s"] - best
    keep = [c for c in FEATURES + [TARGET] if c in df.columns]
    df = df.dropna(subset=keep)
    return df


def train(df: pd.DataFrame):
    """Train GradientBoostingRegressor pipeline; returns sklearn Pipeline."""
    try:
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.impute import SimpleImputer
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as e:
        raise ImportError("scikit-learn required for ML") from e
    frame = prepare_training_frame(df)
    feats = [c for c in FEATURES if c in frame.columns]
    if not feats or frame.empty:
        raise ValueError("Not enough data to train")
    X, y = frame[feats], frame[TARGET]
    pipe: Any = Pipeline(
        [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", GradientBoostingRegressor(random_state=42))]
    )
    pipe.fit(X, y)
    pipe.feature_names_ = feats  # type: ignore[attr-defined]
    logger.info("Trained qualifying model on %s rows", len(frame))
    return pipe


def save_model(pipe: Any, path: str | Path) -> Path:
    import pickle

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "wb") as f:
        pickle.dump(pipe, f)
    return out


def load_model(path: str | Path) -> Any:
    import pickle

    with open(path, "rb") as f:
        return pickle.load(f)


def predict(pipe: Any, features_df: pd.DataFrame) -> pd.Series:
    feats = getattr(pipe, "feature_names_", FEATURES)
    feats = [c for c in feats if c in features_df.columns]
    return pd.Series(pipe.predict(features_df[feats]), index=features_df.index)
