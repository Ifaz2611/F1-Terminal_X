"""
Central configuration for F1 Terminal X.

Single source of truth for cache dir, figure DPI, year range, log level, etc.
Replaces hardcoded constants previously scattered across modules.

Usage:
    from f1_terminal.config import settings, get_logger
    logger = get_logger(__name__)
    logger.info("Loading %s %s ...", year, track)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    HAS_PYDANTIC_SETTINGS = True
except ImportError:  # pragma: no cover - fallback if pydantic-settings missing
    from pydantic import BaseSettings  # type: ignore[no-redef,attr-defined]

    SettingsConfigDict = dict  # type: ignore[misc,assignment]
    HAS_PYDANTIC_SETTINGS = False


def _default_cache_dir() -> Path:
    """Resolve cache dir relative to project root, not cwd."""
    # f1_terminal/config.py -> project root is parent of f1_terminal
    return (Path(__file__).parent.parent / "cache").resolve()


if HAS_PYDANTIC_SETTINGS:

    class Settings(BaseSettings):  # type: ignore[no-redef]
        """Application settings with env overrides (prefix F1_)."""

        # Core paths / constants
        cache_dir: Path = _default_cache_dir()
        figure_dpi: int = 150
        min_year: int = 2018
        max_year: int = 2030
        default_season: int = 2026

        # Logging
        log_level: str = "INFO"
        log_format: str = "%(message)s"

        # Optional overrides
        verbose: bool = False

        model_config = SettingsConfigDict(env_prefix="F1_", env_file=".env", extra="ignore")

else:

    class Settings(BaseSettings):  # type: ignore[no-redef]
        """Application settings with env overrides (prefix F1_)."""

        # Core paths / constants
        cache_dir: Path = _default_cache_dir()
        figure_dpi: int = 150
        min_year: int = 2018
        max_year: int = 2030
        default_season: int = 2026

        # Logging
        log_level: str = "INFO"
        log_format: str = "%(message)s"

        # Optional overrides
        verbose: bool = False

        class Config:
            env_prefix = "F1_"
            env_file = ".env"


# Singleton
settings = Settings()

# Ensure cache_dir is resolved
try:
    settings.cache_dir = settings.cache_dir.resolve()
except Exception:
    pass


def _get_rich_handler() -> Optional[logging.Handler]:
    """Return RichHandler if rich is installed, else None."""
    try:
        from rich.logging import RichHandler  # type: ignore[import-not-found]

        return RichHandler(
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
    except Exception:
        return None


def get_logger(name: str) -> logging.Logger:
    """Get a logger with RichHandler when available.

    Callers should use ``logger.info("Loading %s %s", year, track)``
    style (lazy formatting) instead of ``print()``.
    """
    logger = logging.getLogger(name)
    # Avoid duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    level_name = os.getenv("F1_LOG_LEVEL", settings.log_level).upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = _get_rich_handler()
    if handler is None:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(settings.log_format)
        handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if settings.verbose else level)
    logger.propagate = False
    return logger


def setup_logging(verbose: bool = False, level: Optional[str] = None) -> None:
    """Configure root logging.

    Args:
        verbose: If True, set level to DEBUG.
        level: Override log level name (e.g. "DEBUG", "WARNING").
    """
    if verbose:
        settings.verbose = True

    resolved_level = "DEBUG" if verbose else (level or settings.log_level)
    # Reconfigure root handlers
    root = logging.getLogger()
    # Remove existing handlers to avoid duplicates
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = _get_rich_handler()
    if handler is None:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(settings.log_format))

    root.addHandler(handler)
    try:
        root.setLevel(getattr(logging, resolved_level.upper(), logging.INFO))
    except Exception:
        root.setLevel(logging.INFO)

    # Also align f1_terminal loggers
    for name in ("f1_terminal", "F1_Main_py"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.addHandler(handler)
        lg.setLevel(root.level)
        lg.propagate = True


# Convenience re-exports for legacy code
CACHE_DIR: Path = settings.cache_dir
FIGURE_DPI: int = settings.figure_dpi
MIN_YEAR: int = settings.min_year
MAX_YEAR: int = settings.max_year
YEAR_RANGE: tuple[int, int] = (settings.min_year, settings.max_year)
