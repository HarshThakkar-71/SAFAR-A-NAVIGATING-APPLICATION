"""
safar_app.py - SAFAR Smart Navigation System
Professional AI-powered navigation with safety intelligence.
Run: streamlit run safar_app.py
"""

import streamlit as st
import time
import json

# ── Page config (MUST be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="SAFAR — Smart Navigation",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from safar_core import (
    plan_routes, init_tracking, predict_next_offline,
    trigger_sos, generate_danger_zones, RouteInfo, TrackingState
)
from map_utils import build_route_map, map_to_html
from geo_utils import get_place_suggestions, KNOWN_LOCATIONS

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

/* Reset & base */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'DM Sans', sans-serif;
    background: #F8FAFC !important;
    color: #1E293B;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Header bar ─────────────────────────────────────────────────────────── */
.safar-header {
    background: white;
    border-bottom: 1px solid #E2E8F0;
    padding: 14px 32px;
    display: flex;
    align-items: center;
    gap: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    position: sticky; top: 0; z-index: 100;
}
.safar-logo {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 22px;
    font-weight: 700;
    background: linear-gradient(135deg, #2563EB, #7C3AED);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
}
.safar-tagline {
    font-size: 12px;
    color: #64748B;
    font-weight: 400;
    margin-top: 1px;
}
.status-pill {
    margin-left: auto;
    background: #ECFDF5;
    color: #059669;
    border: 1px solid #A7F3D0;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 500;
}

/* ── Main layout ─────────────────────────────────────────────────────────── */
.main-layout {
    display: flex;
    height: calc(100vh - 57px);
    overflow: hidden;
}
.left-panel {
    width: 380px;
    min-width: 340px;
    background: white;
    border-right: 1px solid #E2E8F0;
    overflow-y: auto;
    padding: 20px 18px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}
.right-panel {
    flex: 1;
    position: relative;
    background: #EFF6FF;
}

/* ── Cards ──────────────────────────────────────────────────────────────── */
.card {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 16px 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.card-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ── Inputs ──────────────────────────────────────────────────────────────── */
[data-testid="stTextInput"] input {
    border: 1.5px solid #E2E8F0 !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    font-family: 'DM Sans', sans-serif !important;
    background: #F8FAFC !important;
    color: #1E293B !important;
    transition: border-color 0.15s, box-shadow 0.15s;
}
[data-testid="stTextInput"] input:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
    background: white !important;
}
[data-testid="stTextInput"] label {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #374151 !important;
    margin-bottom: 4px !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────────── */
[data-testid="stButton"] button {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all 0.15s !important;
    border: none !important;
    cursor: pointer !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(37,99,235,0.35) !important;
    padding: 12px 0 !important;
    width: 100%;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(37,99,235,0.4) !important;
}

/* ── Route cards ─────────────────────────────────────────────────────────── */
.route-card {
    border: 2px solid #E2E8F0;
    border-radius: 12px;
    padding: 14px 16px;
    cursor: pointer;
    transition: all 0.15s;
    background: white;
}
.route-card.active {
    border-color: #2563EB;
    background: #EFF6FF;
}
.route-card.safe-active {
    border-color: #16A34A;
    background: #F0FDF4;
}
.route-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.route-name {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 15px;
    font-weight: 600;
    color: #1E293B;
    margin-bottom: 8px;
}
.route-meta {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
}
.route-stat {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    color: #475569;
}
.route-stat span.val {
    font-weight: 600;
    color: #1E293B;
}
.safety-badge {
    display: inline-block;
    margin-top: 8px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    background: #F1F5F9;
    color: #334155;
}

/* ── Tracking progress ───────────────────────────────────────────────────── */
.progress-outer {
    background: #E2E8F0;
    border-radius: 99px;
    height: 8px;
    overflow: hidden;
    margin: 8px 0;
}
.progress-inner {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #2563EB, #7C3AED);
    transition: width 0.4s ease;
}

/* ── SOS button ──────────────────────────────────────────────────────────── */
.sos-btn {
    background: #FEF2F2;
    border: 2px solid #FECACA;
    border-radius: 12px;
    padding: 14px;
    text-align: center;
    cursor: pointer;
}
.sos-btn .sos-label {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 16px;
    font-weight: 700;
    color: #DC2626;
}

/* ── SOS response ────────────────────────────────────────────────────────── */
.sos-response {
    background: #FEF2F2;
    border: 1.5px solid #FECACA;
    border-radius: 12px;
    padding: 14px;
    margin-top: 12px;
    animation: pulse-red 1s ease;
}
@keyframes pulse-red {
    0% { box-shadow: 0 0 0 0 rgba(220,38,38,0.4); }
    70% { box-shadow: 0 0 0 10px rgba(220,38,38,0); }
    100% { box-shadow: 0 0 0 0 rgba(220,38,38,0); }
}

/* ── Map overlay ─────────────────────────────────────────────────────────── */
.map-frame {
    width: 100%;
    height: 100%;
    border: none;
}
.map-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #94A3B8;
    gap: 12px;
}
.map-placeholder .icon {
    font-size: 56px;
    opacity: 0.5;
}
.map-placeholder .text {
    font-size: 16px;
    font-weight: 500;
}

/* ── Suggestion pills ────────────────────────────────────────────────────── */
.suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 4px;
}
.sug-pill {
    background: #F1F5F9;
    border: 1px solid #E2E8F0;
    border-radius: 99px;
    padding: 3px 10px;
    font-size: 12px;
    color: #334155;
    cursor: pointer;
}
.sug-pill:hover { background: #E0E7FF; border-color: #A5B4FC; }

/* ── Info banner ─────────────────────────────────────────────────────────── */
.info-banner {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
    color: #1D4ED8;
}

/* ── Section divider ─────────────────────────────────────────────────────── */
.section-gap { height: 8px; }

/* ── Scrollbar ───────────────────────────────────────────────────────────── */
.left-panel::-webkit-scrollbar { width: 4px; }
.left-panel::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 4px; }

