from pathlib import Path
from io import StringIO
import json

import altair as alt
import joblib
import pandas as pd
import streamlit as st


# -----------------------------
# App configuration
# -----------------------------
st.set_page_config(
    page_title="Predictive Maintenance Dashboard",
    page_icon="✈️",
    layout="wide",
)

BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / "models"
SAMPLE_FILE = BASE_DIR / "test_FD001.txt"
SAMPLE_RUL_FILE = BASE_DIR / "RUL_FD001.txt"

COLUMN_NAMES = [
    "engine_id", "cycle",
    "setting_1", "setting_2", "setting_3",
    *[f"sensor_{i}" for i in range(1, 22)],
]

# (name, upper RUL bound in cycles, strong colour, light tint)
RISK_LEVELS = [
    ("Critical", 15, "#d62728", "#fbd5d5"),
    ("High", 30, "#ff7f0e", "#ffe3c7"),
    ("Medium", 60, "#e6b800", "#fff3bf"),
    ("Low", float("inf"), "#2ca02c", "#d3f2d3"),
]
RISK_ORDER = [name for name, *_ in RISK_LEVELS]
RISK_COLORS = {name: color for name, _, color, _ in RISK_LEVELS}
RISK_TINTS = {name: tint for name, _, _, tint in RISK_LEVELS}

DISPLAY_NAMES = {
    "engine_id": "Engine ID",
    "last_observed_cycle": "Last Observed Cycle",
    "predicted_RUL": "Predicted RUL (cycles)",
    "actual_RUL": "Actual RUL (cycles)",
    "risk_level": "Risk Level",
}


# -----------------------------
# Load saved model artifacts
# -----------------------------
@st.cache_resource
def load_artifacts():
    paths = {
        "model": MODEL_DIR / "best_random_forest.joblib",
        "scaler": MODEL_DIR / "scaler.joblib",
        "config": MODEL_DIR / "model_config.json",
    }
    for path in paths.values():
        if not path.exists():
            raise FileNotFoundError(f"{path.name} was not found.")

    model = joblib.load(paths["model"])
    scaler = joblib.load(paths["scaler"])
    with open(paths["config"]) as file:
        config = json.load(file)

    return model, scaler, config


# -----------------------------
# Feature engineering
# -----------------------------
def add_engine_features(data, sensors, window, lags):
    data = data.sort_values(["engine_id", "cycle"]).copy()
    grouped = data.groupby("engine_id")

    for sensor in sensors:
        data[f"{sensor}_roll_mean_{window}"] = grouped[sensor].transform(
            lambda values: values.rolling(window, min_periods=1).mean()
        )
        data[f"{sensor}_roll_std_{window}"] = grouped[sensor].transform(
            lambda values: values.rolling(window, min_periods=1).std(ddof=0)
        )
        for lag in lags:
            data[f"{sensor}_lag_{lag}"] = grouped[sensor].shift(lag)

    return data


def classify_risk(rul):
    for name, upper, *_ in RISK_LEVELS:
        if rul <= upper:
            return name
    return RISK_ORDER[-1]


# -----------------------------
# Predict RUL for all engines
# -----------------------------
@st.cache_data(show_spinner=False)
def predict_all_engines(data):
    model, scaler, config = load_artifacts()

    feature_columns = config["feature_columns"]
    sequence_length = config["sequence_length"]

    data = add_engine_features(
        data, config["sensor_columns"], config["rolling_window"], config["lags"]
    )

    # First rows of each engine do not have lag values.
    data = data.dropna(subset=feature_columns).copy()
    data[feature_columns] = scaler.transform(data[feature_columns])

    predictions = []
    for engine_id, engine_data in data.groupby("engine_id"):
        engine_data = engine_data.sort_values("cycle")
        if len(engine_data) < sequence_length:
            continue

        # Random Forest uses flattened sequences.
        latest_sequence = (
            engine_data[feature_columns].tail(sequence_length).to_numpy().reshape(1, -1)
        )
        predicted_rul = max(float(model.predict(latest_sequence)[0]), 0.0)

        predictions.append({
            "engine_id": int(engine_id),
            "last_observed_cycle": int(engine_data["cycle"].max()),
            "predicted_RUL": predicted_rul,
            "risk_level": classify_risk(predicted_rul),
        })

    return pd.DataFrame(predictions)


