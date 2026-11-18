"""Shared look-and-feel: CSS, HTML components and chart styling."""
from html import escape

import altair as alt
import pandas as pd
import streamlit as st

from core import RISK, RISK_ORDER, SENSOR_LABELS

INK = "#0f172a"
MUTED = "#64748b"
LINE = "#e2e8f0"
BLUE = "#2563eb"


CSS = """
<style>
/* ---- Chrome ---- */
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"] {display: none !important;}
[data-testid="stHeader"] {background: rgba(255,255,255,.85); backdrop-filter: blur(10px);
  border-bottom: 1px solid #e2e8f0;}
.block-container {max-width: 1180px; padding-top: 4.5rem; padding-bottom: 2rem;}
h1, h2, h3 {letter-spacing: -0.02em;}

/* Buttons */
.stButton button, .stDownloadButton button, [data-testid="stPageLink"] a {font-weight: 600;}
.stButton button[kind="primary"] {box-shadow: 0 6px 18px -6px rgba(37,99,235,.55);}

/* Bordered containers become cards */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) {
  background: #fff;}
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: #e2e8f0;}

/* ---- Custom components ---- */
.es-eyebrow {display:inline-flex; align-items:center; gap:.45rem; font-size:.8rem; font-weight:600;
  color:#1d4ed8; background:#dbeafe; padding:.3rem .75rem; border-radius:999px; margin-bottom:1rem;}
.es-dot {width:7px; height:7px; border-radius:50%; background:#2563eb; box-shadow:0 0 0 4px rgba(37,99,235,.18);}
.es-hero h1 {font-size: clamp(2.2rem, 4.6vw, 3.4rem); line-height:1.06; font-weight:800; margin:0 0 1rem; color:#0f172a;}
.es-hero h1 span {background:linear-gradient(90deg,#2563eb,#7c3aed); -webkit-background-clip:text;
  background-clip:text; color:transparent;}
.es-hero p.lead {font-size:1.15rem; color:#475569; line-height:1.6; max-width:34rem; margin:0 0 1.5rem;}

.es-section-title {text-align:center; margin: 3.5rem 0 .4rem; font-size:1.9rem; font-weight:800; color:#0f172a;}
.es-section-sub {text-align:center; color:#64748b; margin:0 auto 2rem; max-width:40rem; font-size:1.05rem;}
.es-page-title {font-size:2rem; font-weight:800; margin:0 0 .25rem; color:#0f172a; letter-spacing:-0.02em;}
.es-page-sub {color:#64748b; font-size:1.05rem; margin:0 0 1.5rem;}

.es-card {background:#fff; border:1px solid #e2e8f0; border-radius:16px; padding:1.4rem 1.5rem;
  box-shadow:0 1px 2px rgba(15,23,42,.04); height:100%;}
.es-card h4 {margin:.8rem 0 .35rem; font-size:1.08rem; font-weight:700; color:#0f172a;}
.es-card p {margin:0; color:#64748b; line-height:1.55; font-size:.95rem;}
.es-icon {width:42px; height:42px; border-radius:12px; display:flex; align-items:center; justify-content:center;
  font-size:1.3rem; background:#eff6ff;}

.es-kpi {background:#fff; border:1px solid #e2e8f0; border-radius:16px; padding:1.1rem 1.25rem;
  box-shadow:0 1px 2px rgba(15,23,42,.04);}
.es-kpi .label {color:#64748b; font-size:.85rem; font-weight:600; display:flex; align-items:center; gap:.4rem;}
.es-kpi .value {font-size:2rem; font-weight:800; color:#0f172a; line-height:1.15; margin-top:.25rem;}
.es-kpi .hint {color:#94a3b8; font-size:.8rem; margin-top:.15rem;}

.es-badge {display:inline-flex; align-items:center; gap:.35rem; font-size:.78rem; font-weight:700;
  padding:.22rem .6rem; border-radius:999px; white-space:nowrap;}
.es-badge i {width:7px; height:7px; border-radius:50%; display:inline-block;}

.es-engine {display:flex; flex-direction:column; gap:.2rem;}
.es-engine .top {display:flex; justify-content:space-between; align-items:center;}
.es-engine .name {font-weight:700; color:#0f172a;}
.es-engine .rul {font-size:1.9rem; font-weight:800; color:#0f172a; line-height:1.1; margin-top:.35rem;}
.es-engine .rul small {font-size:.85rem; font-weight:600; color:#64748b; margin-left:.25rem;}
.es-engine .act {color:#64748b; font-size:.85rem;}

.es-preview {background:linear-gradient(160deg,#0f172a,#1e293b); color:#e2e8f0; border-radius:20px;
  padding:1.4rem; box-shadow:0 30px 60px -25px rgba(15,23,42,.55);}
.es-preview .hdr {display:flex; justify-content:space-between; align-items:center; font-size:.85rem; color:#94a3b8;}
.es-preview .live {display:inline-flex; gap:.4rem; align-items:center; color:#4ade80; font-weight:600;}
.es-preview .live i {width:7px; height:7px; border-radius:50%; background:#4ade80;}
.es-preview .row {display:flex; justify-content:space-between; align-items:center; padding:.7rem .2rem;
  border-bottom:1px solid rgba(148,163,184,.15);}
.es-preview .row:last-child {border-bottom:none;}
.es-preview .eng {font-weight:600; color:#f8fafc;}
.es-preview .bar {flex:1; height:6px; background:rgba(148,163,184,.2); border-radius:9px; margin:0 1rem; overflow:hidden;}
.es-preview .bar span {display:block; height:100%; border-radius:9px;}
.es-preview .num {font-variant-numeric:tabular-nums; font-weight:700; width:4.2rem; text-align:right;}
.es-preview .stats {display:grid; grid-template-columns:repeat(3,1fr); gap:.6rem; margin:1rem 0 .6rem;}
.es-preview .stat {background:rgba(148,163,184,.1); border-radius:12px; padding:.65rem .8rem;}
.es-preview .stat b {display:block; font-size:1.35rem; color:#fff;}
.es-preview .stat span {font-size:.75rem; color:#94a3b8;}

.es-proof {display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; margin-top:3rem; padding:1.4rem;
  background:#fff; border:1px solid #e2e8f0; border-radius:18px;}
.es-proof div {text-align:center;}
.es-proof b {display:block; font-size:1.7rem; font-weight:800; color:#0f172a;}
.es-proof span {color:#64748b; font-size:.9rem;}
@media (max-width: 760px) {.es-proof {grid-template-columns:repeat(2,1fr);} .es-preview .stats{grid-template-columns:repeat(3,1fr);} }

.es-step {display:flex; gap:1rem; align-items:flex-start;}
.es-step .n {flex:none; width:34px; height:34px; border-radius:50%; background:#2563eb; color:#fff; font-weight:700;
  display:flex; align-items:center; justify-content:center;}
.es-step h4 {margin:.2rem 0 .3rem; font-size:1.05rem; color:#0f172a;}
.es-step p {margin:0; color:#64748b; font-size:.95rem; line-height:1.55;}

.es-cta {margin-top:3.5rem; border-radius:22px; padding:2.4rem 2rem; text-align:center; color:#fff;
  background:radial-gradient(circle at 20% 0%, #3b82f6 0%, #1d4ed8 45%, #312e81 100%);}
.es-cta h3 {color:#fff; font-size:1.7rem; margin:0 0 .4rem; font-weight:800;}
.es-cta p {color:#dbeafe; margin:0;}

.es-result {border-radius:18px; padding:1.6rem; border:1px solid; }
.es-result .big {font-size:3.4rem; font-weight:800; line-height:1; color:#0f172a;}
.es-result .big small {font-size:1.1rem; color:#475569; font-weight:600; margin-left:.4rem;}
.es-result h3 {margin:.9rem 0 .25rem; font-size:1.25rem; color:#0f172a;}
.es-result p {margin:0; color:#334155;}
.es-track {position:relative; display:flex; height:10px; border-radius:99px; overflow:hidden; margin:1.4rem 0 .4rem;}
.es-track span {display:block; height:100%;}
.es-marker {position:relative; height:16px; margin-top:-23px;}
.es-marker i {position:absolute; top:0; width:4px; height:22px; background:#0f172a; border-radius:3px;
  transform:translateX(-50%); box-shadow:0 0 0 3px #fff;}
.es-scale {position:relative; height:1rem; color:#64748b; font-size:.75rem; margin-top:.6rem;}
.es-scale span {position:absolute; transform:translateX(-50%);}
.es-scale span:first-child {transform:none;} .es-scale span:last-child {transform:translateX(-100%);}

.es-empty {border:2px dashed #cbd5e1; border-radius:18px; padding:3rem 1.5rem; text-align:center; color:#64748b; background:#fff;}
.es-empty b {display:block; color:#0f172a; font-size:1.1rem; margin:.6rem 0 .3rem;}

.es-tier {display:flex; gap:1rem; align-items:center; padding:.9rem 0; border-bottom:1px solid #e2e8f0;}
.es-tier:last-child {border-bottom:none;}
.es-tier .rng {width:8.5rem; flex:none; font-weight:700; color:#0f172a; font-variant-numeric:tabular-nums;}
.es-tier .txt {color:#475569; font-size:.95rem;}

.es-footer {margin-top:4rem; padding:1.6rem 0 .5rem; border-top:1px solid #e2e8f0; display:flex;
  justify-content:space-between; flex-wrap:wrap; gap:.6rem; color:#94a3b8; font-size:.85rem;}
.es-footer b {color:#0f172a;}
</style>
"""


