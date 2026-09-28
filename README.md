# F1 Terminal X

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-2ea44f)
![Status](https://img.shields.io/badge/status-v1.5%20MVP%20complete-22c55e)
![CI](https://github.com/Ifaz2611/F1-Terminal_X/actions/workflows/ci.yml/badge.svg)

</div>

A modern Python toolkit for Formula 1 telemetry, lap analysis, and terminal-first race insights.

F1 Terminal X combines live FastF1 data, deterministic offline fixtures, and reusable analysis utilities to help you explore telemetry, compare drivers, and build race-day insights from a clean and developer-friendly interface.

## Why this project

- Built for speed and clarity in telemetry analysis
- Supports both live FastF1 sessions and offline sample data
- Keeps the project grounded in a single core engine
- Provides CLI and TUI workflows from the same toolkit
- Designed for reproducible analysis and clean local experimentation

## At a glance

| Capability | What it gives you |
| --- | --- |
| Session loading | Load data from FastF1, CSV, or Parquet sources |
| Telemetry prep | Clean traces with reliable `Distance` handling |
| Lap analysis | Compare fastest laps and engineer lap-level features |
| Visualization | Track maps, speed traces, sector bars, gear visuals |
| CLI workflow | Fast scripting with `f1` commands |
| Offline mode | Run with bundled sample telemetry when no network session is available |

## Installation

Requirements: Python 3.10+

```bash
git clone https://github.com/Ifaz2611/F1-Terminal_X.git
cd F1-Terminal_X

python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -e .
```

For development and TUI tools:

```bash
pip install -e ".[dev,tui]"
```

## Quick start

### Load telemetry

```python
from f1_terminal.io import load_session_data

# FastF1 first, fallback to bundled sample if needed
laps = load_session_data(2023, "Monza", "Q")
print(laps[["Speed", "Throttle", "Brake", "Distance"]].head())

# Explicit offline sample
sample = load_session_data(
    2023,
    "Monza",
    "Q",
    source="csv",
    path="data/telemetry_sample.csv",
)
```

### Prepare a lap trace

```python
from f1_terminal.transform import prepare_telemetry_trace

telemetry = prepare_telemetry_trace(session, "VER", lap="fastest")
print(telemetry[["Distance", "Speed", "Throttle", "Brake", "nGear"]].head())
```

### Engineer lap features

```python
from f1_terminal.features import engineer_lap_features

features = engineer_lap_features(session, drivers=["VER", "HAM"])
print(features[["Driver", "LapTime_s", "AvgSpeed", "MaxSpeed", "DRSPct"]].head())
```

Supported session codes include `FP1`, `FP2`, `FP3`, `Q`, `R`, `S`, and `SQ`.

## CLI workflows

The primary entry point is the `f1` command:

```bash
f1 --help
f1 schedule --year 2023
f1 telemetry --year 2023 --gp Monza --driver VER --plot speed --save speed.png --no-show
f1 compare --drivers VER,HAM --track Monza --year 2023 --no-show
f1 cache --status
```

Additional utilities:

```bash
f1-tui --demo --ascii
f1-tui --demo
python -m f1_terminal

f1-advanced
f1-qualifying
f1-practice
f1-telemetry
f1-driver
f1-schedule
```

## Feature set

### Telemetry and data

- FastF1 session support for live loading
- CSV and Parquet fallback loading paths
- Synthetic sample fixtures for offline runs and tests
- Canonical track metadata and circuit lookup utilities

### Analysis tools

- Lap comparison and telemetry preparation
- Feature engineering for lap-level metrics
- Track map and speed-trace visualizations
- Sector and pace summaries for race analysis

### User experience

- Terminal-first CLI workflows
- Textual TUI support for local terminal exploration
- Clean configuration with environment-based overrides
- Offline-ready sample dataset for demos and CI-safe workflows

## Offline demo and examples

The project ships with example assets and sample telemetry data for local use:

- `examples/telemetry_overview.ipynb`
- `examples/lap_time_analysis.ipynb`
- `examples/predict_qualifying.py`
- `examples/real_time_dashboard.py`

Run the dashboard without a live session:

```bash
python examples/real_time_dashboard.py
```

The bundled sample file `data/telemetry_sample.csv` includes `X`, `Y`, `Speed`, `Throttle`, `Brake`, `nGear`, `DRS`, and `Distance`.

## Configuration

Settings are centralized in `f1_terminal.config` and can be overridden through `F1_` environment variables:

| Setting | Default | Environment variable |
| --- | --- | --- |
| Cache directory | `cache/` | `F1_CACHE_DIR` |
| Figure DPI | `150` | `F1_FIGURE_DPI` |
| Min year | `2018` | `F1_MIN_YEAR` |
| Max year | `2030` | `F1_MAX_YEAR` |
| Default season | `2026` | `F1_DEFAULT_SEASON` |
| Log level | `INFO` | `F1_LOG_LEVEL` |

Example:

```powershell
$env:F1_CACHE_DIR = "D:\fastf1-cache"
$env:F1_LOG_LEVEL = "DEBUG"
```

## Project structure

```text
F1-Terminal_X/
├── README.md                    # Project overview and quick start
├── TODO.md                      # Roadmap and project status
├── CHANGELOG.md                 # Release notes
├── CONTRIBUTING.md              # Contributor workflow
├── SECURITY.md                  # Security reporting guidance
├── pyproject.toml               # Package metadata and console scripts
├── requirements.txt             # Runtime dependencies
├── f1_terminal/                # Main package
│   ├── __init__.py
│   ├── config.py               # Settings, cache, logging, year range
│   ├── tracks.py               # Canonical track database
│   ├── io.py                   # Public re-export
│   ├── transform.py            # Public transform re-export
│   ├── features.py             # Public feature-engineering re-export
│   ├── core/                   # Session, telemetry, plotting, feature logic
│   ├── cli/                   # Typer-based commands
│   ├── tui/                   # Textual TUI app
│   ├── gui/                   # Optional GUI layer
│   ├── web/                   # Optional web layer
│   ├── f1_advanced_visualizer.py
│   ├── f1_qualifying.py
│   └── PracticeSession.py
├── F1_Main_py/                 # Legacy compatibility wrappers
├── data/                       # Local sample datasets and metadata
├── examples/                   # Jupyter and runnable example scripts
├── docs/                       # Reference and project documentation
├── tests/                      # Unit and smoke tests
├── cache/                      # FastF1 cache (gitignored)
├── LICENSE                     # MIT license
├── .github/                    # Issue templates and contributor docs
└── .gitignore
```

## Development and testing

Run the checks used across the project:

```bash
pip install -e ".[dev]"
python -m py_compile F1_Main_py/f1.py F1_Main_py/driver.py f1_terminal/*.py f1_terminal/core/*.py
ruff check .
mypy f1_terminal/core --ignore-missing-imports --allow-untyped-decorators
pytest -q
```

This keeps the project lightweight while still validating performance, stability, and import health.

## Contributing

Bug reports, ideas, documentation updates, and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance.

## Security

Please report security issues responsibly. See [SECURITY.md](SECURITY.md) for the disclosure process.

## License

This project is licensed under the MIT License. See [License](License).
