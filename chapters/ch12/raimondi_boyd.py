"""
chapters/ch12/raimondi_boyd.py
Raimondi–Boyd journal bearing design charts with per-chart calculators.
"""

import os
import sys
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DATA_DIR = os.path.join(ROOT, "data", "ch12")

# ── helpers ───────────────────────────────────────────────────────────────────

def _p(name):
    return os.path.join(DATA_DIR, name)

def _load(name):
    df = pd.read_csv(_p(name), header=None, names=["S", "y"])
    return df.sort_values("S").drop_duplicates("S")

def _interp_df(df, s_vals):
    return np.interp(s_vals, df["S"].values, df["y"].values, left=np.nan, right=np.nan)

COLORS = {
    "∞":   "#00d4aa",
    "1":   "#4f9cf9",
    "1/2": "#f4a432",
    "1/4": "#e05c5c",
    "interp": "#bb86fc",
}

def _base_fig():
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(family="IBM Plex Mono", color="#cdd6f4", size=11),
        margin=dict(l=60, r=40, t=40, b=70),
        legend=dict(bgcolor="#161b22", bordercolor="#2d3748", borderwidth=1,
                    font=dict(size=10), x=0.01, y=0.99),
        xaxis=dict(
            type="log", gridcolor="#1e2633", gridwidth=1, zerolinecolor="#2d3748",
            title=dict(text="Bearing Characteristic Number,  S = (r/c)² μN/P",
                       font=dict(size=11)),
            tickfont=dict(size=10), showgrid=True,
            minor=dict(showgrid=True, gridcolor="#161b22"),
        ),
        yaxis=dict(gridcolor="#1e2633", gridwidth=1, zerolinecolor="#2d3748",
                   tickfont=dict(size=10), showgrid=True),
        height=500,
    )
    return fig

# ── data (cached) ─────────────────────────────────────────────────────────────

@st.cache_resource
def _load_data():
    film = {
        "∞":   _load("film_infinity.csv"),
        "1":   _load("film_one.csv"),
        "1/2": _load("film_half.csv"),
        "1/4": _load("film_quarter.csv"),
    }
    friction = {
        "∞":   _load("friction_infinity.csv"),
        "1":   _load("friction_one.csv"),
        "1/2": _load("friction_half.csv"),
        "1/4": _load("friction_quarter.csv"),
    }
    flowrate = {
        "∞":   _load("flowrate_infinity.csv"),
        "1":   _load("flowrate_one.csv"),
        "1/2": _load("flowrate_half.csv"),
        "1/4": _load("flowrate_quarter.csv"),
    }
    # l/d = ∞ → Qs/Q = 0 by definition (infinite bearing, no side leakage)
    flowratio = {
        "∞":   None,
        "1":   _load("flowratio_one.csv"),
        "1/2": _load("flowratio_half.csv"),
        "1/4": _load("flowratio_quarter.csv"),
    }
    return film, friction, flowrate, flowratio

# ── Raimondi–Boyd interpolation ───────────────────────────────────────────────

def _rb(r, s_vals, data):
    s_vals = np.asarray(s_vals, dtype=float)
    def get(key):
        if data[key] is None:
            return np.zeros_like(s_vals)
        return _interp_df(data[key], s_vals)
    pi, p1, ph, pq = get("∞"), get("1"), get("1/2"), get("1/4")
    return (1/r**3) * (
        -(1/8)  * (1-r) * (1-2*r) * (1-4*r) * pi
        +(1/3)  * (1-2*r) * (1-4*r)          * p1
        -(1/4)  * (1-r)   * (1-4*r)           * ph
        +(1/24) * (1-r)   * (1-2*r)           * pq
    )

# ── temperature curve fits ────────────────────────────────────────────────────

TEMP_FITS = {
    "1":   lambda S: 0.349109 + 6.009400*S + 0.047467*S**2,
    "1/2": lambda S: 0.394552 + 6.392527*S - 0.036013*S**2,
    "1/4": lambda S: 0.933828 + 6.437512*S - 0.011048*S**2,
}

