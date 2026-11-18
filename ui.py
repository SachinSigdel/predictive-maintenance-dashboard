"""Shared look-and-feel: CSS, HTML components and chart styling (dark theme)."""
from html import escape
import base64
import math

import altair as alt
import pandas as pd
import streamlit as st

from core import RISK, RISK_ORDER, SENSOR_LABELS

INK = "#f1f5f9"
TEXT = "#cbd5e1"
MUTED = "#94a3b8"
LINE = "#1e293b"
BLUE = "#3b82f6"


CSS = """
<style>
:root {
  --bg: #070b16; --surface: rgba(17, 24, 39, .72); --surface-solid: #0f1626;
  --border: rgba(148, 163, 184, .14); --border-strong: rgba(148, 163, 184, .24);
  --ink: #f1f5f9; --text: #cbd5e1; --muted: #94a3b8; --faint: #64748b;
  --blue: #3b82f6; --blue-soft: rgba(59, 130, 246, .14); --violet: #8b5cf6;
}

/* ---- App chrome ---- */
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"] {display: none !important;}
.stApp {background:
  radial-gradient(1200px 600px at 85% -10%, rgba(59,130,246,.10), transparent 60%),
  radial-gradient(900px 500px at -10% 30%, rgba(139,92,246,.07), transparent 60%),
  var(--bg);}
.block-container {max-width: 1180px; padding-top: 6rem; padding-bottom: 2rem; position: relative; z-index: 1;}
h1, h2, h3 {letter-spacing: -0.02em; color: var(--ink);}

/* ---- Sticky navbar, links on the right ---- */
[data-testid="stHeader"] {
  position: fixed !important; top: 0; left: 0; right: 0; height: 4rem; z-index: 999990;
  background: rgba(7, 11, 22, .72) !important;
  backdrop-filter: blur(16px) saturate(150%); -webkit-backdrop-filter: blur(16px) saturate(150%);
  border-bottom: 1px solid var(--border);
}
[data-testid="stToolbar"] {width: 100%; height: 100%; padding: 0 clamp(1rem, 4vw, 3rem); align-items: center;}
[data-testid="stToolbar"] > div:first-child {flex: 1; min-width: 0; justify-content: space-between; align-items: center;}
[data-testid="stToolbar"] .rc-overflow {flex: 1; justify-content: flex-end; gap: .25rem;}
[data-testid="stHeaderLogo"] {height: 2.1rem !important; max-width: none;}
[data-testid="stTopNavLinkContainer"] a {border-radius: 999px; padding: .45rem .95rem; transition: background .15s, color .15s;}
[data-testid="stTopNavLinkContainer"] a span {color: var(--muted); font-weight: 600;}
[data-testid="stTopNavLinkContainer"] a:hover {background: rgba(148,163,184,.10);}
[data-testid="stTopNavLinkContainer"] a:hover span {color: var(--ink);}
[data-testid="stTopNavLinkContainer"] a[aria-current="page"],
[data-testid="stTopNavLinkContainer"] a[aria-current="page"]:hover {background: var(--blue-soft);}
[data-testid="stTopNavLinkContainer"] a[aria-current="page"] span {color: #93c5fd;}

/* ---- Widgets ---- */
.stButton button, .stDownloadButton button {font-weight: 600;}
.stButton button[kind="primary"] {background: linear-gradient(135deg, #3b82f6, #6366f1); border: none;
  box-shadow: 0 8px 24px -8px rgba(59,130,246,.7);}
.stButton button[kind="primary"]:hover {filter: brightness(1.1);}
.stButton button[kind="secondary"], .stDownloadButton button {background: rgba(15,23,42,.6); border-color: var(--border-strong);}
[data-testid="stVerticalBlockBorderWrapper"] {background: var(--surface); border-color: var(--border) !important;
  backdrop-filter: blur(6px);}
[data-testid="stDialog"] [role="dialog"] {background: #0b1222; border: 1px solid var(--border-strong);}
[data-testid="stExpander"] details {background: var(--surface); border-color: var(--border);}

/* ---- Custom components ---- */
.es-eyebrow {display:inline-flex; align-items:center; gap:.5rem; font-size:.8rem; font-weight:600;
  color:#93c5fd; background:rgba(59,130,246,.12); border:1px solid rgba(59,130,246,.3);
  padding:.32rem .8rem; border-radius:999px; margin-bottom:1.2rem;}
.es-dot {width:7px; height:7px; border-radius:50%; background:#60a5fa; box-shadow:0 0 0 4px rgba(96,165,250,.2);
  animation: es-blink 2s ease-in-out infinite;}
.es-hero h1 {font-size: clamp(2.3rem, 4.8vw, 3.6rem); line-height:1.05; font-weight:800; margin:0 0 1.1rem; color:var(--ink);}
.es-hero h1 span {background:linear-gradient(90deg,#60a5fa,#a78bfa); -webkit-background-clip:text;
  background-clip:text; color:transparent;}
.es-hero p.lead {font-size:1.15rem; color:var(--text); line-height:1.65; max-width:34rem; margin:0 0 1.6rem;}

.es-section-title {text-align:center; margin: 4rem 0 .5rem; font-size:2rem; font-weight:800; color:var(--ink);}
.es-section-sub {text-align:center; color:var(--muted); margin:0 auto 2rem; max-width:40rem; font-size:1.05rem;}
.es-page-title {font-size:2.1rem; font-weight:800; margin:0 0 .3rem; color:var(--ink); letter-spacing:-0.02em;}
.es-page-sub {color:var(--muted); font-size:1.05rem; margin:0 0 1.6rem;}

.es-card {background:var(--surface); border:1px solid var(--border); border-radius:18px; padding:1.5rem;
  height:100%; backdrop-filter: blur(8px); transition: border-color .2s, transform .2s;}
.es-card:hover {border-color: rgba(96,165,250,.4); transform: translateY(-2px);}
.es-card h4 {margin:.9rem 0 .35rem; font-size:1.08rem; font-weight:700; color:var(--ink);}
.es-card p {margin:0; color:var(--muted); line-height:1.6; font-size:.95rem;}
.es-icon {width:44px; height:44px; border-radius:12px; display:flex; align-items:center; justify-content:center;
  font-size:1.3rem; background:var(--blue-soft); border:1px solid var(--border);}

.es-kpi {background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:1.1rem 1.25rem;}
.es-kpi .label {color:var(--muted); font-size:.85rem; font-weight:600; display:flex; align-items:center; gap:.4rem;}
.es-kpi .value {font-size:2rem; font-weight:800; color:var(--ink); line-height:1.15; margin-top:.25rem;}
.es-kpi .hint {color:var(--faint); font-size:.8rem; margin-top:.15rem;}

.es-badge {display:inline-flex; align-items:center; gap:.35rem; font-size:.78rem; font-weight:700;
  padding:.22rem .6rem; border-radius:999px; white-space:nowrap;}
.es-badge i {width:7px; height:7px; border-radius:50%; display:inline-block;}

.es-engine {display:flex; flex-direction:column; gap:.2rem;}
.es-engine .top {display:flex; justify-content:space-between; align-items:center;}
.es-engine .name {font-weight:700; color:var(--ink);}
.es-engine .rul {font-size:1.9rem; font-weight:800; color:var(--ink); line-height:1.1; margin-top:.35rem;}
.es-engine .rul small {font-size:.85rem; font-weight:600; color:var(--muted); margin-left:.25rem;}
.es-engine .act {color:var(--muted); font-size:.85rem;}

.es-preview {background:linear-gradient(160deg, rgba(15,23,42,.85), rgba(30,41,59,.6)); color:var(--text);
  border:1px solid var(--border-strong); border-radius:20px; padding:1.4rem; backdrop-filter: blur(12px);
  box-shadow:0 30px 80px -30px rgba(59,130,246,.45);}
.es-preview .hdr {display:flex; justify-content:space-between; align-items:center; font-size:.85rem; color:var(--muted);}
.es-preview .live {display:inline-flex; gap:.4rem; align-items:center; color:#4ade80; font-weight:600;}
.es-preview .live i {width:7px; height:7px; border-radius:50%; background:#4ade80; animation: es-blink 1.6s infinite;}
.es-preview .row {display:flex; justify-content:space-between; align-items:center; padding:.7rem .2rem;
  border-bottom:1px solid rgba(148,163,184,.12);}
.es-preview .row:last-child {border-bottom:none;}
.es-preview .eng {font-weight:600; color:var(--ink);}
.es-preview .bar {flex:1; height:6px; background:rgba(148,163,184,.15); border-radius:9px; margin:0 1rem; overflow:hidden;}
.es-preview .bar span {display:block; height:100%; border-radius:9px;}
.es-preview .num {font-variant-numeric:tabular-nums; font-weight:700; width:4.2rem; text-align:right;}
.es-preview .stats {display:grid; grid-template-columns:repeat(3,1fr); gap:.6rem; margin:1rem 0 .6rem;}
.es-preview .stat {background:rgba(148,163,184,.08); border:1px solid var(--border); border-radius:12px; padding:.65rem .8rem;}
.es-preview .stat b {display:block; font-size:1.35rem; color:var(--ink);}
.es-preview .stat span {font-size:.75rem; color:var(--muted);}

.es-proof {display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; margin-top:3.5rem; padding:1.5rem;
  background:var(--surface); border:1px solid var(--border); border-radius:18px; backdrop-filter: blur(10px);}
.es-proof div {text-align:center;}
.es-proof b {display:block; font-size:1.7rem; font-weight:800; color:var(--ink);}
.es-proof span {color:var(--muted); font-size:.9rem;}
@media (max-width: 760px) {.es-proof {grid-template-columns:repeat(2,1fr);}}

.es-step {display:flex; gap:1rem; align-items:flex-start;}
.es-step .n {flex:none; width:36px; height:36px; border-radius:50%; color:#fff; font-weight:700;
  background:linear-gradient(135deg,#3b82f6,#6366f1); box-shadow:0 0 0 6px rgba(59,130,246,.12);
  display:flex; align-items:center; justify-content:center;}
.es-step h4 {margin:.2rem 0 .3rem; font-size:1.05rem; color:var(--ink);}
.es-step p {margin:0; color:var(--muted); font-size:.95rem; line-height:1.6;}

.es-cta {margin-top:4rem; border-radius:22px; padding:2.6rem 2rem; text-align:center;
  border:1px solid rgba(96,165,250,.3);
  background:radial-gradient(circle at 20% 0%, rgba(59,130,246,.45) 0%, rgba(49,46,129,.55) 55%, rgba(15,23,42,.8) 100%);}
.es-cta h3 {color:#fff; font-size:1.7rem; margin:0 0 .4rem; font-weight:800;}
.es-cta p {color:#bfdbfe; margin:0;}

.es-result {border-radius:18px; padding:1.6rem; border:1px solid;}
.es-result .cap {color:var(--muted); font-weight:600; font-size:.9rem; margin-bottom:.4rem;}
.es-result .big {font-size:3.4rem; font-weight:800; line-height:1; color:var(--ink);}
.es-result .big small {font-size:1.1rem; color:var(--muted); font-weight:600; margin-left:.4rem;}
.es-result h3 {margin:.9rem 0 .25rem; font-size:1.25rem; color:var(--ink);}
.es-result p {margin:0; color:var(--text);}
.es-result p.note {color:var(--faint); font-size:.85rem; margin-top:.8rem;}
.es-track {position:relative; display:flex; height:10px; border-radius:99px; overflow:hidden; margin:1.4rem 0 .4rem;}
.es-track span {display:block; height:100%;}
.es-marker {position:relative; height:16px; margin-top:-23px;}
.es-marker i {position:absolute; top:0; width:4px; height:22px; background:#fff; border-radius:3px;
  transform:translateX(-50%); box-shadow:0 0 0 3px #0b1222, 0 0 12px rgba(255,255,255,.6);}
.es-scale {position:relative; height:1rem; color:var(--muted); font-size:.75rem; margin-top:.6rem;}
.es-scale span {position:absolute; transform:translateX(-50%);}
.es-scale span:first-child {transform:none;} .es-scale span:last-child {transform:translateX(-100%);}

.es-empty {border:2px dashed var(--border-strong); border-radius:18px; padding:3rem 1.5rem; text-align:center;
  color:var(--muted); background:var(--surface);}
.es-empty b {display:block; color:var(--ink); font-size:1.1rem; margin:.6rem 0 .3rem;}

.es-tier {display:flex; gap:1rem; align-items:center; padding:.9rem 0; border-bottom:1px solid var(--border);}
.es-tier:last-child {border-bottom:none;}
.es-tier .rng {width:8.5rem; flex:none; font-weight:700; color:var(--ink); font-variant-numeric:tabular-nums;}
.es-tier .txt {color:var(--text); font-size:.95rem;}
.es-tier .txt b {color:var(--ink);}
.es-list {margin:0; padding-left:1.2rem; color:var(--text); font-size:.9rem;}
.es-list span {color:var(--faint);}

.es-footer {margin-top:4.5rem; padding:1.6rem 0 .5rem; border-top:1px solid var(--border); display:flex;
  justify-content:space-between; flex-wrap:wrap; gap:.6rem; color:var(--faint); font-size:.85rem;}
.es-footer b {color:var(--ink);}

/* ---- Animated engine background (home page) ---- */
.es-bg {position:fixed; inset:0; z-index:-1; pointer-events:none; overflow:hidden;}
.es-bg .engine {position:absolute; right:-9vw; top:50%; width:min(70vw, 900px); aspect-ratio:1;
  transform:translateY(-46%); opacity:.42;
  -webkit-mask-image: radial-gradient(circle, #000 55%, transparent 72%);
          mask-image: radial-gradient(circle, #000 55%, transparent 72%);}
.es-bg .engine {background: var(--engine-svg) center / contain no-repeat;}
.es-bg .fade {position:absolute; inset:0;
  background: linear-gradient(90deg, var(--bg) 0%, rgba(7,11,22,.88) 32%, rgba(7,11,22,.25) 62%, rgba(7,11,22,0) 100%);}
.es-bg .streak {position:absolute; left:0; height:1px; width:22vw; opacity:0;
  background: linear-gradient(90deg, transparent, rgba(96,165,250,.75), transparent);
  animation: es-flow linear infinite;}
.es-bg .grid {position:absolute; inset:0; opacity:.35;
  background-image: radial-gradient(rgba(148,163,184,.18) 1px, transparent 1px); background-size: 28px 28px;
  -webkit-mask-image: radial-gradient(ellipse at 70% 40%, #000 10%, transparent 65%);
          mask-image: radial-gradient(ellipse at 70% 40%, #000 10%, transparent 65%);}

@keyframes es-blink {0%,100% {opacity:1;} 50% {opacity:.35;}}
@keyframes es-flow {0% {transform: translateX(-25vw); opacity:0;} 15% {opacity:1;} 85% {opacity:1;}
  100% {transform: translateX(110vw); opacity:0;}}

@media (max-width: 760px) {
  .es-bg .engine {right:auto; left:50%; top:22%; width:120vw; transform:translate(-50%, -30%); opacity:.3;}
  .es-bg .fade {background: linear-gradient(180deg, rgba(7,11,22,.35), rgba(7,11,22,.9) 60%, var(--bg));}
}
@media (prefers-reduced-motion: reduce) {
  .es-bg *, .es-dot, .es-preview .live i {animation: none !important;}
}
</style>
"""


