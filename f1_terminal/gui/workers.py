"""Background session loading (P3-5).

- PyQt6 path: QThread subclass SessionLoader with loaded/error/progress signals.
- customtkinter/tkinter path: threading.Thread + queue.Queue + after() polling.
- headless: synchronous load_session_sync.
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Any, Callable

from f1_terminal.config import get_logger

logger = get_logger(__name__)


@dataclass
class GuiLoadResult:
    ok: bool
    wrapper: Any = None
    error: str = ""


def load_blocking(year: int, track: Any, session_code: str) -> GuiLoadResult:
    from f1_terminal.tui.workers.session_loader import load_session_sync

    res = load_session_sync(year, track, session_code)
    return GuiLoadResult(ok=res.ok, wrapper=res.wrapper, error=res.error)


# PyQt6 QThread path (import lazily so headless CI never requires PyQt6)
try:
    from PyQt6.QtCore import QThread, pyqtSignal  # type: ignore[import-not-found]

    HAS_QT = True
except ImportError:
    HAS_QT = False
    QThread = object  # type: ignore[assignment,misc]


if HAS_QT:

    class SessionLoader(QThread):  # type: ignore[valid-type,misc]
        loaded = pyqtSignal(object)
        error = pyqtSignal(str)
        progress = pyqtSignal(int)

        def __init__(self, year: int, track: Any, session_code: str):
            super().__init__()
            self.year = year
            self.track = track
            self.session_code = session_code

        def run(self) -> None:
            try:
                self.progress.emit(10)
                res = load_blocking(self.year, self.track, self.session_code)
                self.progress.emit(100)
                if res.ok:
                    self.loaded.emit(res.wrapper)
                else:
                    self.error.emit(res.error)
            except Exception as e:
                self.error.emit(f"{type(e).__name__}: {e}")

else:

    class SessionLoader:  # type: ignore[no-redef]
        """Threading fallback mimicking the QThread interface."""

        def __init__(self, year: int, track: Any, session_code: str):
            self.year = year
            self.track = track
            self.session_code = session_code
            self._callbacks: dict[str, Callable] = {}
            self._queue: queue.Queue = queue.Queue()

        def on(self, event: str, cb: Callable) -> None:
            self._callbacks[event] = cb

        def start(self) -> None:
            def _work():
                try:
                    res = load_blocking(self.year, self.track, self.session_code)
                    if res.ok and "loaded" in self._callbacks:
                        self._callbacks["loaded"](res.wrapper)
                    elif not res.ok and "error" in self._callbacks:
                        self._callbacks["error"](res.error)
                except Exception as e:
                    if "error" in self._callbacks:
                        self._callbacks["error"](f"{type(e).__name__}: {e}")

            threading.Thread(target=_work, daemon=True).start()
