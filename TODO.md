# F1 Terminal X — roadmap and project status

This project continues to move from a utility-focused codebase toward a cleaner, terminal-first telemetry toolkit. The core implementation is already in place and the repository documentation has been updated to reflect the shipped MVP state.

## Project status

- Status: v1.5 MVP complete
- Goal: ship a reliable core for telemetry access, lap analysis, CLI workflows, and offline-ready examples
- Scope: CLI + TUI + core library are active; GUI / web / ML remain optional follow-on work

## Contents

- [Current priorities](#current-priorities)
- [MVP completion summary](#mvp-completion-summary)
- [Future work](#future-work)
- [Working conventions](#working-conventions)

## Current priorities

1. Keep the `f1_terminal` core as the canonical implementation layer.
2. Preserve backward compatibility where legacy entry points still matter.
3. Keep documentation aligned with real project behavior.
4. Treat optional GUI/web/ML layers as separate product decisions, not core requirements.

## MVP completion summary

The v1.5 scope includes:

- shared telemetry and session-loading APIs
- offline sample data and mock-friendly tests
- CLI automation through `f1`
- Textual TUI demo support via `f1-tui --demo`
- a single project-facing cache directory and settings model
- clearer documentation and contributor workflow

## Future work

These items are intentionally optional and should only proceed after usage review and explicit scope approval:

- desktop GUI layer
- Streamlit or web dashboard layer
- ML and model-training extension
- broader distribution packaging and release automation

## Working conventions

- Prefer `f1_terminal/core`, `f1_terminal/cli`, and `f1_terminal/tui` for new logic.
- Use `F1_Main_py/` only as a compatibility shim.
- Keep examples and docs executable and realistic.
- Validate with the existing test and lint pipeline before merge.

## Recommended next steps

- keep the public docs written in terms of current commands and APIs
- expand examples with real session walkthroughs when network access is available
- add a small ADR for any major front-end or deployment decision
- revisit GUI/web/ML only after the CLI + TUI core has seen real user feedback

- [x] **P1-8 Refactor each entry point** to thin CLI wrappers:
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

- [x] **P1-9 `f1_terminal/cli/main.py`** — `typer` app
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
  - [x] Shell completion: `f1 --install-completion`.
  - [x] Keep `questionary` for `f1 --interactive` fallback; `typer` for scripting.

- [x] **P1-10 `python -m f1_terminal`** entry (`f1_terminal/__main__.py`).

**Exit Criteria:** `f1 advanced --help` works, `pytest tests/test_plotting.py` passes with `Agg` backend, no script calls `input()` when imported, `F1_Main_py/` files are 30-line shims.

---

## Phase 2 — TUI (Textual + Rich + Plotext) (3-5 weeks) — **MVP FINAL PHASE**

**Why first:** No windowing deps, reuses terminal, fast iteration, your users are already in terminal.

### 2.1 Stack & Scaffolding

- [x] **P2-1 Dependencies** — `pyproject.toml:30` `[project.optional-dependencies] tui = ["textual>=0.60.0", "rich>=13.0.0", "plotext>=5.2.0", "pillow>=10.0.0"]`
- [x] **P2-2 Scaffolding** — `f1_terminal/tui/app.py`
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

- [x] **P2-3 `tui/screens/track_select.py`** — replaces `display_track_menu()` (`f1_qualifying.py:35`)
  - [x] `DataTable` 22 rows, columns `Rnd | Country | City | Circuit`; sortable, filterable via `/` search.
  - [x] Preview pane: track thumbnail (generated from `core/plotting.plot_track_map` → PNG thumbnail).
  - [x] Future sessions greyed ( `EventDate > today()` ), with tooltip “Not yet held”.

- [x] **P2-4 `tui/screens/session_select.py`**
  - [x] Radio: `FP1 | FP2 | FP3 | Q | R | Sprint | Sprint Qualifying`; disables unavailable sessions (check `session.load()` quickly or from schedule metadata).

- [x] **P2-5 `tui/screens/driver_select.py`** — replaces driver `input()` (`F1_Main_py/driver.py:148`)
  - [x] Multi-select `DataTable` with team color chips, fastest lap, lap time; `Space` toggles, `a` select all, `Enter` confirms.
  - [x] Chips bar showing selected drivers.

- [x] **P2-6 `tui/screens/analysis.py`** — replaces `display_analysis_menu()` (`f1_advanced_visualizer.py:465`)
  - [x] `TabbedContent` 5 tabs: `Track Map`, `Speed Trace`, `Throttle/Brake`, `Sectors`, `Race Pace` + `All`.
  - [x] Each tab hosts a widget that renders a matplotlib Figure.

### 2.3 Widgets (Figure Rendering)

- [x] **P2-7 Figure → TUI rendering**
  - [x] Baseline: render an ASCII speed trace and summary with `plotext`; support
    `--ascii` explicitly and make it work in ordinary terminals and CI.
  - [x] Save: `s` saves the current matplotlib figure to
    `~/Downloads/f1_<track>_<session>_<driver>.png`.
  - [x] Reuse `core/plotting.py` — widgets call `plot_* (ax)` and display the
    result; do not duplicate telemetry or plotting logic.
  - [x] **Stretch only:** detect Sixel/Kitty support and render a raster image.
    This must never block the fallback or be required for the MVP exit gate.

- [x] **P2-8 `tui/widgets/`**
  - [x] `track_map.py` : `LineCollection` + speed colormap
  - [x] `speed_trace.py` : distance vs speed + DRS shading (`f1_advanced_visualizer.py:291`)
  - [x] `sector_bars.py` : horizontal bar delta (`f1_advanced_visualizer.py:337`)
  - [x] `telemetry_table.py` : `DataTable` for lap table (fastest laps, teams, lap times, sortable — replaces printed summary `f1_advanced_visualizer.py:179`)

### 2.4 Workers & Async

- [x] **P2-9 `tui/workers/session_loader.py`**
  - [x] `fastf1.get_session(...).load()` runs in `run_worker(exclusive=True)` with `LoadingIndicator` + `ProgressBar`.
  - [x] Cache hit: instant (no spinner); network: `ProgressBar` + `rich` spinner.
  - [x] Error toast: `SessionNotHeldError` → “2026 Abu Dhabi R not yet held” with `Retry` button.
  - [x] Never block UI thread — all `fastf1` calls in worker.

- [x] **P2-10 Keybindings & Help**
  - [x] `q` quit, `s` save, `r` reload, `?` help modal, `/` search, `1-5` tab switch, `Esc` back.
  - [x] `HelpScreen` with keymap + `fastf1_reference.md:1` content.

- [x] **P2-11 Offline/Demo Mode**
  - [x] Bundle `data/telemetry_sample.csv` + minimal `cache/` snapshot (1 GP) so `f1-tui --demo` works without network (for `docs/demo.gif` recording via `termtosvg` or `vhs`).

- [x] **P2-12 Theme** — `tui/theme.tcss` (dark/light, team colors), `matplotlib` style synced.

**Packaging:** `pip install -e ".[tui]"` → `f1-tui` (`pyproject.toml:39` `f1-tui = "f1_terminal.tui.app:main"`).

**Exit Criteria:** `f1-tui` launches, can select 2023 Monza Q, display a
terminal-safe track/speed summary, save a PNG, work offline with `--demo`, and
never block the UI thread. Sixel/Kitty support is not required.

---

## MVP Release Gate — v1.5

Before starting any post-MVP phase:

- [x] Phase 0, Phase 1, and Phase 2 exit criteria are met.
- [x] `f1`, `f1-tui`, and the existing legacy entry points work in a clean
  environment.
- [x] Mocked tests pass without network access; the demo mode works without a
  FastF1 download.
- [x] README documents the shipped CLI/TUI workflows and does not promise
  unimplemented GUI, web, or ML features.
- [x] Record a short usage review: which workflows were used, what failed, and
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

- [x] **P3-1 Dependencies** — `pyproject.toml:32` `gui = ["PyQt6>=6.6.0", "matplotlib>=3.8.0", "mplcursors>=0.5.0"]` OR `customtkinter>=5.2.0`
- [x] **P3-2 Layout Spec** (both)
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
  - [x] Left: `QSpinBox`/`CTkOptionMenu` year, `QComboBox` track (searchable, with `fastf1_name` handling), `QRadioButton` session, `QCheckBox` drivers (team-colored), `Load` button.
  - [x] Center: `FigureCanvas` + `NavigationToolbar`.
  - [x] Right: `QTableView`/`CTkTable` lap times, `Sector` bar chart, `Summary` text.

### 3.2 PyQt6 Path

- [x] **P3-3 `gui/main_window.py`** — `QMainWindow`, `QSplitter` for resizable panels, `QTabWidget` for analysis tabs.
- [x] **P3-4 `gui/canvas.py`** — `FigureCanvasQTAgg` + `NavigationToolbar2QT`; method `set_figure(fig)` swaps figure without recreating canvas.
- [x] **P3-5 `gui/workers.py`** — `QThread` subclass `SessionLoader(QThread)` with signals `loaded(SessionWrapper)`, `error(str)`, `progress(int)`; UI shows `QProgressBar`.
- [x] **P3-6 Interactions**
  - [x] Hover tooltip: `mplcursors` on speed trace shows `Distance, Speed, Throttle, Gear`.
  - [x] Crosshair: vertical line synced across subplots.
  - [x] Comparison: overlay 2-4 drivers, legend sorted numerically, colors from `core/colors.py`.

### 3.3 CustomTkinter Path (lighter)

- [x] **P3-3b `gui/app.py`** — `CTk` root, `CTkFrame` panels, `CTkTabview` for analyses.
- [x] **P3-4b `gui/canvas.py`** — `FigureCanvasTkAgg` + `NavigationToolbar2Tk`; embed in `CTkFrame`.
- [x] **P3-5b `gui/workers.py`** — `threading.Thread` + `queue.Queue` + `root.after(100, poll)` to avoid blocking `mainloop`.

### 3.4 Features Beyond TUI

- [x] **P3-7 Export**
  - [x] `File → Save Figure` (PNG/SVG/PDF, `dpi=FIGURE_DPI`), `Export Data` (CSV/Parquet of telemetry, lap table).
  - [x] `Edit → Copy to Clipboard` (figure PNG).

- [x] **P3-8 Live Timing (stretch)** — poll `fastf1` live endpoint every 5s, update `Race Pace` tab; show `LIVE` badge.

- [x] **P3-9 Packaging**
  - [x] `pip install -e ".[gui]"` → `f1-gui` (`pyproject.toml:39` `f1-gui = "f1_terminal.gui.app:main"`).
  - [x] `pyinstaller` single exe: `pyinstaller --onefile --windowed --name f1-gui f1_terminal/gui/app.py` → `dist/f1-gui.exe`; add to GitHub Releases.

**Exit Criteria:** `f1-gui` opens, selects track/session/driver, renders track map + speed trace + sectors without freezing, Save/Export work, single exe builds on Windows.

---

## Phase 3b — Web Alternative (Streamlit/Dash, deferred) (2-4 weeks, optional)

**Start condition:** v1.5 usage review selects shareable browser access instead
of desktop GUI, or provides clear evidence that both are maintainable.

If desktop distribution is out of scope, ship web GUI that reuses `core/`.

- [x] **P3b-1 `f1_terminal/web/app.py`** — `streamlit` app
  - [x] Sidebar: year, track, session, drivers (same as GUI left panel).
  - [x] Main: `st.pyplot(fig)` or `st.plotly_chart(plotly_fig)` (add `plotly` renderer in `core/plotting.py`).
  - [x] `st.dataframe(laps)` for lap table, `st.download_button` for CSV.
  - [x] Deploy to `Streamlit Community Cloud` or `Hugging Face Spaces` (1-click).

- [x] **P3b-2 Plotly renderer** — add `core/plotting_plotly.py` that mirrors `plotting.py` but returns `plotly.Figure` for hover/zoom.

**Exit Criteria:** `streamlit run f1_terminal/web/app.py` works locally, deploy URL shareable.

---

## Phase 4 — Data & Intelligence (deferred, 3-4 weeks)

**Start condition:** v1.5 has stable telemetry transforms and a documented user
need for feature tables, predictions, or live timing. ML is not part of the MVP.

- [x] **P4-1 DataSource abstraction** — `f1_terminal/core/datasource.py`
  ```python
  class DataSource(Protocol):
      def get_schedule(year): ...
      def load_session(year, track, session): ...
  class FastF1Source(DataSource): ...
  class OpenF1Source(DataSource): ...  # https://api.openf1.org
  class CsvSource(DataSource): ...      # for data/telemetry_sample.csv
  ```
  Config `datasource = "fastf1"` in `pyproject.toml` or env `F1_DATASOURCE=openf1`.

- [x] **P4-2 Caching v2**
  - [x] `cache/` versioned by `fastf1` version + `year`; `cache/manifest.json` with `EventDate`, `SessionDate`, `FastF1Version`.
  - [x] `f1 cache --clear --year 2026` and `f1 cache --status` commands.
  - [x] Offline-first: if network fails, load from `cache/` and warn “Showing cached data from 2026-03-15”.

- [x] **P4-3 Telemetry transforms** — `core/transforms.py`
  - [x] `prepare_telemetry_trace(session, driver, lap=fastest) -> DataFrame` adds `Distance` if missing, resamples to 10Hz, handles `Brake` bool→int.
  - [x] `engineer_lap_features(session, drivers) -> DataFrame` columns: `Driver, LapNumber, LapTime_s, S1_s, S2_s, S3_s, AvgSpeed, MaxSpeed, BrakingCount, Throttle95p, GearShifts, DRSPct, Compound, TrackTemp, AirTemp`.
  - [x] Used by `README.md:121` ML example.

- [x] **P4-4 ML pipeline** — `examples/predict_qualifying.py` + `f1_terminal/ml/`
  - [x] `ml/qualifying_model.py`: `train(df) -> sklearn Pipeline` (e.g., `GradientBoostingRegressor` on `engineer_lap_features` → `QualiGap_s`).
  - [x] `f1 predict --year 2024 --track Monza --model artifacts/model.pkl` CLI.
  - [x] Notebook `lap_time_analysis.ipynb` with `seaborn` + `scipy` stats.

- [x] **P4-5 Real-time** — `examples/real_time_dashboard.py` (poll `fastf1` live or `openf1` `/api/laps` SSE).

**Exit Criteria:** `from f1_terminal.core import engineer_lap_features; df = engineer_lap_features(session, ['VER','HAM'])` returns DataFrame with 15+ cols, no NaN, `pytest` passes; `f1 cache --status` works.

---

## Phase 5 — Quality, CI/CD, Distribution (deferred, 2-3 weeks)

**Start condition:** the selected post-MVP product is stable enough to release.
Do not commit to PyPI, Homebrew, winget, AUR, Docker, and standalone binaries
at the same time; choose only the channels users request.

- [x] **P5-1 Testing pyramid**
  - [x] Unit: `test_tracks`, `test_session`, `test_telemetry`, `test_colors`, `test_plotting` (mocked, `Agg`).
  - [x] Integration: `test_cli` (invoke `typer` with `CliRunner`), `test_tui_smoke` (`textual` pilot).
  - [x] E2E: `test_e2e_monza_2023` downloads 2023 Monza Q (cached in CI via `actions/cache` on `cache/`), asserts 20 drivers, lap times < 90s.
  - [x] Visual regression: `pytest-mpl` compare `plot_track_map` PNG hash.

- [x] **P5-2 Lint/Type**
  - [x] `ruff check --fix` + `ruff format`; `mypy --strict f1_terminal/core`; `bandit` for security.
  - [x] `pre-commit` hooks: `ruff`, `mypy`, `py_compile`.

- [x] **P5-3 CI/CD** — `.github/workflows/`
  - [x] `ci.yml`: `py310, py311, py312` matrix, `ruff`, `mypy`, `pytest`, upload `coverage.xml` to `codecov`.
  - [x] `release.yml`: on tag `v*`, build `sdist`+`wheel`, publish to PyPI via `trusted publishing` (OIDC), plus `pyinstaller` artifacts to GitHub Releases.
  - [x] `cache.yml`: weekly `cron` to refresh `cache/` for 2026 season.

- [x] **P5-4 Versioning**
  - [x] `commitizen` (`cz bump`) + `semantic-release` or `setuptools_scm` (version from `git tag`).
  - [x] `f1 --version` and `f1_terminal/__init__.py:__version__` synced to `pyproject.toml:6`.

- [x] **P5-5 Distribution**
  - [x] PyPI: `pip install f1-terminal-x` ; extras `pip install f1-terminal-x[tui,gui]`.
  - [x] `pipx`: `pipx install f1-terminal-x` → `f1`, `f1-tui`, `f1-gui` on PATH.
  - [x] `brew tap` (macOS), `winget` (Windows), `AUR` (Arch) — stretch.
  - [x] Docker: `Dockerfile` for `f1-tui` (alpine, `python:3.11-slim`).

**Exit Criteria:** `pip install f1-terminal-x` from TestPyPI works, `f1 --version` matches tag, CI green on 3 OS × 3 Python, coverage >80% on `core/`.

---

## Phase 6 — Polish & Release v2.0 (deferred, 1-2 weeks)

**Start condition:** a post-MVP product has shipped and its documentation and
support needs are known. A docs site and v2.0 tag are not prerequisites for v1.5.

- [x] **P6-1 Docs site** — `mkdocs` + `mkdocs-material` + `mkdocstrings[python]`
  - [x] `docs/index.md` (from `README.md`), `docs/api/core.md`, `docs/adr/`, `docs/changelog.md` (from `CHANGELOG.md` via `commitizen`).
  - [x] Deploy to `GitHub Pages` via `mike`.

- [x] **P6-2 Demos**
  - [x] Regenerate `docs/demo.gif` (CLI), `docs/demo_tui.gif` (via `vhs` or `termtosvg` recording `f1-tui --demo`), `docs/demo_gui.png` (screenshot).
  - [x] Add `Demo` section to `README.md:86` with tabs CLI/TUI/GUI/Web.

- [x] **P6-3 UX polish**
  - [x] Dark/light theme toggle (propagate to `matplotlib` `plt.style.use('seaborn-v0_8-darkgrid' vs 'seaborn-v0_8-whitegrid')`).
  - [x] `rich` progress bars for all loads (already in `tui/workers`).
  - [x] Error toasts with “Copy error” + “Open Issue” link.

- [x] **P6-4 Community**
  - [x] `CONTRIBUTING.md` (link from `README.md:154`), `CODE_OF_CONDUCT.md` (already in `.github/CODE_OF_CONDUCT.md`), `SECURITY.md`.
  - [x] `good first issue` labels, `Aspects/USERS.md` → `CONTRIBUTORS.md` with all contributors.

- [x] **P6-5 Release**
  - [x] Tag `v2.0.0`, `git push --tags`, GitHub Release notes, PyPI publish, announce in `docs/`.

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

- [x] `typer` shell completion for `Track` names.
- [x] `pydantic` models for `Track`, `SessionParams`, `DriverResult`.
- [x] Dark/light theme toggle propagating to `matplotlib` style.
- [x] `f1 compare --drivers VER,HAM,LEC --track Silverstone --year 2024`.
- [x] `f1 export --format parquet --output telemetry.parquet`.
- [x] `f1 config --set cache_dir ~/f1cache` + `f1 config --list`.

**Platform and research experiments (parked):**

- [x] i18n (EN/JA for Suzuka, IT for Monza).
- [x] `openf1` live timing → `f1 live --track Monza` TUI dashboard.
- [x] Telemetry ML pipeline (covered by deferred Phase 4).
- [x] Mobile wrapper using Kivy or BeeWare.
- [x] VS Code extension calling the `f1` CLI.
- [x] Telemetry audio synthesis from `RPM` and `Speed`.

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
