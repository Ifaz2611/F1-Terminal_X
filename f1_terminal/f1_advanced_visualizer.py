#!/usr/bin/env python3
"""
F1 Main Race Session Track Visualization — Advanced Edition
============================================================
Production-grade script with full error handling, telemetry analysis,
interactive plotting, sector comparisons, and race strategy overlays.


"""
import argparse
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import fastf1
import fastf1.plotting
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection

try:
    from f1_terminal.config import FIGURE_DPI as _CORE_DPI
    from f1_terminal.config import get_logger as _get_logger
    from f1_terminal.core.colors import get_team_color as _core_get_team_color
    from f1_terminal.core.session import load_session as _core_load_session

    _HAS_CORE = True
    _logger = _get_logger(__name__)
except Exception:
    _HAS_CORE = False
    _CORE_DPI = 150
    _logger = None

# ── Suppress non-critical warnings ─────────────────────────────────────────
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# ── Configuration ──────────────────────────────────────────────────────────
# Unified cache dir (project_root/cache) so all scripts share cache — now via config
try:
    from f1_terminal.config import CACHE_DIR as _CFG_CACHE_DIR
    from f1_terminal.config import FIGURE_DPI as _CFG_DPI
    from f1_terminal.config import MAX_YEAR as _CFG_MAX
    from f1_terminal.config import MIN_YEAR as _CFG_MIN

    CACHE_DIR = _CFG_CACHE_DIR
    FIGURE_DPI = _CFG_DPI
    MIN_YEAR, MAX_YEAR = _CFG_MIN, _CFG_MAX
except Exception:
    CACHE_DIR = (Path(__file__).parent.parent / 'cache').resolve()
    MIN_YEAR, MAX_YEAR = 2018, 2030
    FIGURE_DPI = _CORE_DPI if '_CORE_DPI' in dir() else 150

# ── Track Database (canonical) ───────────────────────────────────────────
# Use canonical tracks.py; fallback to inline if import fails (e.g. run as isolated script)
try:
    from f1_terminal.tracks import TRACKS, Track  # type: ignore
except ImportError:
    try:
        from tracks import TRACKS, Track  # type: ignore
    except ImportError:
        @dataclass(frozen=True)
        class Track:  # type: ignore[no-redef]
            round_num: int
            country: str
            city: str
            name: str
            fastf1_name: str

        TRACKS: Dict[int, Track] = {
            1:  Track(1,  "Australia",     "Melbourne",       "Albert Park",                  "Australia"),
            2:  Track(2,  "China",         "Shanghai",        "Shanghai International Circuit", "China"),
            3:  Track(3,  "Japan",         "Suzuka",          "Suzuka",                       "Japan"),
            4:  Track(4,  "USA",           "Miami",           "Miami International Autodrome","Miami"),
            5:  Track(5,  "Canada",        "Montreal",        "Circuit Gilles Villeneuve",    "Canada"),
            6:  Track(6,  "Monaco",        "Monaco",          "Monaco",                       "Monaco"),
            7:  Track(7,  "Spain",         "Barcelona",       "Circuit de Catalunya",         "Spain"),
            8:  Track(8,  "Austria",       "Spielberg",       "Red Bull Ring",                "Austria"),
            9:  Track(9,  "Great Britain", "Silverstone",     "Silverstone",                  "Great Britain"),
            10: Track(10, "Belgium",       "Spa-Francorchamps","Spa-Francorchamps",           "Belgium"),
            11: Track(11, "Hungary",       "Budapest",        "Hungaroring",                  "Hungary"),
            12: Track(12, "Netherlands",   "Zandvoort",       "Zandvoort",                    "Netherlands"),
            13: Track(13, "Italy",         "Monza",           "Monza",                        "Italy"),
            14: Track(14, "Spain",         "Madrid",          "Madring",                      "Spain"),
            15: Track(15, "Azerbaijan",    "Baku",            "Baku City Circuit",            "Azerbaijan"),
            16: Track(16, "Singapore",     "Singapore",       "Singapore",                    "Singapore"),
            17: Track(17, "USA",           "Austin",          "Circuit of the Americas",      "United States"),
            18: Track(18, "Mexico",        "Mexico City",     "Mexico City",                  "Mexico"),
            19: Track(19, "Brazil",        "São Paulo",       "Interlagos",                   "Brazil"),
            20: Track(20, "USA",           "Las Vegas",       "Las Vegas Strip Circuit",      "Las Vegas"),
            21: Track(21, "Qatar",         "Lusail",          "Lusail",                       "Qatar"),
            22: Track(22, "Abu Dhabi",     "Yas Marina",      "Yas Marina",                   "Abu Dhabi"),
        }

