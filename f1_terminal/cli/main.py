"""Typer CLI — Phase 1 Core Engine Refactor.

Provides scriptable entry point ``f1`` with subcommands:

    f1 advanced --year 2024 --track Austria --session R --analysis all --save out.png --no-show
    f1 qualifying --year 2024 --track Monza --save quali.png
    f1 practice --year 2024 --track Silverstone --session FP1
    f1 telemetry --year 2026 --gp "Abu Dhabi" --driver VER --plot speed --save speed.png
    f1 schedule --year 2026
    f1 driver --year 2026 --round 1
    f1 --interactive

Pure wrappers over ``f1_terminal.core``. No input() when imported.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from f1_terminal import __version__
from f1_terminal.config import FIGURE_DPI, get_logger, setup_logging

logger = get_logger(__name__)

app = typer.Typer(
    name="f1",
    help="F1 Terminal X — scriptable F1 telemetry toolkit (Phase 1 Core Engine).",
    add_completion=True,
    no_args_is_help=False,
    invoke_without_command=True,
)
# For shell completion `f1 --install-completion` is handled by typer itself.


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"f1-terminal-x {__version__}")
        raise typer.Exit(code=0)


@app.callback()
def main_callback(
    ctx: typer.Context,
    interactive: Annotated[
        bool, typer.Option("--interactive", "-i", help="Launch questionary interactive flow (legacy)")  # noqa: F821
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose logging")] = False,
    version: Annotated[Optional[bool], typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version and exit")] = None,
) -> None:
    """F1 Terminal X CLI."""
    if verbose:
        setup_logging(verbose=True)
    else:
        setup_logging(verbose=False)

    # Only launch interactive if no subcommand was invoked
    if interactive and ctx.invoked_subcommand is None:
        from f1_terminal.cli.interactive import interactive_flow

        interactive_flow()
        raise typer.Exit(code=0)


# ── helpers ──────────────────────────────────────────────────────────────────

def _resolve_track_arg(track: Optional[str]) -> Optional[str]:
    if track is None:
        return None
    return track


def _save_fig(fig, save: Optional[Path]) -> None:
    if save is not None:
        save = Path(save)
        save.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(save), dpi=FIGURE_DPI, bbox_inches="tight")
        typer.echo(f"Saved figure to {save}")


def _maybe_show(show: bool) -> None:
    if show:
        try:
            import matplotlib.pyplot as plt

            plt.show()
        except Exception as e:
            logger.warning("plt.show failed: %s", e)


# ── Commands ─────────────────────────────────────────────────────────────────


@app.command("advanced")
def advanced_cmd(
    year: Annotated[int, typer.Option("--year", "-y", help="Season year")] = 2024,
    track: Annotated[str, typer.Option("--track", "-t", help="Track name or fastf1 identifier (e.g. Austria, Monza, 8)")] = "Austria",
    session: Annotated[str, typer.Option("--session", "-s", help="Session code: R, Q, FP1, FP2, FP3, S, SQ")] = "R",
    analysis: Annotated[str, typer.Option("--analysis", "-a", help="Analysis: track, speed, sector, pace, all")] = "all",
    save: Annotated[Optional[Path], typer.Option("--save", help="Save figure path (PNG/SVG/PDF)")] = None,
    no_show: Annotated[bool, typer.Option("--no-show", help="Do not display figure")] = False,
    drivers: Annotated[Optional[str], typer.Option("--drivers", help="Comma-separated driver codes for speed comparison (e.g. VER,HAM)")] = None,
) -> None:
    """Run advanced race session visualization (track map + speed + sectors + pace)."""
    from f1_terminal.core.session import load_session

    try:
        wrapper = load_session(year, track, session)
    except Exception as e:
        typer.echo(f"Failed to load session {year} {track} {session}: {e}", err=True)
        raise typer.Exit(code=1)

    # Build figure via pure core plotting + matplotlib figure management
    import matplotlib

    matplotlib.use("Agg") if no_show else None  # avoid backend issues? keep default
    import matplotlib.pyplot as plt

    from f1_terminal.core.colors import get_team_color
    from f1_terminal.core.plotting import (
        plot_race_pace,
        plot_sector_bars,
        plot_speed_trace,
    )
    from f1_terminal.core.telemetry import get_driver_telemetry

    # Determine what to plot
    analysis = analysis.lower()
    do_track = analysis in ("track", "all")
    do_speed = analysis in ("speed", "all")
    do_sector = analysis in ("sector", "sectors", "all")
    do_pace = analysis in ("pace", "all")

    # For track overlay: plot all drivers fastest laps overlay
    # Use Track from wrapper.track resolution
    try:
        from f1_terminal.tracks import get_track

        # Try to resolve Track for title
        track_obj = None
        if isinstance(wrapper.track, str):
            # find by fastf1_name
            for t in get_track.__wrapped__ if hasattr(get_track, "__wrapped__") else []:
                pass
            # fallback search TRACKS
            from f1_terminal.tracks import TRACKS

            for t in TRACKS.values():
                if t.fastf1_name.lower() == track.lower() or t.country.lower() == track.lower() or t.name.lower() == track.lower():
                    track_obj = t
                    break
            if track_obj is None:
                # try int
                try:
                    track_obj = get_track(int(track))
                except Exception:
                    track_obj = None
        else:
            track_obj = wrapper.track
    except Exception:
        track_obj = None

    if do_track:
        fig, ax = plt.subplots(figsize=(14, 10), dpi=FIGURE_DPI)
        # Overlay all drivers' fastest telemetry
        # Collect valid entries
        from f1_terminal.core.telemetry import get_fastest_lap

        drivers_list = wrapper.drivers
        # sort by lap time? need fastest lap times
        entries = []
        for drv in drivers_list:
            try:
                fastest, tel = get_driver_telemetry(wrapper, drv)
                # Store lap time for legend sort
                lap_sec = fastest.get("LapTime").total_seconds() if hasattr(fastest.get("LapTime"), "total_seconds") else float("inf")
                entries.append((drv, fastest, tel, lap_sec))
            except Exception:
                continue
        entries.sort(key=lambda x: x[3])
        cmap = plt.get_cmap("tab20")
        legend_lines = []
        legend_labels = []
        for idx, (drv, fastest, tel, _) in enumerate(entries):
            color = get_team_color(wrapper, drv, cmap, idx, len(entries))
            try:
                tel_clean = tel.dropna(subset=["X", "Y"]) if "X" in tel.columns else tel
            except Exception:
                tel_clean = tel
            # Use pure plot_track_map per driver overlapped? Instead manually plot
            # Reuse plot_track_map for each driver on same ax with color
            # For overlay, directly plot line
            try:
                ax.plot(tel_clean["X"], tel_clean["Y"], color=color, linewidth=1.8, alpha=0.9, label=drv)
                import pandas as pd

                def _fmt(t):
                    try:
                        if pd.isna(t):
                            return "N/A"
                        return f"{int(t.total_seconds()//60)}:{t.total_seconds()%60:06.3f}"
                    except Exception:
                        return str(t)

                lap_str = _fmt(fastest.get("LapTime"))
                line = ax.plot([], [], color=color, linewidth=2.5)[0]
                legend_lines.append(line)
                legend_labels.append(f"{drv} ({lap_str})")
            except Exception:
                continue
        ax.set_aspect("equal")
        title_track = getattr(track_obj, "name", str(track)) if track_obj else str(track)
        ax.set_title(f"Fastest Laps Overlay — {year} {title_track} {session}", fontsize=14, fontweight="bold")
        ax.axis("off")
        if legend_lines:
            ax.legend(handles=legend_lines, labels=legend_labels, loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=8)
        plt.tight_layout()
        plt.subplots_adjust(right=0.82)
        if save is not None and analysis == "track":
            _save_fig(fig, save)
        elif save is not None and analysis == "all":
            _save_fig(fig, Path(str(save).replace(".png", "_track.png")) if str(save).endswith(".png") else save)
        if not no_show:
            _maybe_show(True)
        plt.close(fig)

    if do_speed:
        # Speed traces per driver
        target_drivers = None
        if drivers:
            target_drivers = [d.strip().upper() for d in drivers.split(",") if d.strip()]
        else:
            target_drivers = wrapper.drivers[:4]

        n = len(target_drivers) if target_drivers else 1
        fig, axes = plt.subplots(n, 1, figsize=(14, 3 * max(n, 1)), sharex=True, dpi=FIGURE_DPI)
        if n == 1:
            axes = [axes]  # type: ignore[list-item]
        else:
            axes = list(axes)  # type: ignore[assignment]
        cmap = plt.get_cmap("tab20")
        for idx, (ax, drv) in enumerate(zip(axes, target_drivers or [])):
            try:
                fastest, tel = get_driver_telemetry(wrapper, drv)
                color = get_team_color(wrapper, drv, cmap, idx, len(target_drivers or []))
                plot_speed_trace(ax, tel, color=color)
                # Title with lap time
                try:
                    import pandas as pd

                    lt = fastest.get("LapTime")
                    lt_str = f"{int(lt.total_seconds()//60)}:{lt.total_seconds()%60:06.3f}" if hasattr(lt, "total_seconds") else str(lt)
                    ax.set_title(f"{drv} — {lt_str}", fontsize=11, loc="left")
                except Exception:
                    ax.set_title(drv)
            except Exception as e:
                ax.text(0.5, 0.5, f"{drv}: {e}", ha="center", va="center", transform=ax.transAxes)
        if target_drivers:
            axes[-1].set_xlabel("Distance (m)")
            fig.suptitle(f"Speed Comparison — {year} {track} {session}", fontsize=13, fontweight="bold", y=1.01)
        plt.tight_layout()
        if save is not None:
            save_path = Path(str(save).replace(".png", "_speed.png")) if do_track and str(save).endswith(".png") and analysis == "all" else save
            _save_fig(fig, save_path)  # type: ignore[arg-type]
        if not no_show:
            _maybe_show(True)
        plt.close(fig)

    if do_sector:
        # Build sector df from fastest laps
        from f1_terminal.core.telemetry import get_fastest_lap

        rows = []
        for drv in wrapper.drivers:
            try:
                fastest = get_fastest_lap(wrapper, drv)
                rows.append(
                    {
                        "Driver": drv,
                        "Sector1Time": fastest.get("Sector1Time"),
                        "Sector2Time": fastest.get("Sector2Time"),
                        "Sector3Time": fastest.get("Sector3Time"),
                    }
                )
            except Exception:
                continue
        import pandas as pd

        df_sectors = pd.DataFrame(rows)
        fig, ax = plt.subplots(figsize=(12, max(6, len(df_sectors) * 0.4)), dpi=FIGURE_DPI)
        plot_sector_bars(ax, df_sectors)
        ax.set_title(f"Sector Time Analysis — {year} {track} {session}", fontsize=13, fontweight="bold")
        plt.tight_layout()
        if save is not None:
            save_path = Path(str(save).replace(".png", "_sector.png")) if analysis == "all" and str(save).endswith(".png") else save
            _save_fig(fig, save_path)  # type: ignore[arg-type]
        if not no_show:
            _maybe_show(True)
        plt.close(fig)

    if do_pace:
        fig, ax = plt.subplots(figsize=(14, 8), dpi=FIGURE_DPI)
        import matplotlib.pyplot as plt

        from f1_terminal.core.colors import get_team_color

        cmap = plt.get_cmap("tab20")
        colors = {drv: get_team_color(wrapper, drv, cmap, i, len(wrapper.drivers)) for i, drv in enumerate(wrapper.drivers)}
        plot_race_pace(ax, wrapper.laps, wrapper.drivers, colors)
        ax.set_title(f"Race Pace Evolution — {year} {track} {session}", fontsize=13, fontweight="bold")
        plt.tight_layout()
        if save is not None:
            save_path = Path(str(save).replace(".png", "_pace.png")) if analysis == "all" and str(save).endswith(".png") else save
            _save_fig(fig, save_path)  # type: ignore[arg-type]
        if not no_show:
            _maybe_show(True)
        plt.close(fig)

    # Single save fallback if only one fig? The per-analysis saves already handled
    typer.echo(f"Advanced analysis complete for {year} {track} {session}")


@app.command("qualifying")
def qualifying_cmd(
    year: Annotated[int, typer.Option("--year", "-y", help="Season year")] = 2024,
    track: Annotated[str, typer.Option("--track", "-t", help="Track name or fastf1 identifier")] = "Monza",
    save: Annotated[Optional[Path], typer.Option("--save", help="Save figure path")] = None,
    no_show: Annotated[bool, typer.Option("--no-show", help="Do not display figure")] = False,
) -> None:
    """Compare all drivers' fastest qualifying laps."""
    from f1_terminal.core.session import load_session

    try:
        wrapper = load_session(year, track, "Q")
    except Exception as e:
        typer.echo(f"Failed to load session {year} {track} Q: {e}", err=True)
        raise typer.Exit(code=1)

    import matplotlib.pyplot as plt

    from f1_terminal.core.colors import get_team_color
    from f1_terminal.core.telemetry import get_driver_telemetry

    fig, ax = plt.subplots(figsize=(12, 9), dpi=FIGURE_DPI)
    cmap = plt.get_cmap("tab20")
    legend_entries = []
    for i, drv in enumerate(sorted(wrapper.drivers)):
        try:
            fastest, tel = get_driver_telemetry(wrapper, drv)
            color = get_team_color(wrapper, drv, cmap, i, len(wrapper.drivers))
            tel_clean = tel.dropna(subset=["X", "Y"]) if "X" in tel.columns else tel
            import pandas as pd

            def _fmt(t):
                try:
                    if pd.isna(t):
                        return "N/A"
                    return f"{int(t.total_seconds()//60)}:{t.total_seconds()%60:06.3f}"
                except Exception:
                    return str(t)

            lap_str = _fmt(fastest.get("LapTime"))
            lap_sec = fastest.get("LapTime").total_seconds() if hasattr(fastest.get("LapTime"), "total_seconds") else float("inf")
            line, = ax.plot(tel_clean["X"], tel_clean["Y"], color=color, linewidth=1.5, alpha=0.85)
            legend_entries.append((line, lap_sec, f"{drv} ({lap_str})"))
        except Exception:
            continue

    ax.set_aspect("equal")
    ax.set_title(f"All Drivers' Fastest Laps - {year} {track} GP Qualifying", fontsize=14, fontweight="bold")
    ax.axis("off")
    if legend_entries:
        legend_entries.sort(key=lambda x: x[1])
        ax.legend(handles=[p[0] for p in legend_entries], labels=[p[2] for p in legend_entries], loc="best", fontsize=8, framealpha=0.9, title="Driver (Fastest Lap)")
    plt.tight_layout()
    if save is not None:
        _save_fig(fig, save)
    if not no_show:
        _maybe_show(True)
    plt.close(fig)
    typer.echo(f"Qualifying plotted for {year} {track}")


