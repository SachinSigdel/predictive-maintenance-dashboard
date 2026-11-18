import pandas as pd
import streamlit as st

from core import (KEY_SENSORS, RISK, RISK_ORDER, SENSOR_LABELS, get_config, load_sample_data,
                  predict_all_engines, read_cmapss_file, required_cycles,
                  sample_fleet_predictions)
from ui import (badge, empty_state, engine_card_html, html, kpi, page_header,
                risk_donut, rul_chart, rul_result, sensor_trends)

sensors = get_config()["sensor_columns"]
need = required_cycles()

page_header("Fleet Dashboard", "Every engine ranked by how soon it needs maintenance.")

# ---- Data source ----
source = st.segmented_control(
    "Data source", ["Demo fleet", "Upload your fleet"], default="Demo fleet",
    key="fleet_source", label_visibility="collapsed",
) or "Demo fleet"

raw_data, predictions, is_demo = None, None, source == "Demo fleet"

if is_demo:
    raw_data = load_sample_data()
    predictions = sample_fleet_predictions()
    st.caption("Showing 100 engines from NASA's C-MAPSS FD001 test set. "
               "Each engine's true remaining life is shown next to the forecast.")
else:
    with st.container(border=True):
        uploaded = st.file_uploader(
            "Upload a C-MAPSS fleet file (.txt)", type=["txt"],
            help="Whitespace-separated, 26 columns: engine id, cycle, 3 operational settings, 21 sensors.",
        )
        st.caption(f"Each engine needs at least {need} cycles of history. "
                   "Don't have a file? Switch to **Demo fleet** above.")
    if uploaded is not None:
        try:
            raw_data = read_cmapss_file(uploaded)
            st.session_state.fleet_upload = (uploaded.name, raw_data)
        except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as error:
            st.error(f"We couldn't read **{uploaded.name}**. {error}")
    elif "fleet_upload" in st.session_state:
        name, raw_data = st.session_state.fleet_upload
        st.caption(f"Using previously uploaded file **{name}**.")

    if raw_data is not None:
        with st.spinner("Forecasting remaining life for every engine…"):
            predictions = predict_all_engines(raw_data)
    else:
        empty_state("📄", "No fleet uploaded yet",
                    "Upload a C-MAPSS file above to rank your engines.")
        st.stop()

if predictions.empty:
    st.error(f"No forecasts could be made. Each engine needs at least {need} consecutive cycles.")
    st.stop()

skipped = raw_data["engine_id"].nunique() - len(predictions)
counts = predictions["risk_level"].value_counts()


# ---- Engine detail dialog ----
@st.dialog("Engine details", width="large")
def engine_dialog(engine_id):
    row = predictions.loc[predictions.engine_id == engine_id].iloc[0]
    html(f'<div style="display:flex;align-items:center;gap:.7rem;margin-bottom:.6rem">'
         f'<span style="font-size:1.4rem;font-weight:800">Engine {engine_id}</span>{badge(row.risk_level)}</div>')
    rul_result(row.predicted_RUL, row.risk_level, int(row.last_observed_cycle))
    if "actual_RUL" in row and pd.notna(row.actual_RUL):
        st.caption(f"Actual remaining life in the NASA test set: **{row.actual_RUL:.0f} cycles** "
                   f"(forecast error {row.predicted_RUL - row.actual_RUL:+.0f}).")

    st.markdown("##### Sensor trends")
    chosen = st.multiselect("Sensors", sensors, default=[s for s in KEY_SENSORS if s in sensors],
                            format_func=lambda s: SENSOR_LABELS.get(s, s),
                            label_visibility="collapsed")
    history = raw_data.loc[raw_data.engine_id == engine_id].sort_values("cycle")
    if chosen:
        st.altair_chart(sensor_trends(history, chosen))
    else:
        st.caption("Pick at least one sensor to see its trend.")


# ---- KPIs ----
k1, k2, k3, k4 = st.columns(4)
kpi(k1, "Engines monitored", len(predictions),
    f"{skipped} skipped (too little history)" if skipped else "All engines scored")
kpi(k2, "Critical", int(counts.get("Critical", 0)), "≤ 15 cycles left", RISK["Critical"]["color"])
kpi(k3, "High risk", int(counts.get("High", 0)), "16–30 cycles left", RISK["High"]["color"])
kpi(k4, "Fleet median life", f"{predictions.predicted_RUL.median():.0f}", "cycles remaining")

# ---- Needs attention ----
urgent = predictions[predictions.risk_level.isin(["Critical", "High"])]
st.markdown("### Needs attention")
if urgent.empty:
    st.success("No engines are in the Critical or High tiers. The fleet looks healthy.")
else:
    st.caption(f"{len(urgent)} engines should be scheduled for maintenance, most urgent first.")
    shown = urgent.head(8)
    cols = st.columns(4)
    for i, r in enumerate(shown.itertuples()):
        with cols[i % 4].container(border=True):
            html(engine_card_html(r.engine_id, r.predicted_RUL, r.risk_level))
            if st.button("View details", key=f"card_{r.engine_id}", width="stretch",
                         icon=":material/open_in_full:"):
                engine_dialog(r.engine_id)
    if len(urgent) > len(shown):
        st.caption(f"…and {len(urgent) - len(shown)} more in the table below.")

# ---- Overview charts ----
st.markdown("### Fleet overview")
c1, c2 = st.columns([2.2, 1], gap="medium")
with c1.container(border=True):
    st.markdown("**Remaining life by engine**")
    st.altair_chart(rul_chart(predictions), width="stretch")
with c2.container(border=True):
    st.markdown("**Risk mix**")
    st.altair_chart(risk_donut(predictions), width="stretch")

# ---- Full table ----
st.markdown("### All engines")
f1, f2 = st.columns([3, 1], vertical_alignment="bottom")
tiers = f1.pills("Filter by risk", RISK_ORDER, default=RISK_ORDER, selection_mode="multi",
                 label_visibility="collapsed")
table = predictions[predictions.risk_level.isin(tiers or RISK_ORDER)].copy()
table["action"] = table.risk_level.map(lambda r: RISK[r]["headline"])

f2.download_button("Download report (CSV)", table.to_csv(index=False).encode(),
                   file_name="enginesight_report.csv", mime="text/csv",
                   icon=":material/download:", width="stretch")

columns = ["engine_id", "risk_level", "predicted_RUL"] + \
          (["actual_RUL"] if "actual_RUL" in table else []) + ["last_observed_cycle", "action"]


def tint(value):
    r = RISK.get(value)
    return f"background-color:{r['tint']};color:{r['color']};font-weight:700" if r else ""


st.caption("Select a row to open that engine's details.")
event = st.dataframe(
    table[columns].style.map(tint, subset=["risk_level"]),
    hide_index=True,
    width="stretch",
    height=min(38 + 35 * len(table), 420),
    on_select="rerun",
    selection_mode="single-row",
    key="engine_table",
    column_config={
        "engine_id": st.column_config.NumberColumn("Engine", format="%d"),
        "risk_level": st.column_config.TextColumn("Risk"),
        "predicted_RUL": st.column_config.ProgressColumn(
            "Forecast (cycles left)", format="%.0f", min_value=0,
            max_value=float(max(150, predictions.predicted_RUL.max()))),
        "actual_RUL": st.column_config.NumberColumn("Actual (cycles left)", format="%d"),
        "last_observed_cycle": st.column_config.NumberColumn("Cycles flown", format="%d"),
        "action": st.column_config.TextColumn("Recommended action"),
    },
)
if event.selection.rows:
    engine_dialog(int(table.iloc[event.selection.rows[0]].engine_id))
