import pandas as pd
import streamlit as st

from core import (KEY_SENSORS, SENSOR_LABELS, get_config, parse_single_engine, predict_all_engines,
                  required_cycles, sample_engine_text)
from ui import empty_state, html, page_header, rul_result, sensor_trends

sensors = get_config()["sensor_columns"]
need = required_cycles()

page_header("Check an Engine",
            "Paste or upload one engine's recent sensor readings to get its remaining-life forecast.")


def load_example(kind):
    st.session_state.engine_text = sample_engine_text(kind)
    st.session_state.pop("engine_result", None)


left, right = st.columns([1, 1.1], gap="large")

with left:
    with st.container(border=True):
        st.markdown("**1 · Provide sensor history**")
        st.caption(f"At least {need} consecutive cycles, one row per cycle, "
                   f"{len(sensors)} sensor values per row.")

        e1, e2 = st.columns(2)
        e1.button("Try a worn engine", on_click=load_example, args=("critical",),
                  icon=":material/warning:", width="stretch")
        e2.button("Try a healthy engine", on_click=load_example, args=("healthy",),
                  icon=":material/check_circle:", width="stretch")

        tab_paste, tab_upload = st.tabs(["Paste readings", "Upload file"])
        with tab_paste:
            text = st.text_area(
                "Sensor readings", key="engine_text", height=200, label_visibility="collapsed",
                placeholder="One cycle per line, values separated by spaces or commas.\n"
                            "Or click one of the example buttons above.",
            )
        with tab_upload:
            upload = st.file_uploader("Engine file (.csv or .txt)", type=["csv", "txt"])

        with st.expander("Which sensors, in what order?"):
            html("<ol class='es-list'>" +
                 "".join(f"<li>{SENSOR_LABELS.get(s, s)} <span>({s})</span></li>"
                         for s in sensors) + "</ol>")
            st.caption("Full 26-column C-MAPSS rows are accepted too.")

        go = st.button("Forecast remaining life", type="primary", width="stretch",
                       icon=":material/insights:")

    if go:
        source = upload.getvalue().decode("utf-8", "replace") if upload else text
        if not source.strip():
            st.warning("Add some sensor readings first, or try one of the example engines.")
        else:
            try:
                parsed = parse_single_engine(source, sensors)
                if len(parsed) < need:
                    st.error(f"We need at least {need} cycles to make a forecast. "
                             f"You provided {len(parsed)}.")
                else:
                    with st.spinner("Analyzing sensor history…"):
                        result = predict_all_engines(parsed)
                    st.session_state.engine_result = (parsed, result.iloc[0])
            except (ValueError, pd.errors.ParserError) as error:
                st.error(f"We couldn't read that data. {error}")

with right:
    if "engine_result" not in st.session_state:
        empty_state("📈", "Your forecast will appear here",
                    "Add sensor readings on the left, or try an example engine.")
    else:
        history, row = st.session_state.engine_result
        st.markdown("**2 · Your forecast**")
        rul_result(row.predicted_RUL, row.risk_level, int(row.last_observed_cycle))

        with st.container(border=True):
            st.markdown("**Sensor trends**")
            chosen = st.multiselect("Sensors", sensors, default=[s for s in KEY_SENSORS if s in sensors],
                                    format_func=lambda s: SENSOR_LABELS.get(s, s),
                                    label_visibility="collapsed")
            if chosen:
                st.altair_chart(sensor_trends(history, chosen, width=175))
