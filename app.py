import streamlit as st

st.set_page_config(
    page_title="Allanray Command Center",
    layout="wide",
    initial_sidebar_state="expanded",  # 👈 paksa terbuka
)

import plotly.graph_objects as go
# app.py — Allanray Teknologi Semesta • Cinema Production Command Center
# v5: Lighter palette · Balanced 3+4 grid · Export PDF/Excel · Mobile responsive

import base64
from pathlib import Path
import streamlit as st

# Streamlit width compat (use_container_width -> width)
def _plotly(fig):
    """Plotly chart width compatibility across Streamlit versions."""
    try:
        # Newer Streamlit: width can be 'stretch'/'content'
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        # Older Streamlit: use_container_width=True
        st.plotly_chart(fig, use_container_width=True)


try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None

from config import BRAND, PROJECTS, EQUIP_CATEGORIES, PEOPLE_ROLES, WAREHOUSE, SITES
from ui.theme import inject_theme, header, panel_open, panel_close, alert_card
from data.mock_data import (
    seed_everything, make_people, make_trucks, make_inventory,
    make_fuel_tanks, make_transactions, make_alerts,
)
from components.sections import (
    radial_gauge, reset_gauge_counter,
    rental_duration_panel,
    fuel_forecast_chart,
    colored_inventory_table,
    colored_audit_table,
    colored_tank_table,
    export_excel_button,
    export_pdf_button,
)
from components.maps import render_street_map, render_pydeck_map


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────
def _b64(path: Path) -> str | None:
    return base64.b64encode(path.read_bytes()).decode() if path.exists() else None


def _sb_section(label: str):
    st.sidebar.markdown(f'<div class="sb-section-label">{label}</div>', unsafe_allow_html=True)


def _sidebar_brand(logo_b64):
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" alt="logo" />' if logo_b64
        else '<span style="font-family:Rajdhani,sans-serif;font-weight:700;color:#fff;font-size:14px;">ATS</span>'
    )
    st.sidebar.markdown(
        f'<div class="sb-brand"><div class="sb-logo">{logo_html}</div>'
        f'<div><div class="name">Allanray<br>Teknologi Semesta</div>'
        f'<div class="tag">Cinema Production • Fleet &amp; Gear</div></div></div>',
        unsafe_allow_html=True,
    )