</style>
""", unsafe_allow_html=True)


# ── Session state defaults ───────────────────────────────────────────────────
def init_state():
    defaults = {
        "map_html": None,
        "fastest_route": None,
        "safest_route": None,
        "selected_route": "fastest",
        "start_coords": None,
        "end_coords": None,
        "start_name": "",
        "end_name": "",
        "status_msg": "",
        "tracking": None,
        "tracking_active": False,
        "sos_triggered": False,
        "sos_response": None,
        "show_heatmap": False,
        "danger_zones": [],
        "offline_mode": False,
        "route_planned": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="safar-header">
    <div>
        <div class="safar-logo">🧭 SAFAR</div>
        <div class="safar-tagline">Smart AI Navigation & Safety</div>
    </div>
    <div class="status-pill">● Live</div>
</div>
""", unsafe_allow_html=True)


# ── Helper: rebuild map ───────────────────────────────────────────────────────
def rebuild_map(vehicle_pos=None, vehicle_progress=0):
    if not st.session_state.start_coords or not st.session_state.end_coords:
        return
    fastest = st.session_state.fastest_route
    safest = st.session_state.safest_route

    m = build_route_map(
        start_coords=st.session_state.start_coords,
        end_coords=st.session_state.end_coords,
        start_name=st.session_state.start_name,
        end_name=st.session_state.end_name,
        fastest_coords=fastest.coords if fastest else None,
        safest_coords=safest.coords if safest else None,
        selected_route=st.session_state.selected_route,
        vehicle_pos=vehicle_pos,
        vehicle_progress=vehicle_progress,
        danger_zones=st.session_state.danger_zones if st.session_state.show_heatmap else None,
        show_heatmap=st.session_state.show_heatmap,
    )
    st.session_state.map_html = map_to_html(m)


# ── Two-column layout ─────────────────────────────────────────────────────────
left_col, right_col = st.columns([1.05, 2.2], gap="small")

