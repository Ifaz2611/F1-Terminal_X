import fastf1
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
fastf1.Cache.enable_cache('cache')

# Load the 2026 Austrian Grand Prix session

#FP1 = Practice Session 1 
#FP2 = Practice Session 2
#FP3 = Practice Session 3
#Qualifying = Q
#Main Race = R


#==========================================Code nome of track=========================================


# Australia - Melbourne (Albert Park)
# China - Shanghai (Shanghai International Circuit)
# Japan - Suzuka
# Miami - USA (Miami International Autodrome)
# Canada - Montreal (Circuit Gilles Villeneuve)
# Monaco - Monaco
# Spain - Barcelona (Circuit de Catalunya)
# Austria - Spielberg (Red Bull Ring)
# Great Britain - Silverstone
# Belgium - Spa-Francorchamps
# Hungary - Budapest (Hungaroring)
# Netherlands - Zandvoort
# Italy - Monza
# Spain - Madrid (Madring) New race
# Azerbaijan - Baku
# Singapore - Singapore
# USA - Austin (Circuit of the Americas)
# Mexico - Mexico City
# Brazil - São Paulo (Interlagos)
# USA - Las Vegas (Las Vegas Strip Circuit)
# Qatar - Lusail
# Abu Dhabi - Yas Marina



session = fastf1.get_session(2026, 'Austria', 'Q')  #<--------------------Main code to change the track name and session type
session.load()

laps = session.laps
print(f"Total laps recorded in session: {len(laps)}\n")
print("=" * 60)
print(f"{'Driver':<8} {'Team':<15} {'Fastest Lap':<12} {'Lap #':<6}")
print("=" * 60)


all_drivers = laps['Driver'].unique()
fig, ax = plt.subplots(figsize=(12, 9))
cmap = plt.get_cmap('tab20')


legend_entries = []

for i, driver_code in enumerate(all_drivers):
    driver_laps = laps.pick_driver(driver_code)

    if driver_laps.empty:
        continue
    fastest_lap = driver_laps.pick_fastest()

    if fastest_lap is None or pd.isna(fastest_lap.get('LapTime')):
        print(f"{driver_code:<8} {'---':<15} {'No valid lap':<12} {'---':<6}")
        continue

    driver_info = session.get_driver(driver_code)
    team_name = driver_info.get('TeamName', 'Unknown')
    team_color = driver_info.get('TeamColor', None)


    if team_color and isinstance(team_color, str) and team_color != '':
        color = f"#{team_color}"
    else:
        color = cmap(i / len(all_drivers))

    lap_time_str = str(fastest_lap['LapTime'])
    lap_number = fastest_lap.get('LapNumber', '?')
    print(f"{driver_code:<8} {team_name:<15} {lap_time_str:<12} {lap_number:<6}")

    telemetry = fastest_lap.get_telemetry()
    if telemetry.empty:
        continue

    line, = ax.plot(telemetry['X'], telemetry['Y'],
                    color=color,
                    linewidth=1.5,
                    alpha=0.85,
                    label=f"{driver_code} ({lap_time_str})")
    legend_entries.append(line)

print("=" * 60)

ax.set_aspect('equal')
ax.set_title("All Drivers' Fastest Laps - 2026 Austrian GP  Qualifying Session",
             fontsize=14, fontweight='bold')
ax.axis('off')

if legend_entries:
    sorted_pairs = sorted(
        zip(legend_entries, [e.get_label() for e in legend_entries]),
        key=lambda p: p[1].split('(')[-1].rstrip(')')
    )
    ax.legend(
        handles=[p[0] for p in sorted_pairs],
        labels=[p[1] for p in sorted_pairs],
        loc='best',
        fontsize=8,
        framealpha=0.9,
        title="Driver (Fastest Lap)",
        title_fontsize=10
    )

plt.tight_layout()
plt.show()