@app.command("practice")
def practice_cmd(
    year: Annotated[int, typer.Option("--year", "-y", help="Season year")] = 2024,
    track: Annotated[str, typer.Option("--track", "-t", help="Track")] = "Silverstone",
    session: Annotated[str, typer.Option("--session", "-s", help="Session code: FP1, FP2, FP3")] = "FP1",
    save: Annotated[Optional[Path], typer.Option("--save", help="Save figure path")] = None,
    no_show: Annotated[bool, typer.Option("--no-show", help="Do not display figure")] = False,
) -> None:
    """Compare all drivers' fastest laps from a practice session."""
    from f1_terminal.core.session import load_session

    if session not in ("FP1", "FP2", "FP3"):
        typer.echo(f"Practice session must be FP1/FP2/FP3, got {session}", err=True)
        raise typer.Exit(code=2)
    try:
        wrapper = load_session(year, track, session)
    except Exception as e:
        typer.echo(f"Failed to load session {year} {track} {session}: {e}", err=True)
        raise typer.Exit(code=1)

    import matplotlib.pyplot as plt

    from f1_terminal.core.colors import get_team_color
    from f1_terminal.core.telemetry import get_driver_telemetry

    fig, ax = plt.subplots(figsize=(12, 9), dpi=FIGURE_DPI)
    cmap = plt.get_cmap("tab20")
    legend_entries = []
    for i, drv in enumerate(sorted(wrapper.drivers)):
        try:
            fastest, tel = get_driver_telemetry(wrapper, drv)
            color = get_team_color(wrapper, drv, cmap, i, len(wrapper.drivers))
            tel_clean = tel.dropna(subset=["X", "Y"]) if "X" in tel.columns else tel
            import pandas as pd

            def _fmt(t):
                try:
                    if pd.isna(t):
                        return "N/A"
                    return f"{int(t.total_seconds()//60)}:{t.total_seconds()%60:06.3f}"
                except Exception:
                    return str(t)

            lap_str = _fmt(fastest.get("LapTime"))
            lap_sec = fastest.get("LapTime").total_seconds() if hasattr(fastest.get("LapTime"), "total_seconds") else float("inf")
            line, = ax.plot(tel_clean["X"], tel_clean["Y"], color=color, linewidth=1.5, alpha=0.85)
            legend_entries.append((line, lap_sec, f"{drv} ({lap_str})"))
        except Exception:
            continue
    ax.set_aspect("equal")
    ax.set_title(f"All Drivers' Fastest Laps - {year} {track} GP {session}", fontsize=14, fontweight="bold")
    ax.axis("off")
    if legend_entries:
        legend_entries.sort(key=lambda x: x[1])
        ax.legend(handles=[p[0] for p in legend_entries], labels=[p[2] for p in legend_entries], loc="best", fontsize=8, framealpha=0.9)
    plt.tight_layout()
    if save is not None:
        _save_fig(fig, save)
    if not no_show:
        _maybe_show(True)
    plt.close(fig)
    typer.echo(f"Practice {session} plotted for {year} {track}")


