"""Streamlit app reusing f1_terminal.core (P3b-1).

Run: streamlit run f1_terminal/web/app.py
Deploy: Streamlit Community Cloud or Hugging Face Spaces (1-click).
"""

from __future__ import annotations


def main() -> None:
    try:
        import streamlit as st  # type: ignore[import-not-found]
    except ImportError:
        print("streamlit not installed; pip install streamlit")
        return

    from f1_terminal.tracks import TRACKS

    st.set_page_config(page_title="F1 Terminal X", layout="wide")
    st.title("F1 Terminal X — Web")

    with st.sidebar:
        st.header("Session")
        year = st.number_input("Year", min_value=2018, max_value=2030, value=2023)
        track_names = [t.fastf1_name for t in TRACKS.values()]
        track = st.selectbox("Track", track_names, index=track_names.index("Monza") if "Monza" in track_names else 0)
        session_code = st.radio("Session", ["FP1", "FP2", "FP3", "Q", "R"], index=3)
        load = st.button("Load")

    if load:
        from f1_terminal.core.session import load_session

        with st.spinner(f"Loading {year} {track} {session_code}…"):
            try:
                wrapper = load_session(int(year), str(track), str(session_code))
            except Exception as e:
                st.error(f"Load failed: {e}")
                st.info("Tip: use the bundled demo via `f1-tui --demo` offline.")
                return
        st.success(f"Loaded {len(wrapper.drivers)} drivers")
        try:
            import pandas as pd

            from f1_terminal.core.telemetry import get_fastest_lap

            rows = []
            for drv in wrapper.drivers:
                try:
                    f = get_fastest_lap(wrapper, drv)
                    rows.append({"Driver": drv, "LapTime": str(f.get("LapTime"))})
                except Exception:
                    continue
            st.dataframe(pd.DataFrame(rows))
        except Exception:
            pass
        # Matplotlib figure (core reuse)
        try:
            import matplotlib.pyplot as plt

            from f1_terminal.core.plotting import plot_track_map
            from f1_terminal.core.telemetry import get_driver_telemetry

            drv = wrapper.drivers[0]
            _f, tel = get_driver_telemetry(wrapper, drv)
            fig, ax = plt.subplots()
            plot_track_map(ax, tel)
            st.pyplot(fig)
        except Exception as e:
            st.warning(f"Plot failed: {e}")
        # Plotly hover/zoom when available
        try:
            from f1_terminal.core.plotting_plotly import plot_speed_plotly
            from f1_terminal.core.telemetry import get_driver_telemetry as _gdt

            _f, tel = _gdt(wrapper, wrapper.drivers[0])
            st.plotly_chart(plot_speed_plotly(tel))
        except Exception:
            pass
        # CSV download
        try:
            st.download_button("Download laps CSV", wrapper.laps.to_csv(index=False), file_name="laps.csv")
        except Exception:
            pass


if __name__ == "__main__":
    main()