def _inject_density():
    """Extra density layer on top of theme.css — keeps layout above fold."""
    st.markdown("""
    <style>
    /* ── mobile viewport lock (added via meta tag simulation) ── */
    @media (max-width: 768px) {
      html { touch-action: manipulation; }
      .stApp { overflow-x: hidden !important; }
    }

    /* ── Shared tightening ── */
    .block-container {
      padding-top: 0.32rem !important; padding-bottom: 0.15rem !important;
      padding-left: 0.85rem !important; padding-right: 0.85rem !important;
      max-width: 100% !important;
    }
    div[data-testid="stVerticalBlock"]   { gap: 0.30rem !important; }
    div[data-testid="stHorizontalBlock"] { gap: 0.36rem !important; }
    div[data-testid="column"] > div      { gap: 0.30rem !important; }

    .stPlotlyChart, .js-plotly-plot { margin: 0 !important; padding: 0 !important; }
    .stMarkdown { margin-bottom: 0 !important; }

    /* ── Subheader sizing ── */
    .stSubheader,
    [data-testid="stHeadingWithActionElements"] h3, h3 {
      font-size: clamp(12.5px, 1.02vw, 16.5px) !important;
    }

    /* ── Caption ── */
    .stCaptionContainer p, .stCaption, .stMarkdown p, p {
      font-size: clamp(9.5px, 0.72vw, 11.5px) !important;
      margin: 0 0 3px 0 !important;
    }

    /* ── Button compact ── */
    div.stButton > button {
      padding: 7px 12px !important;
      font-size: clamp(11px, 0.85vw, 13.5px) !important;
      border-radius: 11px !important;
    }

    /* ── Tab compact ── */
    button[role="tab"] { padding: 5px 12px !important; font-size: clamp(10.5px, 0.78vw, 12.5px) !important; }

    /* ── Download button match style ── */
    div[data-testid="stDownloadButton"] > button {
      font-family: 'Rajdhani', sans-serif !important;
      font-weight: 700 !important; font-size: 12px !important;
      letter-spacing: 0.10em !important; text-transform: uppercase !important;
      border-radius: 11px !important; padding: 7px 12px !important;
      background: linear-gradient(135deg, rgba(45,236,160,0.20), rgba(0,212,200,0.15)) !important;
      color: #2deca0 !important; border: 1px solid rgba(45,236,160,0.35) !important;
      box-shadow: 0 4px 14px rgba(45,236,160,0.22) !important;
      transition: transform 140ms ease !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
      transform: translateY(-2px) !important;
      box-shadow: 0 8px 22px rgba(45,236,160,0.35) !important;
    }

    /* ── Sidebar compact ── */
    div[data-testid="stSidebarContent"] { padding-top: 0.30rem !important; }
    .sb-brand    { padding: 10px !important; margin-bottom: 8px !important; }
    .sb-logo     { width: 38px !important; height: 38px !important; }
    .sb-brand .name { font-size: 11px !important; }
    .sb-brand .tag  { font-size: 9px   !important; }
    .sb-section-label { font-size: 8.5px !important; margin: 9px 0 3px 0 !important; }
    section[data-testid="stSidebar"] label { font-size: 10.5px !important; }
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div { min-height: 30px !important; }
    section[data-testid="stSidebar"] input { min-height: 30px !important; }

    /* ── Alert compact ── */
    .alert-row      { padding: 6px 12px 6px 16px !important; margin-bottom: 5px !important; }
    .alert-severity { font-size: 8.5px !important; }
    .alert-msg      { font-size: clamp(10.5px, 0.78vw, 12.5px) !important; }
    .alert-ts       { font-size: 9px !important; }

    /* ── iframe ── */
    iframe { border-radius: 12px !important; }

    /* ── Watermark ── */
    .watermark { padding: 6px 13px !important; font-size: 9.5px !important; }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Detail Panels (Map / Inventory / Company Info)
# ─────────────────────────────────────────────────────────────
def _render_company_info():
    st.markdown("### Company / Contract Info")
    st.markdown(
        (
            "**Allanray Teknologi Semesta (ATS)**  \n"
            "Cinema Production - Fleet & Gear Command Center\n\n"
            "**Alamat**: (isi alamat kamu di sini)\n"
            "**Kontak**: (PIC / WA / Telp)\n"
            "**Email**: (email)\n"
            "**Website**: (website)\n\n"
            "**Catatan Kontrak (template)**\n"
            "- SLA pengembalian gear: H-0 sebelum wrap / sesuai jadwal call sheet\n"
            "- Denda overdue: per hari / per jam (isi)\n"
            "- Audit log: checkout/return wajib tercatat\n"
            "- Kondisi barang saat serah-terima: foto + checklist"
        )
    )


def _render_map_detail(trucks_df, site_obj, map_engine_choice):
    st.caption("Tampilan map ukuran besar + tabel detail armada.")
    cols = ["truck_id", "status", "driver_name", "lat", "lon", "speed_kmh", "fuel_liters"]
    if map_engine_choice.startswith("Street"):
        render_street_map(trucks_df[cols], site_obj, height=520, zoom_start=12)
    else:
        render_pydeck_map(trucks_df[cols], site_obj)

    st.markdown("#### Fleet Table")
    st.dataframe(
        trucks_df[["truck_id", "status", "driver_name", "speed_kmh", "fuel_liters", "lat", "lon"]]
        .sort_values(["status", "truck_id"]),
        use_container_width=True,
        height=260,
    )


def _render_inventory_detail(inv_df, tanks_df, tx_df, alerts_df):
    st.caption("Tabel full inventory + fuel tanks + audit log + alerts.")
    st.markdown("#### Inventory")
    st.dataframe(inv_df, use_container_width=True, height=320)
    st.markdown("#### Fuel Tanks")
    st.dataframe(tanks_df, use_container_width=True, height=220)
    st.markdown("#### Audit Log")
    st.dataframe(tx_df, use_container_width=True, height=280)
    st.markdown("#### Alerts")
    st.dataframe(alerts_df, use_container_width=True, height=220)


# ─────────────────────────────────────────────────────────────
# Page config — MUST be first
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Allanray Command Center",
    layout="wide",
    initial_sidebar_state="expanded",
)


inject_theme()
_inject_density()
header(BRAND)
_sidebar_brand(_b64(Path("ui/assets/logo.png")))

# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────
# --- APP TITLE (VISIBLE IN CANVAS) ---
st.markdown("""
<div class="app-title-bar">
    <div class="app-title-main">
        ALLANRAY COMMAND CENTER
    </div>
    <div class="app-title-sub">
        Cinema Production • Fleet • Gear • Operations
    </div>
</div>
""", unsafe_allow_html=True)

_sb_section("Simulation")
seed     = st.sidebar.number_input("Random seed", min_value=1, max_value=9999, value=42)
n_trucks = st.sidebar.slider("Jumlah Truck", 10, 15, 12)

_sb_section("Filtering")
active_project = st.sidebar.selectbox("Filter Project", ["ALL"] + PROJECTS, index=0)
view_site      = st.sidebar.selectbox("Target Set / Site", [s["name"] for s in SITES], index=0)

_sb_section("Live Mode")
auto_refresh = st.sidebar.toggle("Auto-refresh (live)", value=True)

_sb_section("Map")
map_engine = st.sidebar.selectbox("Map Engine", ["Street Map (Recommended)", "Deck (Fallback)"])

_sb_section("Detail")
detail_choice = st.sidebar.radio(
    "Open Detail Panel",
    ["None", "Map Detail", "Inventory Detail", "Company Info"],
    index=0,
    key="detail_choice",
)
pin_below = st.sidebar.toggle("Pin detail below (open)", value=False, key="detail_pin")




# Heights — tuned for 1366×768 laptop, scale up on larger screens
MAP_H      = 258
GAUGE_H    = 155
TABLE_H    = 152
FORECAST_H = 162
RENT_N     = 5    # rows in rental tracker
ALERT_N    = 5

if auto_refresh and st_autorefresh:
    st_autorefresh(interval=4_000, key="refresh")

seed_everything(int(seed))

# ─────────────────────────────────────────────────────────────
# Data
# ─────────────────────────────────────────────────────────────
people = make_people(35, roles=PEOPLE_ROLES)
trucks = make_trucks(n_trucks=int(n_trucks), warehouse=WAREHOUSE, people=people)
pmap   = dict(zip(people["person_id"], people["name"]))
trucks["driver_name"] = trucks["driver_id"].map(lambda x: pmap.get(x, x))

inventory = make_inventory(EQUIP_CATEGORIES, PROJECTS)
tanks     = make_fuel_tanks()
tx        = make_transactions(inventory, people, n=160, projects=PROJECTS)
alerts    = make_alerts(trucks, inventory, tanks)

if active_project != "ALL":
    inventory_view = inventory[
        (inventory["project"] == active_project) | (inventory["project"] == "-")].copy()
    tx_view = tx[tx["project"] == active_project].copy()
else:
    inventory_view = inventory.copy()
    tx_view        = tx.copy()

site = next(s for s in SITES if s["name"] == view_site)

# KPIs
kpi_prods   = len([p for p in PROJECTS if (inventory["project"] == p).any()])
kpi_trucks  = int((trucks["status"].isin(["MOVING", "ON-SITE"])).sum())
kpi_fuel    = int(tanks["level_l"].sum())
kpi_onrent  = int((inventory["status"] == "ON-RENT").sum())
kpi_avail   = int((inventory["status"] == "AVAILABLE").sum())
kpi_maint   = int((inventory["status"] == "MAINTENANCE").sum())
kpi_lost    = int((inventory["status"] == "LOST").sum())

# ═══════════════════════════════════════════════════════════
# TOP ROW — 3 columns: KPIs | Map | Alerts
# ═══════════════════════════════════════════════════════════
reset_gauge_counter()
c1, c2, c3 = st.columns([1.05, 1.65, 1.0], gap="medium")

with c1:
    panel_open()
    st.markdown('<div class="kpi-flex">', unsafe_allow_html=True)

    st.subheader("Executive Summary")
    st.caption("Real-time KPI operasional.")

    g1, g2, g3 = st.columns(3)
    with g1: radial_gauge("Trucks",   kpi_trucks, 0, 15, "", height=GAUGE_H)
    with g2: radial_gauge("Fuel",     kpi_fuel,   0, 3000, " L", height=GAUGE_H)
    with g3: radial_gauge("Projects", kpi_prods,  0, len(PROJECTS), "", height=GAUGE_H)

    g4, g5, g6 = st.columns(3)
    with g4: radial_gauge("On Rent",   kpi_onrent, 0, 300, "", height=GAUGE_H)
    with g5: radial_gauge("Available", kpi_avail,  0, 500, "", height=GAUGE_H)
    with g6: radial_gauge("Maint.",    kpi_maint,  0, 120, "", height=GAUGE_H)

    st.markdown('<div class="kpi-spacer"></div>', unsafe_allow_html=True)

    b1, b2 = st.columns(2)
    with b1: st.button("🗺️ Map Detail", use_container_width=True)
    with b2: st.button("📦 Inventory Detail", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)
    panel_close()


# ─────────────────────────────────────────────────────────────
# Detail Panels (expander / sidebar-driven) — no dialogs
# ─────────────────────────────────────────────────────────────
if st.session_state.get("detail_choice", "None") != "None":
    expanded = bool(st.session_state.get("detail_pin", False))
    title = st.session_state["detail_choice"]
    with st.expander(f"DETAIL — {title}", expanded=expanded):
        if title == "Map Detail":
            _render_map_detail(trucks, site, map_engine)
        elif title == "Inventory Detail":
            _render_inventory_detail(inventory_view, tanks, tx_view, alerts)
        elif title == "Company Info":
            _render_company_info()


with c2:
    panel_open()
    st.subheader("Live Fleet Map")
    st.caption("Jakarta · CartoDB Dark Matter · Zoom untuk street detail.")
    tc = ["truck_id","status","driver_name","lat","lon","speed_kmh","fuel_liters"]
    if map_engine.startswith("Street"):
        render_street_map(trucks[tc], site, height=MAP_H, zoom_start=12)
    else:
        render_pydeck_map(trucks[tc], site)
    panel_close()

    panel_open()
    st.subheader("Operations")
    st.caption("Inventory &amp; Audit Log — warna per status.")
    tab_inv, tab_aud = st.tabs(["📦 Inventory", "🧾 Audit Log"])
    with tab_inv:
        colored_inventory_table(inventory_view, max_rows=7, height_px=TABLE_H)
    with tab_aud:
        colored_audit_table(tx_view, max_rows=7, height_px=TABLE_H)
    panel_close()

with c3:
    panel_open()
    st.subheader("Alerts Feed")
    st.caption("Overdue · Fuel Low · Geofence · Lost")
    if alerts.empty:
        st.info("No alerts (demo).")
    else:
        for _, r in alerts.head(ALERT_N).iterrows():
            alert_card(r["severity"], r["message"], r["time"].strftime("%m-%d %H:%M"))
    panel_close()

    panel_open()
    st.subheader("Export Report")
    st.caption("Download data ke Excel atau cetak PDF.")
    export_excel_button(inventory_view, tanks, tx_view, alerts)
    export_pdf_button()
    panel_close()

# ═══════════════════════════════════════════════════════════
# BOTTOM ROW — 4 equal columns
# ═══════════════════════════════════════════════════════════
b1, b2, b3, b4 = st.columns([1, 1, 1, 1], gap="medium")

with b1:
    panel_open()
    st.subheader("Rental Duration")
    st.caption("Masa sewa aktif · Progress urgency.")
    rental_duration_panel(inventory_view, n=RENT_N)
    panel_close()

with b2:
    panel_open()
    st.subheader("Fuel Tanks")
    st.caption("Level · Kapasitas · Burn-rate · Reorder")
    colored_tank_table(tanks, height_px=TABLE_H)
    panel_close()

with b3:
    panel_open()
    st.subheader("Fuel Forecast")
    st.caption("Proyeksi 7 hari · ⚠ garis reorder")
    fuel_forecast_chart(tanks, height=FORECAST_H)
    panel_close()

with b4:
    panel_open()
    st.subheader("Fleet Status")
    st.caption("Distribusi status armada saat ini.")
    # Truck status donut
    status_counts = trucks["status"].value_counts()
    status_colors = {
        "MOVING":  "#18e8ff", "ON-SITE": "#2deca0",
        "IDLE":    "#bb6fff", "PARKED":  "#ffc107",
    }
    fig_donut = go.Figure(go.Pie(
        labels=status_counts.index.tolist(),
        values=status_counts.values.tolist(),
        hole=0.60,
        marker=dict(
            colors=[status_colors.get(s, "#5599ff") for s in status_counts.index],
            line=dict(color="rgba(14,24,48,0.90)", width=2),
        ),
        textfont=dict(family="JetBrains Mono", size=10, color="#eef3ff"),
        hovertemplate="<b>%{label}</b><br>%{value} trucks (%{percent})<extra></extra>",
    ))
    fig_donut.update_layout(
        height=FORECAST_H + 10,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=4, r=4, t=4, b=4),
        showlegend=True,
        legend=dict(
            font=dict(color="rgba(210,225,255,0.72)", size=9, family="JetBrains Mono"),
            bgcolor="rgba(0,0,0,0)", orientation="v", x=1.0, y=0.5,
        ),
        annotations=[dict(
            text=f"<b>{int(status_counts.sum())}</b><br><span style='font-size:9px'>Trucks</span>",
            x=0.5, y=0.5, showarrow=False, font=dict(size=18, family="Rajdhani", color="#eef3ff"),
        )],
    )
    _plotly(fig_donut)
    panel_close()

