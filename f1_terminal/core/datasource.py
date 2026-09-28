"""DataSource abstraction (P4-1): FastF1 / OpenF1 / CSV behind one Protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

import pandas as pd

from f1_terminal.config import get_logger

logger = get_logger(__name__)


class DataSource(Protocol):
    def get_schedule(self, year: int) -> pd.DataFrame: ...
    def load_session(self, year: int, track: Any, session: str) -> Any: ...


class FastF1Source:
    """Primary source — wraps f1_terminal.core.session."""

    def get_schedule(self, year: int) -> pd.DataFrame:
        from f1_terminal.core.session import get_schedule

        return get_schedule(year)

    def load_session(self, year: int, track: Any, session: str) -> Any:
        from f1_terminal.core.session import load_session

        return load_session(year, track, session)


class CsvSource:
    """Offline source — data/telemetry_sample.csv + tracks_2026.json."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else (Path("data") / "telemetry_sample.csv")

    def get_schedule(self, year: int) -> pd.DataFrame:
        try:
            import json

            p = Path("data") / "tracks_2026.json"
            if p.exists():
                data = json.loads(p.read_text())
                return pd.DataFrame(data)
        except Exception:
            pass
        return pd.DataFrame()

    def load_session(self, year: int, track: Any, session: str) -> Any:
        from f1_terminal.tui.workers.session_loader import load_demo_session

        res = load_demo_session()
        if not res.ok:
            raise RuntimeError(res.error)
        return res.wrapper


class OpenF1Source:
    """Future source via https://api.openf1.org (best-effort, optional dep)."""

    BASE = "https://api.openf1.org"

    def get_schedule(self, year: int) -> pd.DataFrame:
        try:
            import json
            import urllib.request

            with urllib.request.urlopen(f"{self.BASE}/v1/sessions?year={year}", timeout=10) as r:
                data = json.loads(r.read().decode())
            return pd.DataFrame(data)
        except Exception as e:
            logger.warning("OpenF1 schedule failed: %s", e)
            return FastF1Source().get_schedule(year)

    def load_session(self, year: int, track: Any, session: str) -> Any:
        logger.warning("OpenF1 load_session not fully implemented; delegating to FastF1")
        return FastF1Source().load_session(year, track, session)


def get_source(name: str = "fastf1") -> DataSource:
    """Select source by name or F1_DATASOURCE env (fastf1|openf1|csv)."""
    import os

    name = os.getenv("F1_DATASOURCE", name).lower()
    if name == "csv":
        return CsvSource()
    if name == "openf1":
        return OpenF1Source()
    return FastF1Source()