def inject_css():
    st.html(CSS)


def html(markup):
    st.html(markup)


# -----------------------------
# Animated engine background
# -----------------------------
def _engine_svg():
    cx = cy = 300
    blade = ("M -9 -66 C -6 -122, 12 -182, 40 -236 "
             "L 68 -226 C 40 -174, 22 -120, 12 -64 Z")
    blades = "".join(f'<path d="{blade}" transform="rotate({i * 360 / 22:.2f})"/>' for i in range(22))
    vanes = "".join(
        f'<line x1="{cx + 250 * math.cos(a):.1f}" y1="{cy + 250 * math.sin(a):.1f}" '
        f'x2="{cx + 268 * math.cos(a):.1f}" y2="{cy + 268 * math.sin(a):.1f}"/>'
        for a in (i * 2 * math.pi / 60 for i in range(60))
    )
    return f'''
<svg viewBox="0 0 600 600" xmlns="http://www.w3.org/2000/svg">
  <style>
    .fan, .stator, .pulse {{transform-box: view-box; transform-origin: 300px 300px;}}
    .fan {{animation: spin 2.4s linear infinite;}}
    .fan.blur {{animation-delay: -.08s; opacity: .35;}}
    .stator {{animation: spin 40s linear infinite reverse;}}
    .pulse {{animation: pulse 4s ease-out infinite;}}
    .pulse.p2 {{animation-delay: 2s;}}
    .glow {{animation: breathe 5s ease-in-out infinite;}}
    @keyframes spin {{to {{transform: rotate(360deg);}}}}
    @keyframes pulse {{0% {{transform: scale(.82); opacity: .55;}} 100% {{transform: scale(1.18); opacity: 0;}}}}
    @keyframes breathe {{0%, 100% {{opacity: .55;}} 50% {{opacity: 1;}}}}
    @media (prefers-reduced-motion: reduce) {{* {{animation: none !important;}}}}
  </style>
  <defs>
    <radialGradient id="esGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="#3b82f6" stop-opacity=".55"/>
      <stop offset=".6" stop-color="#1d4ed8" stop-opacity=".12"/>
      <stop offset="1" stop-color="#1d4ed8" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="esRing" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#93c5fd"/><stop offset=".5" stop-color="#3b82f6"/>
      <stop offset="1" stop-color="#6d28d9"/>
    </linearGradient>
    <linearGradient id="esBlade" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0" stop-color="#1e3a8a"/><stop offset="1" stop-color="#60a5fa"/>
    </linearGradient>
    <radialGradient id="esHub" cx="40%" cy="35%" r="70%">
      <stop offset="0" stop-color="#e2e8f0"/><stop offset=".35" stop-color="#64748b"/>
      <stop offset="1" stop-color="#0f172a"/>
    </radialGradient>
  </defs>
  <circle class="glow" cx="300" cy="300" r="300" fill="url(#esGlow)"/>
  <circle class="pulse" cx="300" cy="300" r="276" fill="none" stroke="#60a5fa" stroke-width="1.5"/>
  <circle class="pulse p2" cx="300" cy="300" r="276" fill="none" stroke="#a78bfa" stroke-width="1.2"/>
  <circle cx="300" cy="300" r="272" fill="#050913" stroke="url(#esRing)" stroke-width="10"/>
  <g class="stator" stroke="#334155" stroke-width="2">{vanes}</g>
  <circle cx="300" cy="300" r="246" fill="none" stroke="#1e3a8a" stroke-width="2"/>
  <g class="fan blur" transform="translate(300 300)">
    <g fill="#3b82f6" opacity=".5">{blades}</g>
  </g>
  <g class="fan">
    <g transform="translate(300 300)" fill="url(#esBlade)" stroke="#93c5fd" stroke-opacity=".55" stroke-width="1">
      {blades}
    </g>
    <circle cx="300" cy="300" r="66" fill="url(#esHub)" stroke="#94a3b8" stroke-opacity=".5" stroke-width="2"/>
    <path d="M300 300 C 318 296, 332 280, 330 258 M300 300 C 284 306, 272 322, 274 342"
          stroke="#f8fafc" stroke-width="5" stroke-linecap="round" fill="none" opacity=".85"/>
  </g>
  <circle cx="300" cy="300" r="8" fill="#0f172a"/>
</svg>'''


