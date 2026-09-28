"""TUI smoke tests — textual Pilot when available, else ASCII/demo fallback."""

from __future__ import annotations


def test_ascii_demo_mode():
    from f1_terminal.tui.app import run_ascii_mode

    rc = run_ascii_mode(2023, "Monza", "Q", "VER", demo=True)
    assert rc == 0


def test_ascii_demo_save(tmp_path):
    from f1_terminal.tui.app import run_ascii_mode

    out = tmp_path / "demo.png"
    rc = run_ascii_mode(2023, "Monza", "Q", "VER", demo=True, save=str(out))
    assert rc == 0
    assert out.exists()


def test_track_rows_filter():
    from f1_terminal.tui.screens.track_select import filter_tracks, track_rows

    rows = track_rows(2023)
    assert len(rows) == 22
    assert len(filter_tracks("monza", 2023)) >= 1
    assert len(filter_tracks("", 2023)) == 22


def test_speed_ascii_no_plotext(monkeypatch):
    import sys

    from f1_terminal.tui import ascii as a

    monkeypatch.setitem(sys.modules, "plotext", None)
    import pandas as pd

    tel = pd.DataFrame({"Speed": [200, 210], "Distance": [0, 10]})
    # force ImportError path by blocking import
    monkeypatch.setattr("builtins.__import__", _guard_import)
    txt = a.telemetry_summary_text(tel, "VER")
    assert "VER" in txt or "Speed" in txt


def _guard_import(name, *args, **kwargs):
    if name == "plotext":
        raise ImportError("blocked")
    import builtins

    return builtins.__import__.__wrapped__(name, *args, **kwargs) if hasattr(builtins.__import__, "__wrapped__") else __import__orig(name, *args, **kwargs)


try:
    import builtins as _b

    __import__orig = _b.__import__
except Exception:
    __import__orig = __import__


def test_textual_pilot_smoke():
    try:
        import textual  # noqa: F401
    except ImportError:
        import pytest

        pytest.skip("textual not installed")
        return
    import asyncio

    from f1_terminal.tui.app import F1TerminalApp

    async def _run():
        app = F1TerminalApp(year=2023, track="Monza", session_code="Q", demo=True).build_textual_app()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app is not None

    asyncio.run(_run())
