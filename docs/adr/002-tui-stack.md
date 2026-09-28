# ADR 002: TUI Stack — Textual + Rich + Plotext

Status: accepted (v1.5 MVP).

## Context
Phase 2 needs a terminal-first UI reusing `f1_terminal/core`. Users are already
in the terminal; windowing deps must be avoided for the MVP.

## Decision
- `textual>=0.60` for App, DataTable, Tabs, workers (`run_worker(exclusive=True)`).
- `rich>=13` for logging (`RichHandler`), tables, progress.
- `plotext>=5.2` for ASCII speed-trace fallback (`--ascii`, CI-safe).
- `pillow>=10` for PNG thumbnails.
- Matplotlib figures are built only via `core/plotting.py` and saved with `s`.
- Sixel/Kitty raster rendering is stretch-only, never required for exit gate.

## Consequences
- `pip install -e ".[tui]"` provides `f1-tui`.
- `f1-tui --demo` works offline (sample CSV); `f1-tui --ascii` works without textual.
- All fastf1 calls run in workers; UI never blocks.