# -----------------------------
# Input parsing
# -----------------------------
def read_cmapss_file(source):
    """Read a whitespace-separated C-MAPSS file and validate its shape."""
    data = pd.read_csv(source, sep=r"\s+", header=None)
    data = data.dropna(axis=1, how="all")

    if data.shape[1] != len(COLUMN_NAMES):
        raise ValueError(
            f"Expected {len(COLUMN_NAMES)} columns per row (engine id, cycle, "
            f"3 settings, 21 sensors), but the file has {data.shape[1]}."
        )

    data.columns = COLUMN_NAMES
    try:
        data = data.astype(float)
    except ValueError as error:
        raise ValueError("The file contains non-numeric values.") from error

    data[["engine_id", "cycle"]] = data[["engine_id", "cycle"]].astype(int)
    return data


def parse_single_engine(text, sensors):
    """Parse one engine's history: 15 model sensors, or full 26-column rows."""
    table = pd.read_csv(
        StringIO(text.strip()), sep=r"[\s,]+", header=None, engine="python"
    )

    # Allow an optional header row.
    first_row = pd.to_numeric(table.iloc[0], errors="coerce")
    if first_row.isna().any():
        table = table.iloc[1:].reset_index(drop=True)

    try:
        table = table.astype(float)
    except ValueError as error:
        raise ValueError("The data contains non-numeric values.") from error

    if table.shape[1] == len(COLUMN_NAMES):
        table.columns = COLUMN_NAMES
        table = table[sensors]
    elif table.shape[1] == len(sensors):
        table.columns = sensors
    else:
        raise ValueError(
            f"Each row must contain {len(sensors)} sensor values (or a full "
            f"{len(COLUMN_NAMES)}-column C-MAPSS row). "
            f"Found {table.shape[1]} values per row."
        )

    table.insert(0, "cycle", range(1, len(table) + 1))
    table.insert(0, "engine_id", 1)
    return table


@st.cache_data
def load_sample_data():
    return read_cmapss_file(SAMPLE_FILE)


@st.cache_data
def load_sample_rul():
    rul = pd.read_csv(SAMPLE_RUL_FILE, header=None, names=["actual_RUL"])
    rul.insert(0, "engine_id", range(1, len(rul) + 1))
    return rul


def sample_engine_text(sensors, required_cycles):
    """Pick a near-failure engine from the sample set and format its history."""
    data = load_sample_data()
    rul = load_sample_rul()
    cycles = data.groupby("engine_id")["cycle"].count()
    eligible = rul[rul["engine_id"].map(cycles) >= required_cycles + 10]
    engine_id = eligible.sort_values("actual_RUL").iloc[0]["engine_id"]

    history = data.loc[data["engine_id"] == engine_id, sensors].tail(required_cycles + 10)
    return history.to_csv(sep=" ", header=False, index=False).strip()


def fill_sample_engine(sensors, required_cycles):
    st.session_state.sensor_history = sample_engine_text(sensors, required_cycles)


# -----------------------------
# Charts
# -----------------------------
def risk_color_scale():
    return alt.Scale(domain=RISK_ORDER, range=[RISK_COLORS[r] for r in RISK_ORDER])


def rul_chart(predictions):
    tooltip = [
        alt.Tooltip("engine_id:N", title="Engine"),
        alt.Tooltip("predicted_RUL:Q", title="Predicted RUL", format=".1f"),
        alt.Tooltip("risk_level:N", title="Risk"),
        alt.Tooltip("last_observed_cycle:Q", title="Last cycle"),
    ]
    bars = alt.Chart(predictions).mark_bar().encode(
        x=alt.X(
            "engine_id:N",
            sort=alt.EncodingSortField("predicted_RUL", order="ascending"),
            title="Engine (sorted by urgency)",
            axis=alt.Axis(labelAngle=-90, labelOverlap=True),
        ),
        y=alt.Y("predicted_RUL:Q", title="Predicted RUL (cycles)"),
        color=alt.Color("risk_level:N", scale=risk_color_scale(), title="Risk"),
        tooltip=tooltip,
    )

    thresholds = pd.DataFrame(
        [{"rul": upper, "label": f"{name} ≤ {upper}"}
         for name, upper, *_ in RISK_LEVELS if upper != float("inf")]
    )
    rules = alt.Chart(thresholds).mark_rule(strokeDash=[4, 4], color="gray").encode(
        y="rul:Q"
    )
    labels = alt.Chart(thresholds).mark_text(
        align="left", dx=4, dy=-6, color="gray", fontSize=11
    ).encode(y="rul:Q", x=alt.value(0), text="label:N")

    return (bars + rules + labels).properties(height=360)


