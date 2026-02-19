import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import io

# ─────────────────────────────────────────────────────────────
# Palette — brighter, readable on projectors
# ─────────────────────────────────────────────────────────────
_GAUGE_COLORS = ["#ff4444", "#18e8ff", "#bb6fff", "#2deca0", "#ffc107", "#5599ff"]
_gauge_counter = [0]

def _next_color() -> str:
    c = _GAUGE_COLORS[_gauge_counter[0] % len(_GAUGE_COLORS)]
    _gauge_counter[0] += 1
    return c

def reset_gauge_counter():
    _gauge_counter[0] = 0

# ─────────────────────────────────────────────────────────────
# RADIAL GAUGE
# ─────────────────────────────────────────────────────────────
def radial_gauge(title, value, vmin, vmax, suffix="", height=158, color=None):
    if color is None:
        color = _next_color()
    v = max(vmin, min(value, vmax))

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=v,
        number={"suffix": suffix, "font": {"size": 34, "family": "Rajdhani", "color": color}},
        title={"text": f"<span style='font-family:Rajdhani,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.10em;text-transform:uppercase;color:rgba(210,225,255,0.85)'>{title}</span>"},
        gauge={
            "axis": {"range": [vmin, vmax], "tickwidth": 0,
                     "tickcolor": "rgba(0,0,0,0)",
                     "tickfont": {"color": "rgba(0,0,0,0)", "size": 1}},
            "bar": {"thickness": 0.28, "color": color, "line": {"width": 0}},
            "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
            "steps": [{"range": [vmin, vmax], "color": "rgba(255,255,255,0.05)"}],
            "threshold": {"line": {"color": color, "width": 2}, "thickness": 0.82, "value": v},
        },
    ))
    fig.update_layout(
        margin=dict(l=4, r=4, t=48, b=4), height=height,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color=color,
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# RENTAL DURATION TRACKER
# ─────────────────────────────────────────────────────────────
def rental_duration_panel(inventory: pd.DataFrame, n: int = 6):
    rented = inventory[inventory["status"] == "ON-RENT"].copy()
    if rented.empty:
        st.caption("Tidak ada aset yang sedang disewa.")
        return

    now = datetime.now()
    rows_html = ""

    for _, row in rented.head(n).iterrows():
        rng = random.Random(abs(hash(str(row["asset_id"]))) % 9999)
        dur   = rng.randint(5, 30)
        elaps = rng.randint(1, dur)
        pct   = elaps / dur
        left  = dur - elaps
        pct_s = f"{pct*100:.0f}"

        s_dt = (now - timedelta(days=elaps)).strftime("%d/%m")
        e_dt = (now + timedelta(days=left)).strftime("%d/%m")

        if pct >= 0.85:
            bc, gc, lbl, lbl_c = "#ff4444", "rgba(255,68,68,0.45)", "OVERDUE", "#ff6666"
        elif pct >= 0.60:
            bc, gc, lbl, lbl_c = "#ffc107", "rgba(255,193,7,0.40)", "SOON", "#ffd740"
        else:
            bc, gc, lbl, lbl_c = "#2deca0", "rgba(45,236,160,0.38)", "OK", "#50ffb8"

        a_id = str(row["asset_id"])
        cat  = str(row.get("category", "-") or "-")
        proj = str(row.get("project",  "-") or "-")

        rows_html += (
            f'<div style="margin-bottom:10px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">'
            f'<div style="display:flex;gap:7px;align-items:center;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:11px;color:#18e8ff;font-weight:700;">{a_id}</span>'
            f'<span style="font-size:9.5px;color:rgba(200,220,255,0.55);">{cat} &middot; {proj}</span>'
            f'</div>'
            f'<div style="display:flex;gap:8px;align-items:center;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:9px;color:rgba(180,200,240,0.48);">{s_dt}&rarr;{e_dt}</span>'
            f'<span style="font-family:Rajdhani,sans-serif;font-size:11.5px;font-weight:700;color:{lbl_c};">{left}d &bull; {lbl}</span>'
            f'</div></div>'
            f'<div style="height:5px;border-radius:99px;background:rgba(255,255,255,0.08);overflow:hidden;">'
            f'<div style="height:100%;width:{pct_s}%;border-radius:99px;background:{bc};box-shadow:0 0 8px {gc};"></div>'
            f'</div></div>'
        )

    html = (
        '<div style="background:transparent;font-family:DM Sans,sans-serif;padding:2px 0;">'
        + rows_html + '</div>'
    )
    components.html(html, height=n * 54 + 10, scrolling=False)


# ─────────────────────────────────────────────────────────────
# FUEL FORECAST CHART
# ─────────────────────────────────────────────────────────────
def fuel_forecast_chart(tanks: pd.DataFrame, height: int = 170):
    now  = datetime.now()
    days = [now + timedelta(days=i - 3) for i in range(11)]

    # Valid rgba fill colors for Plotly
    fills = [
        "rgba(255,68,68,0.14)", "rgba(24,232,255,0.14)",
        "rgba(187,111,255,0.14)", "rgba(255,193,7,0.14)", "rgba(45,236,160,0.14)",
    ]
    lines = ["#ff6666", "#40eeff", "#cc88ff", "#ffd740", "#50ffb8"]

    fig = go.Figure()
    x_labels = [d.strftime("%d/%m") for d in days]

    for idx, (_, tank) in enumerate(tanks.iterrows()):
        burn  = float(tank.get("burn_l_per_day", 40))
        lvl   = float(tank.get("level_l", 500))
        cap   = float(tank.get("capacity_l", 1800))
        reord = float(tank.get("reorder_point_l", 200))
        name  = str(tank.get("tank_name", f"Tank {idx}"))

        levels = [max(0, min(cap, lvl - burn * (d - now).total_seconds() / 86400)) for d in days]

        fig.add_trace(go.Scatter(
            x=x_labels, y=levels, name=name, mode="lines",
            line=dict(color=lines[idx % len(lines)], width=2, shape="spline"),
            fill="tozeroy", fillcolor=fills[idx % len(fills)],
            hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y:.0f}} L<extra></extra>",
        ))

        if idx == 0:
            fig.add_hline(y=reord, line_dash="dot",
                          line_color="rgba(255,193,7,0.55)", line_width=1,
                          annotation_text="⚠ Reorder",
                          annotation_font_color="rgba(255,193,7,0.85)", annotation_font_size=9)

    today = now.strftime("%d/%m")
    fig.add_vline(x=today, line_dash="dash", line_color="rgba(255,255,255,0.22)", line_width=1)
    fig.add_annotation(x=today, y=1, yref="paper", text="TODAY", showarrow=False,
                       font=dict(color="rgba(210,225,255,0.45)", size=8, family="JetBrains Mono"),
                       yanchor="top", xanchor="left", xshift=4)

    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=2, r=6, t=8, b=2),
        legend=dict(font=dict(color="rgba(210,225,255,0.70)", size=9, family="JetBrains Mono"),
                    bgcolor="rgba(0,0,0,0)", x=0, y=1.08, orientation="h"),
        xaxis=dict(showgrid=False, tickfont=dict(color="rgba(180,200,240,0.50)", size=8),
                   linecolor="rgba(255,255,255,0.08)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)",
                   tickfont=dict(color="rgba(180,200,240,0.50)", size=8),
                   title=dict(text="L", font=dict(color="rgba(160,185,230,0.40)", size=8))),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="rgba(14,24,48,0.95)", font=dict(color="#eef3ff", size=10),
                        bordercolor="rgba(255,255,255,0.14)"),
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────
# TABLE SHARED STYLES
# ─────────────────────────────────────────────────────────────
_TH = (
    "padding:6px 10px;text-align:left;"
    "font-family:Rajdhani,sans-serif;font-size:11px;font-weight:700;"
    "letter-spacing:0.12em;text-transform:uppercase;"
    "color:rgba(180,205,255,0.70);"
    "border-bottom:1px solid rgba(255,255,255,0.10);"
    "white-space:nowrap;"
)
_TD = "padding:5px 10px;border-bottom:1px solid rgba(255,255,255,0.05);"

