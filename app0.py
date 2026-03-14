"""
app.py  —  entry point, routing only.
Run with:  streamlit run app.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

st.set_page_config(
    page_title="Shigley's Reference",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stTabs [data-baseweb="tab-list"] {
    gap: 0px; background: #0f1117; padding: 0 1rem;
    border-bottom: 2px solid #00d4aa;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase; color: #8892a4;
    padding: 0.75rem 1.2rem; border-radius: 0; border: none; background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #00d4aa !important; background: transparent !important;
    border-bottom: 2px solid #00d4aa !important;
}
h1 {
    font-family: 'IBM Plex Mono', monospace; font-size: 1.1rem; font-weight: 600;
    letter-spacing: 0.15em; text-transform: uppercase; color: #00d4aa;
}
.subtitle {
    font-family: 'IBM Plex Sans', sans-serif; font-size: 0.85rem;
    color: #8892a4; margin-bottom: 1.5rem; letter-spacing: 0.04em;
}
</style>
""", unsafe_allow_html=True)

# ── chapter imports ───────────────────────────────────────────────────────────
# Each chapter module exposes a single render() function.
# To add a new chapter: import it here and add one tab below.

from chapters.ch11 import tables as ch11_tables
from chapters.ch12 import raimondi_boyd as ch12_rb

# ── header ────────────────────────────────────────────────────────────────────

st.title("Shigley's — Charts & Tables Reference")
st.markdown(
    '<div class="subtitle">Mechanical Engineering Design · '
    'Interactive chart readout and table lookup</div>',
    unsafe_allow_html=True,
)

# ── tabs ──────────────────────────────────────────────────────────────────────
# Add a tab here when a new chapter module is ready.

tab_ch11, tab_ch12 = st.tabs([
    "Ch 11 — Rolling Bearings",
    "Ch 12 — Journal Bearings",
])

with tab_ch11:
    ch11_tables.render()

with tab_ch12:
    ch12_rb.render()