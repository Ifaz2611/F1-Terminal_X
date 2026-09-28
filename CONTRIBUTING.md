# Contributing

1. `python -m venv .venv` + `pip install -e ".[dev,tui]"`
2. `pre-commit install` (ruff, mypy, py_compile)
3. `pytest -q`, `f1 --help`, `f1-tui --demo --ascii`
4. Keep new logic in `f1_terminal/core|cli|tui|gui`; `F1_Main_py/` is legacy shim only.