def inject_css():
    st.html(CSS)


def html(markup):
    st.html(markup)


# -----------------------------
# Small components
# -----------------------------
def badge(risk):
    r = RISK[risk]
    return (f'<span class="es-badge" style="background:{r["tint"]};color:{r["color"]}">'
            f'<i style="background:{r["color"]}"></i>{escape(risk)}</span>')


def page_header(title, subtitle):
    html(f'<div class="es-page-title">{escape(title)}</div>'
         f'<div class="es-page-sub">{escape(subtitle)}</div>')


def kpi(col, label, value, hint="", dot=None):
    dot_html = f'<i class="es-badge" style="padding:0"><i style="background:{dot}"></i></i>' if dot else ""
    col.html(f'<div class="es-kpi"><div class="label">{dot_html}{escape(label)}</div>'
             f'<div class="value">{escape(str(value))}</div>'
             f'<div class="hint">{escape(hint)}</div></div>')


def feature_card(col, icon, title, text, tint="#eff6ff"):
    col.html(f'<div class="es-card"><div class="es-icon" style="background:{tint}">{icon}</div>'
             f'<h4>{escape(title)}</h4><p>{escape(text)}</p></div>')


def engine_card_html(engine_id, rul, risk):
    return (f'<div class="es-engine"><div class="top"><span class="name">Engine {engine_id}</span>'
            f'{badge(risk)}</div>'
            f'<div class="rul">{rul:.0f}<small>cycles left</small></div>'
            f'<div class="act">{escape(RISK[risk]["headline"])}</div></div>')


