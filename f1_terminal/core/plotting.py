"""Plotting helpers — Phase 1 core.

Pure functions: ``ax`` injected, no ``plt.show()``, handle NaN/empty gracefully.
Returns None (draws on ax). Callers may do ``fig.savefig``.

Reuses logic from f1_advanced_visualizer.py and driver.py.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from f1_terminal.config import get_logger

logger = get_logger(__name__)


def _safe_ax(ax: Any) -> bool:
    return ax is not None


def plot_track_map(
    ax: Any,
    telemetry: pd.DataFrame,
    color: str = "#E10600",
    cmap: str = "viridis",
    show_colorbar: bool = True,
) -> None:
    """Plot track layout colored by speed.

    Args:
        ax: Matplotlib Axes to draw on.
        telemetry: DataFrame with X, Y, Speed (Distance optional).
        color: Fallback color if Speed missing.
        cmap: Colormap name for speed.
        show_colorbar: Add speed colorbar.
    """
    if not _safe_ax(ax):
        logger.warning("plot_track_map: ax is None")
        return
    if telemetry is None or telemetry.empty:
        logger.warning("plot_track_map: empty telemetry")
        ax.text(0.5, 0.5, "No telemetry", ha="center", va="center", transform=ax.transAxes)
        return
    if "X" not in telemetry.columns or "Y" not in telemetry.columns:
        logger.warning("plot_track_map: missing X/Y")
        ax.text(0.5, 0.5, "Position data unavailable", ha="center", va="center", transform=ax.transAxes)
        return

    tel_clean = telemetry.dropna(subset=["X", "Y"]).copy()
    if tel_clean.empty:
        logger.warning("plot_track_map: all X/Y NaN")
        ax.text(0.5, 0.5, "No valid position data", ha="center", va="center", transform=ax.transAxes)
        return

    # Speed-colored line via LineCollection if possible
    if "Speed" in tel_clean.columns and tel_clean["Speed"].notna().any():
        speeds = tel_clean["Speed"].fillna(tel_clean["Speed"].median()).values
        vmin, vmax = float(np.nanmin(speeds)), float(np.nanmax(speeds))
        if not np.isfinite(vmin) or not np.isfinite(vmax) or vmax == vmin:
            vmax = vmin + 1 if np.isfinite(vmin) else 1
        points = np.array([tel_clean["X"].values, tel_clean["Y"].values]).T.reshape(-1, 1, 2)
        if len(points) < 2:
            ax.plot(tel_clean["X"], tel_clean["Y"], color=color, linewidth=2.0, alpha=0.85)
        else:
            import matplotlib.pyplot as plt
            from matplotlib.collections import LineCollection

            segments = np.concatenate([points[:-1], points[1:]], axis=1)
            lc = LineCollection(segments, cmap=cmap, norm=plt.Normalize(vmin, vmax))
            lc.set_array(speeds)
            lc.set_linewidth(3.0)
            ax.add_collection(lc)
            ax.autoscale()
            if show_colorbar:
                try:
                    # Only add colorbar if ax has figure
                    fig = ax.get_figure()
                    if fig is not None:
                        # Avoid duplicate colorbars: check if already has one? simplified
                        cbar = fig.colorbar(lc, ax=ax, shrink=0.6, pad=0.02)
                        cbar.set_label("Speed (km/h)", fontsize=10)
                except Exception:
                    pass
    else:
        ax.plot(tel_clean["X"], tel_clean["Y"], color=color, linewidth=2.0, alpha=0.85)

    # Start/finish marker
    try:
        ax.scatter(
            tel_clean["X"].iloc[0],
            tel_clean["Y"].iloc[0],
            c="white",
            s=100,
            marker="o",
            edgecolors="black",
            linewidths=2,
            zorder=10,
        )
    except Exception:
        pass

    ax.set_aspect("equal")
    ax.axis("off")


def plot_speed_trace(
    ax: Any,
    telemetry: pd.DataFrame,
    color: str = "#E10600",
    show_drs: bool = True,
    show_gear_shifts: bool = True,
) -> None:
    """Plot speed vs distance with optional DRS shading and gear shifts."""
    if not _safe_ax(ax):
        logger.warning("plot_speed_trace: ax is None")
        return
    if telemetry is None or telemetry.empty:
        logger.warning("plot_speed_trace: empty telemetry")
        ax.text(0.5, 0.5, "No telemetry", ha="center", va="center", transform=ax.transAxes)
        return
    if "Speed" not in telemetry.columns:
        logger.warning("plot_speed_trace: Speed missing")
        ax.text(0.5, 0.5, "Speed unavailable", ha="center", va="center", transform=ax.transAxes)
        return
    if "Distance" not in telemetry.columns:
        logger.warning("plot_speed_trace: Distance missing, attempting add_distance")
        try:
            telemetry = telemetry.add_distance()  # type: ignore[attr-defined]
        except Exception:
            ax.text(0.5, 0.5, "Distance unavailable", ha="center", va="center", transform=ax.transAxes)
            return

    tel = telemetry.dropna(subset=["Distance", "Speed"]).copy()
    if tel.empty:
        logger.warning("plot_speed_trace: all Speed/Distance NaN")
        return

    ax.fill_between(tel["Distance"], tel["Speed"], alpha=0.25, color=color)
    ax.plot(tel["Distance"], tel["Speed"], color=color, linewidth=1.2, label="Speed")

    if show_drs and "DRS" in tel.columns:
        try:
            drs_on = tel["DRS"] > 0
            if drs_on.any():
                ax.fill_between(
                    tel["Distance"],
                    0,
                    tel["Speed"].max() * 1.1,
                    where=drs_on,
                    alpha=0.08,
                    color="green",
                    label="DRS",
                )
        except Exception:
            pass

    if show_gear_shifts and "nGear" in tel.columns:
        try:
            gear_changes = tel["nGear"].diff().abs() > 0
            change_points = tel[gear_changes]
            if not change_points.empty:
                ax.scatter(
                    change_points["Distance"],
                    change_points["Speed"],
                    c="white",
                    s=15,
                    edgecolors="black",
                    linewidths=0.5,
                    zorder=5,
                    alpha=0.7,
                    label="Gear Shift",
                )
        except Exception:
            pass

    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Speed (km/h)")
    ax.grid(True, alpha=0.3)
    try:
        ax.set_ylim(0, float(tel["Speed"].max()) * 1.15)
    except Exception:
        pass
    # Legend only if labels exist
    try:
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(fontsize=8)
    except Exception:
        pass


def plot_throttle_brake(ax: Any, telemetry: pd.DataFrame) -> None:
    """Plot throttle and brake traces overlaid vs distance."""
    if not _safe_ax(ax):
        logger.warning("plot_throttle_brake: ax is None")
        return
    if telemetry is None or telemetry.empty:
        logger.warning("plot_throttle_brake: empty")
        ax.text(0.5, 0.5, "No telemetry", ha="center", va="center", transform=ax.transAxes)
        return

    if "Distance" not in telemetry.columns:
        try:
            telemetry = telemetry.add_distance()  # type: ignore[attr-defined]
        except Exception:
            logger.warning("plot_throttle_brake: Distance missing")
            ax.text(0.5, 0.5, "Distance unavailable", ha="center", va="center", transform=ax.transAxes)
            return

    tel = telemetry.copy()
    has_throttle = "Throttle" in tel.columns and tel["Throttle"].notna().any()
    has_brake = "Brake" in tel.columns and tel["Brake"].notna().any()

    if not has_throttle and not has_brake:
        logger.warning("plot_throttle_brake: no Throttle/Brake")
        ax.text(0.5, 0.5, "Throttle/Brake unavailable", ha="center", va="center", transform=ax.transAxes)
        return

    if has_throttle:
        try:
            ax.fill_between(tel["Distance"], tel["Throttle"], alpha=0.3, color="green", label="Throttle %")
            ax.plot(tel["Distance"], tel["Throttle"], color="green", linewidth=1.0)
        except Exception:
            pass

    if has_brake:
        try:
            brake_vals = tel["Brake"]
            # Convert bool to int if needed
            try:
                if brake_vals.dtype == bool:
                    brake_vals = brake_vals.astype(int) * 100
                else:
                    # If values are 0/1, scale to 100
                    if brake_vals.max() <= 1:
                        brake_vals = brake_vals.astype(int) * 100
            except Exception:
                pass
            ax.fill_between(tel["Distance"], brake_vals, alpha=0.3, color="red", label="Brake")
            ax.plot(tel["Distance"], brake_vals, color="red", linewidth=1.0)
        except Exception:
            pass

    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Input %")
    ax.set_ylim(-5, 105)
    ax.grid(True, alpha=0.3)
    try:
        handles, _ = ax.get_legend_handles_labels()
        if handles:
            ax.legend(fontsize=8)
    except Exception:
        pass


def plot_gear_map(ax: Any, telemetry: pd.DataFrame) -> None:
    """Plot gear usage across distance (horizontal bar)."""
    if not _safe_ax(ax):
        logger.warning("plot_gear_map: ax is None")
        return
    if telemetry is None or telemetry.empty:
        logger.warning("plot_gear_map: empty")
        ax.text(0.5, 0.5, "No telemetry", ha="center", va="center", transform=ax.transAxes)
        return
    if "nGear" not in telemetry.columns or "Distance" not in telemetry.columns:
        logger.warning("plot_gear_map: nGear/Distance missing")
        # Try add_distance
        if "Distance" not in telemetry.columns:
            try:
                telemetry = telemetry.add_distance()  # type: ignore[attr-defined]
            except Exception:
                ax.text(0.5, 0.5, "Gear/Distance unavailable", ha="center", va="center", transform=ax.transAxes)
                return
        if "nGear" not in telemetry.columns:
            ax.text(0.5, 0.5, "Gear unavailable", ha="center", va="center", transform=ax.transAxes)
            return

    tel = telemetry.dropna(subset=["Distance", "nGear"]).copy()
    if tel.empty:
        logger.warning("plot_gear_map: empty after dropna")
        return

    try:
        gears = tel["nGear"].astype(int)
        import matplotlib.pyplot as plt

        cmap = plt.get_cmap("Set3")
        for gear in sorted(gears.unique()):
            mask = gears == gear
            # Use distance segments where gear==gear
            # Simplify: fill_between where mask holds, but need contiguous
            ax.fill_between(tel["Distance"][mask], 0, 1, alpha=0.8, color=cmap(int(gear) % cmap.N), label=f"Gear {gear}")

        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("")
        ax.set_yticks([])
        ax.set_ylim(0, 1)
        try:
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(loc="upper right", ncol=8, fontsize=8)
        except Exception:
            pass
    except Exception as e:
        logger.warning("plot_gear_map failed: %s", e)


def plot_sector_bars(ax: Any, sector_df: pd.DataFrame) -> None:
    """Horizontal bar with sector delta from best.

    Args:
        ax: Axes.
        sector_df: DataFrame with columns Driver, Sector1Time, Sector2Time, Sector3Time
                   values in seconds (float) or Timedelta. Or DataFrame from f1_advanced_visualizer.
    """
    if not _safe_ax(ax):
        logger.warning("plot_sector_bars: ax is None")
        return
    if sector_df is None or sector_df.empty:
        logger.warning("plot_sector_bars: empty")
        ax.text(0.5, 0.5, "No sector data", ha="center", va="center", transform=ax.transAxes)
        return

    # Normalize column names
    df = sector_df.copy()
    # Convert Timedelta to seconds if needed
    for col in ["Sector1Time", "Sector2Time", "Sector3Time", "S1_s", "S2_s", "S3_s"]:
        if col in df.columns:
            try:
                if df[col].dtype == object or str(df[col].dtype).startswith("timedelta"):
                    df[col] = pd.to_timedelta(df[col]).dt.total_seconds()
                else:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            except Exception:
                pass

    # Map alternative names
    col_map = {}
    if "S1_s" in df.columns and "Sector1Time" not in df.columns:
        col_map["S1_s"] = "Sector1Time"
    if "S2_s" in df.columns and "Sector2Time" not in df.columns:
        col_map["S2_s"] = "Sector2Time"
    if "S3_s" in df.columns and "Sector3Time" not in df.columns:
        col_map["S3_s"] = "Sector3Time"
    if col_map:
        df = df.rename(columns=col_map)

    required = ["Sector1Time", "Sector2Time", "Sector3Time"]
    if not all(c in df.columns for c in required):
        logger.warning("plot_sector_bars: missing sector columns %s", df.columns.tolist())
        ax.text(0.5, 0.5, "Incomplete sector data", ha="center", va="center", transform=ax.transAxes)
        return

    df = df.dropna(subset=required)
    if df.empty:
        logger.warning("plot_sector_bars: all sectors NaN")
        ax.text(0.5, 0.5, "No valid sector times", ha="center", va="center", transform=ax.transAxes)
        return

    # Need Driver column
    if "Driver" not in df.columns:
        df["Driver"] = [f"D{i}" for i in range(len(df))]

    df["Total"] = df[required].sum(axis=1)
    df = df.sort_values("Total")

    drivers = df["Driver"].values
    s1 = df["Sector1Time"].values
    s2 = df["Sector2Time"].values
    s3 = df["Sector3Time"].values

    y_pos = np.arange(len(drivers))
    bar_height = 0.6

    s1_min, s2_min, s3_min = np.nanmin(s1), np.nanmin(s2), np.nanmin(s3)
    s1_n = s1 - s1_min
    s2_n = s2 - s2_min
    s3_n = s3 - s3_min

    ax.barh(y_pos, s1_n, bar_height, label="Sector 1", color="#FF6B6B", left=0)
    ax.barh(y_pos, s2_n, bar_height, label="Sector 2", color="#4ECDC4", left=s1_n)
    ax.barh(y_pos, s3_n, bar_height, label="Sector 3", color="#45B7D1", left=s1_n + s2_n)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(drivers)
    ax.invert_yaxis()
    ax.set_xlabel("Sector Time Delta from Best (s)")
    ax.grid(True, axis="x", alpha=0.3)
    try:
        ax.legend(loc="lower right", fontsize=8)
    except Exception:
        pass

    # Annotate total
    for i, total in enumerate(df["Total"].values):
        try:
            ax.text(float(s1_n[i] + s2_n[i] + s3_n[i]) + 0.02, i, f"{total:.3f}s", va="center", fontsize=8)
        except Exception:
            pass


def plot_race_pace(
    ax: Any,
    laps: pd.DataFrame,
    drivers: Optional[List[str]] = None,
    colors: Optional[Dict[str, str]] = None,
) -> None:
    """Plot lap times evolution for drivers.

    Args:
        ax: Axes.
        laps: Laps DataFrame with columns Driver, LapNumber, LapTime, PitInTime, PitOutTime.
        drivers: List of driver codes to plot; if None plots all.
        colors: Dict driver -> hex color; if None uses tab20.
    """
    if not _safe_ax(ax):
        logger.warning("plot_race_pace: ax is None")
        return
    if laps is None or laps.empty:
        logger.warning("plot_race_pace: empty laps")
        ax.text(0.5, 0.5, "No lap data", ha="center", va="center", transform=ax.transAxes)
        return
    if "LapTime" not in laps.columns or "LapNumber" not in laps.columns:
        logger.warning("plot_race_pace: missing columns")
        ax.text(0.5, 0.5, "Lap data incomplete", ha="center", va="center", transform=ax.transAxes)
        return

    if drivers is None:
        try:
            drivers = sorted(laps["Driver"].dropna().unique().tolist())
        except Exception:
            drivers = []

    if not drivers:
        logger.warning("plot_race_pace: no drivers")
        return

    # Resolve colors
    if colors is None:
        try:
            import matplotlib.pyplot as plt

            cmap = plt.get_cmap("tab20")
            colors = {drv: cmap(i / max(len(drivers), 1)) for i, drv in enumerate(drivers)}
            # Convert RGBA to hex if needed
            import matplotlib.colors as mcolors

            for k, v in list(colors.items()):
                if not isinstance(v, str):
                    try:
                        colors[k] = mcolors.to_hex(v)
                    except Exception:
                        pass
        except Exception:
            colors = {}

    for drv in drivers:
        try:
            # Filter laps for driver
            dlaps = laps[laps["Driver"] == drv] if "Driver" in laps.columns else pd.DataFrame()
            # Support pick_drivers style already filtered? but laps is full
            if dlaps.empty:
                # try pick method if laps has it
                try:
                    fn = getattr(laps, "pick_drivers", None) or getattr(laps, "pick_driver", None)
                    if fn is not None:
                        dlaps = fn(drv)  # type: ignore[operator]
                except Exception:
                    pass
            if dlaps.empty:
                continue

            # Filter pit laps
            pace_laps = dlaps
            try:
                if "PitInTime" in dlaps.columns and "PitOutTime" in dlaps.columns:
                    pace_laps = dlaps[dlaps["PitInTime"].isna() & dlaps["PitOutTime"].isna()]
                pace_laps = pace_laps[~pace_laps["LapTime"].isna()]
            except Exception:
                pass

            if pace_laps.empty:
                continue

            lap_times_sec = pd.to_timedelta(pace_laps["LapTime"]).dt.total_seconds()
            # Filter outliers? keep simple
            x = pace_laps["LapNumber"]
            y = lap_times_sec
            col = colors.get(drv, "#333333") if isinstance(colors, dict) else "#333333"
            # If col is RGBA tuple, convert
            if not isinstance(col, str):
                try:
                    import matplotlib.colors as mcolors

                    col = mcolors.to_hex(col)
                except Exception:
                    col = "#333333"
            ax.plot(x, y, color=col, linewidth=1.2, alpha=0.7, marker="o", markersize=2, label=drv)
        except Exception as e:
            logger.debug("plot_race_pace driver %s failed: %s", drv, e)
            continue

    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Lap Time (s)")
    ax.grid(True, alpha=0.3)
    try:
        handles, _ = ax.get_legend_handles_labels()
        if handles:
            ax.legend(loc="upper right", fontsize=8, ncol=2)
    except Exception:
        pass

    # Format y-axis as M:SS
    try:
        import matplotlib.pyplot as plt

        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda s, _: f"{int(s//60)}:{s%60:05.2f}")
        )
    except Exception:
        pass


def plot_tire_strategy(
    ax: Any,
    laps: pd.DataFrame,
    drivers: Optional[List[str]] = None,
) -> None:
    """Scatter tire strategy: lap vs driver colored by compound.

    Args:
        ax: Axes.
        laps: DataFrame with LapNumber, Driver, Compound.
        drivers: List to filter; None = all with >5 laps.
    """
    if not _safe_ax(ax):
        logger.warning("plot_tire_strategy: ax is None")
        return
    if laps is None or laps.empty:
        logger.warning("plot_tire_strategy: empty")
        ax.text(0.5, 0.5, "No lap data", ha="center", va="center", transform=ax.transAxes)
        return

    try:
        import fastf1.plotting

        compound_colors = getattr(
            fastf1.plotting,
            "COMPOUND_COLORS",
            {
                "SOFT": "#FF3333",
                "MEDIUM": "#FFD700",
                "HARD": "#FFFFFF",
                "INTERMEDIATE": "#39B54A",
                "WET": "#00AEEF",
                "UNKNOWN": "#888888",
            },
        )
    except Exception:
        compound_colors = {
            "SOFT": "#FF3333",
            "MEDIUM": "#FFD700",
            "HARD": "#FFFFFF",
            "INTERMEDIATE": "#39B54A",
            "WET": "#00AEEF",
            "UNKNOWN": "#888888",
        }

    # Resolve drivers
    if drivers is None:
        try:
            # Only active drivers with >5 laps
            counts = laps["Driver"].value_counts() if "Driver" in laps.columns else pd.Series()
            drivers = [d for d, c in counts.items() if c > 5]
            if not drivers:
                drivers = sorted(laps["Driver"].dropna().unique().tolist()) if "Driver" in laps.columns else []
        except Exception:
            drivers = []

    if not drivers:
        logger.warning("plot_tire_strategy: no drivers")
        ax.text(0.5, 0.5, "Not enough lap data", ha="center", va="center", transform=ax.transAxes)
        return

    for driver in drivers:
        try:
            dlaps = laps[laps["Driver"] == driver] if "Driver" in laps.columns else pd.DataFrame()
            if dlaps.empty:
                continue
            compounds = (
                dlaps["Compound"].fillna("UNKNOWN") if "Compound" in dlaps.columns else pd.Series(["UNKNOWN"] * len(dlaps))
            )
            colors = [compound_colors.get(str(c).upper(), "#888888") for c in compounds]
            lap_nums = dlaps["LapNumber"] if "LapNumber" in dlaps.columns else range(len(dlaps))
            ax.scatter(lap_nums, [driver] * len(dlaps), c=colors, s=80, edgecolors="black", linewidths=0.5)
        except Exception as e:
            logger.debug("tire_strategy driver %s failed: %s", driver, e)
            continue

    ax.set_xlabel("Lap Number")
    ax.set_ylabel("Driver")
    ax.set_title("Tire Strategy")
    ax.grid(True, alpha=0.3)
