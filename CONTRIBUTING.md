# Contributing

Thanks for helping improve F1 Terminal X.

## Local setup

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev,tui]"
pre-commit install
```

## Development workflow

1. Keep business logic in `f1_terminal/core`, `f1_terminal/cli`, `f1_terminal/tui`, or `f1_terminal/gui`.
2. Treat `F1_Main_py/` as a compatibility layer rather than a place for new implementations.
3. Run the project verification checks before submitting changes:

```bash
python -m py_compile F1_Main_py/f1.py F1_Main_py/driver.py f1_terminal/*.py f1_terminal/core/*.py
ruff check .
mypy f1_terminal/core --ignore-missing-imports --allow-untyped-decorators
pytest -q
f1 --help
f1-tui --demo --ascii
```

## Pull request expectations

- Keep changes focused and well-described.
- Prefer small, testable improvements with clear intent.
- Update documentation when behavior, dependencies, or setup change.
- Add or adjust tests for bug fixes and new functionality when relevant.

## Documentation

- Project overview: `README.md`
- Roadmap status: `TODO.md`
- Reference docs: `docs/reference/`
- Changelog: `CHANGELOG.md`

## Code of conduct

Please keep discussions constructive and respectful. Reviewers and contributors are expected to help maintain a safe and welcoming project environment.