def rul_result(rul, risk, cycles_seen):
    r = RISK[risk]
    scale_max = max(150, rul * 1.1)
    segments = [(0, 15, "Critical"), (15, 30, "High"), (30, 60, "Medium"), (60, scale_max, "Low")]
    track = "".join(
        f'<span style="width:{(hi - lo) / scale_max * 100:.2f}%;background:{RISK[name]["color"]};'
        f'opacity:{1 if name == risk else .28}"></span>'
        for lo, hi, name in segments
    )
    pos = min(rul / scale_max * 100, 99.5)
    scale = "".join(f'<span style="left:{v / scale_max * 100:.2f}%">{label}</span>'
                    for v, label in [(0, "0"), (15, "15"), (30, "30"), (60, "60"),
                                     (scale_max, f"{scale_max:.0f}+")])
    html(f'''
<div class="es-result" style="background:{r["tint"]}55;border-color:{r["tint"]}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem">
    <div><div style="color:#475569;font-weight:600;font-size:.9rem;margin-bottom:.4rem">Predicted remaining useful life</div>
    <div class="big">{rul:.0f}<small>cycles</small></div></div>
    {badge(risk)}
  </div>
  <div class="es-track">{track}</div>
  <div class="es-marker"><i style="left:{pos:.2f}%"></i></div>
  <div class="es-scale">{scale}</div>
  <h3>{escape(r["headline"])}</h3>
  <p>{escape(r["action"])}</p>
  <p style="color:#64748b;font-size:.85rem;margin-top:.8rem">Based on the last {cycles_seen} cycles of sensor history.</p>
</div>''')