def risk_count_chart(predictions):
    counts = (
        predictions["risk_level"].value_counts()
        .reindex(RISK_ORDER, fill_value=0)
        .rename_axis("risk_level").reset_index(name="engines")
    )
    base = alt.Chart(counts).encode(
        x=alt.X("risk_level:N", sort=RISK_ORDER, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("engines:Q", title="Engines"),
    )
    bars = base.mark_bar().encode(
        color=alt.Color("risk_level:N", scale=risk_color_scale(), legend=None),
        tooltip=["risk_level:N", "engines:Q"],
    )
    text = base.mark_text(dy=-8).encode(text="engines:Q")
    return (bars + text).properties(height=360)


def sensor_trend_chart(engine_history, sensors):
    long = engine_history.melt(
        id_vars="cycle", value_vars=sensors, var_name="sensor", value_name="value"
    )
    return (
        alt.Chart(long)
        .mark_line(point=False)
        .encode(
            x=alt.X("cycle:Q", title="Cycle"),
            y=alt.Y("value:Q", title=None, scale=alt.Scale(zero=False)),
            tooltip=["sensor:N", "cycle:Q", alt.Tooltip("value:Q", format=".2f")],
        )
        .properties(height=180, width=320)
        .facet(facet=alt.Facet("sensor:N", title=None), columns=2)
        .resolve_scale(y="independent")
    )


# -----------------------------
# Dashboard display
# -----------------------------
def style_risk(value):
    tint = RISK_TINTS.get(value)
    if tint is None:
        return ""
    return f"background-color: {tint}; color: #111; font-weight: 600"


def show_dashboard(predictions, raw_data, sensors):
    predictions = predictions.sort_values("predicted_RUL").reset_index(drop=True)
    counts = predictions["risk_level"].value_counts()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Engines analyzed", len(predictions))
    col2.metric("🔴 Critical", int(counts.get("Critical", 0)))
    col3.metric("🟠 High", int(counts.get("High", 0)))
    col4.metric("Lowest predicted RUL", f"{predictions['predicted_RUL'].min():.0f} cycles")

    # ---- Priority table ----
    st.subheader("Maintenance Priority")

    filter_col, download_col = st.columns([3, 1], vertical_alignment="bottom")
    selected_risks = filter_col.multiselect(
        "Filter by risk level", RISK_ORDER, default=RISK_ORDER
    )
    filtered = predictions[predictions["risk_level"].isin(selected_risks)]

    table = filtered.rename(columns=DISPLAY_NAMES)
    download_col.download_button(
        "⬇️ Download CSV",
        table.to_csv(index=False).encode(),
        file_name="rul_predictions.csv",
        mime="text/csv",
        width="stretch",
    )

    number_formats = {DISPLAY_NAMES["predicted_RUL"]: "{:.1f}"}
    if DISPLAY_NAMES["actual_RUL"] in table:
        number_formats[DISPLAY_NAMES["actual_RUL"]] = "{:.0f}"

    st.dataframe(
        table.style.format(number_formats).map(style_risk, subset=[DISPLAY_NAMES["risk_level"]]),
        width="stretch",
        hide_index=True,
        height=min(38 + 35 * len(table), 400),
    )

    # ---- Charts ----
    chart_col, count_col = st.columns([3, 1])
    with chart_col:
        st.subheader("Predicted Remaining Useful Life")
        st.altair_chart(rul_chart(filtered if len(filtered) else predictions), width="stretch")
    with count_col:
        st.subheader("Risk-Level Counts")
        st.altair_chart(risk_count_chart(predictions), width="stretch")

    # ---- Engine drill-down ----
    st.subheader("Engine Drill-Down")
    engine_ids = predictions["engine_id"].tolist()
    pick_col, sensor_col = st.columns([1, 3])
    engine_id = pick_col.selectbox(
        "Engine (most urgent first)",
        engine_ids,
        format_func=lambda e: (
            f"Engine {e} — "
            f"{predictions.loc[predictions.engine_id == e, 'risk_level'].iat[0]}"
        ),
    )
    chosen_sensors = sensor_col.multiselect(
        "Sensors to plot", sensors, default=sensors[:4]
    )

    row = predictions.loc[predictions["engine_id"] == engine_id].iloc[0]
    pick_col.metric("Predicted RUL", f"{row['predicted_RUL']:.1f} cycles")
    pick_col.metric("Risk level", row["risk_level"])
    pick_col.metric("Cycles observed", int(row["last_observed_cycle"]))

    engine_history = raw_data.loc[raw_data["engine_id"] == engine_id].sort_values("cycle")
    with sensor_col:
        if chosen_sensors:
            st.altair_chart(sensor_trend_chart(engine_history, chosen_sensors))
        else:
            st.caption("Pick at least one sensor to plot its trend.")


# -----------------------------
# Main user interface
# -----------------------------
try:
    model, scaler, config = load_artifacts()
except FileNotFoundError as error:
    st.error(f"{error} Place the saved model files inside: {MODEL_DIR}")
    st.stop()

sensors = config["sensor_columns"]
required_cycles = config["sequence_length"] + max(config["lags"])

st.title("✈️ Predictive Maintenance Dashboard")
st.write(
    "Estimate the **remaining useful life (RUL)** of turbofan engines from "
    "recent sensor history, and see which engines need maintenance first."
)

with st.expander("ℹ️ About this model"):
    st.markdown(
        f"""
- **Model:** {config.get("model_name", "Random Forest")}, trained on NASA's
  C-MAPSS FD001 turbofan degradation dataset.
- **RUL** is the number of operating cycles an engine is expected to run before failure.
- **Input:** the last {config["sequence_length"]} cycles of {len(sensors)} sensors,
  plus {config["rolling_window"]}-cycle rolling statistics and lags {config["lags"]}
  — so each engine needs at least **{required_cycles} cycles** of history.
- **Risk levels:** 🔴 Critical ≤ 15 · 🟠 High ≤ 30 · 🟡 Medium ≤ 60 · 🟢 Low > 60 cycles.
"""
    )

# ---- Sidebar inputs ----
with st.sidebar:
    st.header("Data Input")
    input_method = st.radio(
        "Data source",
        ["Sample fleet (FD001 test set)", "Upload C-MAPSS file", "Single engine"],
    )

raw_data = None
show_actual = False

if input_method == "Sample fleet (FD001 test set)":
    with st.sidebar:
        st.caption(
            "100 engines from NASA's C-MAPSS FD001 test set. "
            "The true RUL is shown next to each prediction."
        )
    raw_data = load_sample_data()
    show_actual = True

elif input_method == "Upload C-MAPSS file":
    with st.sidebar:
        uploaded_file = st.file_uploader(
            "C-MAPSS test file (.txt)",
            type=["txt"],
            help="Whitespace-separated, 26 columns: engine id, cycle, "
                 "3 operational settings, 21 sensors.",
        )
        st.caption(
            "Don't have one? Get it from the "
            "[NASA Prognostics Data Repository]"
            "(https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/), "
            "or pick **Sample fleet** above."
        )
    if uploaded_file is None:
        st.info("⬅️ Upload a C-MAPSS file in the sidebar to analyze a fleet.")
    else:
        try:
            raw_data = read_cmapss_file(uploaded_file)
        except (ValueError, pd.errors.ParserError, UnicodeDecodeError) as error:
            st.error(f"Could not read **{uploaded_file.name}**: {error}")

else:
    with st.sidebar:
        st.caption(
            f"Provide at least **{required_cycles}** consecutive cycles for one "
            f"engine — one row per cycle, {len(sensors)} sensor values per row."
        )
        st.button(
            "✨ Load sample engine",
            on_click=fill_sample_engine,
            args=(sensors, required_cycles),
            width="stretch",
        )
        engine_file = st.file_uploader(
            "…or upload one engine (.csv / .txt)", type=["csv", "txt"]
        )
        with st.expander("Required sensor order"):
            st.code(", ".join(sensors), wrap_lines=True)

    sensor_history = st.text_area(
        "Sensor readings",
        key="sensor_history",
        height=250,
        placeholder=(
            "One cycle per line. Separate values with spaces or commas.\n"
            "Tip: click “Load sample engine” in the sidebar to try it out."
        ),
    )

    if st.button("Predict Remaining Engine Life", type="primary"):
        text = engine_file.getvalue().decode("utf-8", "replace") if engine_file else sensor_history
        if not text.strip():
            st.warning("Paste sensor readings or upload a file first.")
        else:
            try:
                parsed = parse_single_engine(text, sensors)
                if len(parsed) < required_cycles:
                    st.error(
                        f"Enter at least {required_cycles} cycles. You entered {len(parsed)}."
                    )
                else:
                    st.session_state.single_engine = parsed
            except (ValueError, pd.errors.ParserError) as error:
                st.error(str(error))

    raw_data = st.session_state.get("single_engine")

# ---- Results ----
if raw_data is not None:
    with st.spinner("Predicting remaining useful life…"):
        predictions = predict_all_engines(raw_data)

    if predictions.empty:
        st.error(
            "No prediction could be made. Each engine needs at least "
            f"{required_cycles} consecutive cycles."
        )
    else:
        if show_actual:
            predictions = predictions.merge(load_sample_rul(), on="engine_id", how="left")
            predictions = predictions[
                ["engine_id", "last_observed_cycle", "predicted_RUL", "actual_RUL", "risk_level"]
            ]
        st.divider()
        skipped = raw_data["engine_id"].nunique() - len(predictions)
        if skipped:
            st.caption(
                f"⚠️ {skipped} engine(s) skipped — fewer than {required_cycles} cycles of history."
            )
        show_dashboard(predictions, raw_data, sensors)