_STATUS_MAP = {
    "AVAILABLE":   ("#2deca0", "rgba(45,236,160,0.14)"),
    "ON-RENT":     ("#18e8ff", "rgba(24,232,255,0.14)"),
    "MAINTENANCE": ("#ffc107", "rgba(255,193,7,0.14)"),
    "LOST":        ("#ff4444", "rgba(255,68,68,0.16)"),
    "MOVING":      ("#18e8ff", "rgba(24,232,255,0.14)"),
    "ON-SITE":     ("#2deca0", "rgba(45,236,160,0.14)"),
    "IDLE":        ("#bb6fff", "rgba(187,111,255,0.14)"),
}


def _badge(val: str) -> str:
    c, bg = _STATUS_MAP.get(val.upper(), ("#aabbdd", "rgba(170,187,221,0.12)"))
    return (
        f'<span style="display:inline-flex;align-items:center;gap:4px;padding:2px 9px;'
        f'border-radius:100px;background:{bg};border:1px solid {c}55;'
        f'font-family:JetBrains Mono,monospace;font-size:9.5px;font-weight:700;'
        f'letter-spacing:0.06em;color:{c};">'
        f'<span style="width:5px;height:5px;border-radius:50%;'
        f'background:{c};box-shadow:0 0 5px {c};"></span>{val}</span>'
    )