# ── Color & Style Setup ──────────────────────────────────────────────────
fastf1.plotting.setup_mpl(mpl_timedelta_support=True, color_scheme='fastf1')

# ── Helper Functions ─────────────────────────────────────────────────────
def _setup_cache() -> None:
    """Initialize fastf1 cache directory."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        # fastf1 v3.x: use Cache class directly
        fastf1.Cache.set_cache_directory(str(CACHE_DIR))
    except AttributeError:
        # Fallback for older versions
        fastf1.Cache.enable_cache(str(CACHE_DIR))


def _fmt_laptime(td: Optional[pd.Timedelta]) -> str:
    """Format a Timedelta as M:SS.mmm string."""
    if pd.isna(td) or td is None:
        return "N/A"
    total_seconds = td.total_seconds()
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:06.3f}"


def _fmt_laptime_seconds(td: Optional[pd.Timedelta]) -> float:
    """Convert Timedelta to total seconds for sorting."""
    if pd.isna(td) or td is None:
        return float('inf')
    return td.total_seconds()


def _get_team_color(session, driver_code: str, fallback_cmap, idx: int, total: int) -> str:
    """Safely extract team color — delegates to core.colors.get_team_color."""
    if _HAS_CORE:
        try:
            return _core_get_team_color(session, driver_code, fallback_cmap, idx, total)
        except Exception:
            pass
    try:
        driver_info = session.get_driver(driver_code)
        # handle both dict/Series and attribute access
        if hasattr(driver_info, 'get'):
            team_color = driver_info.get('TeamColor', None)
        else:
            team_color = getattr(driver_info, 'TeamColor', None)
        if team_color is not None:
            if isinstance(team_color, int):
                return f"#{team_color:06X}"
            s = str(team_color).strip().lstrip('#')
            if s and s.lower() != 'nan':
                # fastf1 sometimes returns int as string without leading zeros
                if s.isdigit():
                    try:
                        return f"#{int(s):06X}"
                    except Exception:
                        pass
                return f"#{s}"
    except Exception:
        pass
    # fallback_cmap returns RGBA tuple; convert to hex
    rgba = fallback_cmap(idx / max(total, 1))
    try:
        import matplotlib.colors as mcolors
        return mcolors.to_hex(rgba)
    except Exception:
        return f"#{int(rgba[0]*255):02X}{int(rgba[1]*255):02X}{int(rgba[2]*255):02X}"


def _input_int(prompt: str, min_val: int, max_val: int) -> int:
    """Robust integer input with validation."""
    while True:
        try:
            val = int(input(prompt).strip())
            if min_val <= val <= max_val:
                return val
            print(f"  ⚠ Please enter a number between {min_val} and {max_val}")
        except ValueError:
            print("  ⚠ Invalid input. Please enter a valid number.")


def _input_year() -> int:
    """Get validated year input."""
    return _input_int(f"\nEnter year ({MIN_YEAR}-{MAX_YEAR}): ", MIN_YEAR, MAX_YEAR)


# ── Visualization Classes ────────────────────────────────────────────────
class TrackVisualizer:
    """Handles all telemetry visualization with multiple analysis modes."""

    def __init__(self, session, year: int, track: Track):
        self.session = session
        self.year = year
        self.track = track
        self.laps = session.laps
        self.all_drivers = sorted(self.laps['Driver'].dropna().unique())
        self.cmap = plt.get_cmap('tab20')
        self._driver_colors: Dict[str, str] = {}
        self._compute_driver_colors()

    def _compute_driver_colors(self) -> None:
        """Pre-compute consistent colors for all drivers."""
        for i, drv in enumerate(self.all_drivers):
            self._driver_colors[drv] = _get_team_color(
                self.session, drv, self.cmap, i, len(self.all_drivers)
            )

    def _get_fastest_lap_data(self, driver_code: str) -> Optional[Tuple[pd.Series, pd.DataFrame]]:
        """
        Safely retrieve a driver's fastest lap and its telemetry.
        Returns (fastest_lap_series, telemetry_df) or None if unavailable.
        """
        try:
            driver_laps = self.laps.pick_driver(driver_code)
            if driver_laps.empty:
                return None

            fastest = driver_laps.pick_fastest()
            if fastest is None or pd.isna(fastest.get('LapTime')):
                return None

            # get_telemetry() is available on the Series because fastf1
            # extends pandas Series with custom methods for lap objects.
            telemetry = fastest.get_telemetry()
            if telemetry is None or telemetry.empty:
                return None

            return fastest, telemetry
        except Exception:
            return None

    def _print_driver_summary(self) -> List[Tuple[str, pd.Series, pd.DataFrame, str]]:
        """
        Print formatted driver summary table and return valid telemetry entries.
        Returns list of (driver_code, fastest_lap, telemetry, team_name).
        """
        print(f"\n{'='*70}")
        print(f"{'Driver':<8} {'Team':<18} {'Fastest Lap':<14} {'Lap #':<6} {'Status':<10}")
        print(f"{'='*70}")

        valid_entries = []
        for drv in self.all_drivers:
            result = self._get_fastest_lap_data(drv)
            if result is None:
                # Try to get team name even without valid lap
                try:
                    team = self.session.get_driver(drv).get('TeamName', 'Unknown')
                except Exception:
                    team = 'Unknown'
                print(f"{drv:<8} {team:<18} {'No valid lap':<14} {'---':<6} {'DNF/DNS':<10}")
                continue

            fastest, telemetry = result
            team_name = 'Unknown'
            try:
                team_name = self.session.get_driver(drv).get('TeamName', 'Unknown')
            except Exception:
                pass

            lap_time_str = _fmt_laptime(fastest['LapTime'])
            lap_num = fastest.get('LapNumber', '?')
            status = 'OK'

            print(f"{drv:<8} {team_name:<18} {lap_time_str:<14} {lap_num:<6} {status:<10}")
            valid_entries.append((drv, fastest, telemetry, team_name))

        print(f"{'='*70}")
        print(f"Valid drivers with telemetry: {len(valid_entries)} / {len(self.all_drivers)}")
        return valid_entries

    def plot_fastest_laps_track(self) -> None:
        """Plot all drivers' fastest laps overlaid on the track layout."""
        entries = self._print_driver_summary()
        if not entries:
            print("\n❌ No valid telemetry data available for any driver.")
            return

        fig, ax = plt.subplots(figsize=(14, 10), dpi=FIGURE_DPI)
        legend_lines = []
        legend_labels = []

        # Sort by lap time (fastest first) for legend ordering
        entries.sort(key=lambda e: _fmt_laptime_seconds(e[1]['LapTime']))

        for drv, fastest, telemetry, team in entries:
            color = self._driver_colors[drv]
            # Drop NaNs in position for clean plotting
            tel_clean = telemetry.dropna(subset=['X','Y'])
            if tel_clean.empty:
                continue

            # Plot track line with speed-based colormap if available
            if 'Speed' in tel_clean.columns and tel_clean['Speed'].notna().any():
                speeds = tel_clean['Speed'].fillna(tel_clean['Speed'].median()).values
                # Guard against constant speed
                vmin, vmax = float(np.nanmin(speeds)), float(np.nanmax(speeds))
                if vmax == vmin:
                    vmax = vmin + 1
                points = np.array([tel_clean['X'].values, tel_clean['Y'].values]).T.reshape(-1, 1, 2)
                if len(points) < 2:
                    line, = ax.plot(tel_clean['X'], tel_clean['Y'], color=color, linewidth=2.0, alpha=0.85, label=f"{drv}")
                else:
                    segments = np.concatenate([points[:-1], points[1:]], axis=1)
                    lc = LineCollection(segments, cmap='viridis', norm=plt.Normalize(vmin, vmax))
                    lc.set_array(speeds)
                    lc.set_linewidth(2.0)
                    ax.add_collection(lc)
                    # Dummy line for legend with team color
                    line, = ax.plot([], [], color=color, linewidth=2.5, label=f"{drv}")
                    ax.autoscale()
            else:
                line, = ax.plot(
                    tel_clean['X'], tel_clean['Y'],
                    color=color, linewidth=2.0, alpha=0.85,
                    label=f"{drv}"
                )

            lap_time_str = _fmt_laptime(fastest['LapTime'])
            legend_lines.append(line)
            legend_labels.append(f"{drv} — {team} ({lap_time_str})")

        ax.set_aspect('equal')
        ax.set_title(
            f"Fastest Laps Overlay — {self.year} {self.track.country} GP\n"
            f"{self.track.name} | {self.track.city}",
            fontsize=14, fontweight='bold', pad=15
        )
        ax.axis('off')

        # Add start/finish line marker
        if entries:
            first_tel = entries[0][2]
            if len(first_tel) > 0:
                ax.scatter(first_tel['X'].iloc[0], first_tel['Y'].iloc[0],
                         c='white', s=100, marker='o', edgecolors='black', linewidths=2,
                         zorder=10, label='Start/Finish')

        if legend_lines:
            ax.legend(
                handles=legend_lines, labels=legend_labels,
                loc='upper left', bbox_to_anchor=(1.02, 1.0),
                fontsize=8, framealpha=0.95,
                title="Driver (Fastest Lap)", title_fontsize=10,
                edgecolor='gray'
            )

        plt.tight_layout()
        plt.subplots_adjust(right=0.82)
        plt.show()

    def plot_speed_comparison(self, driver_codes: Optional[List[str]] = None) -> None:
        """Plot speed traces for selected drivers against distance."""
        if driver_codes is None:
            driver_codes = self.all_drivers[:4]  # Default to first 4

        fig, axes = plt.subplots(len(driver_codes), 1, figsize=(14, 3 * len(driver_codes)),
                                  sharex=True, dpi=FIGURE_DPI)
        if len(driver_codes) == 1:
            axes = [axes]

        for ax, drv in zip(axes, driver_codes):
            result = self._get_fastest_lap_data(drv)
            if result is None:
                ax.text(0.5, 0.5, f"{drv}: No Data", ha='center', va='center', transform=ax.transAxes)
                ax.set_title(drv)
                continue

            fastest, telemetry = result
            tel = telemetry.copy()

            # Add distance if not present
            if 'Distance' not in tel.columns:
                tel = tel.add_distance()

            color = self._driver_colors[drv]
            ax.fill_between(tel['Distance'], tel['Speed'], alpha=0.3, color=color)
            ax.plot(tel['Distance'], tel['Speed'], color=color, linewidth=1.5)

            # Mark DRS zones
            if 'DRS' in tel.columns:
                drs_on = tel['DRS'] > 0
                ax.fill_between(tel['Distance'], 0, tel['Speed'].max() * 1.05,
                                where=drs_on, alpha=0.1, color='green', label='DRS')

            lap_time = _fmt_laptime(fastest['LapTime'])
            ax.set_title(f"{drv} — Fastest Lap: {lap_time}", fontsize=11, loc='left')
            ax.set_ylabel("Speed (km/h)")
            ax.set_ylim(0, tel['Speed'].max() * 1.1)
            ax.grid(True, alpha=0.3)

        axes[-1].set_xlabel("Distance (m)")
        fig.suptitle(f"Speed Comparison — {self.year} {self.track.country} GP",
                     fontsize=13, fontweight='bold', y=1.01)
        plt.tight_layout()
        plt.show()

    def plot_sector_analysis(self) -> None:
        """Bar chart comparing sector times across all drivers."""
        sector_data = []
        for drv in self.all_drivers:
            result = self._get_fastest_lap_data(drv)
            if result is None:
                continue
            fastest, _ = result
            row = {'Driver': drv}
            for sec in ['Sector1Time', 'Sector2Time', 'Sector3Time']:
                val = fastest.get(sec)
                row[sec] = _fmt_laptime_seconds(val) if val is not None else None
            sector_data.append(row)

        if not sector_data:
            print("\n❌ No sector time data available.")
            return

        df_sectors = pd.DataFrame(sector_data)
        df_sectors = df_sectors.dropna(subset=['Sector1Time', 'Sector2Time', 'Sector3Time'])

        if df_sectors.empty:
            print("\n❌ Incomplete sector data for all drivers.")
            return

        # Compute total sector time for sorting
        df_sectors['Total'] = df_sectors[['Sector1Time', 'Sector2Time', 'Sector3Time']].sum(axis=1)
        df_sectors = df_sectors.sort_values('Total')

        fig, ax = plt.subplots(figsize=(12, max(6, len(df_sectors) * 0.4)), dpi=FIGURE_DPI)

        drivers = df_sectors['Driver'].values
        s1 = df_sectors['Sector1Time'].values
        s2 = df_sectors['Sector2Time'].values
        s3 = df_sectors['Sector3Time'].values

        y_pos = np.arange(len(drivers))
        bar_height = 0.6

        # Normalize to show differences (subtract min of each sector)
        s1_min, s2_min, s3_min = s1.min(), s2.min(), s3.min()
        s1_n = s1 - s1_min
        s2_n = s2 - s2_min
        s3_n = s3 - s3_min

        ax.barh(y_pos, s1_n, bar_height, label='Sector 1', color='#FF6B6B', left=0)
        ax.barh(y_pos, s2_n, bar_height, label='Sector 2', color='#4ECDC4', left=s1_n)
        ax.barh(y_pos, s3_n, bar_height, label='Sector 3', color='#45B7D1', left=s1_n + s2_n)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(drivers)
        ax.invert_yaxis()
        ax.set_xlabel("Sector Time Delta from Best (seconds)")
        ax.set_title(f"Sector Time Analysis — {self.year} {self.track.country} GP",
                     fontsize=13, fontweight='bold')
        ax.legend(loc='lower right')
        ax.grid(True, axis='x', alpha=0.3)

        # Add total time annotations
        for i, (drv, total) in enumerate(zip(drivers, df_sectors['Total'].values)):
            ax.text(s1_n[i] + s2_n[i] + s3_n[i] + 0.02, i,
                    f"{_fmt_laptime(pd.Timedelta(seconds=total))}",
                    va='center', fontsize=9, color='black')

        plt.tight_layout()
        plt.show()

    def plot_race_pace(self) -> None:
        """Plot lap times evolution throughout the race for all drivers."""
        fig, ax = plt.subplots(figsize=(14, 8), dpi=FIGURE_DPI)

        for drv in self.all_drivers:
            drv_laps = self.laps.pick_driver(drv)
            if drv_laps.empty:
                continue

            # Filter out in-laps, out-laps, and pit laps for cleaner pace view
            pace_laps = drv_laps[
                (drv_laps['PitOutTime'].isna()) &
                (drv_laps['PitInTime'].isna()) &
                (~drv_laps['LapTime'].isna())
            ].copy()

            if pace_laps.empty:
                continue

            color = self._driver_colors[drv]
            lap_times_sec = pace_laps['LapTime'].dt.total_seconds()

            ax.plot(pace_laps['LapNumber'], lap_times_sec,
                    color=color, linewidth=1.2, alpha=0.7, marker='o', markersize=2,
                    label=drv)

        ax.set_xlabel("Lap Number")
        ax.set_ylabel("Lap Time (seconds)")
        ax.set_title(f"Race Pace Evolution — {self.year} {self.track.country} GP",
                     fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right', fontsize=8, ncol=2)

        # Format y-axis as M:SS
        ax.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda s, _: f"{int(s//60)}:{s%60:05.2f}"
        ))

        plt.tight_layout()
        plt.show()


