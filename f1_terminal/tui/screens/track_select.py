"""Track-select screen model (P2-3).

Replaces ``display_track_menu()`` with a filterable 22-row table model.
The Textual DataTable wiring lives in ``app.py``; this module holds the
pure data logic so it is testable without a terminal.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from f1_terminal.tracks import TRACKS


@dataclass
class TrackRow:
    rnd: int
    country: str
    city: str
    circuit: str
    fastf1_name: str
    future: bool = False


def track_rows(year: int = 2026, today: date | None = None) -> list[TrackRow]:
    """Return 22 rows; mark future sessions greyed via schedule EventDate when available."""
    future_rounds: set[int] = set()
    try:
        from f1_terminal.core.session import get_schedule

        sched = get_schedule(year)
        t = today or date.today()
        for _, r in sched.iterrows():
            try:
                ed = r.get("EventDate")
                rn = int(r.get("RoundNumber", -1))
                if ed is not None and str(ed) != "NaT":
                    import pandas as pd

                    d = pd.to_datetime(ed).date()
                    if d > t:
                        future_rounds.add(rn)
            except Exception:
                continue
    except Exception:
        pass
    rows = []
    for n in sorted(TRACKS):
        tr = TRACKS[n]
        rows.append(
            TrackRow(
                rnd=tr.round_num,
                country=tr.country,
                city=tr.city,
                circuit=tr.name,
                fastf1_name=tr.fastf1_name,
                future=(tr.round_num in future_rounds),
            )
        )
    return rows


def filter_tracks(query: str, year: int = 2026) -> list[TrackRow]:
    """Case-insensitive `/` search over country/city/circuit/fastf1_name."""
    q = query.strip().lower()
    rows = track_rows(year)
    if not q:
        return rows
    return [
        r
        for r in rows
        if q in r.country.lower() or q in r.city.lower() or q in r.circuit.lower() or q in r.fastf1_name.lower()
    ]


def track_thumbnail_text(row: TrackRow) -> str:
    """Preview-pane placeholder generated from core plotting in the full app."""
    return f"{row.circuit} ({row.city}, {row.country}) — id '{row.fastf1_name}'"
