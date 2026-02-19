from typing import Any, cast
import pandas as pd
import streamlit as st

import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

try:
    import pydeck as pdk
except Exception:
    pdk = None


# ── Status colours (consistent with theme palette) ───────────
_STATUS_COLOR = {
    "MOVING":  "#00e5ff",   # cyan
    "ON-SITE": "#00e676",   # green
    "IDLE":    "#b060ff",   # violet
    "PARKED":  "#ffaa00",   # amber
}
_DEFAULT_COLOR = "#4488ff"

_SITE_COLOR = "#ff3535"   # red


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def render_street_map(
    trucks_df: pd.DataFrame,
    site: dict,
    height: int = 380,
    zoom_start: int = 12,
):
    """
    Street-level Folium map — CartoDB Dark Matter tiles.
    Cinematic dark edition: glowing circle markers, clustered.
    """
    m = folium.Map(
        location=[site["lat"], site["lon"]],
        zoom_start=zoom_start,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # ── Warehouse / Set Site marker ───────────────────────────
    folium.CircleMarker(
        location=[site["lat"], site["lon"]],
        radius=11,
        color=_SITE_COLOR,
        fill=True,
        fill_color=_SITE_COLOR,
        fill_opacity=0.95,
        weight=2,
        popup=folium.Popup(
            f"""<div style="font-family:'Rajdhani',sans-serif;font-weight:700;
                           font-size:13px;color:#ff3535;letter-spacing:0.06em;">
                  📍 {site['name']}
                </div>""",
            max_width=200,
        ),
        tooltip=f"📍 {site['name']}",
    ).add_to(m)

    # Outer pulse ring
    folium.CircleMarker(
        location=[site["lat"], site["lon"]],
        radius=18,
        color=_SITE_COLOR,
        fill=False,
        weight=1,
        opacity=0.35,
    ).add_to(m)

    # ── Truck cluster ─────────────────────────────────────────
    cluster = MarkerCluster(
        options={
            "spiderfyOnMaxZoom": True,
            "showCoverageOnHover": False,
            "zoomToBoundsOnClick": True,
            "maxClusterRadius": 50,
        }
    ).add_to(m)

    for _, r in trucks_df.iterrows():
        status = str(r.get("status", "IDLE")).upper()
        color  = _STATUS_COLOR.get(status, _DEFAULT_COLOR)

        popup_html = f"""
        <div style="font-family:'Rajdhani',sans-serif; min-width:180px;
                    background:#090e1c; border:1px solid rgba(255,255,255,0.12);
                    border-radius:10px; padding:12px; color:#dce8ff;">
          <div style="font-size:14px; font-weight:700; letter-spacing:0.06em;
                      color:{color}; margin-bottom:6px;">
            🚛 {r.get('truck_id','TRK')}
          </div>
          <div style="font-size:11px; line-height:1.6; color:rgba(180,200,240,0.80);">
            Status &nbsp;&nbsp;: <b style="color:{color}">{status}</b><br/>
            Driver &nbsp;&nbsp;: {r.get('driver_name','-')}<br/>
            Speed &nbsp;&nbsp;&nbsp;: {r.get('speed_kmh','-')} km/h<br/>
            Fuel &nbsp;&nbsp;&nbsp;&nbsp;: {r.get('fuel_liters','-')} L
          </div>
        </div>
        """

        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=1.0,
            weight=2,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"{r.get('truck_id','TRK')} · {status}",
        ).add_to(cluster)

    result = st_folium(m, width=None, height=height, returned_objects=["zoom"])

    zoom = result.get("zoom") if result else None
    if zoom is not None:
        st.caption(
            f"Zoom: **{zoom}** — scroll untuk lihat street detail. "
            "🔴 Warehouse  🔵 Moving  🟢 On-Site  🟣 Idle"
        )


def render_pydeck_map(trucks_df: pd.DataFrame, site: dict):
    """
    Fallback pydeck map — 3-D scatter with tilt for cinematic feel.
    """
    if pdk is None:
        st.warning("pydeck tidak tersedia. Menampilkan tabel data.")
        st.dataframe(trucks_df, width="stretch", height=360)
        return

    df = trucks_df.copy()

    def _color(s):
        s = str(s).upper()
        return list(_hex_to_rgb(_STATUS_COLOR.get(s, _DEFAULT_COLOR)))

    df["_color"] = df["status"].apply(_color)

    site_df = pd.DataFrame(
        [{"lat": site["lat"], "lon": site["lon"], "name": site["name"]}]
    )

    layer_site = pdk.Layer(
        "ScatterplotLayer",
        data=site_df,
        get_position="[lon, lat]",
        get_radius=250,
        get_fill_color=[255, 53, 53, 210],
        pickable=True,
        stroked=True,
        get_line_color=[255, 53, 53],
        line_width_min_pixels=2,
    )

    layer_trucks = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position="[lon, lat]",
        get_radius=160,
        get_fill_color="_color",
        pickable=True,
        opacity=0.92,
    )

    view = pdk.ViewState(
        latitude=site["lat"],
        longitude=site["lon"],
        zoom=11.5,
        pitch=38,
        bearing=-10,
    )

    deck = pdk.Deck(
        layers=[layer_site, layer_trucks],
        initial_view_state=view,
        tooltip={
            "html": (
                "<b style='color:#00e5ff'>{truck_id}</b><br/>"
                "Status: {status}<br/>"
                "Driver: {driver_name}<br/>"
                "Speed: {speed_kmh} km/h | Fuel: {fuel_liters} L"
            ),
            "style": {
                "backgroundColor": "#090e1c",
                "color": "#dce8ff",
                "fontFamily": "monospace",
                "fontSize": "12px",
                "border": "1px solid rgba(255,255,255,0.12)",
                "borderRadius": "8px",
            },
        },
        map_style="mapbox://styles/mapbox/dark-v11",
    )

    st.pydeck_chart(deck, use_container_width=True)