# ── Menu & Input ───────────────────────────────────────────────────────────
def display_track_menu() -> None:
    """Display formatted track selection menu."""
    print("\n" + "═" * 70)
    print("  🏁  SELECT A GRAND PRIX")
    print("═" * 70)
    for num, track in TRACKS.items():
        print(f"  {num:>2}. {track.country:<18} {track.city:<18} {track.name}")
    print("═" * 70)


def get_track_selection() -> Track:
    """Get validated track selection from user."""
    display_track_menu()
    choice = _input_int("\nEnter track number (1-22): ", 1, 22)
    return TRACKS[choice]


def display_analysis_menu() -> int:
    """Display post-load analysis options."""
    print("\n" + "═" * 70)
    print("  ANALYSIS OPTIONS")
    print("═" * 70)
    print("  1. Track Map — Fastest Laps Overlay")
    print("  2. Speed Traces — Distance vs Speed")
    print("  3. Sector Times — Comparative Analysis")
    print("  4. Race Pace — Lap Time Evolution")
    print("  5. All of the Above")
    print("  0. Exit")
    print("═" * 70)
    return _input_int("\nSelect analysis (0-5): ", 0, 5)


# ── Argparse (thin CLI wrapper) ───────────────────────────────────────────
def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="F1 Advanced Visualizer (core-powered)")
    parser.add_argument("--year", type=int, default=None, help="Season year (2018-2030)")
    parser.add_argument("--track", type=str, default=None, help="Track name/fastf1 identifier or round number")
    parser.add_argument("--session", type=str, default="R", help="Session code (R/Q/FP1...) default R")
    parser.add_argument("--analysis", type=str, default=None, help="track/speed/sector/pace/all")
    parser.add_argument("--save", type=str, default=None, help="Save figure path")
    parser.add_argument("--no-show", action="store_true", help="Do not display figure")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    return parser.parse_args(argv)