def engine_background():
    streaks = "".join(
        f'<div class="streak" style="top:{top}%;animation-duration:{dur}s;animation-delay:{delay}s"></div>'
        for top, dur, delay in [(14, 3.8, 0), (23, 5.2, 1.4), (31, 4.4, 2.6), (42, 3.4, .7),
                                (49, 6.0, 3.1), (58, 4.0, 1.9), (66, 5.4, .3), (77, 4.6, 2.2),
                                (85, 3.6, 3.6)]
    )
    svg = base64.b64encode(_engine_svg().encode()).decode()
    html(f'<style>:root {{--engine-svg: url("data:image/svg+xml;base64,{svg}");}}</style>'
         f'<div class="es-bg"><div class="grid"></div><div class="engine"></div>'
         f'{streaks}<div class="fade"></div></div>')


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


def feature_card(col, icon, title, text, tint="rgba(59,130,246,.14)"):
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
        f'opacity:{1 if name == risk else .25}"></span>'
        for lo, hi, name in segments
    )
    pos = min(rul / scale_max * 100, 99.5)
    scale = "".join(f'<span style="left:{v / scale_max * 100:.2f}%">{label}</span>'
                    for v, label in [(0, "0"), (15, "15"), (30, "30"), (60, "60"),
                                     (scale_max, f"{scale_max:.0f}+")])
    html(f'''
<div class="es-result" style="background:{r["tint"]};border-color:{r["color"]}55">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem">
    <div><div class="cap">Predicted remaining useful life</div>
    <div class="big">{rul:.0f}<small>cycles</small></div></div>
    {badge(risk)}
  </div>
  <div class="es-track">{track}</div>
  <div class="es-marker"><i style="left:{pos:.2f}%"></i></div>
  <div class="es-scale">{scale}</div>
  <h3>{escape(r["headline"])}</h3>
  <p>{escape(r["action"])}</p>
  <p class="note">Based on the last {cycles_seen} cycles of sensor history.</p>
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
    return (chart.configure(font="Inter", background="transparent")
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor="#1a2336",
                            domainColor=LINE, tickColor=LINE, labelFontSize=11, titleFontSize=12)
            .configure_legend(labelColor=TEXT, titleColor=MUTED, orient="top", direction="horizontal"))


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
    rules = alt.Chart(thresholds).mark_rule(strokeDash=[4, 4], color="#475569").encode(y="rul:Q")
    return _style((bars + rules).properties(height=300))


def risk_donut(predictions):
    counts = (predictions["risk_level"].value_counts().reindex(RISK_ORDER, fill_value=0)
              .rename_axis("risk").reset_index(name="engines"))
    counts["order"] = range(len(counts))
    base = alt.Chart(counts).encode(
        theta=alt.Theta("engines:Q", stack=True),
        color=alt.Color("risk:N", scale=_risk_scale(), legend=alt.Legend(title=None, orient="bottom", columns=2, labelFontSize=12)),
        order="order:Q",
        tooltip=["risk:N", "engines:Q"],
    )
    donut = base.mark_arc(innerRadius=70, outerRadius=110, cornerRadius=4, padAngle=0.02,
                          stroke="#0b1222", strokeWidth=2)
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
    raw = base.mark_line(color="#1e40af", strokeWidth=1, opacity=.9).encode(
        y=alt.Y("value:Q", title=None, scale=alt.Scale(zero=False)))
    trend = base.mark_line(color="#60a5fa", strokeWidth=2.5).encode(
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
