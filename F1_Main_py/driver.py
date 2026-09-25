"""
Formula 1 Data Analyzer — fixed edition
- No top-level execution on import (guarded by __main__)
- fastf1 3.x cache compatible
- Robust driver object handling (dict / Series / attribute)
- Safe plotting with NaN filtering
"""
from __future__ import annotations

import warnings
from pathlib import Path

import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# ----------------------------------------
# INITIAL SETUP
# ----------------------------------------
CACHE_DIR = (Path(__file__).parent.parent / "cache").resolve()

def setup_cache() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        fastf1.Cache.set_cache_directory(str(CACHE_DIR))
    except AttributeError:
        fastf1.Cache.enable_cache(str(CACHE_DIR))

setup_cache()
try:
    fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme='fastf1')
except Exception:
    try:
        fastf1.plotting.setup_mpl()
    except Exception:
        pass

# Global session data – initially empty
session = None
laps = None

# ----------------------------------------
# HELPERS
# ----------------------------------------
def _get_driver_field(driver, key: str, default: str = "Unknown") -> str:
    """Robust field extraction for fastf1 driver objects."""
    for accessor in (
        lambda d, k: d[k] if k in d else None,
        lambda d, k: d.get(k, None) if hasattr(d, "get") else None,
        lambda d, k: getattr(d, k, None),
    ):
        try:
            val = accessor(driver, key)
            if val is not None and str(val) != "nan" and str(val).strip():
                return str(val)
        except Exception:
            continue
    return default

def _resolve_driver_laps(target_laps: pd.DataFrame, code: str) -> pd.DataFrame:
    """Try pick_drivers / pick_driver with fallback."""
    if target_laps is None or target_laps.empty:
        return target_laps
    for method in ("pick_drivers", "pick_driver"):
        try:
            fn = getattr(target_laps, method)
            result = fn(code)
            if result is not None and not result.empty:
                return result
            # also try list form
            if method == "pick_drivers":
                result = fn([code])
                if result is not None and not result.empty:
                    return result
        except Exception:
            continue
    # fallback manual filter
    try:
        return target_laps[target_laps['Driver'] == code]
    except Exception:
        return target_laps.iloc[0:0]

# ----------------------------------------
# RACE SELECTION (YEAR + GRAND PRIX)
# ----------------------------------------
def select_race():
    global session, laps

    while True:
        try:
            yr = input("\nEnter F1 season year (e.g., 2024): ").strip()
            year = int(yr)
            if year < 2018 or year > 2026:
                print("Please enter a year between 2018 and 2026.")
                continue
            break
        except ValueError:
            print("Invalid year. Enter a number.")

    try:
        schedule = fastf1.get_event_schedule(year)
    except Exception as e:
        print(f"Error fetching schedule for {year}: {e}")
        return

    events = schedule[['RoundNumber', 'EventName', 'Location', 'EventDate']].copy()
    try:
        events['EventDate'] = pd.to_datetime(events['EventDate']).dt.strftime('%Y-%m-%d')
    except Exception:
        pass

    print(f"\n--- {year} F1 Grand Prix Calendar ---")
    for idx, row in events.iterrows():
        print(f"{idx+1:2d}. {row['EventName']:<30}  {row['Location']:<20}  {row['EventDate']}")

    while True:
        try:
            choice = input("\nEnter the number of the Grand Prix: ").strip()
            choice_idx = int(choice) - 1
            if choice_idx < 0 or choice_idx >= len(events):
                print("Invalid selection. Pick a number from the list.")
                continue
            break
        except ValueError:
            print("Please enter a number.")

    event_name = events.iloc[choice_idx]['EventName']

    print(f"\nLoading {year} {event_name} GP...")
    try:
        event = fastf1.get_event(year, event_name)
        session = event.get_race()
        session.load()
        laps = session.laps
        if laps is None or laps.empty:
            print("Warning: No lap data returned for this session.")
        else:
            print("Session loaded successfully!\n")
    except Exception as e:
        print(f"Error loading session: {e}")
        session = None
        laps = None