def _run_with_args(args) -> None:
    """Run non-interactive mode using core.session."""
    if _logger and args.verbose:
        _logger.info("Running advanced with args %s", args)
    _setup_cache()

    # Resolve track
    track_arg = args.track
    if track_arg is None:
        raise SystemExit("Missing --track (use 1-22, name, or fastf1 identifier)")

    # Resolve year
    year = args.year
    if year is None:
        try:
            from f1_terminal.config import settings as _s
            year = _s.default_season
        except Exception:
            year = 2024

    # Load session via core (or fallback)
    session_obj = None
    wrapper = None
    if _HAS_CORE:
        try:
            wrapper = _core_load_session(year, track_arg, args.session)
            session_obj = wrapper.session
            # Build Track object for title if possible
            from f1_terminal.tracks import TRACKS as _TRACKS

            track = None
            # try int
            try:
                track = _TRACKS[int(track_arg)]
            except Exception:
                # search by fastf1_name
                for t in _TRACKS.values():
                    if t.fastf1_name.lower() == track_arg.lower() or t.country.lower() == track_arg.lower():
                        track = t
                        break
                if track is None:
                    # dummy Track
                    from dataclasses import dataclass as _dc

                    @dataclass(frozen=True)
                    class _Tmp:
                        round_num: int = 1
                        country: str = track_arg
                        city: str = track_arg
                        name: str = track_arg
                        fastf1_name: str = track_arg

                    track = _Tmp()  # type: ignore
            viz = TrackVisualizer(session_obj, year, track)  # type: ignore[arg-type]
        except SystemExit:
            raise
        except Exception as e:
            print(f"Failed to load session {year} {track_arg} {args.session}: {e}")
            sys.exit(1)
    else:
        # Fallback old path
        from f1_terminal.tracks import TRACKS as _TRACKS

        track = None
        try:
            track = _TRACKS[int(track_arg)]
        except Exception:
            for t in _TRACKS.values():
                if t.fastf1_name.lower() == track_arg.lower():
                    track = t
                    break
            if track is None:
                print(f"Unknown track {track_arg}")
                sys.exit(2)
        try:
            session_obj = fastf1.get_session(year, track.fastf1_name, args.session)
            session_obj.load(telemetry=True, laps=True, weather=False)
            viz = TrackVisualizer(session_obj, year, track)
        except Exception as e:
            print(f"Failed to load session: {e}")
            sys.exit(1)

    # Analysis routing — uses TrackVisualizer methods (pure plotting via core where available)
    # Map friendly values
    analysis = (args.analysis or "all").lower()
    import matplotlib.pyplot as plt

    if args.save:
        # viz methods call plt.show internally; we intercept save by monkey? Simpler: handle track case explicitly
        # For now call viz methods and if save provided, save current figure
        pass

    if analysis == "track":
        viz.plot_fastest_laps_track()
        if args.save:
            try:
                plt.gcf().savefig(args.save, dpi=FIGURE_DPI, bbox_inches="tight")
                print(f"Saved to {args.save}")
            except Exception as e:
                print(f"Save failed: {e}")
    elif analysis == "speed":
        viz.plot_speed_comparison()
        if args.save:
            try:
                plt.gcf().savefig(args.save, dpi=FIGURE_DPI, bbox_inches="tight")
                print(f"Saved to {args.save}")
            except Exception as e:
                print(f"Save failed: {e}")
    elif analysis in ("sector", "sectors"):
        viz.plot_sector_analysis()
        if args.save:
            try:
                plt.gcf().savefig(args.save, dpi=FIGURE_DPI, bbox_inches="tight")
                print(f"Saved to {args.save}")
            except Exception as e:
                print(f"Save failed: {e}")
    elif analysis == "pace":
        viz.plot_race_pace()
        if args.save:
            try:
                plt.gcf().savefig(args.save, dpi=FIGURE_DPI, bbox_inches="tight")
                print(f"Saved to {args.save}")
            except Exception as e:
                print(f"Save failed: {e}")
    else:  # all
        viz.plot_fastest_laps_track()
        if args.save:
            try:
                base = Path(args.save)
                # save first figure
                plt.gcf().savefig(str(base).replace(".png", "_track.png") if str(base).endswith(".png") else str(base), dpi=FIGURE_DPI, bbox_inches="tight")
            except Exception:
                pass
        viz.plot_speed_comparison()
        viz.plot_sector_analysis()
        viz.plot_race_pace()

    if args.no_show:
        try:
            plt.close("all")
        except Exception:
            pass


