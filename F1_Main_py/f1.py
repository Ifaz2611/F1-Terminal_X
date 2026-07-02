"""
FastF1 Telemetry Analyzer — 2026 Season (Advanced Edition)
============================================================
Production-grade F1 telemetry analysis with interactive selection,
rich visualizations, and comprehensive error handling.

"""

from __future__ import annotations

import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Tuple

import fastf1
import fastf1.plotting
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection
import seaborn as sns

# Optional: questionary for interactive CLI (falls back to built-in input)
try:
    import questionary
    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False
    print("ℹquestionary not installed — falling back to standard input.")

# ── Suppress non-critical warnings ─────────────────────────────────────────
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# ── Configuration ──────────────────────────────────────────────────────────
CACHE_DIR = Path("cache")
SEASON = 2026
SESSION_TYPE = "R"
FIGURE_DPI = 150

# ── Cache & Session Setup ──────────────────────────────────────────────────
def setup_cache() -> None:
    """Initialize fastf1 cache with v3.x compatible API."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        fastf1.Cache.set_cache_directory(str(CACHE_DIR))
    except AttributeError:
        # Fallback for older versions
        fastf1.Cache.enable_cache(str(CACHE_DIR))


# ── Interactive Selection (with fallback) ────────────────────────────────
def _select_questionary(choices: List[Tuple[str, str]], prompt: str) -> Optional[str]:
    """Use questionary for interactive selection."""
    if not HAS_QUESTIONARY:
        return None
    q_choices = [
        questionary.Choice(title=title, value=value)
        for title, value in choices
    ]
    picked = questionary.select(prompt, choices=q_choices).ask()
    return picked


def _select_fallback(choices: List[Tuple[str, str]], prompt: str) -> str:
    """Fallback to standard input if questionary unavailable."""
    print(f"\n{prompt}")
    for i, (title, _) in enumerate(choices, 1):
        print(f"  {i}. {title}")
    while True:
        try:
            idx = int(input("Enter number: ").strip()) - 1
            if 0 <= idx < len(choices):
                return choices[idx][1]
            print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a valid number.")


def select_grand_prix() -> str:
    """Let user pick a GP from the season schedule."""
    try:
        schedule = fastf1.get_event_schedule(SEASON)
    except Exception as e:
        print(f"❌ Failed to load {SEASON} schedule: {e}")
        print("   Falling back to manual entry.")
        return input("Enter Grand Prix name (e.g., 'Australian Grand Prix'): ").strip()

    events = schedule[["RoundNumber", "EventName", "Location"]].dropna(subset=["EventName"])

    choices = [
        (f"R{int(row.RoundNumber):02d}  {row.EventName} ({row.Location})", row.EventName)
        for row in events.itertuples()
    ]

    result = _select_questionary(choices, "Select a Grand Prix:")
    if result is not None:
        return result
    return _select_fallback(choices, "Select a Grand Prix:")


def select_driver(session: fastf1.core.Session) -> Tuple[str, str]:
    """Let user pick a driver from the loaded session."""
    drivers = [str(d) for d in session.drivers]
    results = session.results

    driver_data: List[Tuple[int, str, str, str]] = []

    if results is not None and not results.empty:
        use_numbers = any(d.isdigit() for d in drivers)

        for _, row in results.iterrows():
            key = str(row.get("DriverNumber" if use_numbers else "Abbreviation", ""))
            if key not in drivers:
                continue

            name = str(row.get("FullName", ""))
            if not name or name == "nan":
                first = str(row.get("FirstName", "")).strip()
                last = str(row.get("LastName", "")).strip()
                name = f"{first} {last}".strip() or key

            team = str(row.get("TeamName", ""))
            pos = row.get("Position")
            try:
                pos = int(float(pos))
            except Exception:
                pos = 999

            label = f"{name} ({key})"
            if team:
                label += f" — {team}"

            driver_data.append((pos, key, name, label))

    if not driver_data:
        driver_data = [(999, code, code, code) for code in drivers]

    driver_data.sort(key=lambda x: x[0])

    choices = [(item[3], item[1]) for item in driver_data]
    result = _select_questionary(choices, "Select a driver:")
    if result is not None:
        # Find full name
        for item in driver_data:
            if item[1] == result:
                return result, item[2]
        return result, result
    return _select_fallback(choices, "Select a driver:"), result


# ── Telemetry Fetching (Fixed) ────────────────────────────────────────────
def load_session(grand_prix: str) -> fastf1.core.Session:
    """Load session with comprehensive error handling."""
    try:
        session = fastf1.get_session(SEASON, grand_prix, SESSION_TYPE)
        session.load(telemetry=True, laps=True, weather=False)
        return session
    except fastf1.core.DataNotLoadedError as e:
        print(f"Failed to load session data: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


def get_fastest_lap_telemetry(
    session: fastf1.core.Session,
    driver_code: str,
    driver_name: str,
) -> Optional[pd.DataFrame]:
    
    """
    Fetch fastest lap telemetry using fastf1's built-in get_telemetry().
    This is the CORRECT approach — it handles interpolation, merging,
    and Date column management automatically.
    """

    driver_laps = session.laps.pick_drivers(driver_code)

    if driver_laps.empty:
        print(f"⚠️  No lap data found for {driver_name}.")
        return None

    fastest_lap = driver_laps.pick_fastest()

    if fastest_lap is None or pd.isna(fastest_lap.get("LapTime")):
        print(f"⚠️  {driver_name} did not set a valid fastest lap.")
        return None

    lap_time = fastest_lap["LapTime"]
    print(f"🏁 Fastest lap for {driver_name}: {lap_time}")

    # FIXED: Use get_telemetry() — the official fastf1 method
    # It merges car_data + pos_data with proper interpolation
    try:
        telemetry = fastest_lap.get_telemetry()
    except Exception as e:
        print(f"Failed to get telemetry: {e}")
        return None

    if telemetry is None or telemetry.empty:
        print(f"Telemetry data is empty for {driver_name}.")
        return None

    # Add distance if not present (useful for plots)
    if "Distance" not in telemetry.columns:
        try:
            telemetry = telemetry.add_distance()
        except Exception:
            pass

    return telemetry


# ── Visualization Engine ───────────────────────────────────────────────────
class TelemetryVisualizer:
    """Handles all telemetry plotting with multiple analysis modes."""

    def __init__(self, telemetry: pd.DataFrame, driver_code: str, driver_name: str,
                 session: fastf1.core.Session, grand_prix: str):
        self.telemetry = telemetry
        self.driver_code = driver_code
        self.driver_name = driver_name
        self.session = session
        self.grand_prix = grand_prix
        self.color = self._get_driver_color()

    def _get_driver_color(self) -> str:
        """Extract team color for the driver."""
        try:
            driver_info = self.session.get_driver(self.driver_code)
            team_color = driver_info.get("TeamColor", None)
            if isinstance(team_color, int):
                return f"#{team_color:06X}"
            elif isinstance(team_color, str) and team_color.strip():
                return f"#{team_color.lstrip('#')}"
        except Exception:
            pass
        return "#E10600"  # Default F1 red

    def _fmt_time(self, td: pd.Timedelta) -> str:
        """Format timedelta as M:SS.mmm."""
        if pd.isna(td):
            return "N/A"
        total = td.total_seconds()
        return f"{int(total // 60)}:{total % 60:06.3f}"

    def plot_speed_trace(self) -> None:
        """Plot speed vs distance with DRS zones and gear shifts."""
        tel = self.telemetry.copy()
        if "Distance" not in tel.columns:
            try:
                tel = tel.add_distance()
            except Exception:
                print("⚠️  Cannot add distance — skipping speed trace.")
                return

        fig, ax = plt.subplots(figsize=(14, 5), dpi=FIGURE_DPI)

        # Speed line
        ax.fill_between(tel["Distance"], tel["Speed"], alpha=0.25, color=self.color)
        ax.plot(tel["Distance"], tel["Speed"], color=self.color, linewidth=1.2, label="Speed")

        # DRS zones
        if "DRS" in tel.columns:
            drs_on = tel["DRS"] > 0
            ax.fill_between(tel["Distance"], 0, tel["Speed"].max() * 1.1,
                            where=drs_on, alpha=0.08, color="green", label="DRS Active")

        # Gear shifts (if available)
        if "nGear" in tel.columns:
            gear_changes = tel["nGear"].diff().abs() > 0
            change_points = tel[gear_changes]
            ax.scatter(change_points["Distance"], change_points["Speed"],
                      c="white", s=15, edgecolors="black", linewidths=0.5,
                      zorder=5, alpha=0.7, label="Gear Shift")

        ax.set_xlabel("Distance (m)", fontsize=11)
        ax.set_ylabel("Speed (km/h)", fontsize=11)
        ax.set_title(
            f"Speed Trace — {self.driver_name} ({self.driver_code})\n"
            f"{SEASON} {self.grand_prix} — Fastest Lap",
            fontsize=13, fontweight="bold"
        )
        ax.legend(loc="upper right", fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, tel["Speed"].max() * 1.15)

        plt.tight_layout()
        plt.show()

    def plot_throttle_brake(self) -> None:
        """Plot throttle and brake traces overlaid."""
        tel = self.telemetry.copy()
        if "Distance" not in tel.columns:
            try:
                tel = tel.add_distance()
            except Exception:
                return

        fig, ax = plt.subplots(figsize=(14, 5), dpi=FIGURE_DPI)

        # Throttle
        if "Throttle" in tel.columns:
            ax.fill_between(tel["Distance"], tel["Throttle"], alpha=0.3, color="green", label="Throttle %")
            ax.plot(tel["Distance"], tel["Throttle"], color="green", linewidth=1.0)

        # Brake
        if "Brake" in tel.columns:
            # Brake is boolean in fastf1 — convert to 0/100 for visibility
            brake_vals = tel["Brake"].astype(int) * 100
            ax.fill_between(tel["Distance"], brake_vals, alpha=0.3, color="red", label="Brake")
            ax.plot(tel["Distance"], brake_vals, color="red", linewidth=1.0)

        ax.set_xlabel("Distance (m)", fontsize=11)
        ax.set_ylabel("Input %", fontsize=11)
        ax.set_title(
            f"Throttle & Brake — {self.driver_name} ({self.driver_code})\n"
            f"{SEASON} {self.grand_prix} — Fastest Lap",
            fontsize=13, fontweight="bold"
        )
        ax.legend(loc="upper right", fontsize=9)
        ax.set_ylim(-5, 105)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

    def plot_track_map(self) -> None:
        """Plot the fastest lap on the track layout with speed heatmap."""
        if "X" not in self.telemetry.columns or "Y" not in self.telemetry.columns:
            print("⚠️  Position data (X, Y) not available — skipping track map.")
            return

        tel = self.telemetry.copy()

        fig, ax = plt.subplots(figsize=(12, 10), dpi=FIGURE_DPI)

        # Create line collection colored by speed
        points = np.array([tel["X"].values, tel["Y"].values]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)

        if "Speed" in tel.columns:
            speeds = tel["Speed"].values
            norm = plt.Normalize(speeds.min(), speeds.max())
            lc = LineCollection(segments, cmap="plasma", norm=norm)
            lc.set_array(speeds)
            lc.set_linewidth(3.0)
            ax.add_collection(lc)

            # Colorbar
            cbar = plt.colorbar(lc, ax=ax, shrink=0.6, pad=0.02)
            cbar.set_label("Speed (km/h)", fontsize=10)
        else:
            ax.plot(tel["X"], tel["Y"], color=self.color, linewidth=2.0)

        # Start/finish marker
        ax.scatter(tel["X"].iloc[0], tel["Y"].iloc[0],
                  c="white", s=120, marker="o", edgecolors="black",
                  linewidths=2, zorder=10, label="Start/Finish")

        ax.set_aspect("equal")
        ax.set_title(
            f"Fastest Lap Track Map — {self.driver_name} ({self.driver_code})\n"
            f"{SEASON} {self.grand_prix}",
            fontsize=13, fontweight="bold"
        )
        ax.axis("off")
        ax.legend(loc="upper left", fontsize=9)

        plt.tight_layout()
        plt.show()

    def plot_gear_map(self) -> None:
        """Plot gear usage across the lap."""
        if "nGear" not in self.telemetry.columns or "Distance" not in self.telemetry.columns:
            print("Gear data not available — skipping gear map.")
            return

        tel = self.telemetry.copy()
        if "Distance" not in tel.columns:
            try:
                tel = tel.add_distance()
            except Exception:
                return

        fig, ax = plt.subplots(figsize=(14, 4), dpi=FIGURE_DPI)

        gears = tel["nGear"].astype(int)
        colors = plt.cm.Set3(np.linspace(0, 1, gears.max() + 1))

        for gear in sorted(gears.unique()):
            mask = gears == gear
            ax.fill_between(tel["Distance"][mask], 0, 1, alpha=0.8,
                           color=colors[gear], label=f"Gear {gear}")

        ax.set_xlabel("Distance (m)", fontsize=11)
        ax.set_ylabel("")
        ax.set_title(
            f"Gear Usage — {self.driver_name} ({self.driver_code})\n"
            f"{SEASON} {self.grand_prix} — Fastest Lap",
            fontsize=13, fontweight="bold"
        )
        ax.set_yticks([])
        ax.legend(loc="upper right", ncol=8, fontsize=8)
        ax.set_ylim(0, 1)

        plt.tight_layout()
        plt.show()

    def print_telemetry_summary(self) -> None:
        """Print a formatted summary of key telemetry stats."""
        tel = self.telemetry
        print("\n" + "═" * 60)
        print(f"  TELEMETRY SUMMARY — {self.driver_name} ({self.driver_code})")
        print("═" * 60)

        stats = {}
        if "Speed" in tel.columns:
            stats["Max Speed"] = f"{tel['Speed'].max():.1f} km/h"
            stats["Avg Speed"] = f"{tel['Speed'].mean():.1f} km/h"
        if "Throttle" in tel.columns:
            stats["Avg Throttle"] = f"{tel['Throttle'].mean():.1f}%"
            stats["Full Throttle %"] = f"{(tel['Throttle'] == 100).mean() * 100:.1f}%"
        if "Brake" in tel.columns:
            stats["Braking %"] = f"{tel['Brake'].mean() * 100:.1f}%"
        if "nGear" in tel.columns:
            stats["Max Gear"] = f"{int(tel['nGear'].max())}"
            stats["Avg Gear"] = f"{tel['nGear'].mean():.1f}"
        if "Distance" in tel.columns:
            stats["Track Distance"] = f"{tel['Distance'].max():.1f} m"
        if "DRS" in tel.columns:
            stats["DRS Usage %"] = f"{(tel['DRS'] > 0).mean() * 100:.1f}%"

        for key, val in stats.items():
            print(f"  {key:<20} {val}")
        print("═" * 60)


def display_analysis_menu() -> int:
    """Display post-load analysis options."""
    print("\n" + "═" * 60)
    print(" ANALYSIS OPTIONS")
    print("═" * 60)
    print("  1. Speed Trace (Distance vs Speed)")
    print("  2. Throttle & Brake Inputs")
    print("  3. Track Map with Speed Heatmap")
    print("  4. Gear Usage Map")
    print("  5. Telemetry Summary (Text)")
    print("  6. All Visualizations")
    print("  0. Exit")
    print("═" * 60)

    while True:
        try:
            choice = int(input("\nSelect analysis (0-6): ").strip())
            if 0 <= choice <= 6:
                return choice
            print("  ⚠ Please enter a number between 0 and 6.")
        except ValueError:
            print("  ⚠ Invalid input. Please enter a number.")


# ── Entry Point ────────────────────────────────────────────────────────────
def main() -> None:
    """Main entry point."""
    print("\n" + "═" * 60)
    print("  FASTF1 TELEMETRY ANALYZER — ADVANCED EDITION")
    print("  Season: 2026  |  Interactive Analysis & Visualization")
    print("═" * 60)

    setup_cache()

    grand_prix = select_grand_prix()
    print(f"\n⏳ Loading {SEASON} {grand_prix} — Race Session...")

    session = load_session(grand_prix)
    print(f"Loaded! Total laps recorded: {len(session.laps)}")

    driver_code, driver_name = select_driver(session)
    telemetry = get_fastest_lap_telemetry(session, driver_code, driver_name)

    if telemetry is None:
        print("\n Could not retrieve telemetry. Exiting.")
        sys.exit(1)

    # Initialize visualizer
    viz = TelemetryVisualizer(telemetry, driver_code, driver_name, session, grand_prix)

    # Analysis loop
    while True:
        choice = display_analysis_menu()
        if choice == 0:
            print("\n Goodbye! Engineer.")
            break
        elif choice == 1:
            viz.plot_speed_trace()
        elif choice == 2:
            viz.plot_throttle_brake()
        elif choice == 3:
            viz.plot_track_map()
        elif choice == 4:
            viz.plot_gear_map()
        elif choice == 5:
            viz.print_telemetry_summary()
        elif choice == 6:
            viz.plot_speed_trace()
            viz.plot_throttle_brake()
            viz.plot_track_map()
            viz.plot_gear_map()
            viz.print_telemetry_summary()


if __name__ == "__main__":
    main()