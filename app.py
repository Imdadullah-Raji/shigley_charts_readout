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

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 0px;
    background: #0f1117;
    padding: 0 1rem;
    border-bottom: 2px solid #00d4aa;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #8892a4;
    padding: 0.75rem 1.2rem;
    border-radius: 0;
    border: none;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #00d4aa !important;
    background: transparent !important;
    border-bottom: 2px solid #00d4aa !important;
}
h1 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.1rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #00d4aa;
}
.subtitle {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.85rem;
    color: #8892a4;
    margin-bottom: 1.5rem;
    letter-spacing: 0.04em;
}
.chart-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #8892a4;
    background: #161b22;
    padding: 0.3rem 0.8rem;
    border-left: 3px solid #00d4aa;
    margin-bottom: 0.5rem;
    display: inline-block;
}
.formula-box {
    background: #161b22;
    border: 1px solid #2d3748;
    border-left: 3px solid #00d4aa;
    padding: 1rem 1.2rem;
    border-radius: 4px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #cdd6f4;
    margin: 1rem 0;
    line-height: 1.8;
}
</style>
""", unsafe_allow_html=True)

# ── helpers ──────────────────────────────────────────────────────────────────

def load(path):
    df = pd.read_csv(path, header=None, names=["S", "y"])
    df = df.sort_values("S").drop_duplicates("S")
    return df

def interp(df, s_vals):
    return np.interp(s_vals, df["S"].values, df["y"].values,
                     left=np.nan, right=np.nan)

COLORS = {
    "∞":  "#00d4aa",
    "1":  "#4f9cf9",
    "1/2":"#f4a432",
    "1/4":"#e05c5c",
    "interpolated": "#bb86fc",
}

def base_fig(xlog=True):
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(family="IBM Plex Mono", color="#cdd6f4", size=11),
        margin=dict(l=60, r=40, t=40, b=70),
        legend=dict(
            bgcolor="#161b22", bordercolor="#2d3748", borderwidth=1,
            font=dict(size=10), x=0.01, y=0.99
        ),
        xaxis=dict(
            type="log" if xlog else "linear",
            gridcolor="#1e2633", gridwidth=1,
            zerolinecolor="#2d3748",
            title=dict(text="Bearing Characteristic Number, S = (r/c)² μN/P",
                       font=dict(size=11)),
            tickfont=dict(size=10),
            showgrid=True, minor=dict(showgrid=True, gridcolor="#161b22"),
        ),
        yaxis=dict(
            gridcolor="#1e2633", gridwidth=1,
            zerolinecolor="#2d3748",
            tickfont=dict(size=10),
            showgrid=True,
        ),
        height=520,
    )
    return fig

# ── data ─────────────────────────────────────────────────────────────────────

film = {
    "∞":  load("./film_infinity.csv"),
    "1":  load("./film_one.csv"),
    "1/2":load("./film_half.csv"),
    "1/4":load("./film_quarter.csv"),
}
friction = {
    "∞":  load("./friction_infinity.csv"),
    "1":  load("./friction_one.csv"),
    "1/2":load("./friction_half.csv"),
    "1/4":load("./friction_quarter.csv"),
}
flowrate = {
    "∞":  load("./flowrate_infinity.csv"),
    "1":  load("./flowrate_one.csv"),
    "1/2":load("./flowrate_half.csv"),
    "1/4":load("./flowrate_quarter.csv"),
}
flowratio = {
    "1":  load("./flowratio_one.csv"),
    "1/2":load("./flowratio_half.csv"),
    "1/4":load("./flowratio_quarter.csv"),
}

# ── interpolation formula ─────────────────────────────────────────────────────

def rb_interp(r, s_vals, data):
    """Raimondi-Boyd interpolation for arbitrary l/d = r"""
    pi = interp(data["∞"],   s_vals)
    p1 = interp(data["1"],   s_vals)
    ph = interp(data["1/2"], s_vals)
    pq = interp(data["1/4"], s_vals)
    result = (1/r**3) * (
        -(1/8)*(1-r)*(1-2*r)*(1-4*r)*pi
        +(1/3)*(1-2*r)*(1-4*r)*p1
        -(1/4)*(1-r)*(1-4*r)*ph
        +(1/24)*(1-r)*(1-2*r)*pq
    )
    return result

# ── header ────────────────────────────────────────────────────────────────────

st.title("Raimondi & Boyd — Journal Bearing Design Charts")
st.markdown('<div class="subtitle">Chapter 12 · Hydrodynamic and Hydrostatic Bearings · Digitized Data + Interpolation</div>',
            unsafe_allow_html=True)

# ── sidebar: interpolation tool ───────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Interpolation Tool")
    st.markdown("Compute properties for arbitrary *l/d* using the Raimondi–Boyd formula.")
    r_val = st.number_input("l/d value", min_value=0.05, max_value=4.0, value=0.75, step=0.05)
    S_val = st.number_input("Sommerfeld number S", min_value=0.005, max_value=10.0, value=0.1, step=0.005, format="%.4f")
    s_pt  = np.array([S_val])
    if st.button("Compute", use_container_width=True):
        h0c  = rb_interp(r_val, s_pt, film)[0]
        fric = rb_interp(r_val, s_pt, friction)[0]
        fr   = rb_interp(r_val, s_pt, flowrate)[0]
        frat = rb_interp(r_val, s_pt, flowratio)[0]
        st.metric("h₀/c (film thickness)", f"{h0c:.4f}")
        st.metric("(r/c)·f (friction var.)", f"{fric:.4f}")
        st.metric("Q/(rcNl) (flow rate)", f"{fr:.4f}")
        st.metric("Qs/Q (flow ratio)", f"{frat:.4f}")

# ── tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📐 Film Thickness",
    "🔩 Friction Variable",
    "💧 Flow Rate",
    "⚖️ Flow Ratio",
    "🌡️ Temperature Rise",
])

# ─── common S grid for interpolated curves
s_fine = np.logspace(np.log10(0.005), np.log10(10), 300)

# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="chart-label">Fig 12-16 · Minimum Film Thickness Variable h₀/c vs Sommerfeld Number</div>',
                unsafe_allow_html=True)

    col_chart, col_opts = st.columns([5, 1])
    with col_opts:
        show_interp = st.checkbox("Show interpolated l/d", value=False, key="f1")
        if show_interp:
            r_film = st.slider("l/d", 0.25, 2.0, 0.75, 0.05, key="r_film")

    with col_chart:
        fig = base_fig(xlog=True)
        for label, df in film.items():
            fig.add_trace(go.Scatter(
                x=df["S"], y=df["y"], mode="lines", name=f"l/d = {label}",
                line=dict(color=COLORS[label], width=2),
            ))
        if show_interp:
            y_interp = rb_interp(r_film, s_fine, film)
            mask = ~np.isnan(y_interp)
            fig.add_trace(go.Scatter(
                x=s_fine[mask], y=y_interp[mask], mode="lines",
                name=f"l/d = {r_film} (interp)",
                line=dict(color=COLORS["interpolated"], width=2, dash="dash"),
            ))
        fig.update_layout(
            yaxis_title="h₀/c (dimensionless)",
            yaxis=dict(range=[0, 1.05]),
            xaxis=dict(range=[np.log10(0.005), np.log10(10)]),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="formula-box">Eccentricity ratio: ε = 1 − h₀/c<br>Left axis: h₀/c &nbsp;|&nbsp; Right axis: ε = 1 − h₀/c</div>',
                unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="chart-label">Coefficient-of-Friction Variable (r/c)·f vs Sommerfeld Number</div>',
                unsafe_allow_html=True)

    col_chart, col_opts = st.columns([5, 1])
    with col_opts:
        show_interp2 = st.checkbox("Show interpolated l/d", value=False, key="f2")
        if show_interp2:
            r_fric = st.slider("l/d", 0.25, 2.0, 0.75, 0.05, key="r_fric")

    with col_chart:
        fig2 = base_fig(xlog=True)
        for label, df in friction.items():
            fig2.add_trace(go.Scatter(
                x=df["S"], y=df["y"], mode="lines", name=f"l/d = {label}",
                line=dict(color=COLORS[label], width=2),
            ))
        if show_interp2:
            y_interp2 = rb_interp(r_fric, s_fine, friction)
            mask = ~np.isnan(y_interp2)
            fig2.add_trace(go.Scatter(
                x=s_fine[mask], y=y_interp2[mask], mode="lines",
                name=f"l/d = {r_fric} (interp)",
                line=dict(color=COLORS["interpolated"], width=2, dash="dash"),
            ))
        fig2.update_layout(
            yaxis_title="(r/c)·f (dimensionless)",
            yaxis=dict(type="log"),
        )
        st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="chart-label">Flow Variable Q/(rcNl) vs Sommerfeld Number</div>',
                unsafe_allow_html=True)

    col_chart, col_opts = st.columns([5, 1])
    with col_opts:
        show_interp3 = st.checkbox("Show interpolated l/d", value=False, key="f3")
        if show_interp3:
            r_flow = st.slider("l/d", 0.25, 2.0, 0.75, 0.05, key="r_flow")

    with col_chart:
        fig3 = base_fig(xlog=True)
        for label, df in flowrate.items():
            fig3.add_trace(go.Scatter(
                x=df["S"], y=df["y"], mode="lines", name=f"l/d = {label}",
                line=dict(color=COLORS[label], width=2),
            ))
        if show_interp3:
            y_interp3 = rb_interp(r_flow, s_fine, flowrate)
            mask = ~np.isnan(y_interp3)
            fig3.add_trace(go.Scatter(
                x=s_fine[mask], y=y_interp3[mask], mode="lines",
                name=f"l/d = {r_flow} (interp)",
                line=dict(color=COLORS["interpolated"], width=2, dash="dash"),
            ))
        fig3.update_layout(
            yaxis_title="Q / (rcNl) (dimensionless)",
        )
        st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="chart-label">Side-Leakage Flow Ratio Qs/Q vs Sommerfeld Number</div>',
                unsafe_allow_html=True)

    col_chart, col_opts = st.columns([5, 1])
    with col_opts:
        show_interp4 = st.checkbox("Show interpolated l/d", value=False, key="f4")
        if show_interp4:
            r_frat = st.slider("l/d", 0.25, 2.0, 0.75, 0.05, key="r_frat")

    with col_chart:
        fig4 = base_fig(xlog=True)
        # flowratio has no infinity curve — plot only 1, 1/2, 1/4
        for label, df in flowratio.items():
            fig4.add_trace(go.Scatter(
                x=df["S"], y=df["y"], mode="lines", name=f"l/d = {label}",
                line=dict(color=COLORS[label], width=2),
            ))
        if show_interp4:
            # For flowratio we need an infinity proxy — use a flat ~0 line
            # Actually the formula requires all 4; skip infinity for flowratio
            st.info("Interpolation for flow ratio requires l/d = ∞ data (not available). Showing digitized curves only.")
        fig4.update_layout(
            yaxis_title="Qs / Q (dimensionless)",
            yaxis=dict(range=[0, 1.05]),
        )
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="chart-label">Temperature Rise Variable vs Sommerfeld Number — Curve Fits (Raimondi & Boyd)</div>',
                unsafe_allow_html=True)

    st.markdown("""
