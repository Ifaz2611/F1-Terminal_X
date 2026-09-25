"""
Real-time dashboard example — polls telemetry and prints summary.

In offline/demo mode uses data/telemetry_sample.csv.
"""

import time
from pathlib import Path

import pandas as pd

from f1_terminal.io import load_session_data

SAMPLE = Path(__file__).parent.parent / "data" / "telemetry_sample.csv"


def stream_demo(iterations: int = 3, delay: float = 0.5) -> None:
    df = pd.read_csv(SAMPLE)
    print(f"Streaming {len(df)} points from sample CSV")
    for i in range(min(iterations, len(df))):
        row = df.iloc[i]
        print(f"[{i+1}/{len(df)}] Speed={row['Speed']} km/h Throttle={row['Throttle']}% Distance={row['Distance']}m")
        time.sleep(delay)
    print("Demo complete — replace with fastf1 live polling for real sessions.")


if __name__ == "__main__":
    # Try live FastF1 first
    try:
        df = load_session_data(2023, "Monza", "R", source="auto")
        print(f"Loaded {len(df)} rows — live mode would poll here")
        stream_demo()
    except Exception as e:
        print(f"Live load failed ({e}), running offline demo")
        stream_demo()