def _wrap_table(header_html: str, body_html: str, height_px: int) -> str:
    return (
        f'<div style="overflow-x:auto;border-radius:13px;'
        f'border:1px solid rgba(255,255,255,0.12);'
        f'background:rgba(14,22,44,0.85);max-height:{height_px}px;overflow-y:auto;">'
        f'<table style="width:100%;border-collapse:collapse;min-width:420px;">'
        f'<thead><tr style="position:sticky;top:0;background:rgba(12,20,42,0.98);z-index:1;">'
        f'{header_html}</tr></thead>'
        f'<tbody>{body_html}</tbody>'
        f'</table></div>'
    )


# ─────────────────────────────────────────────────────────────
# COLORED INVENTORY TABLE
# ─────────────────────────────────────────────────────────────
def colored_inventory_table(df: pd.DataFrame, max_rows: int = 8, height_px: int = 210):
    show_cols = [c for c in ["asset_id", "category", "status", "project", "location"] if c in df.columns]
    view = df[show_cols].head(max_rows)

    ths = "".join(f'<th style="{_TH}">{c.replace("_"," ").upper()}</th>' for c in show_cols)
    rows = ""
    for i, (_, row) in enumerate(view.iterrows()):
        bg = "rgba(255,255,255,0.03)" if i % 2 == 0 else "rgba(0,0,0,0)"
        tds = ""
        for c in show_cols:
            val = str(row.get(c) or "—")
            if c == "status":
                cell = _badge(val)
            elif c == "asset_id":
                cell = f'<span style="font-family:JetBrains Mono,monospace;font-size:10px;color:#18e8ff;font-weight:700;">{val}</span>'
            elif c == "project" and val not in ("-", "—", ""):
                cell = f'<span style="font-family:JetBrains Mono,monospace;font-size:9.5px;color:#bb6fff;font-weight:600;">{val}</span>'
            else:
                cell = f'<span style="font-size:10.5px;color:rgba(210,225,255,0.78);">{val}</span>'
            tds += f'<td style="{_TD}">{cell}</td>'
        rows += f'<tr style="background:{bg};">{tds}</tr>'

    components.html(_wrap_table(ths, rows, height_px), height=height_px + 48, scrolling=False)


