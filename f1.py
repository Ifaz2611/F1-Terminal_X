import fastf1
import pandas as pd
import matplotlib.pyplot as plt

# Enable cache in a local directory
fastf1.Cache.enable_cache('cache')

# Load the 2024 Spanish Grand Prix Race (A race that has already happened)
session = fastf1.get_session(2025, 'Spain', 'R')
session.load()

# Access lap data
laps = session.laps
print(f"Total laps recorded in session: {len(laps)}\n")

# Get fastest lap from a specific driver
driver_code = 'HAM'
driver_laps = laps.pick_driver(driver_code)

if driver_laps.empty:
    print(f"No lap data found for driver {driver_code}.")
else:
    fastest_lap = driver_laps.pick_fastest()
    
    # Check if a valid fastest lap was actually set
    if fastest_lap is None or pd.isna(fastest_lap.get('LapTime')):
        print(f"{driver_code} did not set a valid fastest lap.")
    else:
        print(f"Fastest lap for {driver_code}: {fastest_lap['LapTime']}")
        
        # Get telemetry data
        telemetry = fastest_lap.get_telemetry()

        # Access speed, throttle, brake, and GPS data
        telemetry_data = telemetry[['Speed', 'Throttle', 'Brake', 'X', 'Y']]
        print("\nTelemetry Sample (First 10 rows):")
        print(telemetry_data.head(10))
        
        # --- BONUS: Plot the track map colored by speed ---
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Plot the track map using X and Y coordinates, colored by Speed
        scatter = ax.scatter(telemetry['X'], telemetry['Y'], 
                             c=telemetry['Speed'], 
                             cmap='plasma', 
                             s=2) 
        
        plt.colorbar(scatter, label='Speed (km/h)')
        ax.set_title(f"{driver_code}'s Fastest Lap Speed Trace - 2024 Spanish GP")
        ax.set_aspect('equal') 
        plt.axis('off') 
        
        plt.tight_layout()
        plt.show()