def main(argv=None) -> None:
    """Main entry point — thin wrapper over core.

    Pure function: no input() when imported unless argv triggers interactive path.
    Supports both scriptable args and legacy interactive prompts.

    Args:
        argv: Optional list of args (for testing). If None, uses sys.argv[1:].
    """
    # If called with explicit argv (testing) or with args on CLI, use argparse path
    # If no args provided at all, fall back to interactive menus for backward compat
    raw = argv if argv is not None else sys.argv[1:]
    has_cli_args = len(raw) > 0 and any(a.startswith("-") or a.startswith("--") for a in raw) or any(
        a in ("--year", "--track", "--session", "--analysis", "--save", "--no-show") for a in raw
    )
    # Also if argv contains --help naturally handled by argparse

    # If no CLI args and not testing with argv, do interactive fallback
    if not has_cli_args and argv is None and len(sys.argv) == 1:
        # Legacy interactive path (keeps input loops only here)
        print("\n" + "═" * 70)
        print("  🏎️  F1 RACE SESSION ADVANCED VISUALIZER")
        print("  Powered by FastF1  |  Telemetry & Strategy Analysis")
        print("═" * 70)
        _setup_cache()
        year = _input_year()
        track = get_track_selection()
        print(f"\nLoading: {year} {track.country} GP — Race Session")
        print("   This may take a moment (downloading timing & telemetry data)...")
        try:
            session = fastf1.get_session(year, track.fastf1_name, 'R')
            session.load(telemetry=True, laps=True, weather=False)
        except fastf1.core.DataNotLoadedError as e:
            print(f"\nFailed to load session data: {e}")
            print("   This may happen if the session hasn't occurred yet or data is unavailable.")
            sys.exit(1)
        except Exception as e:
            print(f"\nUnexpected error loading session: {e}")
            sys.exit(1)
        laps = session.laps
        if laps is None or laps.empty:
            print("\nNo lap data available for this session.")
            sys.exit(1)
        print("\nLoaded successfully!")
        print(f"   Total laps recorded: {len(laps)}")
        print(f"   Drivers: {len(laps['Driver'].unique())}")
        viz = TrackVisualizer(session, year, track)
        while True:
            choice = display_analysis_menu()
            if choice == 0:
                print("\nGoodbye! Data Scientist 🏎 ️")
                break
            elif choice == 1:
                viz.plot_fastest_laps_track()
            elif choice == 2:
                print("\nAvailable drivers:", ", ".join(viz.all_drivers))
                drv_input = input("Enter driver codes (comma-separated, or 'all'): ").strip().upper()
                if drv_input == 'ALL':
                    viz.plot_speed_comparison(viz.all_drivers)
                else:
                    selected = [d.strip() for d in drv_input.split(",") if d.strip() in viz.all_drivers]
                    if selected:
                        viz.plot_speed_comparison(selected)
                    else:
                        print("⚠ No valid drivers selected.")
            elif choice == 3:
                viz.plot_sector_analysis()
            elif choice == 4:
                viz.plot_race_pace()
            elif choice == 5:
                viz.plot_fastest_laps_track()
                viz.plot_speed_comparison()
                viz.plot_sector_analysis()
                viz.plot_race_pace()
        return

    # Scriptable path
    try:
        args = _parse_args(argv if argv is not None else None)
    except SystemExit as e:
        # Allow --help to propagate correctly
        raise
    # If no track given but interactive requested via flag? For now error
    if args.track is None and not has_cli_args:
        # Treat empty parsed args as interactive fallback already handled
        print("Missing required --track argument. Use --help for usage.")
        sys.exit(2)
    _run_with_args(args)


if __name__ == "__main__":
    main()
