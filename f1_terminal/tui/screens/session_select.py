"""Session-select screen model (P2-4)."""

from __future__ import annotations

SESSION_CODES = ["FP1", "FP2", "FP3", "Q", "R", "S", "SQ"]
SESSION_LABELS = {
    "FP1": "Practice 1",
    "FP2": "Practice 2",
    "FP3": "Practice 3",
    "Q": "Qualifying",
    "R": "Race",
    "S": "Sprint",
    "SQ": "Sprint Qualifying",
}


def available_sessions(year: int, track: str) -> dict[str, bool]:
    """Best-effort availability: Sprint sessions only where scheduled.

    Tries schedule metadata; on failure enables the classic FP1/FP2/FP3/Q/R set.
    """
    avail = {c: True for c in SESSION_CODES}
    try:
        from f1_terminal.core.session import get_schedule

        sched = get_schedule(year)
        # If schedule has EventFormat column, disable S/SQ when not sprint
        mask = None
        for col in ("EventName", "OfficialEventName", "Country", "Location"):
            if col in sched.columns:
                try:
                    m = sched[col].astype(str).str.lower() == str(track).lower()
                    if m.any():
                        mask = m
                        break
                except Exception:
                    continue
        if mask is not None and "EventFormat" in sched.columns:
            fmt = str(sched[mask].iloc[0].get("EventFormat", "")).lower()
            if "sprint" not in fmt:
                avail["S"] = False
                avail["SQ"] = False
    except Exception:
        avail["S"] = False
        avail["SQ"] = False
    return avail
