import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Raimondi & Boyd Bearing Charts",
    layout="wide",
    initial_sidebar_state="collapsed"
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
    font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem;
    font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
    color: #8892a4; padding: 0.75rem 1.2rem;
    border-radius: 0; border: none; background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #00d4aa !important; background: transparent !important;
    border-bottom: 2px solid #00d4aa !important;
}
h1 {
    font-family: 'IBM Plex Mono', monospace; font-size: 1.1rem;
    font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase;
    color: #00d4aa;
}
.subtitle {
    font-family: 'IBM Plex Sans', sans-serif; font-size: 0.85rem;
    color: #8892a4; margin-bottom: 1.5rem; letter-spacing: 0.04em;
}
.chart-label {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem;
    color: #8892a4; background: #161b22; padding: 0.3rem 0.8rem;
    border-left: 3px solid #00d4aa; margin-bottom: 0.5rem; display: inline-block;
}
.formula-box {
    background: #161b22; border: 1px solid #2d3748;
    border-left: 3px solid #00d4aa; padding: 1rem 1.2rem;
    border-radius: 4px; font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem; color: #cdd6f4; margin: 1rem 0; line-height: 1.8;
}
.calc-box {
    background: #161b22; border: 1px solid #2d3748;
    border-radius: 6px; padding: 1.2rem 1.4rem; margin-top: 0.5rem;
}
.result-value {
    font-family: 'IBM Plex Mono', monospace; font-size: 1.6rem;
    font-weight: 600; color: #00d4aa;
}
.result-label { font-family: 'IBM Plex Sans', sans-serif; font-size: 0.78rem; color: #8892a4; }
.divider { border: none; border-top: 1px solid #2d3748; margin: 0.6rem 0; }
</style>
""", unsafe_allow_html=True)

# ── helpers ───────────────────────────────────────────────────────────────────

DATA_DIR = os.path.dirname(os.path.abspath(__file__))

def p(name):
    return os.path.join(DATA_DIR, name)

def load(path):
    df = pd.read_csv(path, header=None, names=["S", "y"])
    return df.sort_values("S").drop_duplicates("S")

def interp_df(df, s_vals):
    return np.interp(s_vals, df["S"].values, df["y"].values, left=np.nan, right=np.nan)

COLORS = {"∞": "#00d4aa", "1": "#4f9cf9", "1/2": "#f4a432", "1/4": "#e05c5c", "interp": "#bb86fc"}

def base_fig():
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font=dict(family="IBM Plex Mono", color="#cdd6f4", size=11),
        margin=dict(l=60, r=40, t=40, b=70),
        legend=dict(bgcolor="#161b22", bordercolor="#2d3748", borderwidth=1, font=dict(size=10), x=0.01, y=0.99),
        xaxis=dict(
            type="log", gridcolor="#1e2633", gridwidth=1, zerolinecolor="#2d3748",
            title=dict(text="Bearing Characteristic Number,  S = (r/c)² μN/P", font=dict(size=11)),
            tickfont=dict(size=10), showgrid=True, minor=dict(showgrid=True, gridcolor="#161b22"),
        ),
        yaxis=dict(gridcolor="#1e2633", gridwidth=1, zerolinecolor="#2d3748", tickfont=dict(size=10), showgrid=True),
        height=500,
    )
    return fig

# ── data ──────────────────────────────────────────────────────────────────────

film = {
    "∞":   load(p("film_infinity.csv")),
    "1":   load(p("film_one.csv")),
    "1/2": load(p("film_half.csv")),
    "1/4": load(p("film_quarter.csv")),
}
friction = {
    "∞":   load(p("friction_infinity.csv")),
    "1":   load(p("friction_one.csv")),
    "1/2": load(p("friction_half.csv")),
    "1/4": load(p("friction_quarter.csv")),
}
flowrate = {
    "∞":   load(p("flowrate_infinity.csv")),
    "1":   load(p("flowrate_one.csv")),
    "1/2": load(p("flowrate_half.csv")),
    "1/4": load(p("flowrate_quarter.csv")),
}
# l/d=∞ → Qs/Q = 0 (no side leakage in infinite bearing), stored as None
flowratio = {
    "∞":   None,
    "1":   load(p("flowratio_one.csv")),
    "1/2": load(p("flowratio_half.csv")),
    "1/4": load(p("flowratio_quarter.csv")),
}

# ── Raimondi–Boyd interpolation ───────────────────────────────────────────────

def rb_interp(r, s_vals, data):
    s_vals = np.asarray(s_vals, dtype=float)
    def get(key):
        if data[key] is None:
            return np.zeros_like(s_vals)   # hardcoded 0 for ∞ flowratio
        return interp_df(data[key], s_vals)
    pi, p1, ph, pq = get("∞"), get("1"), get("1/2"), get("1/4")
    return (1/r**3) * (
        -(1/8)  * (1-r) * (1-2*r) * (1-4*r) * pi
        +(1/3)  * (1-2*r) * (1-4*r)          * p1
        -(1/4)  * (1-r)   * (1-4*r)           * ph
        +(1/24) * (1-r)   * (1-2*r)           * pq
    )

# ── temperature curve fits ────────────────────────────────────────────────────

temp_fits = {
    "1":   lambda S: 0.349109 + 6.009400*S + 0.047467*S**2,
    "1/2": lambda S: 0.394552 + 6.392527*S - 0.036013*S**2,
    "1/4": lambda S: 0.933828 + 6.437512*S - 0.011048*S**2,
}

s_fine = np.logspace(np.log10(0.005), np.log10(10), 400)

# ── reusable calculator ───────────────────────────────────────────────────────

def calc_widget(key, options):
    """
    options: dict { display_label: callable(r, S) -> float }
    """
    st.markdown("---")
    st.markdown("#### 🔢 Calculator")
    c1, c2, c3, c4 = st.columns([1, 1, 1.6, 1])
    with c1:
        ld = st.number_input("l/d", min_value=0.05, max_value=4.0,
                             value=1.0, step=0.05, format="%.2f", key=f"ld_{key}")
    with c2:
        S_in = st.number_input("Sommerfeld number S", min_value=0.001, max_value=10.0,
                               value=0.1, step=0.001, format="%.4f", key=f"S_{key}")
    with c3:
        var = st.selectbox("Output variable", options=list(options.keys()), key=f"var_{key}")
    with c4:
        st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
        compute = st.button("Compute", key=f"btn_{key}", use_container_width=True)

    if compute:
        val = options[var](ld, S_in)
        if val is None or np.isnan(val):
            st.warning("Result out of digitized data range for the given S value.")
        else:
            st.markdown(
                f"<div class='calc-box'>"
                f"<div class='result-label'>l/d = {ld:.2f} &nbsp;·&nbsp; S = {S_in:.4f} &nbsp;·&nbsp; {var}</div>"
                f"<hr class='divider'>"
                f"<div class='result-value'>{val:.6g}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

# ── page header ───────────────────────────────────────────────────────────────

st.title("Raimondi & Boyd — Journal Bearing Design Charts")
st.markdown(
    '<div class="subtitle">Chapter 12 · Hydrodynamic and Hydrostatic Bearings · '
    'Digitized Data + Raimondi–Boyd Interpolation</div>',
    unsafe_allow_html=True
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📐 Film Thickness",
    "🔩 Friction Variable",
    "💧 Flow Rate",
    "⚖️ Flow Ratio",
    "🌡️ Temperature Rise",
])

# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="chart-label">Fig 12-16 · Minimum Film Thickness Variable h₀/c vs Sommerfeld Number</div>', unsafe_allow_html=True)
    cc, co = st.columns([5, 1])
    with co:
        si1 = st.checkbox("Show interpolated curve", False, key="si1")
        if si1:
            ri1 = st.slider("l/d", 0.05, 2.0, 0.75, 0.05, key="ri1")
    with cc:
        fig1 = base_fig()
        for lbl, df in film.items():
            fig1.add_trace(go.Scatter(x=df["S"], y=df["y"], mode="lines",
                name=f"l/d = {lbl}", line=dict(color=COLORS[lbl], width=2)))
        if si1:
            yi = rb_interp(ri1, s_fine, film)
            m = ~np.isnan(yi)
            fig1.add_trace(go.Scatter(x=s_fine[m], y=yi[m], mode="lines",
                name=f"l/d = {ri1:.2f} (interp)",
                line=dict(color=COLORS["interp"], width=2, dash="dash")))
        fig1.update_layout(yaxis_title="h₀/c  (dimensionless)", yaxis=dict(range=[0, 1.05]))
        st.plotly_chart(fig1, use_container_width=True)
    st.markdown('<div class="formula-box">Eccentricity ratio &nbsp;ε = 1 − h₀/c</div>', unsafe_allow_html=True)

    calc_widget("film", {
        "h₀/c  — Film Thickness Variable":
            lambda r, S: float(rb_interp(r, [S], film)[0]),
        "ε = 1 − h₀/c  — Eccentricity Ratio":
            lambda r, S: float(1 - rb_interp(r, [S], film)[0]),
    })

# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="chart-label">Coefficient-of-Friction Variable (r/c)·f vs Sommerfeld Number</div>', unsafe_allow_html=True)
    cc, co = st.columns([5, 1])
    with co:
        si2 = st.checkbox("Show interpolated curve", False, key="si2")
        if si2:
            ri2 = st.slider("l/d", 0.05, 2.0, 0.75, 0.05, key="ri2")
    with cc:
        fig2 = base_fig()
        for lbl, df in friction.items():
            fig2.add_trace(go.Scatter(x=df["S"], y=df["y"], mode="lines",
                name=f"l/d = {lbl}", line=dict(color=COLORS[lbl], width=2)))
        if si2:
            yi = rb_interp(ri2, s_fine, friction)
            m = ~np.isnan(yi)
            fig2.add_trace(go.Scatter(x=s_fine[m], y=yi[m], mode="lines",
                name=f"l/d = {ri2:.2f} (interp)",
                line=dict(color=COLORS["interp"], width=2, dash="dash")))
        fig2.update_layout(yaxis_title="(r/c)·f  (dimensionless)", yaxis=dict(type="log"))
        st.plotly_chart(fig2, use_container_width=True)

    calc_widget("fric", {
        "(r/c)·f  — Friction Variable":
            lambda r, S: float(rb_interp(r, [S], friction)[0]),
    })

# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="chart-label">Flow Variable Q/(rcNl) vs Sommerfeld Number</div>', unsafe_allow_html=True)
    cc, co = st.columns([5, 1])
    with co:
        si3 = st.checkbox("Show interpolated curve", False, key="si3")
        if si3:
            ri3 = st.slider("l/d", 0.05, 2.0, 0.75, 0.05, key="ri3")
    with cc:
        fig3 = base_fig()
        for lbl, df in flowrate.items():
            fig3.add_trace(go.Scatter(x=df["S"], y=df["y"], mode="lines",
                name=f"l/d = {lbl}", line=dict(color=COLORS[lbl], width=2)))
        if si3:
            yi = rb_interp(ri3, s_fine, flowrate)
            m = ~np.isnan(yi)
            fig3.add_trace(go.Scatter(x=s_fine[m], y=yi[m], mode="lines",
                name=f"l/d = {ri3:.2f} (interp)",
                line=dict(color=COLORS["interp"], width=2, dash="dash")))
        fig3.update_layout(yaxis_title="Q / (rcNl)  (dimensionless)")
        st.plotly_chart(fig3, use_container_width=True)

    calc_widget("flowrate", {
        "Q/(rcNl)  — Flow Rate Variable":
            lambda r, S: float(rb_interp(r, [S], flowrate)[0]),
    })

# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="chart-label">Side-Leakage Flow Ratio Qs/Q vs Sommerfeld Number</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="formula-box">l/d = ∞ not plotted — Qs/Q ≡ 0 for an infinite bearing (no side leakage). '
        'This value is hardcoded as 0 in the Raimondi–Boyd interpolation.</div>',
        unsafe_allow_html=True
    )
    cc, co = st.columns([5, 1])
    with co:
        si4 = st.checkbox("Show interpolated curve", False, key="si4")
        if si4:
            ri4 = st.slider("l/d", 0.05, 2.0, 0.75, 0.05, key="ri4")
    with cc:
        fig4 = base_fig()
        for lbl, df in flowratio.items():
            if df is None:
                continue
            fig4.add_trace(go.Scatter(x=df["S"], y=df["y"], mode="lines",
                name=f"l/d = {lbl}", line=dict(color=COLORS[lbl], width=2)))
        if si4:
            yi = rb_interp(ri4, s_fine, flowratio)
            m = ~np.isnan(yi)
            fig4.add_trace(go.Scatter(x=s_fine[m], y=yi[m], mode="lines",
                name=f"l/d = {ri4:.2f} (interp)",
                line=dict(color=COLORS["interp"], width=2, dash="dash")))
        fig4.update_layout(yaxis_title="Qs / Q  (dimensionless)", yaxis=dict(range=[0, 1.05]))
        st.plotly_chart(fig4, use_container_width=True)

    calc_widget("flowratio", {
        "Qs/Q  — Side-Leakage Flow Ratio":
            lambda r, S: float(rb_interp(r, [S], flowratio)[0]),
    })

# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="chart-label">Temperature Rise Dimensionless Variable vs Sommerfeld Number</div>', unsafe_allow_html=True)
    st.markdown("""
<div class="formula-box">
Dimensionless variable = 9.70·ΔT_F / P_psi &nbsp;=&nbsp; 0.120·ΔT_C / P_MPa<br><br>
<b>Curve-fit equations (valid S ≈ 0.01 – 1.0):</b><br>
&nbsp; l/d = 1 &nbsp;&nbsp;&nbsp;: 0.349 109 + 6.009 40·S + 0.047 467·S²<br>
&nbsp; l/d = 1/2 : 0.394 552 + 6.392 527·S − 0.036 013·S²<br>
&nbsp; l/d = 1/4 : 0.933 828 + 6.437 512·S − 0.011 048·S²
</div>
""", unsafe_allow_html=True)

    S_range = np.logspace(np.log10(0.01), np.log10(1.0), 300)
    fig5 = base_fig()
    for lbl, fn in temp_fits.items():
        fig5.add_trace(go.Scatter(x=S_range, y=fn(S_range), mode="lines",
            name=f"l/d = {lbl}", line=dict(color=COLORS[lbl], width=2)))
    fig5.update_layout(
        yaxis_title="9.70·ΔT_F/P_psi  or  0.120·ΔT_C/P_MPa",
        xaxis=dict(range=[np.log10(0.01), np.log10(1.0)]),
    )
    st.plotly_chart(fig5, use_container_width=True)

    # Temperature calculator (slightly different — needs l/d dropdown + optional P)
    st.markdown("---")
    st.markdown("#### 🔢 Calculator")
    c1, c2, c3, c4, c5 = st.columns([0.8, 1, 1.6, 1, 1])
    with c1:
        ld_t = st.selectbox("l/d", ["1", "1/2", "1/4"], key="ld_t")
    with c2:
        S_t = st.number_input("S", min_value=0.01, max_value=1.0,
                              value=0.1, step=0.001, format="%.4f", key="S_t")
    with c3:
        out_t = st.selectbox("Output variable", [
            "Dimensionless variable",
            "ΔT  in °F  (enter P in psi)",
            "ΔT  in °C  (enter P in MPa)",
        ], key="out_t")
    with c4:
        P_t = 1.0
        if out_t != "Dimensionless variable":
            unit_str = "psi" if "°F" in out_t else "MPa"
            P_t = st.number_input(f"P ({unit_str})", min_value=0.01,
                                  value=100.0, step=1.0, format="%.2f", key="P_t")
    with c5:
        st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
        if st.button("Compute", key="btn_t", use_container_width=True):
            dv = temp_fits[ld_t](S_t)
            if out_t == "Dimensionless variable":
                val_t, unit_t = dv, ""
            elif "°F" in out_t:
                val_t, unit_t = dv * P_t / 9.70, " °F"
            else:
                val_t, unit_t = dv * P_t / 0.120, " °C"
            st.markdown(
                f"<div class='calc-box'>"
                f"<div class='result-label'>l/d = {ld_t} &nbsp;·&nbsp; S = {S_t:.4f} &nbsp;·&nbsp; {out_t}</div>"
                f"<hr class='divider'>"
                f"<div class='result-value'>{val_t:.6g}{unit_t}</div>"
                f"</div>",
                unsafe_allow_html=True
            )