# ════════════════════════════════════════════════════════
# LEFT PANEL
# ════════════════════════════════════════════════════════
with left_col:
    # ── Route planning card ──────────────────────────────────────────────────
    st.markdown('<div class="card-title">📍 Plan Route</div>', unsafe_allow_html=True)

    start_input = st.text_input(
        "Starting Point",
        value=st.session_state.start_name,
        placeholder="e.g. Connaught Place, Delhi",
        key="start_input_field",
    )
    end_input = st.text_input(
        "Destination",
        value=st.session_state.end_name,
        placeholder="e.g. Hauz Khas, Delhi",
        key="end_input_field",
    )

    # Quick-pick suggestions
    all_places = sorted([k.title() for k in KNOWN_LOCATIONS.keys() if k != "india"])
    suggestions_html = "".join(
        f'<span class="sug-pill">{p}</span>'
        for p in all_places[:10]
    )
    st.markdown(
        f'<div style="font-size:11px;color:#94A3B8;margin-bottom:2px;">Popular locations:</div>'
        f'<div class="suggestions">{suggestions_html}</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    plan_btn = st.button("🗺️ Find Routes", use_container_width=True, type="primary")

    if plan_btn:
        if not start_input.strip() or not end_input.strip():
            st.error("Please enter both starting point and destination.")
        else:
            with st.spinner("Finding the best routes..."):
                fastest, safest, status = plan_routes(start_input.strip(), end_input.strip())

            if fastest is None:
                st.error(status)
            else:
                st.session_state.fastest_route = fastest
                st.session_state.safest_route = safest
                st.session_state.start_name = start_input.strip()
                st.session_state.end_name = end_input.strip()
                st.session_state.start_coords = fastest.coords[0]
                st.session_state.end_coords = fastest.coords[-1]
                st.session_state.status_msg = status
                st.session_state.route_planned = True
                st.session_state.tracking = None
                st.session_state.tracking_active = False
                st.session_state.sos_triggered = False

                # Danger zones
                mid = fastest.coords[len(fastest.coords)//2]
                st.session_state.danger_zones = generate_danger_zones(mid)

                rebuild_map()
                st.rerun()

    # Status message
    if st.session_state.status_msg:
        st.markdown(
            f'<div class="info-banner">{st.session_state.status_msg}</div>',
            unsafe_allow_html=True
        )

    # ── Route comparison cards ───────────────────────────────────────────────
    if st.session_state.route_planned:
        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🛣️ Route Options</div>', unsafe_allow_html=True)

        fastest = st.session_state.fastest_route
        safest  = st.session_state.safest_route
        sel     = st.session_state.selected_route

        # Fastest Route
        fast_active = "active" if sel == "fastest" else ""
        st.markdown(f"""
        <div class="route-card {fast_active}">
            <div class="route-name">⚡ Fastest Route</div>
            <div class="route-meta">
                <div class="route-stat">🛣️ <span class="val">{fastest.distance_km} km</span></div>
                <div class="route-stat">⏱️ <span class="val">{fastest.time_min} min</span></div>
                <div class="route-stat">🛡️ <span class="val">{fastest.safety_score}/100</span></div>
            </div>
            <div class="safety-badge">{fastest.safety_label}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Select Fastest", use_container_width=True, key="sel_fast"):
            st.session_state.selected_route = "fastest"
            rebuild_map()
            st.rerun()

        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

        # Safest Route
        safe_active = "safe-active" if sel == "safest" else ""
        st.markdown(f"""
        <div class="route-card {safe_active}">
            <div class="route-name">🛡️ Safest Route</div>
            <div class="route-meta">
                <div class="route-stat">🛣️ <span class="val">{safest.distance_km} km</span></div>
                <div class="route-stat">⏱️ <span class="val">{safest.time_min} min</span></div>
                <div class="route-stat">🛡️ <span class="val">{safest.safety_score}/100</span></div>
            </div>
            <div class="safety-badge">{safest.safety_label}</div>
        </div>
        """, unsafe_allow_html=True)

        safe_exp = safest.safety_explanation
        st.markdown(
            f'<div style="font-size:12px;color:#475569;margin-top:6px;padding:0 2px;">'
            f'💡 {safe_exp}</div>',
            unsafe_allow_html=True
        )

        if st.button("Select Safest", use_container_width=True, key="sel_safe"):
            st.session_state.selected_route = "safest"
            rebuild_map()
            st.rerun()

        # ── Map options ──────────────────────────────────────────────────────
        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🗺️ Map Options</div>', unsafe_allow_html=True)

        show_heat = st.toggle("Show Danger Heatmap", value=st.session_state.show_heatmap)
        if show_heat != st.session_state.show_heatmap:
            st.session_state.show_heatmap = show_heat
            rebuild_map()
            st.rerun()

        # ── Live Tracking ────────────────────────────────────────────────────
        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🚗 Live Tracking</div>', unsafe_allow_html=True)

        offline_mode = st.toggle("Simulate Offline Mode", value=st.session_state.offline_mode)
        if offline_mode != st.session_state.offline_mode:
            st.session_state.offline_mode = offline_mode

        tracking = st.session_state.tracking
        tracking_active = st.session_state.tracking_active

        if not tracking_active:
            if st.button("▶ Start Simulation", use_container_width=True):
                selected = (
                    st.session_state.fastest_route
                    if st.session_state.selected_route == "fastest"
                    else st.session_state.safest_route
                )
                st.session_state.tracking = init_tracking(selected)
                st.session_state.tracking_active = True
                st.rerun()
        else:
            if st.button("⏹ Stop Simulation", use_container_width=True):
                st.session_state.tracking_active = False
                st.session_state.tracking = None
                rebuild_map()
                st.rerun()

        # Show progress
        if tracking and tracking_active:
            progress = tracking.progress_pct
            pos = tracking.current_position
            mode_label = "📡 Offline (predicted)" if st.session_state.offline_mode else "📶 Online"

            st.markdown(f"""
            <div style="margin-top:8px;">
                <div style="display:flex;justify-content:space-between;font-size:12px;color:#64748B;margin-bottom:4px;">
                    <span>{mode_label}</span><span>{progress}% complete</span>
                </div>
                <div class="progress-outer">
                    <div class="progress-inner" style="width:{progress}%;"></div>
                </div>
                <div style="font-size:12px;color:#64748B;margin-top:4px;">
                    📍 {pos[0]:.4f}°N, {pos[1]:.4f}°E
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Advance tracking
            if st.session_state.offline_mode:
                predicted = predict_next_offline(tracking)
                rebuild_map(vehicle_pos=predicted, vehicle_progress=progress)
            else:
                tracking.advance(steps=2)
                rebuild_map(vehicle_pos=tracking.current_position, vehicle_progress=tracking.progress_pct)

            if not tracking.is_active:
                st.success("🏁 You have arrived at your destination!")
                st.session_state.tracking_active = False
            else:
                time.sleep(0.8)
                st.rerun()

        # ── Emergency SOS ────────────────────────────────────────────────────
        st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
        st.markdown('<div class="card-title">🆘 Emergency SOS</div>', unsafe_allow_html=True)

        if st.button("🚨 TRIGGER SOS ALERT", use_container_width=True):
            pos = None
            if st.session_state.tracking:
                pos = st.session_state.tracking.current_position
            elif st.session_state.start_coords:
                pos = st.session_state.start_coords
            st.session_state.sos_triggered = True
            st.session_state.sos_response = trigger_sos(pos)

        if st.session_state.sos_triggered and st.session_state.sos_response:
            resp = st.session_state.sos_response
            st.markdown(f"""
            <div class="sos-response">
                <div style="font-weight:700;color:#DC2626;font-size:14px;margin-bottom:8px;">
                    🚨 SOS Alert Sent — {resp['timestamp']}
                </div>
                <div style="font-size:12px;color:#7F1D1D;margin-bottom:8px;">
                    📍 {resp['location']}
                </div>
                <div style="font-size:12px;color:#991B1B;margin-bottom:8px;">
                    {resp['message']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            for name, info in resp["contacts"].items():
                st.markdown(
                    f'<div style="font-size:12px;padding:4px 0;border-bottom:1px solid #FEE2E2;">'
                    f'{info["icon"]} <b>{name}</b> — {info["number"]} &nbsp;|&nbsp; ETA: {info["eta"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )
            if st.button("✖ Dismiss SOS"):
                st.session_state.sos_triggered = False
                st.session_state.sos_response = None
                st.rerun()


# ════════════════════════════════════════════════════════
# RIGHT PANEL — MAP
# ════════════════════════════════════════════════════════
with right_col:
    if st.session_state.map_html:
        # Render the map in an iframe
        map_html_escaped = st.session_state.map_html
        st.components.v1.html(
            map_html_escaped,
            height=800,
            scrolling=False,
        )
    else:
        st.markdown("""
        <div class="map-placeholder" style="height:750px;display:flex;flex-direction:column;
             align-items:center;justify-content:center;background:#F8FAFC;border-radius:16px;
             border:2px dashed #CBD5E1;margin:16px 8px;">
            <div style="font-size:64px;margin-bottom:16px;">🗺️</div>
            <div style="font-size:18px;font-weight:600;color:#475569;">Enter a route to get started</div>
            <div style="font-size:14px;color:#94A3B8;margin-top:8px;text-align:center;max-width:280px;">
                Type your starting point and destination on the left, then click <b>Find Routes</b>
            </div>
            <div style="margin-top:24px;display:flex;gap:16px;flex-wrap:wrap;justify-content:center;">
                <div style="background:white;border:1px solid #E2E8F0;border-radius:10px;padding:10px 16px;
                     font-size:13px;color:#475569;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                    ⚡ Fastest Route
                </div>
                <div style="background:white;border:1px solid #E2E8F0;border-radius:10px;padding:10px 16px;
                     font-size:13px;color:#475569;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                    🛡️ Safest Route
                </div>
                <div style="background:white;border:1px solid #E2E8F0;border-radius:10px;padding:10px 16px;
                     font-size:13px;color:#475569;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                    🚗 Live Tracking
                </div>
                <div style="background:white;border:1px solid #E2E8F0;border-radius:10px;padding:10px 16px;
                     font-size:13px;color:#475569;box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                    🚨 SOS Alert
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)