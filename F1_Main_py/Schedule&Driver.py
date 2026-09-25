"""
DEPRECATED shim for backward compatibility.
Filename contains '&' which breaks imports. Use schedule_driver.py instead.
TODO: Remove this shim in v2.0 (see TODO.md P0-6).
"""
import warnings

warnings.warn(
    "Importing 'Schedule&Driver' is deprecated — use 'schedule_driver' instead. "
    "This shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)
from F1_Main_py.schedule_driver import *  # noqa: F401,F403
from F1_Main_py.schedule_driver import main, show_driver_lineup, show_schedule  # noqa: F401

if __name__ == "__main__":
    main()