@app.command()
def telemetry(
    year: Annotated[int, typer.Option("--year", "-y", help="Season year")] = 2026,
    gp: Annotated[str, typer.Option("--gp", help="Grand Prix name or fastf1 identifier")] = "Abu Dhabi",
    driver: Annotated[str, typer.Option("--driver", "-d", help="Driver code (e.g. VER)")] = "VER",
    plot: Annotated[str, typer.Option("--plot", help="Plot type: speed, throttle, track, gear, summary, all")] = "speed",
    save: Annotated[Optional[Path], typer.Option("--save", help="Save figure path")] = None,
    no_show: Annotated[bool, typer.Option("--no-show", help="Do not display figure")] = False,
) -> None:
    """Inspect a driver's fastest lap telemetry."""
    from f1_terminal.core.session import load_session
    from f1_terminal.core.telemetry import get_driver_telemetry

    # gp maps to track arg, driver to driver code
    try:
        wrapper = load_session(year, gp, "R")
    except Exception as e:
        typer.echo(f"Failed to load session {year} {gp} R: {e}", err=True)
        raise typer.Exit(code=1)

    try:
        fastest, tel = get_driver_telemetry(wrapper, driver)
    except Exception as e:
        typer.echo(f"Telemetry error for {driver}: {e}", err=True)
        raise typer.Exit(code=1)

    import matplotlib.pyplot as plt

    from f1_terminal.core.colors import get_team_color

    cmap = plt.get_cmap("tab20")
    # Find idx
    try:
        idx = sorted(wrapper.drivers).index(driver)
    except Exception:
        idx = 0
    color = get_team_color(wrapper, driver, cmap, idx, max(len(wrapper.drivers), 1))

    plot = plot.lower()
    if plot == "speed":
        fig, ax = plt.subplots(figsize=(14, 5), dpi=FIGURE_DPI)
        from f1_terminal.core.plotting import plot_speed_trace

        plot_speed_trace(ax, tel, color=color)
        ax.set_title(f"Speed Trace — {driver}\n{year} {gp} — Fastest Lap", fontsize=13, fontweight="bold")
        plt.tight_layout()
    elif plot == "throttle":
        fig, ax = plt.subplots(figsize=(14, 5), dpi=FIGURE_DPI)
        from f1_terminal.core.plotting import plot_throttle_brake

        plot_throttle_brake(ax, tel)
        ax.set_title(f"Throttle & Brake — {driver}\n{year} {gp} — Fastest Lap", fontsize=13, fontweight="bold")
        plt.tight_layout()
    elif plot == "track":
        fig, ax = plt.subplots(figsize=(12, 10), dpi=FIGURE_DPI)
        from f1_terminal.core.plotting import plot_track_map

        plot_track_map(ax, tel, color=color)
        ax.set_title(f"Track Map — {driver}\n{year} {gp}", fontsize=13, fontweight="bold")
        plt.tight_layout()
    elif plot == "gear":
        fig, ax = plt.subplots(figsize=(14, 4), dpi=FIGURE_DPI)
        from f1_terminal.core.plotting import plot_gear_map

        plot_gear_map(ax, tel)
        ax.set_title(f"Gear Usage — {driver}\n{year} {gp}", fontsize=13, fontweight="bold")
        plt.tight_layout()
    elif plot == "summary":
        # text summary via telemetry stats
        typer.echo(f"Telemetry summary for {driver} ({year} {gp}) — {len(tel)} points")
        if "Speed" in tel.columns:
            typer.echo(f"  Max Speed: {tel['Speed'].max():.1f} km/h")
            typer.echo(f"  Avg Speed: {tel['Speed'].mean():.1f} km/h")
        fig = None  # type: ignore[assignment]
    elif plot == "all":
        fig, axes = plt.subplots(4, 1, figsize=(14, 12), dpi=FIGURE_DPI)
        from f1_terminal.core.plotting import (
            plot_gear_map,
            plot_speed_trace,
            plot_throttle_brake,
            plot_track_map,
        )

        plot_speed_trace(axes[0], tel, color=color)
        plot_throttle_brake(axes[1], tel)
        plot_gear_map(axes[2], tel)
        plot_track_map(axes[3], tel, color=color)
        plt.tight_layout()
    else:
        typer.echo(f"Unknown plot type: {plot} (choose speed, throttle, track, gear, summary, all)", err=True)
        raise typer.Exit(code=2)

    if plot != "summary":
        if save is not None:
            assert fig is not None
            _save_fig(fig, save)
        if not no_show:
            _maybe_show(True)
        if fig is not None:
            plt.close(fig)


