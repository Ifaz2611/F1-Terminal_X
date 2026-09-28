"""Caching v2 (P4-2): versioned manifest + status/clear helpers + offline-first.

``cache/manifest.json`` records FastF1 version, year, EventDate/SessionDate.
CLI: ``f1 cache --status`` and ``f1 cache --clear --year 2026``.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from f1_terminal.config import get_logger, settings

logger = get_logger(__name__)


def manifest_path() -> Path:
    return Path(settings.cache_dir) / "manifest.json"


def _fastf1_version() -> str:
    try:
        import fastf1

        return getattr(fastf1, "__version__", "unknown")
    except Exception:
        return "unknown"


def record_session(year: int, track: str, session_code: str, extra: dict | None = None) -> None:
    """Append/update manifest entry after a successful load."""
    try:
        mp = manifest_path()
        mp.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {}
        if mp.exists():
            try:
                data = json.loads(mp.read_text())
            except Exception:
                data = {}
        key = f"{year}/{track}/{session_code}"
        entry = {
            "year": year,
            "track": track,
            "session": session_code,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "fastf1_version": _fastf1_version(),
        }
        if extra:
            entry.update(extra)
        data[key] = entry
        data.setdefault("fastf1_version", _fastf1_version())
        mp.write_text(json.dumps(data, indent=2))
    except Exception as e:
        logger.debug("manifest record failed: %s", e)


def cache_status() -> dict[str, Any]:
    """Return status dict: dir, size, entries, fastf1 version."""
    d = Path(settings.cache_dir)
    total = 0
    files = 0
    if d.exists():
        for p in d.rglob("*"):
            try:
                if p.is_file():
                    files += 1
                    total += p.stat().st_size
            except Exception:
                continue
    entries: dict = {}
    mp = manifest_path()
    if mp.exists():
        try:
            entries = json.loads(mp.read_text())
        except Exception:
            entries = {}
    return {
        "cache_dir": str(d.resolve()) if d.exists() else str(d),
        "exists": d.exists(),
        "files": files,
        "bytes": total,
        "fastf1_version": _fastf1_version(),
        "entries": entries,
    }


def clear_cache(year: int | None = None) -> int:
    """Clear cache dir (or per-year subdir when present). Returns removed file count."""
    d = Path(settings.cache_dir)
    if not d.exists():
        return 0
    removed = 0
    if year is None:
        for child in list(d.iterdir()):
            try:
                if child.is_file():
                    child.unlink()
                    removed += 1
                else:
                    shutil.rmtree(child)
                    removed += 1
            except Exception:
                continue
        try:
            if manifest_path().exists():
                manifest_path().unlink()
        except Exception:
            pass
        return removed
    # year-scoped: fastf1 cache layout varies; remove matching entries + files
    try:
        mp = manifest_path()
        if mp.exists():
            data = json.loads(mp.read_text())
            for k in [k for k in data if str(k).startswith(f"{year}/")]:
                del data[k]
            mp.write_text(json.dumps(data, indent=2))
    except Exception:
        pass
    for p in d.rglob(f"*{year}*"):
        try:
            if p.is_file():
                p.unlink()
                removed += 1
        except Exception:
            continue
    return removed