def empty_state(icon, title, text):
    html(f'<div class="es-empty"><div style="font-size:2rem">{icon}</div>'
         f'<b>{escape(title)}</b>{escape(text)}</div>')


def footer():
    html('<div class="es-footer"><span><b>EngineSight</b> · Predictive maintenance for turbofan fleets</span>'
         '<span>Trained on NASA C-MAPSS FD001 · Decision-support only, not certified for flight operations</span></div>')


# -----------------------------
# Charts
# -----------------------------
def _style(chart):
    return (chart.configure(font="Inter")
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor="#eef2f7",
                            domainColor=LINE, tickColor=LINE, labelFontSize=11, titleFontSize=12)
            .configure_legend(labelColor=INK, titleColor=MUTED, orient="top", direction="horizontal"))


def _risk_scale():
    return alt.Scale(domain=RISK_ORDER, range=[RISK[r]["color"] for r in RISK_ORDER])


def rul_chart(predictions):
    bars = alt.Chart(predictions).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
        x=alt.X("engine_id:N", sort=alt.EncodingSortField("predicted_RUL", order="ascending"),
                title="Engines, most urgent first", axis=alt.Axis(labels=False, ticks=False)),
        y=alt.Y("predicted_RUL:Q", title="Predicted cycles left"),
        color=alt.Color("risk_level:N", scale=_risk_scale(), title=None),
        tooltip=[alt.Tooltip("engine_id:N", title="Engine"),
                 alt.Tooltip("predicted_RUL:Q", title="Cycles left", format=".0f"),
                 alt.Tooltip("risk_level:N", title="Risk")],
    )
    thresholds = pd.DataFrame({"rul": [15, 30, 60]})
    rules = alt.Chart(thresholds).mark_rule(strokeDash=[4, 4], color="#94a3b8").encode(y="rul:Q")
    return _style((bars + rules).properties(height=300))


def risk_donut(predictions):
    counts = (predictions["risk_level"].value_counts().reindex(RISK_ORDER, fill_value=0)
              .rename_axis("risk").reset_index(name="engines"))
    counts["order"] = range(len(counts))
    base = alt.Chart(counts).encode(
        theta=alt.Theta("engines:Q", stack=True),
        color=alt.Color("risk:N", scale=_risk_scale(), legend=alt.Legend(title=None, orient="bottom")),
        order="order:Q",
        tooltip=["risk:N", "engines:Q"],
    )
    donut = base.mark_arc(innerRadius=70, outerRadius=110, cornerRadius=4, padAngle=0.015)
    total = alt.Chart(pd.DataFrame({"t": [f"{int(counts.engines.sum())}"]})).mark_text(
        fontSize=30, fontWeight=800, color=INK, dy=-6).encode(text="t:N")
    sub = alt.Chart(pd.DataFrame({"t": ["engines"]})).mark_text(
        fontSize=12, color=MUTED, dy=18).encode(text="t:N")
    return _style((donut + total + sub).properties(height=300))


def sensor_trends(history, sensors, width=300):
    long = history.melt(id_vars="cycle", value_vars=sensors, var_name="sensor", value_name="value")
    long["sensor"] = long["sensor"].map(lambda s: SENSOR_LABELS.get(s, s))
    long["trend"] = long.groupby("sensor")["value"].transform(
        lambda v: v.rolling(10, min_periods=1).mean())
    base = alt.Chart(long).encode(x=alt.X("cycle:Q", title="Cycle"))
    raw = base.mark_line(color="#93c5fd", strokeWidth=1, opacity=.7).encode(
        y=alt.Y("value:Q", title=None, scale=alt.Scale(zero=False)))
    trend = base.mark_line(color=BLUE, strokeWidth=2.5).encode(
        y="trend:Q",
        tooltip=["sensor:N", "cycle:Q", alt.Tooltip("value:Q", title="reading", format=".2f"),
                 alt.Tooltip("trend:Q", title="10-cycle avg", format=".2f")])
    chart = (
        (raw + trend)
        .properties(height=150, width=width)
        .facet(facet=alt.Facet("sensor:N", title=None, header=alt.Header(labelFontWeight=600,
                                labelColor=INK, labelFontSize=12)), columns=2)
        .resolve_scale(y="independent")
    )
    return _style(chart)
