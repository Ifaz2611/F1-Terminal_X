"""F1TerminalApp — Textual TUI (Phase 2 MVP).

Layout:
  Header: Season [year]  Cache ●  Network ●
  Sidebar (22 tracks, `/` search) | Main Tabs [Track Map][Speed][Sectors][Race Pace][Summary]
  Footer: status • log • keybindings

Keybindings: q quit, s save, r reload, ? help, / search, 1-5 tab switch, Esc back.

Modes:
  f1-tui                      -> full Textual app (requires textual)
  f1-tui --demo               -> offline demo (no network, sample CSV)
  f1-tui --ascii               -> terminal-safe summary (works in CI, no textual needed)
  python -m f1_terminal.tui.app --demo --ascii  -> same

Exit criteria: launches, selects 2023 Monza Q, shows terminal-safe
track/speed summary, saves PNG, works offline with --demo, never blocks UI.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

from f1_terminal.config import get_logger

logger = get_logger(__name__)

HELP_TEXT = """F1 Terminal X — TUI Help
q quit | s save PNG | r reload | ? help | / search | 1-5 tabs | Esc back
Tabs: Track Map, Speed Trace, Throttle/Brake, Sectors, Race Pace, Summary(All)
Data: FastF1 (cached) or --demo offline fixture (data/telemetry_sample.csv).
See Aspects/fastf1_reference.md / docs/reference for FastF1 notes.
"""


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="f1-tui", description="F1 Terminal X TUI (Textual)")
    p.add_argument("--year", type=int, default=2023)
    p.add_argument("--track", default="Monza")
    p.add_argument("--session", default="Q")
    p.add_argument("--driver", default="VER")
    p.add_argument("--demo", action="store_true", help="Offline demo mode (sample CSV, no network)")
    p.add_argument("--ascii", action="store_true", help="Print terminal-safe summary and exit (CI-safe)")
    p.add_argument("--save", default=None, help="Save PNG path (ASCII/demo mode)")
    p.add_argument("--verbose", "-v", action="store_true")
    return p


def run_ascii_mode(year: int, track: str, session_code: str, driver: str, demo: bool, save: Optional[str] = None) -> int:
    """Terminal-safe summary path — no textual required. Returns exit code."""
    from f1_terminal.tui.widgets import sector_bars, speed_trace, telemetry_table, track_map
    from f1_terminal.tui.workers.session_loader import (
        get_demo_telemetry,
        load_demo_session,
        load_session_sync,
    )

    if demo:
        res = load_demo_session()
        if not res.ok:
            print(f"Demo load failed: {res.error}")
            return 1
        wrapper = res.wrapper
        tel = get_demo_telemetry(wrapper, driver)
        track_txt = track_map.render_ascii(tel, track)
        speed_txt = speed_trace.render_ascii(tel, driver)
        table_txt = telemetry_table.render_ascii(wrapper)
        print(f"== F1 TUI (demo) {year} {track} {session_code} ==")
        print(track_txt)
        print(speed_txt)
        print("-- Lap table --")
        print(table_txt)
        # sector frame from laps
        try:
            import pandas as pd

            rows = []
            for drv in wrapper.drivers:
                dl = wrapper.laps[wrapper.laps["Driver"] == drv].iloc[0]
                rows.append({"Driver": drv, "Sector1Time": dl.get("Sector1Time"), "Sector2Time": dl.get("Sector2Time"), "Sector3Time": dl.get("Sector3Time")})
            print("-- Sectors --")
            print(sector_bars.render_ascii(pd.DataFrame(rows)))
        except Exception as e:
            print(f"Sectors unavailable: {e}")
        if save:
            try:
                fig = track_map.make_figure(tel)
                fig.savefig(save, bbox_inches="tight")
                print(f"Saved figure to {save}")
            except Exception as e:
                print(f"Save failed: {e}")
                return 1
        return 0

    res = load_session_sync(year, track, session_code)
    if not res.ok:
        print(f"Session load failed: {res.error}")
        print("Tip: retry, check cache, or use --demo for offline mode.")
        return 1
    wrapper = res.wrapper
    from f1_terminal.core.telemetry import get_driver_telemetry

    try:
        _fastest, tel = get_driver_telemetry(wrapper, driver)
    except Exception as e:
        print(f"Telemetry for {driver} unavailable: {e}")
        return 1
    print(f"== F1 TUI {year} {track} {session_code} | driver {driver} ==")
    print(track_map.render_ascii(tel, track))
    print(speed_trace.render_ascii(tel, driver))
    print("-- Lap table --")
    print(telemetry_table.render_ascii(wrapper))
    if save:
        try:
            fig = speed_trace.make_figure(tel)
            fig.savefig(save, bbox_inches="tight")
            print(f"Saved figure to {save}")
        except Exception as e:
            print(f"Save failed: {e}")
            return 1
    return 0


def _try_run_textual(year: int, track: str, session_code: str, driver: str, demo: bool) -> int | None:
    """Return exit code if handled without textual, else None to launch Textual."""
    try:
        import textual  # noqa: F401
    except ImportError:
        print("textual not installed — falling back to --ascii summary.")
        print("Install with: pip install -e '.[tui]' for the full TUI.")
        return run_ascii_mode(year, track, session_code, driver, demo)
    return None


class F1TerminalApp:
    """Lazy Textual App wrapper so ``import f1_terminal.tui.app`` never requires textual."""

    CSS_PATH = str(Path(__file__).parent / "theme.tcss")
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "save", "Save"),
        ("r", "reload", "Reload"),
        ("question_mark", "help", "Help"),
        ("slash", "search", "Search"),
    ]

    def __init__(self, year: int = 2023, track: str = "Monza", session_code: str = "Q", demo: bool = False):
        self.year = year
        self.track = track
        self.session_code = session_code
        self.demo = demo
        self.wrapper: Any = None
        self._app: Any = None

    def build_textual_app(self):
        from textual.app import App, ComposeResult
        from textual.containers import Horizontal, Vertical
        from textual.widgets import (
            DataTable,
            Footer,
            Header,
            LoadingIndicator,
            Static,
            TabbedContent,
            TabPane,
        )

        from f1_terminal.tui.screens import analysis as analysis_model
        from f1_terminal.tui.screens import track_select as track_model
        from f1_terminal.tui.widgets import sector_bars, speed_trace, telemetry_table, track_map
        from f1_terminal.tui.workers.session_loader import (
            friendly_error_message,
            load_demo_session,
            load_session_sync,
        )

        outer = self

        class _App(App):
            CSS_PATH = outer.CSS_PATH
            BINDINGS = F1TerminalApp.BINDINGS

            def compose(self) -> ComposeResult:
                yield Header(show_clock=True)
                with Horizontal():
                    with Vertical(id="sidebar"):
                        yield Static(f"Season [{outer.year}]  Cache ●  Network ●", id="statusline")
                        yield Static("Tracks (/ to search)", id="tracklabel")
                        yield DataTable(id="tracks")
                    with Vertical(id="main"):
                        with TabbedContent():
                            for tab in analysis_model.TABS:
                                with TabPane(tab, id=f"tab-{tab}"):
                                    yield Static("Loading…", id=f"body-{tab}")
                yield LoadingIndicator(id="loader")
                yield Footer()

            def on_mount(self) -> None:
                table = self.query_one("#tracks", DataTable)
                table.add_columns("Rnd", "Country", "City", "Circuit")
                for r in track_model.track_rows(outer.year):
                    label = f"{r.circuit} (future)" if r.future else r.circuit
                    table.add_row(str(r.rnd), r.country, r.city, label)
                table.focus()
                self.load_session()

            def load_session(self) -> None:
                self.run_worker(self._do_load(), exclusive=True)

            async def _do_load(self) -> None:
                if outer.demo:
                    res = load_demo_session()
                else:
                    import asyncio

                    res = await asyncio.to_thread(load_session_sync, outer.year, outer.track, outer.session_code)
                self.call_from_thread(self._on_loaded, res)

            def _on_loaded(self, res) -> None:
                loader = self.query_one("#loader", LoadingIndicator)
                loader.display = False
                if not res.ok:
                    self.notify(friendly_error_message(outer.year, outer.track, outer.session_code, res.error), severity="error")
                    for tab in ["Track Map", "Speed Trace", "Sectors"]:
                        try:
                            self.query_one(f"#body-{tab}", Static).update(f"Error: {res.error}\nPress r to retry, or restart with --demo.")
                        except Exception:
                            pass
                    return
                outer.wrapper = res.wrapper
                self._render_tabs()

            def _render_tabs(self) -> None:
                w = outer.wrapper
                # Track Map
                try:
                    from f1_terminal.core.telemetry import get_driver_telemetry

                    _f, tel = get_driver_telemetry(w, "VER" if "VER" in w.drivers else w.drivers[0])
                    self.query_one("#body-Track Map", Static).update(track_map.render_ascii(tel, outer.track))
                    self.query_one("#body-Speed Trace", Static).update(speed_trace.render_ascii(tel, "VER"))
                except Exception as e:
                    self.query_one("#body-Track Map", Static).update(f"No telemetry: {e}")
                try:
                    self.query_one("#body-Summary(All)", Static).update(telemetry_table.render_ascii(w))
                except Exception:
                    pass
                try:
                    import pandas as pd

                    rows = []
                    for drv in w.drivers:
                        try:
                            from f1_terminal.core.telemetry import get_fastest_lap

                            f = get_fastest_lap(w, drv)
                            rows.append({"Driver": drv, "Sector1Time": f.get("Sector1Time"), "Sector2Time": f.get("Sector2Time"), "Sector3Time": f.get("Sector3Time")})
                        except Exception:
                            continue
                    self.query_one("#body-Sectors", Static).update(sector_bars.render_ascii(pd.DataFrame(rows)))
                except Exception as e:
                    logger.debug("sectors render failed: %s", e)

            def action_save(self) -> None:
                try:
                    from f1_terminal.core.telemetry import get_driver_telemetry
                    from f1_terminal.tui.ascii import save_matplotlib_figure
                    from f1_terminal.tui.widgets import track_map as tm

                    w = outer.wrapper
                    if w is None:
                        self.notify("Nothing to save yet", severity="warning")
                        return
                    drv = "VER" if "VER" in w.drivers else w.drivers[0]
                    _f, tel = get_driver_telemetry(w, drv)
                    out = save_matplotlib_figure(tm.make_figure(tel), outer.track, outer.session_code, drv)
                    self.notify(f"Saved {out}")
                except Exception as e:
                    self.notify(f"Save failed: {e}", severity="error")

            def action_reload(self) -> None:
                self.query_one("#loader", LoadingIndicator).display = True
                self.load_session()

            def action_help(self) -> None:

                self.push_screen(_HelpScreen())

            def action_search(self) -> None:
                self.query_one("#tracks", DataTable).focus()

        from textual.screen import ModalScreen

        class _HelpScreen(ModalScreen):
            def compose(self):
                from textual.widgets import Static

                yield Static(HELP_TEXT, id="help-text")

            def on_key(self, event) -> None:
                self.dismiss()

        return _App()

    def run(self) -> int:
        app = self.build_textual_app()
        app.run()
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    if args.verbose:
        from f1_terminal.config import setup_logging

        setup_logging(verbose=True)
    # --ascii always terminal-safe
    if args.ascii:
        return run_ascii_mode(args.year, args.track, args.session, args.driver, args.demo, args.save)
    # Try textual; fallback to ascii when missing
    fallback = _try_run_textual(args.year, args.track, args.session, args.driver, args.demo)
    if fallback is not None:
        if args.save:
            return run_ascii_mode(args.year, args.track, args.session, args.driver, args.demo, args.save)
        return fallback
    # Full Textual run (may raise if no TTY — degrade to ascii)
    try:
        return F1TerminalApp(year=args.year, track=args.track, session_code=args.session, demo=args.demo).run()
    except Exception as e:
        logger.warning("Textual run failed (%s), falling back to ascii", e)
        return run_ascii_mode(args.year, args.track, args.session, args.driver, args.demo, args.save)


if __name__ == "__main__":
    sys.exit(main())
