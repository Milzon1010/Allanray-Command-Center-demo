from pathlib import Path
import streamlit as st


def inject_theme():
    css = Path("ui/assets/theme.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Sidebar toggle (FIX)
# ─────────────────────────────────────────────
def sidebar_toggle():
    st.markdown(
        """
        <style>
        .sidebar-toggle {
            position: fixed;
            top: 78px;
            left: 10px;
            z-index: 9999;
        }
        .sidebar-toggle button {
            background: linear-gradient(135deg,#ff4444,#bb6fff);
            border:none;
            color:white;
            padding:6px 10px;
            border-radius:10px;
            font-weight:700;
            cursor:pointer;
            box-shadow:0 4px 12px rgba(0,0,0,0.4);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if "sb" not in st.session_state:
        st.session_state.sb = True

    st.markdown('<div class="sidebar-toggle">', unsafe_allow_html=True)
    if st.button("☰"):
        st.session_state.sb = not st.session_state.sb
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.sb:
        st.set_page_config(layout="wide", initial_sidebar_state="expanded")
    else:
        st.set_page_config(layout="wide", initial_sidebar_state="collapsed")


# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
def header(brand: str):
    st.markdown(
        f"""
        <div class="titlebar">
          <div class="title-row">
            <div>
              <div class="h1">{brand} — Production Fleet &amp; Gear Command Center</div>
              <div class="small">
                Executive overview • Truck GPS • Fuel • Rental • Alerts
              </div>
            </div>
            <div class="badges">
              <span class="badge"><span class="dot"></span>LIVE</span>
              <span class="badge">CINEMATIC</span>
              <span class="badge">DEMO</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def panel_open():
    st.markdown('<div class="panel">', unsafe_allow_html=True)


def panel_close():
    st.markdown("</div>", unsafe_allow_html=True)


def alert_card(severity: str, message: str, ts: str):
    sev = severity.upper()
    if sev == "DANGER":
        row = "alert-row"
        icon = "🔴"
    elif sev in ("WARN", "WARNING"):
        row = "alert-row warn"
        icon = "🟡"
    else:
        row = "alert-row info"
        icon = "🔵"

    st.markdown(
        f"""
        <div class="{row}">
          <div class="alert-severity">{icon} {severity}</div>
          <div class="alert-msg">{message}</div>
          <div class="alert-ts">{ts}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
