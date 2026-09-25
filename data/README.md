# Data

- `telemetry_sample.csv` — 30-point curated lap for offline/demo + tests.
  Columns: `X, Y, Speed, Throttle, Brake, nGear, DRS, Distance`.
  Used by `f1_terminal.core.io.load_session_data(source="csv")` fallback and
  `tests/` mocks (no network required).

- `tracks_2026.json` — generated from `f1_terminal/tracks.py` (run
  `python -c "import json; from f1_terminal.tracks import TRACKS; print(json.dumps({k: v.__dict__ for k,v in TRACKS.items()}, indent=2))" > data/tracks_2026.json`).

Both files are safe to commit (small, synthetic). Real FastF1 cache stays in `cache/` (gitignored).