S_FINE = np.logspace(np.log10(0.005), np.log10(10), 400)

# ── shared UI helpers ─────────────────────────────────────────────────────────

def _formula_box(html):
    st.markdown(
        f'<div style="background:#161b22;border:1px solid #2d3748;border-left:3px solid #00d4aa;'
        f'padding:0.9rem 1.1rem;border-radius:4px;font-family:IBM Plex Mono,monospace;'
        f'font-size:0.78rem;color:#cdd6f4;margin:0.8rem 0;line-height:1.8">{html}</div>',
        unsafe_allow_html=True,
    )

def _note_box(html):
    st.markdown(
        f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.75rem;'
        f'color:#8892a4;background:#161b22;border-left:3px solid #00d4aa;'
        f'padding:0.3rem 0.8rem;margin-bottom:0.6rem;display:inline-block">{html}</div>',
        unsafe_allow_html=True,
    )

def _result_box(label, value, unit=""):
    st.markdown(
        f'<div style="background:#161b22;border:1px solid #2d3748;border-radius:6px;'
        f'padding:1rem 1.2rem;margin-top:0.4rem">'
        f'<div style="font-family:IBM Plex Sans,sans-serif;font-size:0.78rem;color:#8892a4">'
        f'{label}</div>'
        f'<hr style="border:none;border-top:1px solid #2d3748;margin:0.5rem 0">'
        f'<div style="font-family:IBM Plex Mono,monospace;font-size:1.5rem;'
        f'font-weight:600;color:#00d4aa">{value:.6g}{unit}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

def _calc_inputs(key, ld_default=1.0, S_default=0.1):
    c1, c2 = st.columns([1, 1])
    with c1:
        ld = st.number_input("l/d", min_value=0.05, max_value=4.0,
                             value=ld_default, step=0.05, format="%.2f",
                             key=f"ld_{key}")
    with c2:
        S = st.number_input("Sommerfeld number S", min_value=0.001, max_value=10.0,
                            value=S_default, step=0.001, format="%.4f",
                            key=f"S_{key}")
    return ld, S

# ── individual chart renderers ────────────────────────────────────────────────

def _render_film(film):
    _note_box("Fig 12-16 · Minimum Film Thickness Variable h₀/c vs Sommerfeld Number")
    cc, co = st.columns([5, 1])
    with co:
        show = st.checkbox("Show interpolated", False, key="sh_film")
        if show:
            ri = st.slider("l/d", 0.05, 2.0, 0.75, 0.05, key="ri_film")
    with cc:
        fig = _base_fig()
        for lbl, df in film.items():
            fig.add_trace(go.Scatter(x=df["S"], y=df["y"], mode="lines",
                name=f"l/d = {lbl}", line=dict(color=COLORS[lbl], width=2)))
        if show:
            yi = _rb(ri, S_FINE, film)
            m = ~np.isnan(yi)
            fig.add_trace(go.Scatter(x=S_FINE[m], y=yi[m], mode="lines",
                name=f"l/d = {ri:.2f} (interp)",
                line=dict(color=COLORS["interp"], width=2, dash="dash")))
        fig.update_layout(yaxis_title="h₀/c  (dimensionless)", yaxis=dict(range=[0, 1.05]))
        st.plotly_chart(fig, use_container_width=True)
    _formula_box("Eccentricity ratio &nbsp; ε = 1 − h₀/c")

    st.markdown("---")
    st.markdown("#### 🔢 Calculator")
    var = st.selectbox("Output variable",
                       ["h₀/c  — Film Thickness Variable",
                        "ε = 1 − h₀/c  — Eccentricity Ratio"],
                       key="var_film")
    ld, S = _calc_inputs("film")
    if st.button("Compute", key="btn_film"):
        raw = float(_rb(ld, [S], film)[0])
        val = raw if "h₀/c" in var else 1 - raw
        _result_box(f"l/d = {ld:.2f}  ·  S = {S:.4f}  ·  {var}", val)


def _render_friction(friction):
    _note_box("Coefficient-of-Friction Variable (r/c)·f vs Sommerfeld Number")
    cc, co = st.columns([5, 1])
    with co:
        show = st.checkbox("Show interpolated", False, key="sh_fric")
        if show:
            ri = st.slider("l/d", 0.05, 2.0, 0.75, 0.05, key="ri_fric")
    with cc:
        fig = _base_fig()
        for lbl, df in friction.items():
            fig.add_trace(go.Scatter(x=df["S"], y=df["y"], mode="lines",
                name=f"l/d = {lbl}", line=dict(color=COLORS[lbl], width=2)))
        if show:
            yi = _rb(ri, S_FINE, friction)
            m = ~np.isnan(yi)
            fig.add_trace(go.Scatter(x=S_FINE[m], y=yi[m], mode="lines",
                name=f"l/d = {ri:.2f} (interp)",
                line=dict(color=COLORS["interp"], width=2, dash="dash")))
        fig.update_layout(yaxis_title="(r/c)·f  (dimensionless)", yaxis=dict(type="log"))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🔢 Calculator")
    ld, S = _calc_inputs("fric")
    if st.button("Compute", key="btn_fric"):
        val = float(_rb(ld, [S], friction)[0])
        _result_box(f"l/d = {ld:.2f}  ·  S = {S:.4f}  ·  (r/c)·f", val)


def _render_flowrate(flowrate):
    _note_box("Flow Variable Q/(rcNl) vs Sommerfeld Number")
    cc, co = st.columns([5, 1])
    with co:
        show = st.checkbox("Show interpolated", False, key="sh_fr")
        if show:
            ri = st.slider("l/d", 0.05, 2.0, 0.75, 0.05, key="ri_fr")
    with cc:
        fig = _base_fig()
        for lbl, df in flowrate.items():
            fig.add_trace(go.Scatter(x=df["S"], y=df["y"], mode="lines",
                name=f"l/d = {lbl}", line=dict(color=COLORS[lbl], width=2)))
        if show:
            yi = _rb(ri, S_FINE, flowrate)
            m = ~np.isnan(yi)
            fig.add_trace(go.Scatter(x=S_FINE[m], y=yi[m], mode="lines",
                name=f"l/d = {ri:.2f} (interp)",
                line=dict(color=COLORS["interp"], width=2, dash="dash")))
        fig.update_layout(yaxis_title="Q / (rcNl)  (dimensionless)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🔢 Calculator")
    ld, S = _calc_inputs("fr")
    if st.button("Compute", key="btn_fr"):
        val = float(_rb(ld, [S], flowrate)[0])
        _result_box(f"l/d = {ld:.2f}  ·  S = {S:.4f}  ·  Q/(rcNl)", val)


def _render_flowratio(flowratio):
    _note_box("Side-Leakage Flow Ratio Qs/Q vs Sommerfeld Number")
    _formula_box(
        "l/d = ∞ not plotted — Qs/Q ≡ 0 for an infinite bearing (no side leakage).<br>"
        "This value is hardcoded as 0 in the Raimondi–Boyd interpolation formula."
    )
    cc, co = st.columns([5, 1])
    with co:
        show = st.checkbox("Show interpolated", False, key="sh_frat")
        if show:
            ri = st.slider("l/d", 0.05, 2.0, 0.75, 0.05, key="ri_frat")
    with cc:
        fig = _base_fig()
        for lbl, df in flowratio.items():
            if df is None:
                continue
            fig.add_trace(go.Scatter(x=df["S"], y=df["y"], mode="lines",
                name=f"l/d = {lbl}", line=dict(color=COLORS[lbl], width=2)))
        if show:
            yi = _rb(ri, S_FINE, flowratio)
            m = ~np.isnan(yi)
            fig.add_trace(go.Scatter(x=S_FINE[m], y=yi[m], mode="lines",
                name=f"l/d = {ri:.2f} (interp)",
                line=dict(color=COLORS["interp"], width=2, dash="dash")))
        fig.update_layout(yaxis_title="Qs / Q  (dimensionless)", yaxis=dict(range=[0, 1.05]))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🔢 Calculator")
    ld, S = _calc_inputs("frat")
    if st.button("Compute", key="btn_frat"):
        val = float(_rb(ld, [S], flowratio)[0])
        _result_box(f"l/d = {ld:.2f}  ·  S = {S:.4f}  ·  Qs/Q", val)


def _render_temp():
    _note_box("Temperature Rise Dimensionless Variable vs Sommerfeld Number")
    _formula_box(
        "Dimensionless variable = 9.70·ΔT_F / P_psi &nbsp;=&nbsp; 0.120·ΔT_C / P_MPa<br><br>"
        "<b>Curve-fit equations (valid S ≈ 0.01 – 1.0):</b><br>"
        "&nbsp; l/d = 1 &nbsp;&nbsp;&nbsp;: 0.349 109 + 6.009 40·S + 0.047 467·S²<br>"
        "&nbsp; l/d = 1/2 : 0.394 552 + 6.392 527·S − 0.036 013·S²<br>"
        "&nbsp; l/d = 1/4 : 0.933 828 + 6.437 512·S − 0.011 048·S²"
    )
    S_range = np.logspace(np.log10(0.01), np.log10(1.0), 300)
    fig = _base_fig()
    for lbl, fn in TEMP_FITS.items():
        fig.add_trace(go.Scatter(x=S_range, y=fn(S_range), mode="lines",
            name=f"l/d = {lbl}", line=dict(color=COLORS[lbl], width=2)))
    fig.update_layout(
        yaxis_title="9.70·ΔT_F/P_psi  or  0.120·ΔT_C/P_MPa",
        xaxis=dict(range=[np.log10(0.01), np.log10(1.0)]),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🔢 Calculator")
    c1, c2, c3 = st.columns([0.8, 1, 1.6])
    with c1:
        ld_t = st.selectbox("l/d", ["1", "1/2", "1/4"], key="ld_temp")
    with c2:
        S_t = st.number_input("S", min_value=0.01, max_value=1.0,
                              value=0.1, step=0.001, format="%.4f", key="S_temp")
    with c3:
        out_t = st.selectbox("Output variable", [
            "Dimensionless variable",
            "ΔT  in °F  (enter P in psi below)",
            "ΔT  in °C  (enter P in MPa below)",
        ], key="out_temp")

    P_t = None
    if out_t != "Dimensionless variable":
        unit_str = "psi" if "°F" in out_t else "MPa"
        P_t = st.number_input(f"Pressure P ({unit_str})",
                              min_value=0.01, value=100.0, step=1.0,
                              format="%.2f", key="P_temp")

    if st.button("Compute", key="btn_temp"):
        dv = TEMP_FITS[ld_t](S_t)
        if out_t == "Dimensionless variable":
            val, unit = dv, ""
        elif "°F" in out_t:
            val, unit = dv * P_t / 9.70, " °F"
        else:
            val, unit = dv * P_t / 0.120, " °C"
        _result_box(f"l/d = {ld_t}  ·  S = {S_t:.4f}  ·  {out_t}", val, unit)

# ── public entry point ────────────────────────────────────────────────────────

CHARTS = {
    "Film Thickness  h₀/c":           "_render_film",
    "Friction Variable  (r/c)·f":     "_render_friction",
    "Flow Rate  Q/(rcNl)":            "_render_flowrate",
    "Flow Ratio  Qs/Q":               "_render_flowratio",
    "Temperature Rise":               "_render_temp",
}

def render():
    film, friction, flowrate, flowratio = _load_data()

    selected = st.selectbox(
        "Select chart",
        list(CHARTS.keys()),
        key="ch12_chart_select"
    )
    st.markdown("---")

    dispatch = {
        "Film Thickness  h₀/c":       lambda: _render_film(film),
        "Friction Variable  (r/c)·f": lambda: _render_friction(friction),
        "Flow Rate  Q/(rcNl)":        lambda: _render_flowrate(flowrate),
        "Flow Ratio  Qs/Q":           lambda: _render_flowratio(flowratio),
        "Temperature Rise":           lambda: _render_temp(),
    }
    dispatch[selected]()