<div class="formula-box">
Temperature Rise Dimensionless Variable = 9.70·ΔT_F / P_psi &nbsp;=&nbsp; 0.120·ΔT_C / P_MPa<br><br>
<b>Curve-fit equations (valid range S ≈ 0.01 – 1.0):</b><br>
&nbsp; l/d = 1 &nbsp;&nbsp;&nbsp;: 0.349 109 + 6.009 40·S + 0.047 467·S²<br>
&nbsp; l/d = 1/2 : 0.394 552 + 6.392 527·S − 0.036 013·S²<br>
&nbsp; l/d = 1/4 : 0.933 828 + 6.437 512·S − 0.011 048·S²<br>
</div>
""", unsafe_allow_html=True)

    S_range = np.logspace(np.log10(0.01), np.log10(1.0), 300)
    fits = {
        "1":   lambda S: 0.349109 + 6.00940*S + 0.047467*S**2,
        "1/2": lambda S: 0.394552 + 6.392527*S - 0.036013*S**2,
        "1/4": lambda S: 0.933828 + 6.437512*S - 0.011048*S**2,
    }

    fig5 = base_fig(xlog=True)
    for label, fn in fits.items():
        fig5.add_trace(go.Scatter(
            x=S_range, y=fn(S_range), mode="lines", name=f"l/d = {label}",
            line=dict(color=COLORS[label], width=2),
        ))
    fig5.update_layout(
        yaxis_title="9.70·ΔT_F/P_psi  or  0.120·ΔT_C/P_MPa",
        xaxis=dict(range=[np.log10(0.01), np.log10(1.0)]),
    )
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown("""
<div class="formula-box">
To find temperature rise:<br>
&nbsp; ΔT_F = (dimensionless variable) × P_psi / 9.70<br>
&nbsp; ΔT_C = (dimensionless variable) × P_MPa / 0.120
</div>
""", unsafe_allow_html=True)