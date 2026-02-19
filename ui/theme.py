from pathlib import Path
import streamlit as st


def inject_theme():
    css = Path("ui/assets/theme.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


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