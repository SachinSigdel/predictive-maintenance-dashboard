import streamlit as st

from core import RISK, RISK_ORDER, SENSOR_LABELS, get_config, required_cycles, sample_accuracy
from ui import badge, html, kpi, page_header

config = get_config()
accuracy = sample_accuracy()

page_header("How It Works",
            "What EngineSight predicts, how the model was built, and how to read the results.")

k1, k2, k3, k4 = st.columns(4)
kpi(k1, "Average error", f"±{accuracy['mae']:.1f}", "cycles (MAE on test set)")
kpi(k2, "RMSE", f"{accuracy['rmse']:.1f}", "cycles on test set")
kpi(k3, "At-risk engines caught", f"{accuracy['urgent_recall']:.0%}", "flagged Critical or High")
kpi(k4, "History needed", required_cycles(), "cycles per engine")

st.write("")
left, right = st.columns([1.2, 1], gap="large")

with left:
    with st.container(border=True):
        st.markdown("#### What is remaining useful life?")
        st.markdown(
            "**Remaining useful life (RUL)** is how many more operating cycles (one flight, "
            "roughly) an engine is expected to run before it reaches failure. Knowing it lets "
            "teams service engines just in time, instead of too early (wasted parts and labour) "
            "or too late (unplanned downtime)."
        )
        st.markdown("#### The model")
        st.markdown(
            f"- **Algorithm:** {config.get('model_name', 'Random Forest')} regression\n"
            "- **Training data:** NASA's C-MAPSS FD001 run-to-failure simulations of 100 turbofan engines\n"
            f"- **Inputs:** the last {config['sequence_length']} cycles of {len(config['sensor_columns'])} "
            f"sensors, plus {config['rolling_window']}-cycle rolling averages, rolling variability "
            f"and lagged values ({', '.join(map(str, config['lags']))} cycles back)\n"
            "- **Output:** estimated cycles remaining, which is then mapped to a risk tier"
        )

with right:
    with st.container(border=True):
        st.markdown("#### Risk tiers")
        ranges = {"Critical": "0 – 15 cycles", "High": "16 – 30 cycles",
                  "Medium": "31 – 60 cycles", "Low": "60+ cycles"}
        html("".join(
            f'<div class="es-tier"><div class="rng">{badge(r)}<div style="margin-top:.35rem">{ranges[r]}</div></div>'
            f'<div class="txt"><b style="color:#0f172a">{RISK[r]["headline"]}.</b> {RISK[r]["action"]}</div></div>'
            for r in RISK_ORDER
        ))

st.markdown("### Sensors the model reads")
cols = st.columns(3)
for i, s in enumerate(config["sensor_columns"]):
    cols[i % 3].markdown(f"- **{SENSOR_LABELS.get(s, s)}** <span style='color:#94a3b8'>· {s}</span>",
                         unsafe_allow_html=True)

st.markdown("### Questions")
with st.expander("What file format can I upload?"):
    st.markdown(
        "For a fleet, use the standard C-MAPSS text format: whitespace-separated, 26 columns "
        "(engine id, cycle, 3 operational settings, 21 sensors). For one engine, you can paste "
        f"or upload rows of just the {len(config['sensor_columns'])} sensors above, in that order, "
        "separated by spaces or commas. A header row is optional."
    )
with st.expander("Why was an engine skipped?"):
    st.markdown(f"The model needs at least **{required_cycles()} cycles** of history per engine "
                "to compute its trend features. Engines with less history are left out.")
with st.expander("Can I use this to make real maintenance decisions?"):
    st.markdown("EngineSight is a demonstration trained on simulated NASA data. It's a "
                "decision-support aid, not a certified airworthiness tool. Always follow your "
                "approved maintenance programme.")