# ─────────────────────────────────────────────────────────────
# COLORED AUDIT TABLE
# ─────────────────────────────────────────────────────────────
_ACTION_C = {
    "RENT_OUT": "#18e8ff", "RETURN": "#2deca0", "INSPECT": "#ffc107",
    "LOST": "#ff4444", "MAINTENANCE": "#bb6fff", "TRANSFER": "#5599ff",
}

def colored_audit_table(df: pd.DataFrame, max_rows: int = 8, height_px: int = 210):
    show_cols = [c for c in ["tx_id", "asset_id", "action", "person_id", "project", "ts"] if c in df.columns]
    if not show_cols:
        show_cols = list(df.columns[:6])
    view = df[show_cols].head(max_rows)

    ths = "".join(f'<th style="{_TH}">{c.replace("_"," ").upper()}</th>' for c in show_cols)
    rows = ""
    for i, (_, row) in enumerate(view.iterrows()):
        bg = "rgba(255,255,255,0.03)" if i % 2 == 0 else "rgba(0,0,0,0)"
        tds = ""
        for c in show_cols:
            val = str(row.get(c) or "—")
            if c == "action":
                col = _ACTION_C.get(val.upper(), "#aabbdd")
                cell = f'<span style="font-family:JetBrains Mono,monospace;font-size:9.5px;font-weight:700;letter-spacing:0.06em;color:{col};">{val}</span>'
            elif c in ("tx_id", "asset_id"):
                cell = f'<span style="font-family:JetBrains Mono,monospace;font-size:9.5px;color:#18e8ff;">{val}</span>'
            elif c == "ts":
                cell = f'<span style="font-family:JetBrains Mono,monospace;font-size:9px;color:rgba(160,185,230,0.50);">{val}</span>'
            else:
                cell = f'<span style="font-size:10.5px;color:rgba(210,225,255,0.75);">{val}</span>'
            tds += f'<td style="{_TD}">{cell}</td>'
        rows += f'<tr style="background:{bg};">{tds}</tr>'

    components.html(_wrap_table(ths, rows, height_px), height=height_px + 48, scrolling=False)


# ─────────────────────────────────────────────────────────────
# COLORED TANK TABLE
# ─────────────────────────────────────────────────────────────
def colored_tank_table(tanks: pd.DataFrame, height_px: int = 165):
    view = tanks.copy()
    view["pct"] = (view["level_l"] / view["capacity_l"] * 100).round(1)

    ths = "".join(f'<th style="{_TH}">{h}</th>' for h in ["Tank", "Level (L)", "Kapasitas", "Burn/day", "Reorder"])
    rows = ""
    for i, (_, r) in enumerate(view.iterrows()):
        bg   = "rgba(255,255,255,0.03)" if i % 2 == 0 else "rgba(0,0,0,0)"
        pct  = float(r["pct"])
        lvl  = int(r.get("level_l", 0))
        burn = int(r.get("burn_l_per_day", 0))
        rord = int(r.get("reorder_point_l", 0))
        name = str(r.get("tank_name", "—"))

        bc   = "#ff4444" if pct < 30 else ("#ffc107" if pct < 60 else "#2deca0")
        tc   = "#ff6666" if pct < 30 else ("#ffd740" if pct < 60 else "#50ffb8")
        warn = " ⚠" if lvl < rord else ""

        bar = (
            f'<div style="display:flex;align-items:center;gap:7px;min-width:100px;">'
            f'<div style="flex:1;height:6px;border-radius:99px;background:rgba(255,255,255,0.09);overflow:hidden;">'
            f'<div style="height:100%;width:{pct:.0f}%;background:{bc};border-radius:99px;box-shadow:0 0 7px {bc}88;"></div>'
            f'</div>'
            f'<span style="font-family:Rajdhani,sans-serif;font-size:11px;font-weight:700;color:{tc};min-width:34px;">{pct:.0f}%</span>'
            f'</div>'
        )
        rows += (
            f'<tr style="background:{bg};">'
            f'<td style="{_TD}"><span style="font-size:11px;color:rgba(210,225,255,0.88);">{name}</span></td>'
            f'<td style="{_TD}"><span style="font-family:JetBrains Mono,monospace;font-size:10px;color:{tc};font-weight:700;">{lvl:,}</span></td>'
            f'<td style="{_TD}">{bar}</td>'
            f'<td style="{_TD}"><span style="font-family:JetBrains Mono,monospace;font-size:9.5px;color:rgba(180,200,240,0.60);">{burn} L/d</span></td>'
            f'<td style="{_TD}"><span style="font-family:JetBrains Mono,monospace;font-size:9.5px;color:rgba(255,193,7,0.80);">{rord:,} L{warn}</span></td>'
            f'</tr>'
        )

    components.html(_wrap_table(ths, rows, height_px), height=height_px + 48, scrolling=False)


