"""GUI entry point ``f1-gui`` (P3-9).

Tries PyQt6 -> customtkinter -> tkinter -> headless info message.
Headless mode still supports --save for CI/manual verification.
"""

from __future__ import annotations

import argparse
import sys


def _parse(argv=None):
    p = argparse.ArgumentParser(prog="f1-gui", description="F1 Terminal X desktop GUI")
    p.add_argument("--year", type=int, default=2026)
    p.add_argument("--track", default="Monza")
    p.add_argument("--session", default="Q")
    p.add_argument("--driver", default="VER")
    p.add_argument("--analysis", default="track")
    p.add_argument("--save", default=None, help="Save figure and exit (headless/CI)")
    return p.parse_args(argv)


def _run_pyqt6(args) -> int | None:
    try:
        from PyQt6.QtWidgets import QApplication, QMainWindow  # type: ignore[import-not-found]
    except ImportError:
        return None
    try:
        from matplotlib.backends.backend_qtagg import (  # type: ignore[import]
            FigureCanvasQTAgg,
            NavigationToolbar2QT,
        )

        from f1_terminal.gui.main_window import MainWindow

        app = QApplication(sys.argv)
        win = QMainWindow()
        win.setWindowTitle(f"F1 Terminal X — {args.year} {args.track} {args.session}")
        mw = MainWindow(args.year, args.track, args.session)
        mw.load()
        fig = mw.figure(args.analysis, args.driver)
        canvas = FigureCanvasQTAgg(fig)
        win.setCentralWidget(canvas)
        win.addToolBar(NavigationToolbar2QT(canvas, win))
        # Hover tooltip (P3-6): mplcursors when available
        try:
            import mplcursors  # type: ignore[import-not-found]

            mplcursors.cursor(canvas.figure.axes, hover=True)
        except ImportError:
            pass
        win.resize(1200, 800)
        win.show()
        return app.exec()
    except Exception as e:
        print(f"PyQt6 GUI failed: {e}")
        return 1


def _run_tk(args) -> int | None:
    try:
        import tkinter as tk  # noqa: F401
    except ImportError:
        return None
    try:
        # customtkinter preferred, plain tkinter fallback
        try:
            import customtkinter as ctk  # type: ignore[import-not-found]

            root = ctk.CTk()
        except ImportError:
            import tkinter as tk2

            root = tk2.Tk()
        from f1_terminal.gui.main_window import MainWindow

        root.title(f"F1 Terminal X — {args.year} {args.track} {args.session}")
        mw = MainWindow(args.year, args.track, args.session)
        mw.load()
        fig = mw.figure(args.analysis, args.driver)
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

            canvas = FigureCanvasTkAgg(fig, master=root)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            NavigationToolbar2Tk(canvas, root).update()
        except Exception as e:
            print(f"Tk canvas embed failed ({e}); figure built successfully.")
            if args.save:
                fig.savefig(args.save, bbox_inches="tight")
                print(f"Saved {args.save}")
                return 0
        root.mainloop()
        return 0
    except Exception as e:
        print(f"Tk GUI failed: {e}")
        return 1


def main(argv=None) -> int:
    args = _parse(argv)
    if args.save and _run_pyqt6 is None:  # placeholder to keep linters quiet
        pass
    # Headless --save fast path (works everywhere, used by tests)
    if args.save:
        try:
            from f1_terminal.gui.main_window import MainWindow

            mw = MainWindow(args.year, args.track, args.session)
            # offline demo fallback when network fails
            try:
                mw.load()
            except Exception:
                from f1_terminal.tui.workers.session_loader import load_demo_session

                mw.wrapper = load_demo_session().wrapper
            fig = mw.figure(args.analysis, args.driver)
            fig.savefig(args.save, bbox_inches="tight")
            print(f"Saved {args.save}")
            return 0
        except Exception as e:
            print(f"Headless save failed: {e}")
            return 1
    # Interactive paths
    rc = _run_pyqt6(args)
    if rc is not None:
        return rc
    rc = _run_tk(args)
    if rc is not None:
        return rc
    print("No GUI toolkit installed. Install one of:")
    print("  pip install -e '.[gui]'   (PyQt6 path)")
    print("  pip install customtkinter (lighter path)")
    print("Or use headless: f1-gui --save out.png")
    return 2


if __name__ == "__main__":
    sys.exit(main())
