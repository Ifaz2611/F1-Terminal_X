"""
F1 Practice Session Visualization — thin wrapper over f1_terminal.core
- Supports both legacy interactive and argparse --year --track --session --save --no-show
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import fastf1
import matplotlib.pyplot as plt
import pandas as pd

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

try:
    from f1_terminal.config import CACHE_DIR, FIGURE_DPI, MAX_YEAR, MIN_YEAR, get_logger
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        fastf1.Cache.set_cache_directory(str(CACHE_DIR))
    except AttributeError:
        fastf1.Cache.enable_cache(str(CACHE_DIR))  # type: ignore[attr-defined]
    _logger = get_logger(__name__)
    _HAS_CORE = True
except Exception:
    CACHE_DIR = (Path(__file__).parent.parent / "cache").resolve()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        fastf1.Cache.set_cache_directory(str(CACHE_DIR))
    except AttributeError:
        fastf1.Cache.enable_cache(str(CACHE_DIR))
    FIGURE_DPI = 150  # type: ignore[no-redef]
    MIN_YEAR, MAX_YEAR = 2018, 2030  # type: ignore[no-redef]
    _HAS_CORE = False

try:
    from f1_terminal.tracks import TRACKS  # type: ignore
except ImportError:
    from tracks import TRACKS  # type: ignore

SESSIONS = {
    1: {"code": "FP1", "name": "Practice Session 1"},
    2: {"code": "FP2", "name": "Practice Session 2"},
    3: {"code": "FP3", "name": "Practice Session 3"}
}

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

def display_session_menu():
    print("\n" + "=" * 60)
    print("SELECT PRACTICE SESSION")
    print("=" * 60)
    for num, session in SESSIONS.items():
        print(f"{num}. {session['name']} ({session['code']})")
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

def get_session_selection():
    display_session_menu()
    while True:
        try:
            choice = int(input("\nEnter session number (1-3): ").strip())
            if 1 <= choice <= 3:
                return SESSIONS[choice]
            print("Please enter a number between 1 and 3")
        except ValueError:
            print("Please enter a valid number")

def _get_fastf1_identifier(track) -> str:
    if hasattr(track, 'fastf1_name'):
        return track.fastf1_name
    return track.get('fastf1_name', track.get('country',''))

def _fmt_lap(t):
    if pd.isna(t) or t is None:
        return "N/A"
    try:
        total = t.total_seconds()
        return f"{int(total//60)}:{total%60:06.3f}"
    except Exception:
        return str(t)

def _team_color(session, driver_code, cmap, idx, total):
    if _HAS_CORE:
        try:
            from f1_terminal.core.colors import get_team_color as _gtc
            return _gtc(session, driver_code, cmap, idx, total)
        except Exception:
            pass
    try:
        info = session.get_driver(driver_code)
        col = info.get('TeamColor', None) if hasattr(info,'get') else getattr(info,'TeamColor',None)
        if col is not None:
            if isinstance(col, int):
                return f"#{col:06X}"
            s = str(col).strip().lstrip('#')
            if s:
                return f"#{s}"
    except Exception:
        pass
    return cmap(idx / max(total, 1))

def _plot_practice(session, year: int, track_label: str, session_code: str, save=None, no_show=False):
    laps = session.laps
    if laps is None or laps.empty:
        print("No lap data available for this session.")
        sys.exit(1)
    print(f"\nTotal laps recorded in session: {len(laps)}\n")
    print("=" * 60)
    print(f"{'Driver':<8} {'Team':<15} {'Fastest Lap':<12} {'Lap #':<6}")
    print("=" * 60)
    all_drivers = sorted(laps['Driver'].dropna().unique())
    fig, ax = plt.subplots(figsize=(12, 9), dpi=FIGURE_DPI)
    cmap = plt.get_cmap('tab20')
    legend_entries = []
    for i, driver_code in enumerate(all_drivers):
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
        team_name = "Unknown"
        try:
            info = session.get_driver(driver_code)
            team_name = info.get('TeamName','Unknown') if hasattr(info,'get') else getattr(info,'TeamName','Unknown')
            if not team_name or str(team_name)=='nan':
                team_name="Unknown"
        except Exception:
            pass
        color = _team_color(session, driver_code, cmap, i, len(all_drivers))
        lap_time = fastest_lap['LapTime']
        lap_time_str = _fmt_lap(lap_time)
        lap_number = fastest_lap.get('LapNumber', '?')
        lap_sec = lap_time.total_seconds() if hasattr(lap_time,'total_seconds') else float('inf')
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
        line, = ax.plot(tel['X'], tel['Y'], color=color, linewidth=1.5, alpha=0.85)
        legend_entries.append((line, lap_sec, f"{driver_code} ({lap_time_str})"))
    print("=" * 60)
    ax.set_aspect('equal')
    ax.set_title(f"All Drivers' Fastest Laps - {year} {track_label} GP {session_code}", fontsize=14, fontweight='bold')
    ax.axis('off')
    if legend_entries:
        legend_entries.sort(key=lambda x: x[1])
        ax.legend(handles=[p[0] for p in legend_entries], labels=[p[2] for p in legend_entries], loc='best', fontsize=8, framealpha=0.9, title="Driver (Fastest Lap)", title_fontsize=10)
    plt.tight_layout()
    if save is not None:
        try:
            Path(save).parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(str(save), dpi=FIGURE_DPI, bbox_inches="tight")
            print(f"Saved to {save}")
        except Exception as e:
            print(f"Save failed: {e}")
    if not no_show:
        try:
            plt.show()
        except Exception:
            pass
    plt.close(fig)

def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="F1 Practice Session (core-powered)")
    parser.add_argument("--year", type=int, default=None, help="Season year")
    parser.add_argument("--track", type=str, default=None, help="Track identifier")
    parser.add_argument("--session", type=str, default="FP1", help="Session code FP1/FP2/FP3")
    parser.add_argument("--save", type=str, default=None, help="Save path")
    parser.add_argument("--no-show", action="store_true", help="Do not display")
    return parser.parse_args(argv)

def _run_with_args(args):
    year = args.year if args.year is not None else 2024
    track_arg = args.track
    if track_arg is None:
        print("Missing --track")
        sys.exit(2)
    identifier = track_arg
    country_label = track_arg
    session_code = args.session
    if session_code not in ("FP1","FP2","FP3"):
        print(f"Practice session must be FP1/FP2/FP3, got {session_code}")
        sys.exit(2)
    try:
        t = TRACKS[int(track_arg)]
        identifier = _get_fastf1_identifier(t)
        country_label = t.country if hasattr(t,'country') else str(t)
    except Exception:
        for t in TRACKS.values():
            cand = getattr(t,'fastf1_name','')
            if cand.lower() == track_arg.lower() or getattr(t,'country','').lower()==track_arg.lower():
                identifier = cand
                country_label = getattr(t,'country', track_arg)
                break
    session = None
    if _HAS_CORE:
        try:
            from f1_terminal.core.session import load_session
            wrapper = load_session(year, identifier, session_code)
            session = wrapper.session
        except Exception as e:
            print(f"Failed to load session {year} {track_arg} {session_code}: {e}")
            sys.exit(1)
    else:
        try:
            session = fastf1.get_session(year, identifier, session_code)
            session.load(telemetry=True, laps=True, weather=False)
        except Exception as e:
            print(f"Failed: {e}")
            sys.exit(1)
    _plot_practice(session, year, country_label, session_code, save=args.save, no_show=args.no_show)

def main(argv=None):
    raw = argv if argv is not None else sys.argv[1:]
    has_cli = len(raw) > 0
    if has_cli:
        try:
            args = _parse_args(argv)
        except SystemExit:
            raise
        _run_with_args(args)
        return
    if argv is None and len(sys.argv) == 1:
        print("\n" + "=" * 60)
        print("F1 PRACTICE SESSION TRACK VISUALIZATION")
        print("=" * 60)
        year = get_year()
        track = get_track_selection()
        session_type = get_session_selection()
        identifier = _get_fastf1_identifier(track)
        country_label = track.country if hasattr(track,'country') else track.get('country','')
        print(f"\nLoading: {year} {country_label} GP - {session_type['name']}")
        print("This may take a moment...")
        try:
            session = fastf1.get_session(year, identifier, session_type['code'])
            session.load(telemetry=True, laps=True, weather=False)
        except fastf1.core.DataNotLoadedError as e:
            print(f"Failed to load session data: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error loading session: {e}")
            sys.exit(1)
        _plot_practice(session, year, country_label, session_type['code'])
        return
    try:
        args = _parse_args(argv if argv is not None else [])
        if args.track is None:
            print("Use --track; --help for usage")
        else:
            _run_with_args(args)
    except SystemExit:
        raise

if __name__ == "__main__":
    main()
