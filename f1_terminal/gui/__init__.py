"""F1 GUI package — desktop front end reusing f1_terminal.core (Phase 3).

Toolkit is chosen per docs/adr/001-gui-stack.md: PyQt6 when available,
customtkinter second, plain tkinter fallback. All paths share the same
layout spec (left controls | center canvas | right details) and the same
core plotting functions.
"""

from __future__ import annotations
