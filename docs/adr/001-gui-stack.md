# ADR 001: GUI Stack — PyQt6 primary, customtkinter fallback

Status: accepted (post-MVP option, Phase 3 deferred until v1.5 usage review).

## Context
The MVP (v1.5) ships CLI + TUI only. A desktop GUI is a post-MVP option.
We must choose one primary toolkit to avoid maintaining two stacks.

## Decision
- Primary: **PyQt6** (`FigureCanvasQTAgg`, `QThread SessionLoader`, `QSplitter`,
  `QTabWidget`, `mplcursors` hover, native menus, `pyinstaller --onefile` exe).
- Fallback: **customtkinter** (`FigureCanvasTkAgg`, `threading+queue+after()`)
  for lighter installs; plain `tkinter` when neither is present.
- All backends share `f1_terminal/gui/main_window.py:build_matplotlib_figure`
  (pure, headless-testable) and `f1_terminal/core` for data/plot.
- `pip install -e ".[gui]"` provides `f1-gui`; `f1-gui --save out.png` works headless.

## Consequences
- Do not develop both stacks in parallel; PyQt6 is the supported path.
- GUI work starts only after the v1.5 usage review selects desktop.
