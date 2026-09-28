"""TUI widgets — thin wrappers reusing f1_terminal.core.plotting (P2-8).

Each widget exposes:
- a ``render_ascii(...)`` helper (plotext / text, always terminal-safe), and
- a ``make_figure(...)`` helper returning a matplotlib Figure for PNG export.

No telemetry or plotting logic is duplicated here.
"""

from __future__ import annotations
