from pathlib import Path
import streamlit as st


def inject_theme():
    css = Path("ui/assets/theme.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Sidebar toggle — tombol ☰ / ✕ di pojok kiri atas
# Tidak pakai st.set_page_config (tidak boleh dipanggil 2x)
# Pakai CSS class inject untuk hide/show sidebar
# ─────────────────────────────────────────────
def sidebar_toggle():
    if "sb_open" not in st.session_state:
        st.session_state.sb_open = True

    # CSS untuk show/hide sidebar via body class
    st.markdown("""
    <style>
    /* Tombol toggle custom */
    #sb-toggle-btn {
        position: fixed;
        top: 12px;
        left: 12px;
        z-index: 99999;
        background: linear-gradient(135deg, #ff4444, #bb6fff);
        border: none;
        color: white;
        width: 34px;
        height: 34px;
        border-radius: 9px;
        font-size: 16px;
        font-weight: 700;
        cursor: pointer;
        box-shadow: 0 4px 14px rgba(0,0,0,0.45);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: opacity 0.2s;
    }
    #sb-toggle-btn:hover { opacity: 0.85; }

    /* Saat sidebar hidden: geser main content ke kiri */
    body.sb-hidden section[data-testid="stSidebar"] {
        display: none !important;
    }
    </style>
    <script>
    (function() {
        // Inject tombol ke DOM langsung
        if (document.getElementById('sb-toggle-btn')) return;
        var btn = document.createElement('button');
        btn.id = 'sb-toggle-btn';
        btn.innerHTML = '☰';
        btn.title = 'Toggle Sidebar';
        btn.onclick = function() {
            document.body.classList.toggle('sb-hidden');
            btn.innerHTML = document.body.classList.contains('sb-hidden') ? '☰' : '✕';
        };
        document.body.appendChild(btn);
    })();
    </script>
    """, unsafe_allow_html=True)



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