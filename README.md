# F1 Terminal X

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-2ea44f)
![CI](https://github.com/Ifaz2611/F1-Terminal_X/actions/workflows/ci.yml/badge.svg)

F1 Terminal X is a Python toolkit for loading, analysing, and visualising
Formula 1 session data. It combines [FastF1](https://docs.fastf1.dev/) for
real session telemetry with small, deterministic local fixtures for offline
development, examples, and tests.

The project provides both reusable library functions and interactive command
line programs for race, qualifying, and practice-session analysis.

## Highlights

- Load laps from FastF1 or telemetry from CSV and Parquet files.
- Use one cache directory for FastF1 downloads, independent of the current
  working directory.
- Resolve circuits through a canonical track database, including unique
  FastF1 identifiers for tracks with ambiguous country names.
- Prepare fastest-lap or selected-lap telemetry with a guaranteed `Distance`
  column.
- Engineer lap-level features for exploratory analysis and machine learning.
- Visualise speed, throttle, braking, DRS, gear usage, and track position.
- Use interactive `questionary` prompts when available, with standard-input
  fallbacks.
- Run without network access using `data/telemetry_sample.csv`.
- Configure cache, season range, logging, and figure DPI through environment
  variables prefixed with `F1_`.

## Installation

F1 Terminal X requires Python 3.10 or newer.

```bash
git clone https://github.com/Ifaz2611/F1-Terminal_X.git
cd F1-Terminal_X

python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install -e .
```

To install the development and notebook tools as well:

```bash
pip install -e ".[dev]"
```

The repository also contains a pinned dependency-group style list in
`requirements.txt` for environments that install dependencies directly.

## Quick start: load local or FastF1 data

`load_session_data` accepts a track name, FastF1 identifier, or track number.
With `source="auto"` (the default), it tries FastF1 first and falls back to
the bundled sample CSV if the session cannot be loaded.

```python
from f1_terminal.io import load_session_data

# FastF1 first; falls back to data/telemetry_sample.csv when unavailable.
laps_or_sample = load_session_data(2023, "Monza", "Q")

# Always use the bundled offline fixture.
sample = load_session_data(
    2023,
    "Monza",
    "Q",
    source="csv",
    path="data/telemetry_sample.csv",
)

print(sample[["Speed", "Throttle", "Brake", "Distance"]].head())
```

For a real FastF1 session, use `source="fastf1"` and ensure the session exists
and can be downloaded:

```python
from f1_terminal.io import load_session_data

race_laps = load_session_data(2023, "Silverstone", "R", source="fastf1")
```

Supported session codes are `FP1`, `FP2`, `FP3`, `Q`, `R`, `S`, and `SQ`.
Errors are exposed as domain exceptions from `f1_terminal.core.errors`,
including `SessionNotHeldError`, `DriverNotFoundError`, and
`TelemetryNotAvailableError`.

## Telemetry and feature engineering

Prepare a telemetry trace from a FastF1 session. The helper selects the
fastest lap by default, or a specific lap number when requested.

```python
from f1_terminal.transform import prepare_telemetry_trace

telemetry = prepare_telemetry_trace(session, "VER", lap="fastest")
telemetry[["Distance", "Speed", "Throttle", "Brake", "nGear"]].head()
```

Build a feature table with one row per lap:

```python
from f1_terminal.features import engineer_lap_features

features = engineer_lap_features(session, drivers=["VER", "HAM"])
print(features[["Driver", "LapTime_s", "AvgSpeed", "MaxSpeed", "DRSPct"]])
```

The generated table includes lap and sector times, speed statistics, braking
events, throttle percentile, gear shifts, DRS usage, tyre compound, and
weather fields when those values are available.

## Interactive programs

After installation, the following console commands are available:

| Command | Purpose |
| --- | --- |
| `f1-advanced` | Select a 2026 race session and inspect a driver's fastest lap with speed, throttle/brake, track-map, gear, and text-summary views. |
| `f1-qualifying` | Compare all drivers' fastest qualifying laps on a selected track, sorted numerically by lap time. |
| `f1-practice` | Compare all drivers' fastest laps from FP1, FP2, or FP3. |
| `f1-telemetry` | Run the legacy general telemetry analyzer. |
| `f1-driver` | Run the driver-focused legacy utility. |
| `f1-schedule` | Browse the schedule and driver utilities. |

The visualisation programs use the shared cache at `cache/`, support FastF1
3.x cache APIs, filter invalid position data, and report unavailable sessions
without producing misleading plots.

You can also run modules directly from the repository:

```bash
python -m f1_terminal.f1_advanced_visualizer
python -m f1_terminal.f1_qualifying
python -m f1_terminal.PracticeSession
```

## Examples and offline demo

- `examples/telemetry_overview.ipynb` — inspect speed, throttle, brake, and
  gear traces.
- `examples/lap_time_analysis.ipynb` — compare lap and stint statistics.
- `examples/predict_qualifying.py` — build a qualifying-gap prediction model.
- `examples/real_time_dashboard.py` — demonstrate a streaming display using
  the local sample when live loading is unavailable.

Run the dashboard example without requiring a network session:

```bash
python examples/real_time_dashboard.py
```

The sample data in `data/telemetry_sample.csv` is synthetic and contains
`X`, `Y`, `Speed`, `Throttle`, `Brake`, `nGear`, `DRS`, and `Distance`.
FastF1's downloaded cache is intentionally kept out of version control.

## Configuration

Settings are defined centrally in `f1_terminal.config` and can be overridden
with environment variables using the `F1_` prefix:

| Setting | Default | Environment variable |
| --- | --- | --- |
| Cache directory | `<project>/cache` | `F1_CACHE_DIR` |
| Figure DPI | `150` | `F1_FIGURE_DPI` |
| Minimum season | `2018` | `F1_MIN_YEAR` |
| Maximum season | `2030` | `F1_MAX_YEAR` |
| Default season | `2026` | `F1_DEFAULT_SEASON` |
| Log level | `INFO` | `F1_LOG_LEVEL` |

For example:

```powershell
$env:F1_CACHE_DIR = "D:\fastf1-cache"
$env:F1_LOG_LEVEL = "DEBUG"
```

The package uses Rich logging when it is installed and falls back to standard
logging otherwise.

## Project layout

```text
F1-Terminal_X/
├── pyproject.toml              # Package metadata and console scripts
├── requirements.txt            # Direct-install dependency list
├── f1_terminal/
│   ├── config.py               # Settings, cache, logging, year range
│   ├── tracks.py               # Canonical Track model and track database
│   ├── io.py                   # Public re-export of core I/O helpers
│   ├── transform.py            # Public telemetry-transform re-export
│   ├── features.py             # Public feature-engineering re-export
│   ├── core/
│   │   ├── io.py               # FastF1, CSV, Parquet, and auto loading
│   │   ├── transforms.py       # Lap selection and telemetry preparation
│   │   ├── features.py         # Lap-level ML feature generation
│   │   └── errors.py           # Domain-specific exceptions
│   ├── f1_advanced_visualizer.py
│   ├── f1_qualifying.py
│   └── PracticeSession.py
├── F1_Main_py/                 # Backward-compatible legacy utilities
├── data/                       # Synthetic fixture and generated track data
├── examples/                   # Notebooks and runnable examples
├── docs/                       # Bug-fix report, reference material, demo
├── tests/                      # Import, track, cache, and visualizer tests
└── cache/                      # Local FastF1 cache (gitignored)
```

## Development

Install the development extras, then run the same checks used by CI:

```bash
pip install -e ".[dev]"
python -m py_compile F1_Main_py/f1.py F1_Main_py/driver.py f1_terminal/*.py f1_terminal/core/*.py
ruff check .
mypy f1_terminal/core --ignore-missing-imports --allow-untyped-decorators
pytest -q
```

Tests mock FastF1 where possible so the suite does not require network access
or a populated cache.

## Contributing

Bug reports and pull requests are welcome. See
[.github/Contributing.md](.github/Contributing.md) for contribution guidance,
[.github/CODE_OF_CONDUCT.md](.github/CODE_OF_CONDUCT.md) for community
standards, and the issue and pull-request templates under `.github/`.

## License

This project is licensed under the MIT License. See [License](License).
