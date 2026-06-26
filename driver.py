import fastf1
import fastf1.plotting
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
import numpy as np

# ----------------------------------------
# INITIAL SETUP
# ----------------------------------------

fastf1.Cache.enable_cache('cache')
fastf1.plotting.setup_mpl()

YEAR = 2026
GRAND_PRIX = "Monaco"

# ----------------------------------------
# LOAD SESSION ONCE
# ----------------------------------------

try:
    event = fastf1.get_event(YEAR, GRAND_PRIX)
    session = event.get_race()

    print(f"\nLoading {YEAR} {GRAND_PRIX} GP...")
    session.load()

    laps = session.laps

except Exception as e:
    print("Error loading session:")
    print(e)
    exit()

# ----------------------------------------
# MENU FUNCTIONS
# ----------------------------------------

def show_schedule():
    print("\n" + "=" * 70)
    print("FULL SEASON SCHEDULE")
    print("=" * 70)

    schedule = fastf1.get_event_schedule(YEAR)

    cols = [
        'RoundNumber',
        'Country',
        'Location',
        'OfficialEventName',
        'EventDate'
    ]

    print(schedule[cols].to_string(index=False))


def show_driver_lineup():

    print("\n" + "=" * 70)
    print("DRIVER LINEUP")
    print("=" * 70)

    for code in session.drivers:

        driver = session.get_driver(code)

        print(f"\n🏎 {driver['BroadcastName']}")
        print(f"Number : {driver['DriverNumber']}")
        print(f"Team   : {driver['TeamName']}")
        print(f"Color  : #{driver['TeamColor']}")


def tire_strategy():

    COMPOUND_COLORS = getattr(
        fastf1.plotting,
        'COMPOUND_COLORS',
        {
            'SOFT': '#FF3333',
            'MEDIUM': '#FFD700',
            'HARD': '#FFFFFF',
            'INTERMEDIATE': '#39B54A',
            'WET': '#00AEEF',
            'UNKNOWN': '#888888'
        }
    )

    fig, ax = plt.subplots(figsize=(12, 8))

    active_drivers = [
        d for d in session.drivers
        if len(laps.pick_drivers(d)) > 5
    ]

    for driver in active_drivers:

        dlaps = laps.pick_drivers(driver)

        compounds = dlaps['Compound'].fillna('UNKNOWN')

        colors = [
            COMPOUND_COLORS.get(c, '#888888')
            for c in compounds
        ]

        ax.scatter(
            dlaps['LapNumber'],
            [driver] * len(dlaps),
            c=colors,
            s=80
        )

    ax.set_title("Tire Strategy")
    ax.set_xlabel("Lap Number")
    ax.grid(True)

    plt.show()


def speed_trace():

    driver = input(
        "\nEnter Driver Code (VER/NOR/LEC/HAM): "
    ).upper()

    driver_laps = laps.pick_drivers(driver)

    if len(driver_laps) == 0:
        print("Driver not found!")
        return

    fastest = driver_laps.pick_fastest()

    if fastest is None:
        print("No fastest lap found.")
        return

    telemetry = fastest.get_telemetry()

    if telemetry.empty:
        print("No telemetry data.")
        return

    fig, ax = plt.subplots(figsize=(10, 8))

    points = telemetry[['X', 'Y']].values.reshape(-1, 1, 2)

    segments = np.concatenate(
        [points[:-1], points[1:]],
        axis=1
    )

    norm = plt.Normalize(
        telemetry['Speed'].min(),
        telemetry['Speed'].max()
    )

    lc = LineCollection(
        segments,
        cmap='plasma',
        norm=norm,
        linewidth=3
    )

    lc.set_array(telemetry['Speed'])

    ax.add_collection(lc)

    plt.colorbar(
        lc,
        ax=ax,
        label='Speed (km/h)'
    )

    ax.set_aspect('equal')
    plt.axis('off')

    plt.title(
        f"{driver} Fastest Lap Speed Trace"
    )

    plt.show()


def pace_comparison():

    d1 = input("Driver 1: ").upper()
    d2 = input("Driver 2: ").upper()

    laps1 = laps.pick_drivers(d1)
    laps2 = laps.pick_drivers(d2)

    if len(laps1) == 0 or len(laps2) == 0:
        print("Invalid driver code.")
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(
        laps1['LapNumber'],
        laps1['LapTime'].dt.total_seconds(),
        label=d1
    )

    ax.plot(
        laps2['LapNumber'],
        laps2['LapTime'].dt.total_seconds(),
        label=d2
    )

    ax.set_title("Race Pace Comparison")
    ax.set_xlabel("Lap")
    ax.set_ylabel("Lap Time (s)")
    ax.legend()
    ax.grid(True)

    plt.show()


# ----------------------------------------
# MAIN MENU LOOP
# ----------------------------------------

while True:

    print("\n" + "=" * 50)
    print("FORMULA 1 DATA ANALYZER")
    print("=" * 50)

    print("1. Full Season Schedule")
    print("2. Driver Lineup")
    print("3. Tire Strategy")
    print("4. Speed Trace")
    print("5. Pace Comparison")
    print("6. Exit")

    choice = input("\nSelect Option: ")

    if choice == "1":
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
        print("\nGoodbye! Future F1 Eniginner")
        break

    else:
        print("\nInvalid option. Try again. Buddy")