# ----------------------------------------
# MENU FUNCTIONS
# ----------------------------------------
def show_schedule():
    print("\n" + "=" * 70)
    print("FULL SEASON SCHEDULE")
    print("=" * 70)
    try:
        year = int(input("Enter year for schedule: ").strip())
    except ValueError:
        print("Invalid year.")
        return
    try:
        schedule = fastf1.get_event_schedule(year)
    except Exception as e:
        print(f"Failed to load schedule: {e}")
        return
    cols = [c for c in ['RoundNumber', 'Country', 'Location', 'OfficialEventName', 'EventDate'] if c in schedule.columns]
    try:
        print(schedule[cols].to_string(index=False))
    except Exception as e:
        print(f"Error displaying schedule: {e}")

def show_driver_lineup():
    if session is None:
        print("\nNo session loaded! Please select a race first (Option 0).")
        return
    print("\n" + "=" * 70)
    print("DRIVER LINEUP")
    print("=" * 70)
    for code in session.drivers:
        try:
            driver = session.get_driver(code)
        except Exception as e:
            print(f"\n{code}: failed to load ({e})")
            continue
        name = _get_driver_field(driver, "BroadcastName", str(code))
        num = _get_driver_field(driver, "DriverNumber", str(code))
        team = _get_driver_field(driver, "TeamName", "Unknown")
        color = _get_driver_field(driver, "TeamColor", "000000").lstrip("#")
        print(f"\n{name}")
        print(f"Number : {num}")
        print(f"Team   : {team}")
        print(f"Color  : #{color}")

def tire_strategy():
    if session is None or laps is None:
        print("\nNo session loaded! Please select a race first (Option 0).")
        return
    COMPOUND_COLORS = getattr(
        fastf1.plotting, 'COMPOUND_COLORS',
        {
            'SOFT': '#FF3333', 'MEDIUM': '#FFD700', 'HARD': '#FFFFFF',
            'INTERMEDIATE': '#39B54A', 'WET': '#00AEEF', 'UNKNOWN': '#888888'
        }
    )
    fig, ax = plt.subplots(figsize=(12, 8))
    active_drivers = [d for d in session.drivers if len(_resolve_driver_laps(laps, d)) > 5]
    if not active_drivers:
        print("Not enough lap data for tire strategy.")
        plt.close(fig)
        return
    for driver in active_drivers:
        dlaps = _resolve_driver_laps(laps, driver)
        if dlaps.empty:
            continue
        compounds = dlaps['Compound'].fillna('UNKNOWN') if 'Compound' in dlaps.columns else pd.Series(['UNKNOWN']*len(dlaps))
        colors = [COMPOUND_COLORS.get(str(c).upper(), '#888888') for c in compounds]
        lap_nums = dlaps['LapNumber'] if 'LapNumber' in dlaps.columns else range(len(dlaps))
        ax.scatter(lap_nums, [driver]*len(dlaps), c=colors, s=80, edgecolors='black', linewidths=0.5)
    ax.set_title("Tire Strategy")
    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Driver")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def speed_trace():
    if session is None or laps is None:
        print("\nNo session loaded! Please select a race first (Option 0).")
        return
    driver = input("\nEnter Driver Code (e.g., VER/NOR/LEC/HAM or number): ").strip().upper()
    if not driver:
        print("No driver entered.")
        return
    driver_laps = _resolve_driver_laps(laps, driver)
    if driver_laps.empty:
        print("Driver not found!")
        return
    try:
        fastest = driver_laps.pick_fastest()
    except Exception:
        # fallback: smallest LapTime
        try:
            valid = driver_laps.dropna(subset=['LapTime'])
            fastest = valid.loc[valid['LapTime'].idxmin()] if not valid.empty else None
        except Exception:
            fastest = None
    if fastest is None or pd.isna(fastest.get('LapTime', None)):
        print("No fastest lap found.")
        return
    try:
        telemetry = fastest.get_telemetry()
    except Exception as e:
        print(f"Failed to get telemetry: {e}")
        return
    if telemetry is None or telemetry.empty:
        print("No telemetry data.")
        return
    if 'X' not in telemetry.columns or 'Y' not in telemetry.columns:
        print("Position data not available for this lap.")
        return
    # Filter NaNs
    tel = telemetry.dropna(subset=['X', 'Y']).copy()
    if tel.empty:
        print("No valid position data.")
        return
    fig, ax = plt.subplots(figsize=(10, 8))
    points = tel[['X', 'Y']].values.reshape(-1, 1, 2)
    if len(points) < 2:
        print("Not enough telemetry points.")
        plt.close(fig)
        return
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    speed = tel['Speed'] if 'Speed' in tel.columns else pd.Series([0]*len(tel))
    speed = speed.fillna(0)
    norm = plt.Normalize(speed.min(), speed.max() if speed.max() != speed.min() else speed.max()+1)
    lc = LineCollection(segments, cmap='plasma', norm=norm, linewidth=3)
    lc.set_array(speed.values[:-1] if len(speed) > 1 else speed.values)
    ax.add_collection(lc)
    plt.colorbar(lc, ax=ax, label='Speed (km/h)')
    ax.set_aspect('equal')
    ax.autoscale()
    plt.axis('off')
    plt.title(f"{driver} Fastest Lap Speed Trace")
    plt.tight_layout()
    plt.show()

