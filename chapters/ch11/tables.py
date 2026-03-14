"""
chapters/ch11/tables.py
Renders the three Ch 11 rolling-bearing tables with query + highlight.
"""

import os
import streamlit as st
import pandas as pd
import sys

# ── make sure shared/ is importable ──────────────────────────────────────────
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from shared.table import Table
from shared.interpolable_table import InterpolableTable
from shared.repository import TableRepository

DATA_DIR = os.path.join(ROOT, "data", "ch11")

# ── load tables once (cached) ─────────────────────────────────────────────────

@st.cache_resource
def load_repo():
    return TableRepository(DATA_DIR)

# ── styling ───────────────────────────────────────────────────────────────────

HIGHLIGHT_BRACKET = "#2a3f2a"   # dark green — bracketing rows
HIGHLIGHT_EXACT   = "#1e3a2f"   # slightly deeper — exact match
INTERP_ROW_COLOR  = "#2a2a4a"   # blue-tinted — interpolated row

# ── helpers ───────────────────────────────────────────────────────────────────

def _flat_rows(table: Table) -> list[dict]:
    """
    Flatten rows for display. Handles the nested 02/03 series in Table 11-3.
    Returns a list of plain dicts with string keys.
    """
    flat = []
    for row in table.rows:
        flat_row = {}
        for k, v in row.items():
            if isinstance(v, dict):
                # nested series — flatten with prefix, e.g. "02 — C10 (kN)"
                for sub_k, sub_v in v.items():
                    flat_row[f"{k} — {sub_k}"] = sub_v
            else:
                flat_row[k] = v
        flat.append(flat_row)
    return flat


def _build_df(table: Table) -> pd.DataFrame:
    return pd.DataFrame(_flat_rows(table))


def _highlight_rows(df: pd.DataFrame, indices: list[int], color: str):
    """Return a Styler with the given row indices highlighted."""
    def style_fn(row):
        return [f"background-color: {color}; color: #e8f4e8;" if row.name in indices else "" for _ in row]
    return df.style.apply(style_fn, axis=1)


def _format_value(v) -> str:
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)

# ── sub-renderers ─────────────────────────────────────────────────────────────

def _render_table(table: Table):
    key_col   = table.key_column
    print(table.valid_range)
    vmin, vmax = table.valid_range

    df = _build_df(table)

    # ── full table display
    st.markdown(f"**{table.name}**")
    if table.notes:
        st.markdown(
            f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.75rem;'
            f'color:#f4a432;background:#1e1a0e;border-left:3px solid #f4a432;'
            f'padding:0.4rem 0.8rem;margin-bottom:0.8rem">'
            f'⚠ {table.notes}</div>',
            unsafe_allow_html=True
        )

    st.dataframe(
        df.style.set_properties(**{
            "background-color": "#0d1117",
            "color": "#cdd6f4",
            "border-color": "#2d3748",
            "font-family": "IBM Plex Mono, monospace",
            "font-size": "0.82rem",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # ── query
    st.markdown("---")
    st.markdown("#### 🔍 Query")

    c1, c2 = st.columns([1, 3])
    with c1:
        query_val = st.number_input(
            f"{key_col}",
            min_value=float(vmin),
            max_value=float(vmax),
            value=float(vmin),
            step=(float(vmax) - float(vmin)) / 100,
            format="%.4g",
            key=f"query_{table.id}",
        )
    with c2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        lookup = st.button("Look up", key=f"lookup_{table.id}", use_container_width=False)

    if lookup:
        _show_result(table, df, key_col, query_val)


def _show_result(table: Table, df: pd.DataFrame, key_col: str, query_val: float):
    keys = [table._extract_key(row, key_col) for row in table.rows]
    is_interpolable = isinstance(table, InterpolableTable)

    # ── exact match
    if query_val in keys:
        idx = keys.index(query_val)
        styled = _highlight_rows(df, [idx], HIGHLIGHT_EXACT)
        st.markdown(f"**Exact match** at {key_col} = {query_val}")
        st.dataframe(styled, use_container_width=True, hide_index=True)
        return

    # ── out of range
    if query_val < keys[0]:
        st.warning(f"{query_val} is below the table minimum ({keys[0]}). Showing first row.")
        styled = _highlight_rows(df, [0], HIGHLIGHT_EXACT)
        st.dataframe(styled, use_container_width=True, hide_index=True)
        return
    if query_val > keys[-1]:
        st.warning(f"{query_val} is above the table maximum ({keys[-1]}). Showing last row.")
        styled = _highlight_rows(df, [len(keys)-1], HIGHLIGHT_EXACT)
        st.dataframe(styled, use_container_width=True, hide_index=True)
        return

    # ── find bracketing indices
    lower_idx, upper_idx = None, None
    for i in range(len(keys) - 1):
        if keys[i] < query_val < keys[i+1]:
            lower_idx, upper_idx = i, i+1
            break

    # highlight both bracketing rows
    styled = _highlight_rows(df, [lower_idx, upper_idx], HIGHLIGHT_BRACKET)
    st.markdown(
        f"**{key_col} = {query_val}** falls between "
        f"**{keys[lower_idx]}** (row {lower_idx+1}) and "
        f"**{keys[upper_idx]}** (row {upper_idx+1})"
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # ── interpolated row (InterpolableTable only)
    if is_interpolable:
        interp_row = table.interpolate_row(key_col, query_val)
        interp_flat = {}
        for k, v in interp_row.items():
            interp_flat[k] = _format_value(v)

        interp_df = pd.DataFrame([interp_flat])
        st.markdown(
            f'<div style="font-family:IBM Plex Mono,monospace;font-size:0.75rem;'
            f'color:#bb86fc;margin-top:0.8rem;margin-bottom:0.3rem">'
            f'↳ Interpolated row at {key_col} = {query_val}</div>',
            unsafe_allow_html=True
        )
        st.dataframe(
            interp_df.style.set_properties(**{
                "background-color": INTERP_ROW_COLOR,
                "color": "#cdd6f4",
                "font-family": "IBM Plex Mono, monospace",
                "font-size": "0.82rem",
                "font-weight": "600",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("This table uses nearest-row lookup — no interpolation applied.")

# ── public entry point ────────────────────────────────────────────────────────

def render():
    repo = load_repo()
    tables = repo.by_chapter(11)

    options = {f"Table {t.id} — {t.name}": t.id for t in tables}
    selected_label = st.selectbox("Select table", list(options.keys()), key="ch11_table_select")
    selected_id    = options[selected_label]
    table          = repo.get(selected_id)

    st.markdown("---")
    _render_table(table)