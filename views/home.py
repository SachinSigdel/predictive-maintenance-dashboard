import streamlit as st

from core import RISK, sample_accuracy, sample_fleet_predictions
from ui import html, feature_card

fleet = sample_fleet_predictions()
accuracy = sample_accuracy()
counts = fleet["risk_level"].value_counts()

# ---- Hero ----
left, right = st.columns([1.1, 1], gap="large", vertical_alignment="center")

with left:
    html(
        '<div class="es-hero">'
        '<div class="es-eyebrow"><span class="es-dot"></span>Predictive maintenance for turbofan fleets</div>'
        '<h1>Know which engine needs you <span>before it fails.</span></h1>'
        '<p class="lead">EngineSight reads your engines\' sensor history and forecasts how many '
        'cycles each one has left, so maintenance teams fix the right engine at the right time '
        'instead of reacting to breakdowns.</p></div>'
    )
    b1, b2, _ = st.columns([1.25, 1, 0.25])
    if b1.button("Open the live dashboard", type="primary", icon=":material/arrow_forward:",
                 width="stretch"):
        st.switch_page("views/fleet.py")
    if b2.button("Check a single engine", width="stretch"):
        st.switch_page("views/engine.py")

with right:
    top = fleet.head(5)
    rows = "".join(
        f'<div class="row"><span class="eng">Engine {r.engine_id}</span>'
        f'<span class="bar"><span style="width:{min(r.predicted_RUL / 150 * 100, 100):.0f}%;'
        f'background:{RISK[r.risk_level]["color"]}"></span></span>'
        f'<span class="num" style="color:{RISK[r.risk_level]["color"]}">{r.predicted_RUL:.0f} cyc</span></div>'
        for r in top.itertuples()
    )
    html(
        '<div class="es-preview">'
        '<div class="hdr"><span>Fleet FD-001 · priority queue</span>'
        '<span class="live"><i></i>Live model</span></div>'
        '<div class="stats">'
        f'<div class="stat"><b>{len(fleet)}</b><span>engines</span></div>'
        f'<div class="stat"><b style="color:#f87171">{counts.get("Critical", 0)}</b><span>critical</span></div>'
        f'<div class="stat"><b style="color:#fb923c">{counts.get("High", 0)}</b><span>high risk</span></div>'
        '</div>' + rows + '</div>'
    )

# ---- Proof strip ----
html(
    '<div class="es-proof">'
    f'<div><b>±{accuracy["mae"]:.0f} cycles</b><span>average forecast error</span></div>'
    f'<div><b>{accuracy["urgent_recall"]:.0%}</b><span>of at-risk engines flagged</span></div>'
    f'<div><b>{accuracy["engines"]}</b><span>engines scored in seconds</span></div>'
    '<div><b>15 sensors</b><span>temperatures, pressures, speeds</span></div>'
    '</div>'
)

# ---- Features ----
html('<div class="es-section-title">Everything a maintenance planner needs</div>'
     '<div class="es-section-sub">From the whole fleet down to one sensor, in one place, with nothing to install.</div>')

c1, c2, c3 = st.columns(3)
feature_card(c1, "🛩️", "Fleet triage",
             "Every engine ranked by urgency, with a clear risk tier and a recommended action.")
feature_card(c2, "🔍", "Engine deep-dive",
             "Open any engine to see its forecast and the sensor trends behind it.", "#f5f3ff")
feature_card(c3, "📤", "Bring your own data",
             "Upload a C-MAPSS fleet file or paste one engine's readings. Results are instant.", "#ecfdf5")

# ---- How it works ----
html('<div class="es-section-title">How it works</div>'
     '<div class="es-section-sub">Three steps from raw sensor readings to a maintenance plan.</div>')

s1, s2, s3 = st.columns(3, gap="large")
for col, n, title, text in [
    (s1, 1, "Upload sensor history",
     "Provide recent cycles of temperature, pressure and speed readings for each engine."),
    (s2, 2, "The model forecasts wear",
     "A Random Forest trained on NASA run-to-failure data estimates the cycles remaining."),
    (s3, 3, "Act on the priorities",
     "Engines are sorted into Critical, High, Medium and Low so the team knows where to start."),
]:
    col.html(f'<div class="es-step"><div class="n">{n}</div><div><h4>{title}</h4><p>{text}</p></div></div>')

# ---- CTA ----
html('<div class="es-cta"><h3>See it on a real fleet</h3>'
     '<p>The dashboard opens with 100 engines from NASA\'s turbofan test set, no upload needed.</p></div>')
st.write("")
_, mid, _ = st.columns([1, 0.6, 1])
if mid.button("Explore the demo fleet", type="primary", icon=":material/rocket_launch:", width="stretch"):
    st.switch_page("views/fleet.py")