def pace_comparison():
    if session is None or laps is None:
        print("\nNo session loaded! Please select a race first (Option 0).")
        return
    d1 = input("Driver 1: ").strip().upper()
    d2 = input("Driver 2: ").strip().upper()
    if not d1 or not d2:
        print("Please enter two driver codes.")
        return
    laps1 = _resolve_driver_laps(laps, d1)
    laps2 = _resolve_driver_laps(laps, d2)
    if laps1.empty or laps2.empty:
        print("Invalid driver code(s).")
        return
    fig, ax = plt.subplots(figsize=(12, 6))
    for dlaps, label in [(laps1, d1), (laps2, d2)]:
        valid = dlaps.dropna(subset=['LapTime']).copy()
        if valid.empty or 'LapNumber' not in valid.columns:
            print(f"No valid lap times for {label}")
            continue
        # filter out pit in/out laps for cleaner comparison
        if 'PitInTime' in valid.columns and 'PitOutTime' in valid.columns:
            valid = valid[valid['PitInTime'].isna() & valid['PitOutTime'].isna()]
        lap_times = valid['LapTime'].dt.total_seconds()
        lap_times = lap_times[lap_times < lap_times.quantile(0.95) * 1.2]  # filter outliers
        ax.plot(valid.loc[lap_times.index, 'LapNumber'], lap_times, label=label, marker='o', markersize=3, linewidth=1.2)
    ax.set_title("Race Pace Comparison")
    ax.set_xlabel("Lap")
    ax.set_ylabel("Lap Time (s)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    # pretty y-axis
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda s, _: f"{int(s//60)}:{s%60:05.2f}"))
    plt.tight_layout()
    plt.show()

# ----------------------------------------
# MAIN MENU
# ----------------------------------------
def main():
    while True:
        print("\n" + "=" * 50)
        print("FORMULA 1 DATA ANALYZER")
        print("=" * 50)
        print("0. Select Race (choose year & Grand Prix)")
        print("1. Full Season Schedule")
        print("2. Driver Lineup (current session)")
        print("3. Tire Strategy (current session)")
        print("4. Speed Trace (current session)")
        print("5. Pace Comparison (current session)")
        print("6. Exit")
        choice = input("\nSelect Option: ").strip()
        if choice == "0":
            select_race()
        elif choice == "1":
            show_schedule()
        elif choice == "2":
            show_driver_lineup()
        elif choice == "3":
            tire_strategy()
        elif choice == "4":
            speed_trace()
        elif choice == "5":
            pace_comparison()
        elif choice == "6":
            print("\nGoodbye! Future F1 Engineer")
            break
        else:
            print("\nInvalid option. Try again, buddy.")

if __name__ == "__main__":
    main()
