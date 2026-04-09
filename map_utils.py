"""
map_utils.py - Folium map generation for SAFAR
"""

import folium
from folium.plugins import HeatMap, AntPath
from typing import List, Tuple, Optional


def build_base_map(center: Tuple[float, float], zoom: int = 13) -> folium.Map:
    """Create a clean base map centered on given coordinates."""
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB positron",
        control_scale=True,
        prefer_canvas=True,
    )
    # Add tile layer toggle
    folium.TileLayer("OpenStreetMap", name="Street Map").add_to(m)
    folium.TileLayer("CartoDB positron", name="Light (Default)").add_to(m)
    folium.LayerControl(collapsed=True).add_to(m)
    return m


def add_route(
    m: folium.Map,
    coords: List[Tuple[float, float]],
    color: str = "#2563EB",
    weight: int = 5,
    name: str = "Route",
    use_antpath: bool = False,
) -> folium.Map:
    """Draw a route polyline on the map."""
    if not coords or len(coords) < 2:
        return m

    if use_antpath:
        AntPath(
            locations=coords,
            color=color,
            weight=weight,
            opacity=0.85,
            delay=800,
            tooltip=name,
        ).add_to(m)
    else:
        folium.PolyLine(
            locations=coords,
            color=color,
            weight=weight,
            opacity=0.85,
            tooltip=name,
            smooth_factor=2,
        ).add_to(m)
    return m


def add_start_marker(m: folium.Map, coords: Tuple[float, float], label: str = "Start") -> folium.Map:
    folium.Marker(
        location=coords,
        popup=folium.Popup(f"<b>🟢 {label}</b>", max_width=120),
        tooltip=f"📍 {label}",
        icon=folium.Icon(color="green", icon="play", prefix="fa"),
    ).add_to(m)
    return m


def add_end_marker(m: folium.Map, coords: Tuple[float, float], label: str = "Destination") -> folium.Map:
    folium.Marker(
        location=coords,
        popup=folium.Popup(f"<b>🔴 {label}</b>", max_width=120),
        tooltip=f"🏁 {label}",
        icon=folium.Icon(color="red", icon="flag", prefix="fa"),
    ).add_to(m)
    return m


def add_vehicle_marker(
    m: folium.Map,
    coords: Tuple[float, float],
    progress: int = 0
) -> folium.Map:
    """Add an animated vehicle position marker."""
    folium.Marker(
        location=coords,
        popup=folium.Popup(f"<b>🚗 Vehicle</b><br>Progress: {progress}%", max_width=150),
        tooltip=f"🚗 {progress}% complete",
        icon=folium.DivIcon(
            html=f"""
            <div style="
                background:#f59e0b;
                border:3px solid white;
                border-radius:50%;
                width:28px; height:28px;
                display:flex; align-items:center; justify-content:center;
                font-size:16px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.35);
            ">🚗</div>
            """,
            icon_size=(28, 28),
            icon_anchor=(14, 14),
        ),
    ).add_to(m)
    return m


def add_danger_heatmap(m: folium.Map, zones: List[dict]) -> folium.Map:
    """Add a danger heatmap layer."""
    intensity_map = {"low": 0.3, "medium": 0.6, "high": 1.0}
    heat_data = [
        [z["lat"], z["lon"], intensity_map.get(z["intensity"], 0.5)]
        for z in zones
    ]
    HeatMap(
        heat_data,
        name="Danger Zones",
        min_opacity=0.3,
        max_zoom=16,
        radius=25,
        blur=20,
        gradient={0.3: "blue", 0.6: "orange", 1.0: "red"},
    ).add_to(m)
    return m


def build_route_map(
    start_coords: Tuple[float, float],
    end_coords: Tuple[float, float],
    start_name: str,
    end_name: str,
    fastest_coords: Optional[List[Tuple[float, float]]] = None,
    safest_coords: Optional[List[Tuple[float, float]]] = None,
    selected_route: str = "fastest",
    vehicle_pos: Optional[Tuple[float, float]] = None,
    vehicle_progress: int = 0,
    danger_zones: Optional[List[dict]] = None,
    show_heatmap: bool = False,
) -> folium.Map:
    """
    Build the complete SAFAR map with all layers.
    """
    # Center the map between start and end
    center_lat = (start_coords[0] + end_coords[0]) / 2
    center_lon = (start_coords[1] + end_coords[1]) / 2

    # Auto zoom based on distance
    import math
    lat_diff = abs(start_coords[0] - end_coords[0])
    lon_diff = abs(start_coords[1] - end_coords[1])
    max_diff = max(lat_diff, lon_diff)
    if max_diff < 0.01:
        zoom = 15
    elif max_diff < 0.05:
        zoom = 14
    elif max_diff < 0.15:
        zoom = 13
    elif max_diff < 0.5:
        zoom = 12
    elif max_diff < 1.5:
        zoom = 11
    else:
        zoom = 10

    m = build_base_map((center_lat, center_lon), zoom=zoom)

    # Draw non-selected route first (dimmed)
    if fastest_coords and selected_route != "fastest":
        add_route(m, fastest_coords, color="#93C5FD", weight=4, name="Fastest Route")
    if safest_coords and selected_route != "safest":
        add_route(m, safest_coords, color="#86EFAC", weight=4, name="Safest Route")

    # Draw selected route on top (animated)
    if fastest_coords and selected_route == "fastest":
        add_route(m, fastest_coords, color="#2563EB", weight=6, name="Fastest Route ✓", use_antpath=True)
    if safest_coords and selected_route == "safest":
        add_route(m, safest_coords, color="#16A34A", weight=6, name="Safest Route ✓", use_antpath=True)

    # Danger heatmap
    if show_heatmap and danger_zones:
        add_danger_heatmap(m, danger_zones)

    # Markers
    add_start_marker(m, start_coords, label=start_name)
    add_end_marker(m, end_coords, label=end_name)

    # Vehicle tracking marker
    if vehicle_pos:
        add_vehicle_marker(m, vehicle_pos, progress=vehicle_progress)

    # Fit bounds
    all_points = [start_coords, end_coords]
    if fastest_coords:
        all_points += fastest_coords[::5]
    if safest_coords:
        all_points += safest_coords[::5]

    sw = [min(p[0] for p in all_points) - 0.005, min(p[1] for p in all_points) - 0.005]
    ne = [max(p[0] for p in all_points) + 0.005, max(p[1] for p in all_points) + 0.005]
    m.fit_bounds([sw, ne])

    return m


def map_to_html(m: folium.Map) -> str:
    """Convert folium map to HTML string."""
    return m._repr_html_()
