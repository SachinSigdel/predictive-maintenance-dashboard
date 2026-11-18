import streamlit as st

from core import load_artifacts, BASE_DIR
from ui import inject_css, footer

st.set_page_config(
    page_title="EngineSight — Predictive Maintenance",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()
st.logo(str(BASE_DIR / "assets" / "logo.svg"), size="large")

try:
    load_artifacts()
except FileNotFoundError as error:
    st.error(f"The prediction model could not be loaded: {error}")
    st.stop()

pages = [
    st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("views/fleet.py", title="Fleet Dashboard", icon=":material/dashboard:"),
    st.Page("views/engine.py", title="Check an Engine", icon=":material/troubleshoot:"),
    st.Page("views/how_it_works.py", title="How It Works", icon=":material/menu_book:"),
]

page = st.navigation(pages, position="top")
page.run()
footer()
