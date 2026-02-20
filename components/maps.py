import pandas as pd
import streamlit as st

import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

try:
    import pydeck as pdk
except Exception:
    pdk = None


def render_street_map(
    trucks_df: pd.DataFrame,
    site: dict,
    height: int = 380,
    zoom_start: int = 12,
    key: str | None = None,   # ✅ IMPORTANT
):
    """
    Folium street map (CartoDB Dark Matter).
    Key param is REQUIRED to avoid StreamlitDuplicateElementKey when map rendered twice.
    """
    lat0 = float(site.get("lat", -6.2))
    lon0 = float(site.get("lon", 106.8))

    m = folium.Map(
        location=[lat0, lon0],
        zoom_start=zoom_start,
        control_scale=True,
        tiles=None,
    )

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark Matter",
        name="Dark Matter",
        control=False,
    ).add_to(m)

    cluster = MarkerCluster().add_to(m)

    # Basic status color mapping (safe fallback)
    def _status_color(status: str) -> str:
        s = (status or "").upper()
        if "RENT" in s or "ON" in s:
            return "#2deca0"
        if "MAINT" in s:
            return "#4aa3ff"
        if "LOST" in s or "ALERT" in s:
            return "#ff3b6b"
        if "AVAIL" in s:
            return "#ffd166"
        return "#7a8aa6"

    for _, r in trucks_df.iterrows():
        try:
            lat = float(r.get("lat", lat0))
            lon = float(r.get("lon", lon0))
        except Exception:
            lat, lon = lat0, lon0

        status = str(r.get("status", "UNKNOWN"))
        color = _status_color(status)

        folium.CircleMarker(
            location=[lat, lon],
            radius=7,
            color=color,
            fill=True,
            fill_opacity=0.85,
            tooltip=f"{r.get('truck_id','TRK')} · {status}",
        ).add_to(cluster)

    # ✅ FIX: unique key per map instance
    st_folium(
        m,
        width=None,
        height=height,
        returned_objects=["zoom"],
        key=key or f"folium_{site.get('name','site')}_{height}_{zoom_start}",
    )


def render_pydeck_map(trucks_df: pd.DataFrame, site: dict):
    """Fast GPU map via pydeck (fallback)."""
    if pdk is None:
        st.warning("pydeck tidak tersedia. Install: pip install pydeck")
        return

    df = trucks_df.copy()

    lat0 = float(site.get("lat", -6.2))
    lon0 = float(site.get("lon", 106.8))

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position="[lon, lat]",
        get_radius=80,
        get_fill_color="[45, 236, 160, 160]",
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(latitude=lat0, longitude=lon0, zoom=11, pitch=30)

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{truck_id}\n{status}\n{driver_name}"},
        map_style="mapbox://styles/mapbox/dark-v11",
    )

    try:
        st.pydeck_chart(deck, width="stretch")
    except TypeError:
        st.pydeck_chart(deck, use_container_width=True)