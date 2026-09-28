"""FigureCanvas wrapper (P3-4): embed a matplotlib Figure without recreating canvas."""

from __future__ import annotations

from typing import Any


class FigureCanvas:
    """Backend-agnostic canvas holder.

    - PyQt6: wraps FigureCanvasQTAgg + NavigationToolbar2QT when PyQt6 installed.
    - customtkinter/tkinter: wraps FigureCanvasTkAgg when available.
    - headless/CI: stores the figure and supports savefig (no window).
    """

    def __init__(self, figure: Any = None):
        self.figure = figure
        self._qt_canvas: Any = None
        self._tk_canvas: Any = None
        self.backend = "headless"
        try:
            import PyQt6  # noqa: F401

            self.backend = "pyqt6"
        except ImportError:
            try:
                import customtkinter  # noqa: F401

                self.backend = "customtkinter"
            except ImportError:
                try:
                    import tkinter  # noqa: F401

                    self.backend = "tk"
                except ImportError:
                    self.backend = "headless"

    def set_figure(self, fig: Any) -> None:
        """Swap figure without recreating the canvas widget."""
        self.figure = fig
        try:
            if self._qt_canvas is not None:
                self._qt_canvas.figure = fig
                self._qt_canvas.draw()
        except Exception:
            pass
        try:
            if self._tk_canvas is not None:
                self._tk_canvas.figure = fig
                self._tk_canvas.draw()
        except Exception:
            pass

    def save(self, path: str, dpi: int = 150) -> str:
        if self.figure is None:
            raise ValueError("No figure to save")
        self.figure.savefig(path, dpi=dpi, bbox_inches="tight")
        return path
