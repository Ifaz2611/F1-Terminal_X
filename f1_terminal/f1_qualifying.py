"""
F1 Qualifying Session Visualization — fixed edition
- FastF1 3.x cache compat
- Unified TRACKS import to fix ambiguous country lookups (Spain/USA duplicates)
- Robust team color handling (strip '#', int vs str)
- Numeric lap-time sorting for legend (not lexicographic)
- Error handling for session.load()
- NaN telemetry filtering
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import fastf1
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# ── Cache setup (fastf1 3.x compat) ──────────────────────────────────────────
CACHE_DIR = (Path(__file__).parent.parent / "cache").resolve()
CACHE_DIR.mkdir(parents=True, exist_ok=True)
try:
    fastf1.Cache.set_cache_directory(str(CACHE_DIR))
except AttributeError:
    fastf1.Cache.enable_cache(str(CACHE_DIR))

# ── Track DB: import canonical source ────────────────────────────────────────
try:
    from f1_terminal.tracks import TRACKS  # type: ignore
except ImportError:
    # Fallback if run as script: load local
    from tracks import TRACKS  # type: ignore

# Back-compat: some code expects dict-of-dicts; TRACKS is Dict[int, Track] dataclass now
def _track_to_dict(t):
    try:
        return {"country": t.country, "city": t.city, "name": t.name, "fastf1_name": t.fastf1_name}
    except AttributeError:
        return dict(t)

#==========================================Menu Functions=========================================
def display_track_menu():
    print("\n" + "=" * 60)
    print("SELECT A TRACK")
    print("=" * 60)
    for num, track in TRACKS.items():
        c = track.country if hasattr(track, 'country') else track['country']
        city = track.city if hasattr(track, 'city') else track['city']
        name = track.name if hasattr(track, 'name') else track['name']
        print(f"{num:>2}. {c:<15} - {city:<15} ({name})")
    print("=" * 60)

def get_year():
    while True:
        try:
            year = int(input("\nEnter year (e.g., 2024): ").strip())
            if 2018 <= year <= 2030:
                return year
            print("Please enter a valid year (2018-2030)")
        except ValueError:
            print("Please enter a valid number")

def get_track_selection():
    display_track_menu()
    while True:
        try:
            choice = int(input("\nEnter track number (1-22): ").strip())
            if 1 <= choice <= 22:
                return TRACKS[choice]
            print("Please enter a number between 1 and 22")
        except ValueError:
            print("Please enter a valid number")

def _get_fastf1_identifier(track) -> str:
    """Resolve unique fastf1 identifier (fixes Spain/USA duplicates)."""
    if hasattr(track, 'fastf1_name'):
        return track.fastf1_name
    return track.get('fastf1_name', track.get('country', ''))

def _fmt_lap(t):
    if pd.isna(t) or t is None:
        return "N/A"
    # Timedelta -> M:SS.mmm
    try:
        total = t.total_seconds()
        return f"{int(total//60)}:{total%60:06.3f}"
    except Exception:
        return str(t)

def _team_color(session, driver_code, cmap, idx, total):
    try:
        info = session.get_driver(driver_code)
        col = info.get('TeamColor', None) if hasattr(info, 'get') else getattr(info, 'TeamColor', None)
        if col is not None:
            if isinstance(col, int):
                return f"#{col:06X}"
            s = str(col).strip().lstrip('#')
            if s:
                return f"#{s}"
    except Exception:
        pass
    return cmap(idx / max(total, 1))

#==========================================Main Program=========================================
def main():
    print("\n" + "=" * 60)
    print("F1 QUALIFYING SESSION TRACK VISUALIZATION")
    print("=" * 60)
    
    year = get_year()
    track = get_track_selection()
    identifier = _get_fastf1_identifier(track)
    country_label = track.country if hasattr(track, 'country') else track.get('country','')
    
    print(f"\nLoading: {year} {country_label} GP - Qualifying Session")
    print("This may take a moment...")
    
    try:
        session = fastf1.get_session(year, identifier, 'Q')
        session.load(telemetry=True, laps=True, weather=False)
    except fastf1.core.DataNotLoadedError as e:
        print(f"Failed to load session data: {e}")
        print("   Session may not have occurred yet or data is unavailable.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error loading session: {e}")
        sys.exit(1)
    
    laps = session.laps
    if laps is None or laps.empty:
        print("No lap data available for this session.")
        sys.exit(1)

    print(f"\nTotal laps recorded in session: {len(laps)}\n")
    print("=" * 60)
    print(f"{'Driver':<8} {'Team':<15} {'Fastest Lap':<12} {'Lap #':<6}")
    print("=" * 60)
    
    all_drivers = sorted(laps['Driver'].dropna().unique())
    fig, ax = plt.subplots(figsize=(12, 9))
    cmap = plt.get_cmap('tab20')
    
    legend_entries = []  # list of (line, lap_seconds, label)
    
    for i, driver_code in enumerate(all_drivers):
        # robust driver laps
        try:
            driver_laps = laps.pick_drivers(driver_code)
            if driver_laps.empty and hasattr(laps, 'pick_driver'):
                driver_laps = laps.pick_driver(driver_code)
        except Exception:
            driver_laps = laps[laps['Driver'] == driver_code]

        if driver_laps.empty:
            continue
        try:
            fastest_lap = driver_laps.pick_fastest()
        except Exception:
            fastest_lap = None
            try:
                valid = driver_laps.dropna(subset=['LapTime'])
                if not valid.empty:
                    fastest_lap = valid.loc[valid['LapTime'].idxmin()]
            except Exception:
                pass
        
        if fastest_lap is None or pd.isna(fastest_lap.get('LapTime')):
            print(f"{driver_code:<8} {'---':<15} {'No valid lap':<12} {'---':<6}")
            continue
        
        # team info robust
        team_name = "Unknown"
        try:
            info = session.get_driver(driver_code)
            team_name = info.get('TeamName', 'Unknown') if hasattr(info,'get') else getattr(info,'TeamName','Unknown')
            if not team_name or str(team_name) == 'nan':
                team_name = "Unknown"
        except Exception:
            pass
        color = _team_color(session, driver_code, cmap, i, len(all_drivers))
        
        lap_time = fastest_lap['LapTime']
        lap_time_str = _fmt_lap(lap_time)
        lap_number = fastest_lap.get('LapNumber', '?')
        lap_sec = lap_time.total_seconds() if hasattr(lap_time, 'total_seconds') else float('inf')
        print(f"{driver_code:<8} {team_name:<15} {lap_time_str:<12} {lap_number:<6}")
        
        try:
            telemetry = fastest_lap.get_telemetry()
        except Exception as e:
            print(f"  -> telemetry error for {driver_code}: {e}")
            continue
        if telemetry is None or telemetry.empty:
            continue
        if 'X' not in telemetry.columns or 'Y' not in telemetry.columns:
            continue
        tel = telemetry.dropna(subset=['X','Y'])
        if tel.empty:
            continue
        
        line, = ax.plot(tel['X'], tel['Y'],
                        color=color,
                        linewidth=1.5,
                        alpha=0.85,
                        label=f"{driver_code} ({lap_time_str})")
        legend_entries.append((line, lap_sec, f"{driver_code} ({lap_time_str})"))
    
    print("=" * 60)
    
    ax.set_aspect('equal')
    cname = country_label
    ax.set_title(f"All Drivers' Fastest Laps - {year} {cname} GP Qualifying",
                 fontsize=14, fontweight='bold')
    ax.axis('off')
    
    if legend_entries:
        # Sort numerically by lap time
        legend_entries.sort(key=lambda x: x[1])
        ax.legend(
            handles=[p[0] for p in legend_entries],
            labels=[p[2] for p in legend_entries],
            loc='best',
            fontsize=8,
            framealpha=0.9,
            title="Driver (Fastest Lap)",
            title_fontsize=10
        )
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
