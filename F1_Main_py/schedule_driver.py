"""
Schedule & Driver Viewer — fixed edition.
- Lazy schedule loading (no network on import)
- Cache compatible with fastf1 3.x + fallback
- No top-level blocking input loops (guarded by __main__)
- Robust driver dict access
"""
from __future__ import annotations

import warnings
from pathlib import Path

import fastf1

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

YEAR = 2026
CACHE_DIR = Path(__file__).parent.parent / "cache"

def setup_cache() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        fastf1.Cache.set_cache_directory(str(CACHE_DIR))
    except AttributeError:
        fastf1.Cache.enable_cache(str(CACHE_DIR))

setup_cache()

def _get_schedule():
    try:
        return fastf1.get_event_schedule(YEAR)
    except Exception as e:
        print(f"Failed to fetch {YEAR} schedule: {e}")
        return None

def show_schedule() -> None:
    schedule = _get_schedule()
    if schedule is None or schedule.empty:
        print("No schedule available.")
        return
    print("\n" + "=" * 90)
    print(f"FORMULA 1 {YEAR} SEASON SCHEDULE")
    print("=" * 90)
    print(f"{'Round':<8}{'Country':<20}{'Grand Prix':<40}{'Date'}")
    print("-" * 90)
    for _, race in schedule.iterrows():
        try:
            date_str = race['EventDate'].date() if hasattr(race['EventDate'], 'date') else str(race['EventDate'])
        except Exception:
            date_str = str(race.get('EventDate', ''))
        print(f"{race['RoundNumber']:<8}{str(race.get('Country','')):<20}{str(race.get('EventName','')):<40}{date_str}")

def _get_driver_field(driver, key: str, default: str = "Unknown") -> str:
    """Handle both Series/dict and attribute access for fastf1 driver objects."""
    # Try dict / Series access
    try:
        val = driver[key] if key in driver else None
        if val is not None and str(val) != "nan" and str(val).strip():
            return str(val)
    except Exception:
        pass
    # Try attribute
    try:
        val = getattr(driver, key, None)
        if val is not None and str(val) != "nan" and str(val).strip():
            return str(val)
    except Exception:
        pass
    # Try get
    try:
        val = driver.get(key, None)
        if val is not None and str(val) != "nan":
            return str(val)
    except Exception:
        pass
    return default

def show_driver_lineup() -> None:
    schedule = _get_schedule()
    if schedule is None or schedule.empty:
        print("Cannot load schedule.")
        return
    try:
        raw = input("\nEnter Round Number: ").strip()
        round_number = int(raw)
        match = schedule[schedule["RoundNumber"] == round_number]
        if match.empty:
            print("Invalid Round Number! No such round.")
            return
        event = match.iloc[0]
    except ValueError:
        print("Invalid Round Number! Please enter a number.")
        return
    except Exception as e:
        print(f"Invalid Round Number! {e}")
        return

    print(f"\nLoading {event['EventName']} ...")
    session = fastf1.get_session(YEAR, event["EventName"], "R")
    try:
        session.load()
    except Exception as e:
        print("Unable to load session.")
        print(e)
        return

    print("\n" + "=" * 70)
    print(f"{event['EventName']} DRIVER LINEUP")
    print("=" * 70)

    for code in session.drivers:
        try:
            driver = session.get_driver(code)
        except Exception as e:
            print(f"\nCode {code}: failed to load driver info ({e})")
            continue
        broadcast = _get_driver_field(driver, "BroadcastName", str(code))
        num = _get_driver_field(driver, "DriverNumber", str(code))
        team = _get_driver_field(driver, "TeamName", "Unknown")
        color = _get_driver_field(driver, "TeamColor", "000000").lstrip("#")
        print(f"\nDriver Name : {broadcast}")
        print(f"Code        : {code}")
        print(f"Number      : {num}")
        print(f"Team        : {team}")
        print(f"Team Color  : #{color}")


def main() -> None:
    while True:
        print("\n" + "=" * 45)
        print("       FORMULA 1 DATA VIEWER")
        print("=" * 45)
        print("1. View Full Season Schedule")
        print("2. View Driver Lineup")
        print("3. Exit")
        choice = input("\nSelect Option: ").strip()
        if choice == "1":
            show_schedule()
        elif choice == "2":
            show_driver_lineup()
        elif choice == "3":
            print("\nThank you for using Formula 1 Data Viewer!")
            break
        else:
            print("Invalid option! Please try again.")

if __name__ == "__main__":
    main()
