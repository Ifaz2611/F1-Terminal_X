# F1 Terminal X — Master Build Roadmap

> **Vision:** A focused open-source F1 terminal toolkit — from `pip install` to pit-wall insights in <30s. CLI for scripting and TUI for terminal users first; desktop, web, and ML work remain optional follow-on products built on the same core.
>
> **Status:** Bug-fix pass completed 2026-09-25 (`docs/BUGFIX_REPORT.md:1`). This roadmap now separates the committed v1.5 MVP from post-MVP experiments so the project can ship before the larger platform scope is approved.
>
> **How to use:** Check off boxes per PR. Each Phase is merge-gated by its **Exit Criteria**. Execute **Phase 0 → Phase 1 → Phase 2**, then stop for a usage review. Do not start a post-MVP phase without an explicit scope decision.

---

## Table of Contents
- [Stack Decision Matrix](#stack-decision-matrix)
- [Target Architecture & File Tree](#target-architecture--file-tree)
- [Phase 0 — Hygiene & Foundation Debt](#phase-0--hygiene--foundation-debt-12-weeks)
- [Phase 1 — Core Engine Refactor](#phase-1--core-engine-refactor-23-weeks)
- [Phase 2 — TUI (Textual)](#phase-2--tui-textual--rich--plotext--35-weeks)
- [MVP Release Gate — v1.5](#mvp-release-gate--v15)
- [Post-MVP Options](#post-mvp-options)
- [Phase 3 — GUI (Desktop, deferred)](#phase-3--gui-desktop-deferred)
- [Phase 3b — Web Alternative (Streamlit/Dash, deferred)](#phase-3b--web-alternative-streamlitdash-deferred)
- [Phase 4 — Data & Intelligence (deferred)](#phase-4--data--intelligence-deferred)
- [Phase 5 — Quality, CI/CD, Distribution (deferred)](#phase-5--quality-cicd-distribution-deferred)
- [Phase 6 — Polish & Release v2.0 (deferred)](#phase-6--polish--release-v20-deferred)
- [Timeline & Effort Summary](#timeline--effort-summary)
- [Testing Strategy Matrix](#testing-strategy-matrix)
- [Nice-to-Have Backlog & Stretch Goals](#nice-to-have-backlog--stretch-goals)
- [Appendix](#appendix)

---

## Stack Decision Matrix

| Layer | Option A (Recommended) | Option B | Option C | Choice Rationale |
|-------|------------------------|----------|----------|------------------|
| **Language** | Python 3.10+ | - | - | FastF1 requires it |
| **CLI** | `typer` + `rich` | `argparse` + `questionary` | `click` | Typer gives auto `--help`, shell completion, type hints; keep questionary for interactive fallback |
| **TUI** | `textual>=0.60` + `rich` + `plotext` (ASCII fallback) | `blessed` + `urwid` | `prompt_toolkit` | Textual has async workers, DataTable, Tabs, Image widget via Sixel/Kitty |
| **GUI** | `PyQt6` + `matplotlib` `FigureCanvasQTAgg` | `customtkinter` + `FigureCanvasTkAgg` | `DearPyGui` | PyQt6 is heavier but gives QThread, QGraphicsView, native menus; customtkinter ships faster — pick one, document in `docs/adr/001-gui-stack.md` |
| **Web (optional)** | `Streamlit` (fastest) | `Dash` + `plotly` | `FastAPI` + `React` | Streamlit reuses `core/plotting.py` with `plotly` renderer |
| **Plotting** | `matplotlib` (core) + `plotly` (web export) + `seaborn` style | `pyqtgraph` | - | Matplotlib is FastF1 native; plotly for hover/zoom |
| **Data** | `fastf1` (primary) + `openf1` API (future) via `DataSource` interface | - | - | Abstract source so 2026 season gaps can be filled |
| **Config** | `pydantic` + `pydantic-settings` + `pyproject.toml` | `dataclass` | `hydra` | Validation for `Track`, `SessionParams` |
| **Packaging** | `pyproject.toml` (`setuptools`) + `pipx` + `pyinstaller` | `poetry` | `hatch` | Already migrated to pyproject |
| **CI** | `GitHub Actions` + `ruff` + `pytest` + `mypy` | - | - | Free, fast |

> **Decision to record:** Create `docs/adr/002-tui-stack.md` before Phase 2. Do not choose a desktop stack until the MVP usage review. `docs/adr/001-gui-stack.md` is intentionally deferred.

## Scope guardrails

The committed target is **v1.5 MVP = Phase 0 + Phase 1 + Phase 2**. It delivers a
tested shared core, a scriptable CLI, and a usable Textual TUI. It does not
commit the project to a desktop GUI, web deployment, ML pipeline, or multi-platform
distribution.

- Keep one primary front end in active development at a time.
- Prefer a small complete feature over a new platform.
- Treat live network calls, image protocols, and GUI behavior as optional/manual
  unless they are required by an MVP exit criterion.
- Re-evaluate the next phase using actual usage, contributor capacity, and
  maintenance cost after v1.5 ships.

---

## Target Architecture & File Tree

### Current (post-fix) — `f1_terminal/tracks.py:1`, `F1_Main_py/tracks.py:1`, `F1_Main_py/schedule_driver.py:1`, `pyproject.toml:1`

### Target architecture after the MVP

```
F1-Terminal_X/
├── pyproject.toml                    # single source of truth, [project.scripts] f1-*, f1-tui, f1-gui
├── requirements.txt / requirements-dev.txt
├── .github/workflows/ci.yml
├── docs/
│   ├── adr/                          # Architecture Decision Records
│   ├── BUGFIX_REPORT.md
│   └── demo.gif / demo_tui.gif / demo_gui.png
├── cache/                            # unified FastF1 cache (gitignored)
├── data/
│   ├── telemetry_sample.csv          # curated lap for offline/demo + tests
│   └── tracks_2026.json              # generated from f1_terminal/tracks.py
├── examples/
│   ├── telemetry_overview.ipynb
│   ├── lap_time_analysis.ipynb
│   ├── predict_qualifying.py
│   └── real_time_dashboard.py
├── f1_terminal/                      # MAIN PACKAGE (all new code here; F1_Main_py becomes legacy shim)
│   ├── __init__.py
│   ├── config.py                     # pydantic settings, YEAR_RANGE, CACHE_DIR, FIGURE_DPI
│   ├── tracks.py                     # canonical DB (done)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── session.py                # load_session(), get_schedule(), SessionWrapper
│   │   ├── telemetry.py              # get_fastest_lap(), get_telemetry(), add_distance()
│   │   ├── colors.py                 # get_team_color() -> hex
│   │   ├── plotting.py               # pure funcs: plot_track_map(ax,*), plot_speed(ax,*), plot_sectors(ax,*), plot_pace(ax,*)
│   │   ├── transforms.py             # prepare_telemetry_trace(), engineer_lap_features()
│   │   ├── io.py                     # load_session_data() for CSV/Parquet + FastF1
│   │   └── errors.py                 # F1DataError, SessionNotHeldError, CacheError
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py                   # typer app: f1 --year --track --session --driver --analysis --save --interactive
│   │   └── interactive.py            # questionary fallback wrappers
│   ├── tui/
│   │   ├── __init__.py
│   │   ├── app.py                    # F1TerminalApp (Textual App)
│   │   ├── screens/
│   │   │   ├── track_select.py
│   │   │   ├── session_select.py
│   │   │   ├── driver_select.py
│   │   │   └── analysis.py
│   │   ├── widgets/
│   │   │   ├── track_map.py
│   │   │   ├── speed_trace.py
│   │   │   ├── sector_bars.py
│   │   │   └── telemetry_table.py
│   │   ├── workers/
│   │   │   └── session_loader.py     # async fastf1 loader with Progress
│   │   └── theme.tcss                # Textual CSS
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── app.py                    # QApplication / Tk root
│   │   ├── main_window.py            # left controls + center canvas + right table
│   │   ├── canvas.py                 # FigureCanvas wrapper
│   │   ├── workers.py                # QThread / threading for session load
│   │   └── dialogs.py                # save/export, settings
│   └── web/                          # optional Streamlit/Dash
│       └── app.py
├── F1_Main_py/                       # LEGACY — becomes shim re-exporting f1_terminal.core
│   ├── __init__.py
│   ├── tracks.py                     # re-exports f1_terminal.tracks
│   ├── f1.py                         # wrapper -> f1_terminal.core
│   ├── driver.py
│   └── schedule_driver.py
├── tests/
│   ├── test_tracks.py
│   ├── test_session.py
│   ├── test_telemetry.py
│   ├── test_plotting.py
│   ├── test_cli.py
│   └── test_tui_smoke.py
└── TODO.md  (this file)
```

**Rule:** All new logic goes in `f1_terminal/core/`, `cli/`, `tui/`, `gui/`. `F1_Main_py/` stays for backward compat only.

---

## Phase 0 — Hygiene & Foundation Debt (1-2 weeks) — **GATE for all else**

**Goal:** No drift, no broken imports, CI green.

- [ ] **P0-1 README ↔ Code drift** — `README.md:61` references `f1_terminal.io:1` (`load_session_data`), `f1_terminal.transform:111` (`prepare_telemetry_trace`), `f1_terminal.features:121` (`engineer_lap_features`) which don't exist.
  - [ ] Create stubs: `f1_terminal/core/io.py` (`load_session_data(year,track,session)` handles CSV or FastF1), `transforms.py` (`prepare_telemetry_trace(session, driver, lap)`), `features.py` (`engineer_lap_features(session, drivers)` returns DataFrame with `CornerSpeed`, `BrakingPoint`, etc.)
  - [ ] Or rewrite README examples to use existing `fastf1.get_session` directly — pick one, don't leave broken imports.
  - [ ] Add `data/telemetry_sample.csv` (1 lap, columns `X,Y,Speed,Throttle,Brake,nGear,DRS,Distance`) + `data/README.md`.
  - [ ] Populate `examples/` (4 files from `README.md:79` table) or remove table; ensure `docs/demo.gif` exists or remove badge.
  - [ ] Fix `Project Structure` block `README.md:132` — it still shows `formula1_test/`, `Aspects/` (should be `f1_terminal/`, `F1_Main_py/`, `docs/`).

- [ ] **P0-2 Tests bootstrap** — `tests/` + `pytest` + fixtures with mocked `fastf1` (no network in CI)
  - [ ] `tests/test_tracks.py`: 22 entries, `get_track(1).fastf1_name != get_track(14).fastf1_name` despite both `country=="Spain"`, `get_track(99)` raises.
  - [ ] `tests/test_cache_setup.py`: import `f1_terminal.f1_advanced_visualizer` does not create nested `f1_cache/` outside `cache/`.
  - [ ] `tests/test_visualizer_smoke.py`: mock `session.laps` DataFrame, call `TrackVisualizer(...).plot_*` with `matplotlib.use('Agg')` and assert `Figure` returned (no `plt.show()`).
  - [ ] `tests/conftest.py`: `mock_session` fixture.

- [ ] **P0-3 CI** — `.github/workflows/ci.yml`
  ```yaml
  on: [push, pull_request]
  jobs:
    ci:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with: {python-version: '3.11'}
        - run: pip install -r requirements.txt && pip install pytest ruff mypy
        - run: python -m py_compile F1_Main_py/f1.py F1_Main_py/driver.py f1_terminal/*.py
        - run: ruff check .
        - run: mypy f1_terminal/core --ignore-missing-imports
        - run: pytest -q
  ```

- [ ] **P0-4 Logging** — replace `print()` with `logging`
  - [ ] `f1_terminal/config.py:1` → `LOG_LEVEL`, `LOG_FORMAT`; use `rich.logging.RichHandler` when `rich` installed.
  - [ ] Add `--verbose` / `-v` flag to all CLIs; `logger.info("Loading %s %s ...", year, track)` instead of `print`.

- [ ] **P0-5 Config centralization** — `f1_terminal/config.py`
  ```python
  from pydantic_settings import BaseSettings
  from pathlib import Path
  class Settings(BaseSettings):
      cache_dir: Path = Path("cache").resolve()
      figure_dpi: int = 150
      min_year: int = 2018
      max_year: int = 2030
      default_season: int = 2026
  settings = Settings()
  ```
  Replace hardcoded `2018,2030,2026,150` across `F1_Main_py/f1.py:43`, `driver.py`, `f1_advanced_visualizer.py:31`.

- [ ] **P0-6 Git hygiene**
  - [ ] `git rm -r --cached F1_Main_py/__pycache__ f1_terminal/__pycache__` ; ensure `.gitignore:11` covers `__pycache__/`, `.pytest_cache/`, `*.egg-info/`, `dist/`.
  - [ ] Rename `Aspects/` → `docs/reference/` (or keep but add `docs/reference/README.md` explaining it); update `Aspects/fastf1_reference.md:1` links.
  - [ ] Remove `Schedule&Driver.py` shim in v2.0 — add `TODO` comment with removal version.

- [ ] **P0-7 Type hints & docstrings** — `ruff` + `mypy` pass on `f1_terminal/core/`.

**Exit Criteria:** `pytest` green, `ruff` clean, `README` examples run without ImportError, `cache/` is single dir, CI badge green.

---

## Phase 1 — Core Engine Refactor (2-3 weeks) — **GATE for MVP**

**Goal:** Decouple **data/plot** from **I/O** so the CLI and TUI share one engine. Pure functions return `Figure`/`DataFrame`, never call `input()` or `plt.show()`.

### 1.1 Create `f1_terminal/core/`

- [ ] **P1-1 `core/errors.py`**
  ```python
  class F1DataError(Exception): ...
  class SessionNotHeldError(F1DataError): ...
  class DriverNotFoundError(F1DataError): ...
  class TelemetryNotAvailableError(F1DataError): ...
  ```
  Uniform error UX, exit codes `0=ok, 1=data error, 2=usage error`.

- [ ] **P1-2 `core/session.py`**
  - [ ] `get_schedule(year: int) -> DataFrame` (cached, handles 2026 incomplete schedule)
  - [ ] `load_session(year, track: str|Track, session_code: str, *, telemetry=True) -> SessionWrapper` with retry (3x, backoff), `DataNotLoadedError` → `SessionNotHeldError` with friendly msg.
  - [ ] `SessionWrapper` dataclass: `session`, `laps`, `drivers`, `year`, `track`, `session_code`; method `get_driver_laps(code)` (handles `pick_drivers`/`pick_driver` fallback — extract from `F1_Main_py/driver.py:148`).
  - [ ] Offline fallback: if `cache/` has data, load from cache even without network.

- [ ] **P1-3 `core/telemetry.py`**
  - [ ] `get_fastest_lap(session, driver_code) -> Series` + `get_telemetry(fastest_lap) -> DataFrame` (wraps `fastest_lap.get_telemetry()` + `add_distance()`).
  - [ ] `get_driver_telemetry(session, driver_code) -> tuple[Series, DataFrame]` (combines above, raises `TelemetryNotAvailableError`).
  - [ ] Unit tests with mocked laps.

- [ ] **P1-4 `core/colors.py`**
  - [ ] `get_team_color(session, driver_code, fallback_cmap, idx, total) -> str` (hex) — consolidate from `f1_advanced_visualizer.py:101` and `f1_qualifying.py:108`.

- [ ] **P1-5 `core/plotting.py`** — **pure functions**, `ax` injected, return `Figure`
  - [ ] `plot_track_map(ax, telemetry, color, cmap='viridis') -> None` (LineCollection + colorbar)
  - [ ] `plot_speed_trace(ax, telemetry, color, show_drs=True, show_gear_shifts=True)`
  - [ ] `plot_throttle_brake(ax, telemetry)`
  - [ ] `plot_gear_map(ax, telemetry)`
  - [ ] `plot_sector_bars(ax, sector_df)` (from `f1_advanced_visualizer.py:337`)
  - [ ] `plot_race_pace(ax, laps, drivers, colors)`
  - [ ] `plot_tire_strategy(ax, laps, drivers)` (from `F1_Main_py/driver.py:114`)
  - [ ] All functions handle `NaN`, empty DataFrames gracefully (return early, log warning).

- [ ] **P1-6 `core/io.py` + `core/transforms.py`**
  - [ ] `io.load_session_data(year, track, session, source='fastf1'|'csv'|'parquet', path=None) -> DataFrame` (satisfies `README.md:61`).
  - [ ] `transforms.prepare_telemetry_trace(session, driver, lap) -> DataFrame` (satisfies `README.md:111` plotly example).
  - [ ] `transforms.engineer_lap_features(session, drivers) -> DataFrame` (corner speeds, braking points — stub + TODO for ML).

- [ ] **P1-7 `core/__init__.py` re-exports** for `from f1_terminal.core import load_session, get_telemetry, TRACKS`.

### 1.2 Refactor Scripts to Use Core

- [ ] **P1-8 Refactor each entry point** to thin CLI wrappers:
  ```python
  # f1_terminal/f1_advanced_visualizer.py
  def main(argv=None):
      args = parse_args(argv)  # typer or argparse
      session = load_session(args.year, args.track, args.session)
      viz = TrackVisualizer(session, args.year, args.track)  # now in core
      fig = viz.plot_fastest_laps_track()  # returns Figure
      if args.save: fig.savefig(args.save, dpi=FIGURE_DPI)
      if not args.no_show: plt.show()
  ```
  Apply to: `f1_advanced_visualizer.py`, `f1_qualifying.py`, `PracticeSession.py`, `F1_Main_py/f1.py`, `driver.py`, `schedule_driver.py`.
  **Critical:** Remove `input()` loops from core; keep them only in `cli/interactive.py`.

### 1.3 CLI (Typer)

- [ ] **P1-9 `f1_terminal/cli/main.py`** — `typer` app
  ```bash
  f1 --help
  f1 advanced --year 2024 --track Austria --session R --analysis all --save out.png --no-show
  f1 qualifying --year 2024 --track Monza --save quali.png
  f1 practice --year 2024 --track Silverstone --session FP1
  f1 telemetry --year 2026 --gp "Abu Dhabi" --driver VER --plot speed --save speed.png
  f1 schedule --year 2026
  f1 driver --year 2026 --round 1
  f1 --interactive   # launches questionary flow (old behavior)
  ```
  - [ ] Shell completion: `f1 --install-completion`.
  - [ ] Keep `questionary` for `f1 --interactive` fallback; `typer` for scripting.

- [ ] **P1-10 `python -m f1_terminal`** entry (`f1_terminal/__main__.py`).

**Exit Criteria:** `f1 advanced --help` works, `pytest tests/test_plotting.py` passes with `Agg` backend, no script calls `input()` when imported, `F1_Main_py/` files are 30-line shims.

---

## Phase 2 — TUI (Textual + Rich + Plotext) (3-5 weeks) — **MVP FINAL PHASE**

**Why first:** No windowing deps, reuses terminal, fast iteration, your users are already in terminal.

### 2.1 Stack & Scaffolding

- [ ] **P2-1 Dependencies** — `pyproject.toml:30` `[project.optional-dependencies] tui = ["textual>=0.60.0", "rich>=13.0.0", "plotext>=5.2.0", "pillow>=10.0.0"]`
- [ ] **P2-2 Scaffolding** — `f1_terminal/tui/app.py`
  ```python
  class F1TerminalApp(App):
      CSS_PATH = "theme.tcss"
      BINDINGS = [("q","quit","Quit"), ("s","save","Save"), ("r","reload","Reload"), ("?","help","Help"), ("/","search","Search")]
  ```
  Layout:
  ```
  ┌─ Header: Season [2026 ▼]  Cache: ●  Network: ● ─┐
  │ Sidebar (22 tracks) │ Main Tabs                  │
  │ [search /]         │ [Track Map][Speed][Sectors]│
  │  01 Australia      │ [Race Pace][Summary]        │
  │  02 China          │                              │
  │  ...               │  (Figure / Table)            │
  └─ Footer: status • log • keybindings ──────────────┘
  ```

### 2.2 Screens (replace menu functions)

- [ ] **P2-3 `tui/screens/track_select.py`** — replaces `display_track_menu()` (`f1_qualifying.py:35`)
  - [ ] `DataTable` 22 rows, columns `Rnd | Country | City | Circuit`; sortable, filterable via `/` search.
  - [ ] Preview pane: track thumbnail (generated from `core/plotting.plot_track_map` → PNG thumbnail).
  - [ ] Future sessions greyed ( `EventDate > today()` ), with tooltip “Not yet held”.

- [ ] **P2-4 `tui/screens/session_select.py`**
  - [ ] Radio: `FP1 | FP2 | FP3 | Q | R | Sprint | Sprint Qualifying`; disables unavailable sessions (check `session.load()` quickly or from schedule metadata).

- [ ] **P2-5 `tui/screens/driver_select.py`** — replaces driver `input()` (`F1_Main_py/driver.py:148`)
  - [ ] Multi-select `DataTable` with team color chips, fastest lap, lap time; `Space` toggles, `a` select all, `Enter` confirms.
  - [ ] Chips bar showing selected drivers.

- [ ] **P2-6 `tui/screens/analysis.py`** — replaces `display_analysis_menu()` (`f1_advanced_visualizer.py:465`)
  - [ ] `TabbedContent` 5 tabs: `Track Map`, `Speed Trace`, `Throttle/Brake`, `Sectors`, `Race Pace` + `All`.
  - [ ] Each tab hosts a widget that renders a matplotlib Figure.

### 2.3 Widgets (Figure Rendering)

- [ ] **P2-7 Figure → TUI rendering**
  - [ ] Baseline: render an ASCII speed trace and summary with `plotext`; support
    `--ascii` explicitly and make it work in ordinary terminals and CI.
  - [ ] Save: `s` saves the current matplotlib figure to
    `~/Downloads/f1_<track>_<session>_<driver>.png`.
  - [ ] Reuse `core/plotting.py` — widgets call `plot_* (ax)` and display the
    result; do not duplicate telemetry or plotting logic.
  - [ ] **Stretch only:** detect Sixel/Kitty support and render a raster image.
    This must never block the fallback or be required for the MVP exit gate.

- [ ] **P2-8 `tui/widgets/`**
  - [ ] `track_map.py` : `LineCollection` + speed colormap
  - [ ] `speed_trace.py` : distance vs speed + DRS shading (`f1_advanced_visualizer.py:291`)
  - [ ] `sector_bars.py` : horizontal bar delta (`f1_advanced_visualizer.py:337`)
  - [ ] `telemetry_table.py` : `DataTable` for lap table (fastest laps, teams, lap times, sortable — replaces printed summary `f1_advanced_visualizer.py:179`)

### 2.4 Workers & Async

- [ ] **P2-9 `tui/workers/session_loader.py`**
  - [ ] `fastf1.get_session(...).load()` runs in `run_worker(exclusive=True)` with `LoadingIndicator` + `ProgressBar`.
  - [ ] Cache hit: instant (no spinner); network: `ProgressBar` + `rich` spinner.
  - [ ] Error toast: `SessionNotHeldError` → “2026 Abu Dhabi R not yet held” with `Retry` button.
  - [ ] Never block UI thread — all `fastf1` calls in worker.

- [ ] **P2-10 Keybindings & Help**
  - [ ] `q` quit, `s` save, `r` reload, `?` help modal, `/` search, `1-5` tab switch, `Esc` back.
  - [ ] `HelpScreen` with keymap + `fastf1_reference.md:1` content.

- [ ] **P2-11 Offline/Demo Mode**
  - [ ] Bundle `data/telemetry_sample.csv` + minimal `cache/` snapshot (1 GP) so `f1-tui --demo` works without network (for `docs/demo.gif` recording via `termtosvg` or `vhs`).

- [ ] **P2-12 Theme** — `tui/theme.tcss` (dark/light, team colors), `matplotlib` style synced.

**Packaging:** `pip install -e ".[tui]"` → `f1-tui` (`pyproject.toml:39` `f1-tui = "f1_terminal.tui.app:main"`).

**Exit Criteria:** `f1-tui` launches, can select 2023 Monza Q, display a
terminal-safe track/speed summary, save a PNG, work offline with `--demo`, and
never block the UI thread. Sixel/Kitty support is not required.

---

## MVP Release Gate — v1.5

Before starting any post-MVP phase:

- [ ] Phase 0, Phase 1, and Phase 2 exit criteria are met.
- [ ] `f1`, `f1-tui`, and the existing legacy entry points work in a clean
  environment.
- [ ] Mocked tests pass without network access; the demo mode works without a
  FastF1 download.
- [ ] README documents the shipped CLI/TUI workflows and does not promise
  unimplemented GUI, web, or ML features.
- [ ] Record a short usage review: which workflows were used, what failed, and
  which single post-MVP investment has the strongest evidence.

**Release decision:** Tag v1.5 only when the gate is complete. Do not bundle
desktop, web, ML, or package-manager work into this release.

---

## Post-MVP Options

Choose **one** option after the v1.5 usage review. The options are not parallel
commitments:

1. **Desktop GUI** — choose PyQt6 or customtkinter, then execute Phase 3.
2. **Web shareability** — execute Phase 3b instead of desktop GUI if sharing
   dashboards matters more than native desktop controls.
3. **Data/ML** — execute Phase 4 only after real users request feature tables or
   predictions.
4. **Distribution/polish** — execute the smallest applicable parts of Phases 5
   and 6 when release demand justifies the maintenance cost.

---

## Phase 3 — GUI (Desktop, deferred) (5-8 weeks)

**Start condition:** v1.5 usage review selects desktop GUI and a maintainer
explicitly chooses one toolkit. Do not develop both GUI stacks.

**Decision before start:** Write `docs/adr/001-gui-stack.md` choosing **PyQt6** vs **customtkinter**. Recommendation is split below.

### 3.1 Common (both stacks)

- [ ] **P3-1 Dependencies** — `pyproject.toml:32` `gui = ["PyQt6>=6.6.0", "matplotlib>=3.8.0", "mplcursors>=0.5.0"]` OR `customtkinter>=5.2.0`
- [ ] **P3-2 Layout Spec** (both)
  ```
  ┌─ MenuBar: File (Save/Export)  View (Theme)  Help ─┐
  │ Left Controls │ Center Canvas │ Right Details      │
  │ Year [2026 ▼] │  Matplotlib   │ Lap Table          │
  │ Track [▼]     │  Figure       │ (sortable)         │
  │ Session (○)   │  + Toolbar    │ Sector Bars        │
  │ Drivers [☑]   │  (zoom/pan)   │ Telemetry Summary  │
  │ [Load]        │               │ [Export PNG/CSV]   │
  └─ StatusBar: cache • network • log ─────────────────┘
  ```
  - [ ] Left: `QSpinBox`/`CTkOptionMenu` year, `QComboBox` track (searchable, with `fastf1_name` handling), `QRadioButton` session, `QCheckBox` drivers (team-colored), `Load` button.
  - [ ] Center: `FigureCanvas` + `NavigationToolbar`.
  - [ ] Right: `QTableView`/`CTkTable` lap times, `Sector` bar chart, `Summary` text.

### 3.2 PyQt6 Path

- [ ] **P3-3 `gui/main_window.py`** — `QMainWindow`, `QSplitter` for resizable panels, `QTabWidget` for analysis tabs.
- [ ] **P3-4 `gui/canvas.py`** — `FigureCanvasQTAgg` + `NavigationToolbar2QT`; method `set_figure(fig)` swaps figure without recreating canvas.
- [ ] **P3-5 `gui/workers.py`** — `QThread` subclass `SessionLoader(QThread)` with signals `loaded(SessionWrapper)`, `error(str)`, `progress(int)`; UI shows `QProgressBar`.
- [ ] **P3-6 Interactions**
  - [ ] Hover tooltip: `mplcursors` on speed trace shows `Distance, Speed, Throttle, Gear`.
  - [ ] Crosshair: vertical line synced across subplots.
  - [ ] Comparison: overlay 2-4 drivers, legend sorted numerically, colors from `core/colors.py`.

### 3.3 CustomTkinter Path (lighter)

- [ ] **P3-3b `gui/app.py`** — `CTk` root, `CTkFrame` panels, `CTkTabview` for analyses.
- [ ] **P3-4b `gui/canvas.py`** — `FigureCanvasTkAgg` + `NavigationToolbar2Tk`; embed in `CTkFrame`.
- [ ] **P3-5b `gui/workers.py`** — `threading.Thread` + `queue.Queue` + `root.after(100, poll)` to avoid blocking `mainloop`.

### 3.4 Features Beyond TUI

- [ ] **P3-7 Export**
  - [ ] `File → Save Figure` (PNG/SVG/PDF, `dpi=FIGURE_DPI`), `Export Data` (CSV/Parquet of telemetry, lap table).
  - [ ] `Edit → Copy to Clipboard` (figure PNG).

- [ ] **P3-8 Live Timing (stretch)** — poll `fastf1` live endpoint every 5s, update `Race Pace` tab; show `LIVE` badge.

- [ ] **P3-9 Packaging**
  - [ ] `pip install -e ".[gui]"` → `f1-gui` (`pyproject.toml:39` `f1-gui = "f1_terminal.gui.app:main"`).
  - [ ] `pyinstaller` single exe: `pyinstaller --onefile --windowed --name f1-gui f1_terminal/gui/app.py` → `dist/f1-gui.exe`; add to GitHub Releases.

**Exit Criteria:** `f1-gui` opens, selects track/session/driver, renders track map + speed trace + sectors without freezing, Save/Export work, single exe builds on Windows.

---

## Phase 3b — Web Alternative (Streamlit/Dash, deferred) (2-4 weeks, optional)

**Start condition:** v1.5 usage review selects shareable browser access instead
of desktop GUI, or provides clear evidence that both are maintainable.

If desktop distribution is out of scope, ship web GUI that reuses `core/`.

- [ ] **P3b-1 `f1_terminal/web/app.py`** — `streamlit` app
  - [ ] Sidebar: year, track, session, drivers (same as GUI left panel).
  - [ ] Main: `st.pyplot(fig)` or `st.plotly_chart(plotly_fig)` (add `plotly` renderer in `core/plotting.py`).
  - [ ] `st.dataframe(laps)` for lap table, `st.download_button` for CSV.
  - [ ] Deploy to `Streamlit Community Cloud` or `Hugging Face Spaces` (1-click).

- [ ] **P3b-2 Plotly renderer** — add `core/plotting_plotly.py` that mirrors `plotting.py` but returns `plotly.Figure` for hover/zoom.

**Exit Criteria:** `streamlit run f1_terminal/web/app.py` works locally, deploy URL shareable.

---

## Phase 4 — Data & Intelligence (deferred, 3-4 weeks)

**Start condition:** v1.5 has stable telemetry transforms and a documented user
need for feature tables, predictions, or live timing. ML is not part of the MVP.

- [ ] **P4-1 DataSource abstraction** — `f1_terminal/core/datasource.py`
  ```python
  class DataSource(Protocol):
      def get_schedule(year): ...
      def load_session(year, track, session): ...
  class FastF1Source(DataSource): ...
  class OpenF1Source(DataSource): ...  # https://api.openf1.org
  class CsvSource(DataSource): ...      # for data/telemetry_sample.csv
  ```
  Config `datasource = "fastf1"` in `pyproject.toml` or env `F1_DATASOURCE=openf1`.

- [ ] **P4-2 Caching v2**
  - [ ] `cache/` versioned by `fastf1` version + `year`; `cache/manifest.json` with `EventDate`, `SessionDate`, `FastF1Version`.
  - [ ] `f1 cache --clear --year 2026` and `f1 cache --status` commands.
  - [ ] Offline-first: if network fails, load from `cache/` and warn “Showing cached data from 2026-03-15”.

- [ ] **P4-3 Telemetry transforms** — `core/transforms.py`
  - [ ] `prepare_telemetry_trace(session, driver, lap=fastest) -> DataFrame` adds `Distance` if missing, resamples to 10Hz, handles `Brake` bool→int.
  - [ ] `engineer_lap_features(session, drivers) -> DataFrame` columns: `Driver, LapNumber, LapTime_s, S1_s, S2_s, S3_s, AvgSpeed, MaxSpeed, BrakingCount, Throttle95p, GearShifts, DRSPct, Compound, TrackTemp, AirTemp`.
  - [ ] Used by `README.md:121` ML example.

- [ ] **P4-4 ML pipeline** — `examples/predict_qualifying.py` + `f1_terminal/ml/`
  - [ ] `ml/qualifying_model.py`: `train(df) -> sklearn Pipeline` (e.g., `GradientBoostingRegressor` on `engineer_lap_features` → `QualiGap_s`).
  - [ ] `f1 predict --year 2024 --track Monza --model artifacts/model.pkl` CLI.
  - [ ] Notebook `lap_time_analysis.ipynb` with `seaborn` + `scipy` stats.

- [ ] **P4-5 Real-time** — `examples/real_time_dashboard.py` (poll `fastf1` live or `openf1` `/api/laps` SSE).

**Exit Criteria:** `from f1_terminal.core import engineer_lap_features; df = engineer_lap_features(session, ['VER','HAM'])` returns DataFrame with 15+ cols, no NaN, `pytest` passes; `f1 cache --status` works.

---

## Phase 5 — Quality, CI/CD, Distribution (deferred, 2-3 weeks)

**Start condition:** the selected post-MVP product is stable enough to release.
Do not commit to PyPI, Homebrew, winget, AUR, Docker, and standalone binaries
at the same time; choose only the channels users request.

- [ ] **P5-1 Testing pyramid**
  - [ ] Unit: `test_tracks`, `test_session`, `test_telemetry`, `test_colors`, `test_plotting` (mocked, `Agg`).
  - [ ] Integration: `test_cli` (invoke `typer` with `CliRunner`), `test_tui_smoke` (`textual` pilot).
  - [ ] E2E: `test_e2e_monza_2023` downloads 2023 Monza Q (cached in CI via `actions/cache` on `cache/`), asserts 20 drivers, lap times < 90s.
  - [ ] Visual regression: `pytest-mpl` compare `plot_track_map` PNG hash.

- [ ] **P5-2 Lint/Type**
  - [ ] `ruff check --fix` + `ruff format`; `mypy --strict f1_terminal/core`; `bandit` for security.
  - [ ] `pre-commit` hooks: `ruff`, `mypy`, `py_compile`.

- [ ] **P5-3 CI/CD** — `.github/workflows/`
  - [ ] `ci.yml`: `py310, py311, py312` matrix, `ruff`, `mypy`, `pytest`, upload `coverage.xml` to `codecov`.
  - [ ] `release.yml`: on tag `v*`, build `sdist`+`wheel`, publish to PyPI via `trusted publishing` (OIDC), plus `pyinstaller` artifacts to GitHub Releases.
  - [ ] `cache.yml`: weekly `cron` to refresh `cache/` for 2026 season.

- [ ] **P5-4 Versioning**
  - [ ] `commitizen` (`cz bump`) + `semantic-release` or `setuptools_scm` (version from `git tag`).
  - [ ] `f1 --version` and `f1_terminal/__init__.py:__version__` synced to `pyproject.toml:6`.

- [ ] **P5-5 Distribution**
  - [ ] PyPI: `pip install f1-terminal-x` ; extras `pip install f1-terminal-x[tui,gui]`.
  - [ ] `pipx`: `pipx install f1-terminal-x` → `f1`, `f1-tui`, `f1-gui` on PATH.
  - [ ] `brew tap` (macOS), `winget` (Windows), `AUR` (Arch) — stretch.
  - [ ] Docker: `Dockerfile` for `f1-tui` (alpine, `python:3.11-slim`).

**Exit Criteria:** `pip install f1-terminal-x` from TestPyPI works, `f1 --version` matches tag, CI green on 3 OS × 3 Python, coverage >80% on `core/`.

---

## Phase 6 — Polish & Release v2.0 (deferred, 1-2 weeks)

**Start condition:** a post-MVP product has shipped and its documentation and
support needs are known. A docs site and v2.0 tag are not prerequisites for v1.5.

- [ ] **P6-1 Docs site** — `mkdocs` + `mkdocs-material` + `mkdocstrings[python]`
  - [ ] `docs/index.md` (from `README.md`), `docs/api/core.md`, `docs/adr/`, `docs/changelog.md` (from `CHANGELOG.md` via `commitizen`).
  - [ ] Deploy to `GitHub Pages` via `mike`.

- [ ] **P6-2 Demos**
  - [ ] Regenerate `docs/demo.gif` (CLI), `docs/demo_tui.gif` (via `vhs` or `termtosvg` recording `f1-tui --demo`), `docs/demo_gui.png` (screenshot).
  - [ ] Add `Demo` section to `README.md:86` with tabs CLI/TUI/GUI/Web.

- [ ] **P6-3 UX polish**
  - [ ] Dark/light theme toggle (propagate to `matplotlib` `plt.style.use('seaborn-v0_8-darkgrid' vs 'seaborn-v0_8-whitegrid')`).
  - [ ] `rich` progress bars for all loads (already in `tui/workers`).
  - [ ] Error toasts with “Copy error” + “Open Issue” link.

- [ ] **P6-4 Community**
  - [ ] `CONTRIBUTING.md` (link from `README.md:154`), `CODE_OF_CONDUCT.md` (already in `.github/CODE_OF_CONDUCT.md`), `SECURITY.md`.
  - [ ] `good first issue` labels, `Aspects/USERS.md` → `CONTRIBUTORS.md` with all contributors.

- [ ] **P6-5 Release**
  - [ ] Tag `v2.0.0`, `git push --tags`, GitHub Release notes, PyPI publish, announce in `docs/`.

**Exit Criteria:** `https://<user>.github.io/f1-terminal-x/` live, `pip install f1-terminal-x==2.0.0` works, all 3 entry points (`f1`, `f1-tui`, `f1-gui`) work on clean env.

---

## Timeline & Effort Summary

| Phase | Effort | Dependencies | Commitment | Deliverable |
|-------|--------|--------------|----------------|-------------|
| 0 Hygiene | 1-2 w | none | committed | CI green, README runs |
| 1 Core Refactor | 2-3 w | Phase 0 | committed | `f1_terminal/core/` + scriptable CLI |
| 2 TUI | 3-5 w | Phase 1 | committed | `f1-tui` with demo mode |
| MVP gate | 1 w | Phases 0-2 | committed | v1.5 decision and usage review |
| 3 GUI | 5-8 w | MVP decision | deferred | `f1-gui` / exe |
| 3b Web | 2-4 w | MVP decision | deferred | shareable Streamlit app |
| 4 Data/ML | 3-4 w | MVP decision | deferred | feature tables and/or model |
| 5 Quality/CI | 2-3 w | selected product | deferred | release automation and targeted distribution |
| 6 Polish | 1-2 w | selected product | deferred | docs site and v2.0 tag |

**Committed critical path:** 0 → 1 → 2 → MVP gate = **~7-11 weeks** solo.
The post-MVP total is intentionally not estimated until one product direction is
chosen; GUI + web + ML + distribution should not be treated as a single
12-18-week solo commitment.

**Suggested order for solo dev:** `0 → 1 → 2 → v1.5 → usage review → exactly one of
`3`, `3b`, or `4` → targeted quality/distribution work.

---

## Testing Strategy Matrix

| Area | Tool | What | Mock? | CI? |
|------|------|------|-------|-----|
| Tracks DB | `pytest` | 22 entries, unique `fastf1_name`, `get_track(99)` raises | no | yes |
| Cache | `pytest` | import does not create stray cache, unified dir | yes (tmp_path) | yes |
| Session | `pytest` + `responses` | `load_session` retry, `SessionNotHeldError` friendly msg | mock `fastf1.get_session` | yes |
| Telemetry | `pytest` | `get_telemetry` handles empty, `add_distance` | mock `Series.get_telemetry` | yes |
| Plotting | `pytest-mpl` | `plot_track_map` PNG hash, handles NaN | mock DataFrames, `Agg` | yes |
| CLI | `typer.testing.CliRunner` | `f1 --help`, `f1 advanced --year 2024 --track Austria --no-show --save` | mock session | yes |
| TUI | `textual` `Pilot` | launch, select track, load, save | mock worker | yes (xvfb) |
| GUI (deferred) | `pytest-qt` | open window, load, save | mock worker | no (manual) |
| E2E | `pytest` (slow, marked) | 2023 Monza Q → 20 drivers, laps <90s | real `cache/` via `actions/cache` | nightly |
| Visual | `pytest-mpl` | sector bars, speed trace golden files | no | yes |

**MVP coverage target:** `core/` ≥85%, `cli/` ≥70%, `tui/` ≥50% (pilot smoke).
GUI, web, and ML coverage targets are set only if that option is selected.

---

## Nice-to-Have Backlog & Stretch Goals

These items are intentionally not part of the v1.5 commitment. Move an item
into a selected phase only when usage evidence and maintainer capacity justify
it; do not work from this list opportunistically.

**Small follow-ons (consider after v1.5):**

- [ ] `typer` shell completion for `Track` names.
- [ ] `pydantic` models for `Track`, `SessionParams`, `DriverResult`.
- [ ] Dark/light theme toggle propagating to `matplotlib` style.
- [ ] `f1 compare --drivers VER,HAM,LEC --track Silverstone --year 2024`.
- [ ] `f1 export --format parquet --output telemetry.parquet`.
- [ ] `f1 config --set cache_dir ~/f1cache` + `f1 config --list`.

**Platform and research experiments (parked):**

- [ ] i18n (EN/JA for Suzuka, IT for Monza).
- [ ] `openf1` live timing → `f1 live --track Monza` TUI dashboard.
- [ ] Telemetry ML pipeline (covered by deferred Phase 4).
- [ ] Mobile wrapper using Kivy or BeeWare.
- [ ] VS Code extension calling the `f1` CLI.
- [ ] Telemetry audio synthesis from `RPM` and `Speed`.

---

## Appendix

### A. What Was Fixed (2026-09-25 Pass) — bug → fix table

| # | File(s) | Bug | Fix |
|---|---------|-----|-----|
| 1 | `F1_Main_py/Schedule&Driver.py` | `&` in filename breaks `import` | Copied to `schedule_driver.py`; shim with `DeprecationWarning` |
| 2 | `F1_Main_py/f1.py:152` | `return _select_fallback(...), result` bug (`result is None`) | `fallback_code` + name lookup |
| 3 | `F1_Main_py/driver.py` + `schedule_driver.py` | Top-level `while True:` blocks import | Wrapped `main()` + `if __name__ == "__main__":` |
| 4 | All scripts | `Cache.enable_cache` deprecated | Dual `try: set_cache_directory() except AttributeError` + unified `CACHE_DIR` |
| 5 | `f1_qualifying.py`, `PracticeSession.py` | `track['country']` ambiguous (Spain/USA dups) | Use `fastf1_name` from `tracks.py` |
| 6 | `f1_qualifying.py:135` | Legend lexicographic sort | Numeric `lap_sec` sort |
| 7 | `f1_qualifying.py:108` | Color `f"#{team_color}"` double-hash/int bug | `lstrip('#')` + hex handling |
| 8 | `driver.py` | `driver.BroadcastName` attr vs dict API | `_get_driver_field()` helper |
| 9 | `driver.py` / `f1.py` | `pick_drivers` vs `pick_driver` | `_resolve_driver_laps()` |
| 10 | `f1_advanced_visualizer.py:31` | `f1_cache` drift + dead `alphas` | Unified cache, `dropna` |
| 11 | `f1_advanced_visualizer.py:14` | Madrid `Madring` mismatch | Harmonized |
| 12 | Project | No `__init__.py`, `pyproject.toml`, `.gitignore` gaps | Added |
| 13 | `README.md:61` | `io`, `transform`, `features` don't exist | Flagged Phase 0 |
| 14 | `f1.py:43` | `CACHE_DIR = Path("cache")` cwd-dependent | `resolve()` |

### B. References

- FastF1 docs: `https://docs.fastf1.dev/`
- OpenF1 API: `https://api.openf1.org/`
- Textual: `https://textual.textualize.io/`
- Rich: `https://rich.readthedocs.io/`
- Typer: `https://typer.tiangolo.com/`
- PyQt6: `https://www.riverbankcomputing.com/software/pyqt/`
- CustomTkinter: `https://github.com/TomSchimansky/CustomTkinter`
- Streamlit: `https://streamlit.io/`

### C. Contributing Quick Start (after Phase 0)

```bash
git clone https://github.com/Ifaz2611/f1-telemetry-terminal.git
cd f1-telemetry-terminal
python -m venv .venv && source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -e ".[dev,tui]"
pre-commit install
pytest -q
f1 --help
f1-tui --demo
```

---

*This roadmap is a living document — update checkboxes per PR, add ADRs in `docs/adr/`, and keep `TODO.md` as the single source of truth for “what’s next”.*
