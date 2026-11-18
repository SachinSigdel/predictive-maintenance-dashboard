"""Model loading, feature engineering, prediction and input parsing."""
from pathlib import Path
from io import StringIO
import json

import joblib
import numpy as np
import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / "models"
SAMPLE_FILE = BASE_DIR / "test_FD001.txt"
SAMPLE_RUL_FILE = BASE_DIR / "RUL_FD001.txt"

COLUMN_NAMES = [
    "engine_id", "cycle",
    "setting_1", "setting_2", "setting_3",
    *[f"sensor_{i}" for i in range(1, 22)],
]

# Friendly names for the C-MAPSS sensors.
SENSOR_LABELS = {
    "sensor_2": "LPC outlet temperature",
    "sensor_3": "HPC outlet temperature",
    "sensor_4": "LPT outlet temperature",
    "sensor_6": "Bypass-duct pressure",
    "sensor_7": "HPC outlet pressure",
    "sensor_8": "Fan speed",
    "sensor_9": "Core speed",
    "sensor_11": "HPC static pressure",
    "sensor_12": "Fuel-flow ratio",
    "sensor_13": "Corrected fan speed",
    "sensor_14": "Corrected core speed",
    "sensor_15": "Bypass ratio",
    "sensor_17": "Bleed enthalpy",
    "sensor_20": "HPT coolant bleed",
    "sensor_21": "LPT coolant bleed",
}

# Sensors that show degradation most clearly, used as chart defaults.
KEY_SENSORS = ["sensor_4", "sensor_11", "sensor_12", "sensor_7"]

# name, upper RUL bound, colour, tint, headline, recommended action
RISK_LEVELS = [
    ("Critical", 15, "#dc2626", "#fee2e2", "Ground for inspection",
     "Expected to reach end of life within ~15 cycles. Schedule maintenance immediately."),
    ("High", 30, "#ea580c", "#ffedd5", "Plan maintenance soon",
     "Book a maintenance slot within the next 15 cycles."),
    ("Medium", 60, "#ca8a04", "#fef9c3", "Monitor closely",
     "Include this engine in the next planned maintenance window."),
    ("Low", float("inf"), "#16a34a", "#dcfce7", "Healthy",
     "No action needed. Keep monitoring as new cycles arrive."),
]
RISK_ORDER = [r[0] for r in RISK_LEVELS]
RISK = {r[0]: dict(upper=r[1], color=r[2], tint=r[3], headline=r[4], action=r[5])
        for r in RISK_LEVELS}


def classify_risk(rul):
    for name, upper, *_ in RISK_LEVELS:
        if rul <= upper:
            return name
    return RISK_ORDER[-1]


@st.cache_resource
def load_artifacts():
    paths = {
        "model": MODEL_DIR / "best_random_forest.joblib",
        "scaler": MODEL_DIR / "scaler.joblib",
        "config": MODEL_DIR / "model_config.json",
    }
    for path in paths.values():
        if not path.exists():
            raise FileNotFoundError(f"{path.name} was not found in {MODEL_DIR}.")

    model = joblib.load(paths["model"])
    scaler = joblib.load(paths["scaler"])
    with open(paths["config"]) as file:
        config = json.load(file)
    return model, scaler, config


def get_config():
    return load_artifacts()[2]


def required_cycles():
    config = get_config()
    return config["sequence_length"] + max(config["lags"])


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
        window = engine_data[feature_columns].tail(sequence_length).to_numpy().reshape(1, -1)
        rul = max(float(model.predict(window)[0]), 0.0)
        predictions.append({
            "engine_id": int(engine_id),
            "last_observed_cycle": int(engine_data["cycle"].max()),
            "predicted_RUL": rul,
            "risk_level": classify_risk(rul),
        })

    columns = ["engine_id", "last_observed_cycle", "predicted_RUL", "risk_level"]
    result = pd.DataFrame(predictions, columns=columns)
    return result.sort_values("predicted_RUL").reset_index(drop=True)


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
    table = pd.read_csv(StringIO(text.strip()), sep=r"[\s,]+", header=None, engine="python")

    # Allow an optional header row.
    if pd.to_numeric(table.iloc[0], errors="coerce").isna().any():
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
            f"Each row needs {len(sensors)} sensor values (or a full "
            f"{len(COLUMN_NAMES)}-column C-MAPSS row). Found {table.shape[1]}."
        )

    table.insert(0, "cycle", range(1, len(table) + 1))
    table.insert(0, "engine_id", 1)
    return table


# -----------------------------
# Sample data
# -----------------------------
@st.cache_data
def load_sample_data():
    return read_cmapss_file(SAMPLE_FILE)


@st.cache_data
def load_sample_rul():
    rul = pd.read_csv(SAMPLE_RUL_FILE, header=None, names=["actual_RUL"])
    rul.insert(0, "engine_id", range(1, len(rul) + 1))
    return rul


@st.cache_data(show_spinner=False)
def sample_fleet_predictions():
    predictions = predict_all_engines(load_sample_data())
    return predictions.merge(load_sample_rul(), on="engine_id", how="left")


@st.cache_data(show_spinner=False)
def sample_accuracy():
    """Error of the model on the held-out FD001 test engines."""
    p = sample_fleet_predictions()
    error = p["predicted_RUL"] - p["actual_RUL"]
    actual_risk = p["actual_RUL"].map(classify_risk)
    urgent = actual_risk.isin(["Critical", "High"])
    flagged = p["risk_level"].isin(["Critical", "High"])
    return {
        "mae": float(error.abs().mean()),
        "rmse": float(np.sqrt((error ** 2).mean())),
        "urgent_recall": float((urgent & flagged).sum() / max(urgent.sum(), 1)),
        "engines": int(len(p)),
    }


def sample_engine_text(kind="critical"):
    """Format one sample engine's recent history as pasteable text."""
    sensors = get_config()["sensor_columns"]
    need = required_cycles() + 10
    data = load_sample_data()
    rul = load_sample_rul()
    cycles = data.groupby("engine_id")["cycle"].count()
    eligible = rul[rul["engine_id"].map(cycles) >= need].sort_values("actual_RUL")
    row = eligible.iloc[0] if kind == "critical" else eligible.iloc[len(eligible) // 2]

    history = data.loc[data["engine_id"] == row["engine_id"], sensors].tail(need)
    return history.to_csv(sep=" ", header=False, index=False).strip()
