"""
FastF1 Telemetry Analyzer — 2026 Season
Interactive selection of Grand Prix and driver.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import fastf1
import pandas as pd
import questionary

if TYPE_CHECKING:
    from fastf1.core import Session


# ── Configuration ───────────────────────────────────────────────
CACHE_DIR = Path("cache")
SEASON = 2026
SESSION_TYPE = "R"
TELEMETRY_COLUMNS = ["Speed", "Throttle", "Brake", "X", "Y"]


# ── Cache & session setup ──────────────────────────────────────
def setup_cache() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(CACHE_DIR))


# ── Selection helpers ───────────────────────────────────────────
def select_grand_prix() -> str:
    """Let the user pick a GP from the season schedule."""
    schedule = fastf1.get_event_schedule(SEASON)
    events = schedule[["RoundNumber", "EventName", "Location"]].dropna(
        subset=["EventName"]
    )

    choices = [
        questionary.Choice(
            title=f"R{int(row.RoundNumber):02d}  {row.EventName} ({row.Location})",
            value=row.EventName,
        )
        for row in events.itertuples()
    ]

    picked = questionary.select(
        "Select a Grand Prix:",
        choices=choices,
        style=questionary.Style([("selected", "bold cyan")]),
    ).ask()

    if picked is None:
        raise SystemExit(0)
    return picked


def select_driver(session: Session) -> tuple[str, str]:
    """Let the user pick a driver from the loaded session."""
    drivers = [str(d) for d in session.drivers]
    results = session.results

    driver_data = []

    if results is not None and not results.empty:
        # Determine whether session.drivers contains numbers or abbreviations
        use_numbers = any(d.isdigit() for d in drivers)

        for _, row in results.iterrows():
            if use_numbers:
                key = str(row.get("DriverNumber", ""))
            else:
                key = str(row.get("Abbreviation", ""))

            if key not in drivers:
                continue

            # Full name
            if "FullName" in row and pd.notna(row["FullName"]):
                name = str(row["FullName"])
            else:
                first = str(row.get("FirstName", "")).strip()
                last = str(row.get("LastName", "")).strip()
                name = f"{first} {last}".strip()

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

    # Fallback if results are unavailable
    if not driver_data:
        driver_data = [
            (999, code, code, code)
            for code in drivers
        ]

    driver_data.sort(key=lambda x: x[0])

    picked = questionary.select(
        "Select a driver:",
        choices=[
            questionary.Choice(
                title=item[3],
                value=(item[1], item[2]),
            )
            for item in driver_data
        ],
    ).ask()

    if picked is None:
        raise SystemExit()

    return picked


# ── Telemetry fetch (fixed) ─────────────────────────────────────
def load_session(grand_prix: str) -> Session:
    session = fastf1.get_session(SEASON, grand_prix, SESSION_TYPE)
    session.load()
    return session


def get_fastest_lap_telemetry(
    session: Session,
    driver_code: str,
    driver_name: str,
) -> pd.DataFrame | None:
    # Fixed deprecation: pick_drivers (plural)
    driver_laps = session.laps.pick_drivers(driver_code)

    if driver_laps.empty:
        print(f"No lap data found for {driver_name}.")
        return None

    fastest_lap = driver_laps.pick_fastest()

    if fastest_lap is None or pd.isna(fastest_lap.get("LapTime")):
        print(f"{driver_name} did not set a valid fastest lap.")
        return None

    print(f"\nFastest lap for {driver_name}: {fastest_lap['LapTime']}")

    # Safe telemetry: handle missing 'Date' in position data
    car_data = fastest_lap.get_car_data()
    pos_data = fastest_lap.get_pos_data()

    if pos_data is not None and not pos_data.empty:
        # If 'Date' is the index, reset it to become a column
        if 'Date' not in pos_data.columns:
            if pos_data.index.name == 'Date':
                pos_data = pos_data.reset_index()
            else:
                print("Position data has no 'Date' column – using car data only.")
                return car_data[TELEMETRY_COLUMNS]

        # Merge car and position data on nearest 'Date'
        telemetry = pd.merge_asof(
            car_data.sort_values('Date'),
            pos_data.sort_values('Date'),
            on='Date',
            direction='nearest'
        )
    else:
        # No position data at all
        telemetry = car_data

    # Return only the columns that actually exist
    available_cols = [col for col in TELEMETRY_COLUMNS if col in telemetry.columns]
    return telemetry[available_cols]


# ── Entry point ─────────────────────────────────────────────────
def main() -> None:
    setup_cache()

    grand_prix = select_grand_prix()
    session = load_session(grand_prix)
    print(f"Total laps recorded: {len(session.laps)}\n")

    driver_code, driver_name = select_driver(session)
    telemetry = get_fastest_lap_telemetry(session, driver_code, driver_name)

    if telemetry is not None:
        print("\nTelemetry Sample (First 10 rows):")
        print(telemetry.head(10))


if __name__ == "__main__":
    main()