@app.command()
def schedule(
    year: Annotated[int, typer.Option("--year", "-y", help="Season year")] = 2026,
) -> None:
    """Display season schedule."""
    from f1_terminal.core.session import get_schedule

    try:
        df = get_schedule(year)
    except Exception as e:
        typer.echo(f"Failed to load schedule for {year}: {e}", err=True)
        raise typer.Exit(code=1)

    if df is None or df.empty:
        typer.echo(f"No schedule for {year}")
        return

    # Pretty print subset
    try:
        cols = [c for c in ["RoundNumber", "Country", "Location", "OfficialEventName", "EventName", "EventDate"] if c in df.columns]
        typer.echo(df[cols].to_string(index=False))
    except Exception:
        typer.echo(df.to_string(index=False))


@app.command()
def driver(
    year: Annotated[int, typer.Option("--year", "-y", help="Season year")] = 2026,
    round: Annotated[int, typer.Option("--round", "-r", help="Round number (1-22)")] = 1,  # noqa: A002 - round is used by typer, ok
) -> None:
    """Show driver lineup for a round."""
    from f1_terminal.core.session import get_schedule, load_session

    try:
        sched = get_schedule(year)
    except Exception as e:
        typer.echo(f"Failed to load schedule: {e}", err=True)
        raise typer.Exit(code=1)

    # Find event name for round
    try:
        match = sched[sched["RoundNumber"] == round]
        if match.empty:
            typer.echo(f"Round {round} not found for {year}", err=True)
            raise typer.Exit(code=2)
        event_name = match.iloc[0].get("EventName") or match.iloc[0].get("OfficialEventName") or str(match.iloc[0].get("Country", round))
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Invalid round: {e}", err=True)
        raise typer.Exit(code=2)

    try:
        wrapper = load_session(year, str(event_name), "R")
    except Exception as e:
        typer.echo(f"Failed to load session for round {round} ({event_name}): {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"\n{event_name} — Driver Lineup ({year} Round {round})")
    typer.echo("=" * 70)
    for code in wrapper.drivers:
        try:
            info = wrapper.session.get_driver(code)
            # robust field extraction
            def _field(key: str, default: str = "Unknown") -> str:
                try:
                    val = info[key] if key in info else None  # type: ignore[index,operator]
                    if val is not None and str(val) != "nan" and str(val).strip():
                        return str(val)
                except Exception:
                    pass
                try:
                    val = getattr(info, key, None)
                    if val is not None and str(val) != "nan":
                        return str(val)
                except Exception:
                    pass
                try:
                    val = info.get(key, None)  # type: ignore[union-attr]
                    if val is not None and str(val) != "nan":
                        return str(val)
                except Exception:
                    pass
                return default

            name = _field("BroadcastName", str(code))
            num = _field("DriverNumber", str(code))
            team = _field("TeamName", "Unknown")
            color = _field("TeamColor", "000000").lstrip("#")
            typer.echo(f"\n{name}")
            typer.echo(f"Code: {code}  Number: {num}  Team: {team}  Color: #{color}")
        except Exception as e:
            typer.echo(f"{code}: failed ({e})")


@app.command("compare")
def compare_cmd(
    year: Annotated[int, typer.Option("--year", "-y")] = 2024,
    track: Annotated[str, typer.Option("--track", "-t")] = "Silverstone",
    session: Annotated[str, typer.Option("--session", "-s")] = "R",
    drivers: Annotated[str, typer.Option("--drivers", help="Comma-separated, e.g. VER,HAM,LEC")] = "VER,HAM",
    save: Annotated[Optional[Path], typer.Option("--save")] = None,
    no_show: Annotated[bool, typer.Option("--no-show")] = False,
) -> None:
    """Compare drivers' speed traces (backlog: f1 compare)."""
    from f1_terminal.core.session import load_session
    from f1_terminal.core.telemetry import get_driver_telemetry

    codes = [d.strip().upper() for d in drivers.split(",") if d.strip()]
    try:
        wrapper = load_session(year, track, session)
    except Exception as e:
        typer.echo(f"Load failed: {e}", err=True)
        raise typer.Exit(code=1)
    import matplotlib.pyplot as plt

    from f1_terminal.core.colors import get_team_color
    from f1_terminal.core.plotting import plot_speed_trace

    fig, axes = plt.subplots(len(codes), 1, figsize=(14, 3 * max(len(codes), 1)), sharex=True, dpi=FIGURE_DPI)
    if len(codes) == 1:
        axes = [axes]  # type: ignore[list-item]
    else:
        axes = list(axes)  # type: ignore[assignment]
    cmap = plt.get_cmap("tab20")
    for i, (ax, drv) in enumerate(zip(axes, codes)):
        try:
            fastest, tel = get_driver_telemetry(wrapper, drv)
            plot_speed_trace(ax, tel, color=get_team_color(wrapper, drv, cmap, i, len(codes)))
            ax.set_title(drv, loc="left")
        except Exception as e:
            ax.text(0.5, 0.5, f"{drv}: {e}", ha="center", transform=ax.transAxes)
    plt.tight_layout()
    if save is not None:
        _save_fig(fig, save)
    if not no_show:
        _maybe_show(True)
    plt.close(fig)
    typer.echo(f"Compared {', '.join(codes)} for {year} {track} {session}")


@app.command("export")
def export_cmd(
    year: Annotated[int, typer.Option("--year", "-y")] = 2024,
    track: Annotated[str, typer.Option("--track", "-t")] = "Monza",
    session: Annotated[str, typer.Option("--session", "-s")] = "Q",
    format: Annotated[str, typer.Option("--format", help="csv or parquet")] = "csv",
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("telemetry.csv"),  # type: ignore[assignment]
    driver: Annotated[Optional[str], typer.Option("--driver", "-d")] = None,
) -> None:
    """Export telemetry/laps (backlog: f1 export --format parquet)."""
    fmt = format.lower()
    if fmt not in ("csv", "parquet"):
        typer.echo("format must be csv or parquet", err=True)
        raise typer.Exit(code=2)
    from f1_terminal.core.session import load_session

    try:
        wrapper = load_session(year, track, session)
    except Exception:
        from f1_terminal.tui.workers.session_loader import load_demo_session

        wrapper = load_demo_session().wrapper
        typer.echo("Using offline demo data")
    if driver:
        from f1_terminal.core.telemetry import get_driver_telemetry

        try:
            _f, df = get_driver_telemetry(wrapper, driver.upper())
        except Exception as e:
            typer.echo(f"Telemetry error: {e}", err=True)
            raise typer.Exit(code=1)
    else:
        df = wrapper.laps
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "csv":
        df.to_csv(str(output), index=False)
    else:
        df.to_parquet(str(output), index=False)
    typer.echo(f"Exported {len(df)} rows to {output}")


@app.command("config")
def config_cmd(
    set: Annotated[Optional[str], typer.Option("--set", help="KEY=VALUE")] = None,  # noqa: A002
    list_all: Annotated[bool, typer.Option("--list", help="List settings")] = False,  # noqa: F821
) -> None:
    """Show or set config (backlog: f1 config --set cache_dir ~/f1cache)."""
    from f1_terminal.config import settings

    if list_all or set is None:
        typer.echo(f"cache_dir={settings.cache_dir}")
        typer.echo(f"figure_dpi={settings.figure_dpi}")
        typer.echo(f"min_year={settings.min_year} max_year={settings.max_year}")
        typer.echo(f"default_season={settings.default_season}")
        typer.echo(f"log_level={settings.log_level}")
        return
    if "=" not in set:
        typer.echo("Use --set KEY=VALUE", err=True)
        raise typer.Exit(code=2)
    key, value = set.split("=", 1)
    key, value = key.strip(), value.strip()
    if key == "cache_dir":
        typer.echo(f"Set cache_dir={value} via env F1_CACHE_DIR={value} (persist in .env)")
    elif key == "figure_dpi":
        typer.echo(f"Set figure_dpi={value} via env F1_FIGURE_DPI={value}")
    else:
        typer.echo(f"Unknown key {key} (known: cache_dir, figure_dpi)", err=True)
        raise typer.Exit(code=2)


@app.command("cache")
def cache_cmd(
    status: Annotated[bool, typer.Option("--status", help="Show cache status")] = False,
    clear: Annotated[bool, typer.Option("--clear", help="Clear cache")] = False,
    year: Annotated[Optional[int], typer.Option("--year", "-y")] = None,
) -> None:
    """Cache management (P4-2): f1 cache --status / --clear --year 2026."""
    from f1_terminal.core.cache import cache_status as _status
    from f1_terminal.core.cache import clear_cache as _clear

    if clear:
        n = _clear(year)
        typer.echo(f"Cleared {n} cache entries" + (f" for {year}" if year else ""))
        return
    info = _status()
    typer.echo(f"cache_dir={info['cache_dir']} exists={info['exists']}")
    typer.echo(f"files={info['files']} bytes={info['bytes']}")
    typer.echo(f"fastf1_version={info['fastf1_version']}")
    entries = info.get("entries", {})
    if isinstance(entries, dict) and entries:
        for k in list(entries)[:10]:
            typer.echo(f"  {k}")
    elif status or True:
        pass


@app.command("predict")
def predict_cmd(
    year: Annotated[int, typer.Option("--year", "-y")] = 2024,
    track: Annotated[str, typer.Option("--track", "-t")] = "Monza",
    model: Annotated[Optional[Path], typer.Option("--model", help="artifacts/model.pkl")] = None,
    train_model: Annotated[bool, typer.Option("--train", help="Train on session and save")] = False,
    output: Annotated[Optional[Path], typer.Option("--output", "-o")] = None,
) -> None:
    """Quali-gap prediction (P4-4): f1 predict --year 2024 --track Monza."""
    from f1_terminal.core.features import engineer_lap_features
    from f1_terminal.core.session import load_session

    try:
        wrapper = load_session(year, track, "Q")
    except Exception:
        from f1_terminal.tui.workers.session_loader import load_demo_session

        wrapper = load_demo_session().wrapper
        typer.echo("Using offline demo data")
    df = engineer_lap_features(wrapper.session if hasattr(wrapper, "session") else wrapper)
    if df.empty:
        typer.echo("No features", err=True)
        raise typer.Exit(code=1)
    from f1_terminal.ml import load_model as _load
    from f1_terminal.ml import predict as _predict
    from f1_terminal.ml import save_model as _save
    from f1_terminal.ml import train as _train

    pipe = None
    if model is not None and Path(model).exists() and not train_model:
        pipe = _load(model)
    else:
        try:
            pipe = _train(df)
        except Exception as e:
            typer.echo(f"Train failed: {e}", err=True)
            raise typer.Exit(code=1)
        if model is not None:
            _save(pipe, model)
            typer.echo(f"Saved model to {model}")
    preds = _predict(pipe, df)
    out_df = df[["Driver", "LapNumber", "LapTime_s"]].copy()
    out_df["PredictedGap_s"] = preds.values
    typer.echo(out_df.to_string(index=False))
    if output is not None:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        out_df.to_csv(str(output), index=False)
        typer.echo(f"Wrote {output}")


def main() -> None:
    """Entrypoint for console script ``f1``."""
    app()


if __name__ == "__main__":
    main()