# ─────────────────────────────────────────────────────────────
# EXPORT — PDF (browser print) & Excel
# ─────────────────────────────────────────────────────────────
def export_excel_button(inventory: pd.DataFrame, tanks: pd.DataFrame, tx: pd.DataFrame, alerts: pd.DataFrame):
    """Generate and offer Excel download with multiple sheets.

    Robustness:
    - Uses openpyxl if available (preferred for .xlsx)
    - Falls back to xlsxwriter if openpyxl is missing
    - Shows a clear UI message if neither engine is installed (and avoids crashing the app)
    """
    buf = io.BytesIO()

    engine = None
    try:
        import openpyxl  # noqa: F401
        engine = "openpyxl"
    except Exception:
        try:
            import xlsxwriter  # noqa: F401
            engine = "xlsxwriter"
        except Exception:
            engine = None

    if engine is None:
        st.error("Excel export butuh dependency tambahan: install `openpyxl` (recommended).")
        st.code("python -m pip install openpyxl", language="bash")
        st.caption("Alternatif: `python -m pip install xlsxwriter`")
        return

    try:
        with pd.ExcelWriter(buf, engine=engine) as writer:
            inventory.to_excel(writer, sheet_name="Inventory",  index=False)
            tanks.to_excel(writer,     sheet_name="Fuel Tanks", index=False)
            tx.to_excel(writer,        sheet_name="Audit Log",  index=False)
            if alerts is not None and (not getattr(alerts, "empty", True)):
                alerts.to_excel(writer, sheet_name="Alerts", index=False)
    except Exception as e:
        st.error(f"Gagal membuat file Excel via engine '{engine}': {e}")
        if engine == "xlsxwriter":
            st.caption("Untuk kompatibilitas maksimal, install `openpyxl` lalu coba lagi.")
        return

    buf.seek(0)
    now_str = datetime.now().strftime("%Y%m%d_%H%M")

    # Compatible download button (Streamlit lama/baru)
    try:
        st.download_button(
            "⬇️ Export Excel",
            data=buf,
            file_name=f"allanray_report_{now_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )
    except TypeError:
        st.download_button(
            "⬇️ Export Excel",
            data=buf,
            file_name=f"allanray_report_{now_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


def export_pdf_button(
):
    """Trigger browser print dialog for PDF export."""
    components.html("""
    <button onclick="window.print()" style="
      width:100%;padding:8px 12px;
      font-family:Rajdhani,sans-serif;font-size:13px;font-weight:700;
      letter-spacing:0.10em;text-transform:uppercase;
      border-radius:12px;border:1px solid rgba(187,111,255,0.35);
      background:linear-gradient(135deg,rgba(187,111,255,0.20),rgba(85,153,255,0.15));
      color:#bb6fff;cursor:pointer;
      box-shadow:0 4px 14px rgba(187,111,255,0.25);
    ">🖨️ EXPORT PDF</button>
    """, height=46)
