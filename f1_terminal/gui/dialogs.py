"""Save/export + settings dialogs (P3-7 helpers, backend-agnostic)."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def save_figure_dialog(fig: Any, default_name: str = "f1_figure.png") -> Path | None:
    """Save figure via native dialog when a GUI toolkit exists, else CWD."""
    out = Path.cwd() / default_name
    try:
        # Try Qt dialog
        from PyQt6.QtWidgets import QFileDialog  # type: ignore[import-not-found]

        path, _ = QFileDialog.getSaveFileName(None, "Save Figure", default_name, "Images (*.png *.svg *.pdf)")
        if path:
            out = Path(path)
    except ImportError:
        try:
            import tkinter.filedialog as fd

            path = fd.asksaveasfilename(defaultextension=".png", initialfile=default_name)
            if path:
                out = Path(path)
        except Exception:
            pass
    try:
        from f1_terminal.config import FIGURE_DPI

        fig.savefig(str(out), dpi=FIGURE_DPI, bbox_inches="tight")
    except Exception:
        fig.savefig(str(out), bbox_inches="tight")
    return out


def export_telemetry_csv(telemetry: Any, default_name: str = "telemetry.csv") -> Path:
    out = Path.cwd() / default_name
    try:
        telemetry.to_csv(str(out), index=False)
    except Exception as e:
        raise ValueError(f"CSV export failed: {e}") from e
    return out
