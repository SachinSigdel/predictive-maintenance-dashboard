# EngineSight — Predictive Maintenance for Turbofan Engines

EngineSight forecasts the **remaining useful life (RUL)** of turbofan engines from their sensor history and ranks a fleet by maintenance urgency, so teams can service the right engine at the right time instead of reacting to breakdowns.

It's a Streamlit web app built around a Random Forest model trained on NASA's **C-MAPSS FD001** run-to-failure dataset.

**Live demo: [enginesight.streamlit.app](https://enginesight.streamlit.app)**

## Features

- **Fleet Dashboard:** every engine is scored and ranked, with:
  - Critical / High / Medium / Low risk tiers
  - a "needs attention" queue
  - remaining-life and risk-mix charts
  - a filterable table and a CSV report download
- **Engine details:** click any engine for its forecast gauge and smoothed sensor trend charts.
- **Check an Engine:** paste or upload one engine's readings, or try a built-in worn or healthy example, and get an instant forecast with a recommended action.
- **Bring your own data:** upload any C-MAPSS-format fleet file.
- **How It Works:** model accuracy, risk thresholds, sensor glossary and FAQ.
- Dark, responsive UI with a sticky navbar and an animated turbofan hero.

## Model

| | |
|---|---|
| Algorithm | Tuned Random Forest regressor |
| Training data | NASA C-MAPSS FD001 (100 simulated turbofan engines run to failure) |
| Inputs | Last 30 cycles of 15 sensors, plus 10-cycle rolling mean/std and lag-1 / lag-5 features |
| History required | At least 35 cycles per engine |
| Test-set MAE | ≈ 17.0 cycles |
| Test-set RMSE | ≈ 22.5 cycles |
| At-risk recall | ≈ 68% of engines with ≤ 30 true cycles left are flagged Critical or High |

### Risk tiers

| Tier | Predicted RUL | Recommended action |
|---|---|---|
| 🔴 Critical | 0 – 15 cycles | Ground for inspection |
| 🟠 High | 16 – 30 cycles | Plan maintenance soon |
| 🟡 Medium | 31 – 60 cycles | Monitor closely |
| 🟢 Low | 60+ cycles | Healthy |

The model was developed in `predictive_maintenance.ipynb`. The trained model, the scaler and the feature configuration are saved in `models/`.

## Getting started

Requires **Python 3.12**.

```bash
git clone https://github.com/SachinSigdel/predictive-maintenance-dashboard.git
cd predictive-maintenance-dashboard

python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run app.py
```

Then open http://localhost:8501. The dashboard opens with the bundled FD001 test fleet, so no upload is needed.

> The package versions in `requirements.txt` are pinned to the versions the model was saved with. Changing the `scikit-learn` version may stop `best_random_forest.joblib` from loading.

## Input data format

**Fleet file** (`.txt`, whitespace-separated, no header): 26 columns per row.

```
engine_id  cycle  setting_1  setting_2  setting_3  sensor_1 … sensor_21
```

This is the standard C-MAPSS format, e.g. `test_FD001.txt`.

**Single engine** (paste, `.csv` or `.txt`): one row per cycle, using either:
- the 15 model sensors in this order: `sensor_2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14, 15, 17, 20, 21`, or
- full 26-column C-MAPSS rows.

Values can be separated by spaces or commas, and a header row is optional.

## Project structure

```
app.py                  Entry point: page config, navbar, routing
core.py                 Model loading, feature engineering, prediction, parsing
ui.py                   Theme CSS, HTML components, Altair chart styling
views/
  home.py               Landing page
  fleet.py              Fleet Dashboard
  engine.py             Check an Engine
  how_it_works.py       Model and methodology
models/                 Trained Random Forest, scaler, model_config.json
assets/logo.svg         Logo
.streamlit/config.toml  Dark theme
*_FD001.txt             NASA C-MAPSS FD001 train/test data and true RULs
predictive_maintenance.ipynb   Model development notebook
```

## Deployment

The app is designed for **[Streamlit Community Cloud](https://share.streamlit.io)** (free):

1. Sign in with GitHub at share.streamlit.io.
2. Click **Create app**, then choose this repository, branch `main` and main file `app.py`.
3. Under **Advanced settings**, choose Python **3.12**, then click **Deploy**.

Other hosts that run a long-lived Python server also work, such as Render, Railway, Fly.io, Hugging Face Spaces (Docker) or any VM. The start command is:

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

> **Vercel isn't supported.** Streamlit needs a persistent server with WebSocket connections. Vercel runs short-lived serverless functions without WebSockets and caps a function at 250 MB, while this app's dependencies take about 360 MB.

## Dataset

A. Saxena and K. Goebel (2008). *Turbofan Engine Degradation Simulation Data Set*, NASA Prognostics Data Repository, NASA Ames Research Center.

## Disclaimer

EngineSight is a demonstration project trained on simulated data. It supports decisions but is **not** a certified airworthiness or maintenance tool.
