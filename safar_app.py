"""
safar_app.py - SAFAR Premium Navigation System
Premium AI-powered navigation with real GPS tracking, login, and live map.
Run: streamlit run safar_app.py
"""

import streamlit as st
import time
import json

# ── Page config (MUST be first Streamlit call) ──────────────────────────────
st.set_page_config(
    page_title="SAFAR — Premium Navigation",
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

# ── Premium CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=Outfit:wght@300;400;500;600;700&display=swap');

:root {
    --bg: #080C14;
    --surface: #0D1421;
    --surface2: #111827;
    --border: rgba(255,255,255,0.07);
    --border-bright: rgba(255,255,255,0.14);
    --accent: #3B82F6;
    --accent2: #6366F1;
    --accent-glow: rgba(59,130,246,0.25);
    --green: #10B981;
    --red: #EF4444;
    --text: #F1F5F9;
    --text2: #94A3B8;
    --text3: #475569;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    font-family: 'Outfit', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
    min-height: 100vh;
}

#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }

.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stVerticalBlock"] { gap: 0 !important; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }

/* HEADER */
.safar-header {
    background: rgba(8,12,20,0.95);
    backdrop-filter: blur(24px);
    border-bottom: 1px solid var(--border);
    padding: 0 28px;
    height: 60px;
    display: flex;
    align-items: center;
    gap: 16px;
    position: sticky; top: 0; z-index: 999;
}
.header-logo {
    font-family: 'Syne', sans-serif;
    font-size: 20px; font-weight: 800;
    background: linear-gradient(135deg, #60A5FA, #818CF8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    letter-spacing: -0.5px;
}
.header-tagline {
    font-size: 12px; color: var(--text3); font-weight: 400;
    border-left: 1px solid var(--border); padding-left: 14px; margin-left: 2px;
}
.live-dot {
    margin-left: auto; display: flex; align-items: center; gap: 8px;
    font-size: 12px; color: var(--green); font-weight: 500;
}
.live-dot::before {
    content: ''; width: 8px; height: 8px; background: var(--green);
    border-radius: 50%; box-shadow: 0 0 8px var(--green);
    animation: blink 2s ease infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.4} }
.user-chip {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 99px; padding: 6px 14px 6px 8px;
    display: flex; align-items: center; gap: 8px;
    font-size: 13px; color: var(--text2);
}
.user-avatar {
    width: 26px; height: 26px; border-radius: 50%;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700; color: white; flex-shrink: 0;
}

/* INPUTS */
[data-testid="stTextInput"] input {
    background: var(--surface2) !important;
    border: 1px solid var(--border-bright) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 14px !important;
    padding: 11px 14px !important;
    transition: all 0.2s !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
}
[data-testid="stTextInput"] input::placeholder { color: var(--text3) !important; }
[data-testid="stTextInput"] label {
    color: var(--text2) !important; font-size: 12px !important;
    font-weight: 500 !important; font-family: 'Outfit', sans-serif !important;
    letter-spacing: 0.3px !important; margin-bottom: 5px !important;
}

/* BUTTONS */
[data-testid="stButton"] > button {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important; font-size: 14px !important;
    border-radius: 10px !important; border: none !important;
    transition: all 0.2s !important; cursor: pointer !important;
}
[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #3B82F6, #6366F1) !important;
    color: white !important;
    box-shadow: 0 4px 20px rgba(99,102,241,0.35) !important;
    padding: 13px 0 !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 28px rgba(99,102,241,0.5) !important;
}
[data-testid="stButton"] > button:not([kind]) {
    background: var(--surface2) !important;
    color: var(--text2) !important;
    border: 1px solid var(--border-bright) !important;
    padding: 10px 0 !important;
}
[data-testid="stButton"] > button:not([kind]):hover {
    background: rgba(255,255,255,0.06) !important;
    color: var(--text) !important;
}

/* TOGGLE */
[data-testid="stToggle"] label { color: var(--text2) !important; font-size: 13px !important; font-family: 'Outfit', sans-serif !important; }
[data-testid="stToggle"] [role="switch"][aria-checked="true"] { background-color: var(--accent) !important; }

/* SECTION LABEL */
.section-label {
    font-family: 'Syne', sans-serif; font-size: 10px; font-weight: 700;
    letter-spacing: 1.2px; color: var(--text3); text-transform: uppercase;
    margin-bottom: 10px; display: flex; align-items: center; gap: 8px;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }

/* ROUTE CARDS */
.route-card {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 14px; padding: 16px; transition: all 0.2s;
    position: relative; overflow: hidden;
}
.route-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 2px; background: transparent; transition: background 0.2s;
}
.route-card.active-fast::before { background: linear-gradient(90deg, #3B82F6, #6366F1); }
.route-card.active-safe::before { background: linear-gradient(90deg, #10B981, #34D399); }
.route-card.active-fast { border-color: rgba(59,130,246,0.4); background: rgba(59,130,246,0.06); }
.route-card.active-safe { border-color: rgba(16,185,129,0.4); background: rgba(16,185,129,0.06); }
.route-card:hover { border-color: var(--border-bright); }
.route-title { font-family: 'Syne', sans-serif; font-size: 15px; font-weight: 700; color: var(--text); margin-bottom: 12px; }
.route-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.stat-box { background: rgba(255,255,255,0.04); border-radius: 8px; padding: 8px; text-align: center; }
.stat-val { font-size: 16px; font-weight: 700; color: var(--text); }
.stat-key { font-size: 10px; color: var(--text3); margin-top: 2px; letter-spacing: 0.5px; text-transform: uppercase; }
.safety-tag {
    display: inline-flex; align-items: center; gap: 5px; margin-top: 10px;
    padding: 4px 10px; border-radius: 99px; font-size: 11px; font-weight: 600;
    background: rgba(255,255,255,0.05); color: var(--text2);
}

/* TRACKING */
.track-box {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 14px; padding: 16px;
}
.track-header { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 12px; }
.track-header .label { color: var(--text2); }
.track-header .pct { color: var(--accent); font-weight: 700; font-size: 14px; }
.prog-bar { height: 6px; background: rgba(255,255,255,0.06); border-radius: 99px; overflow: hidden; }
.prog-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, var(--accent), var(--accent2)); transition: width 0.5s ease; }
.track-pos { margin-top: 10px; font-size: 11px; color: var(--text3); }

/* SOS */
.sos-response {
    background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.25);
    border-radius: 14px; padding: 16px;
    animation: sosPulse 0.6s ease;
}
@keyframes sosPulse {
    0% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }
    70% { box-shadow: 0 0 0 16px rgba(239,68,68,0); }
    100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
}
.sos-contact {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 0; border-bottom: 1px solid rgba(239,68,68,0.12);
    font-size: 12px; color: #FCA5A5;
}
.sos-contact:last-child { border-bottom: none; }

/* INFO */
.info-banner {
    background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.2);
    border-radius: 10px; padding: 10px 14px;
    font-size: 12px; color: #93C5FD; line-height: 1.5;
}
.sug-wrap { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
.sug-chip {
    background: rgba(255,255,255,0.04); border: 1px solid var(--border);
    border-radius: 99px; padding: 4px 10px; font-size: 11px; color: var(--text2);
    cursor: pointer; transition: all 0.15s;
}
.sug-chip:hover { background: rgba(59,130,246,0.12); border-color: rgba(59,130,246,0.3); color: #93C5FD; }

[data-testid="stHorizontalBlock"] { gap: 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ────────────────────────────────────────────────────
def init_state():
    defaults = {
        "logged_in": False,
        "username": "",
        "user_initials": "",
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


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:

    col_center = st.columns([1, 1.1, 1])[1]

    with col_center:
        st.markdown("""
        <div style="padding:60px 0 20px;">
            <div style="text-align:center;margin-bottom:32px;">
                <div style="font-family:'Syne',sans-serif;font-size:42px;font-weight:800;
                     background:linear-gradient(135deg,#60A5FA,#818CF8,#A78BFA);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                     background-clip:text;letter-spacing:-2px;margin-bottom:10px;">
                    🧭 SAFAR
                </div>
                <div style="font-size:14px;color:#475569;letter-spacing:0.3px;margin-bottom:14px;">
                    Smart AI Navigation &amp; Safety System
                </div>
                <div style="display:inline-flex;align-items:center;gap:6px;
                     background:rgba(59,130,246,0.1);border:1px solid rgba(59,130,246,0.25);
                     border-radius:99px;padding:5px 16px;font-size:11px;color:#93C5FD;font-weight:600;">
                    ● Premium Navigation Suite
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("Your Name", placeholder="e.g. Arjun Sharma", key="login_username")
        email    = st.text_input("Email", placeholder="you@example.com", key="login_email")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="login_pass")

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        if st.button("Sign In  →", use_container_width=True, type="primary"):
            if not username.strip():
                st.error("Please enter your name.")
            elif "@" not in email:
                st.error("Please enter a valid email.")
            elif len(password) < 4:
                st.error("Password must be at least 4 characters.")
            else:
                st.session_state.logged_in = True
                st.session_state.username = username.strip()
                st.session_state.user_initials = "".join([w[0].upper() for w in username.strip().split()[:2]]) or "U"
                st.rerun()

        st.markdown("""
        <div style="display:flex;align-items:center;gap:12px;margin:20px 0 16px;">
            <div style="flex:1;height:1px;background:rgba(255,255,255,0.07);"></div>
            <div style="font-size:11px;color:#334155;">quick access</div>
            <div style="flex:1;height:1px;background:rgba(255,255,255,0.07);"></div>
        </div>
        """, unsafe_allow_html=True)

        demo1, demo2 = st.columns(2)
        with demo1:
            if st.button("🚀 Guest Login", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.username = "Guest User"
                st.session_state.user_initials = "G"
                st.rerun()
        with demo2:
            if st.button("📋 Demo Mode", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.username = "Demo User"
                st.session_state.user_initials = "D"
                st.rerun()

        st.markdown("""
        <div style="text-align:center;margin-top:20px;font-size:11px;color:#334155;padding-bottom:40px;">
            By continuing you agree to SAFAR's Terms of Service &amp; Privacy Policy
        </div>
        """, unsafe_allow_html=True)

    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────────────────────────────────────

def rebuild_map(vehicle_pos=None, vehicle_progress=0):
    if not st.session_state.start_coords or not st.session_state.end_coords:
        return
    m = build_route_map(
        start_coords=st.session_state.start_coords,
        end_coords=st.session_state.end_coords,
        start_name=st.session_state.start_name,
        end_name=st.session_state.end_name,
        fastest_coords=st.session_state.fastest_route.coords if st.session_state.fastest_route else None,
        safest_coords=st.session_state.safest_route.coords  if st.session_state.safest_route  else None,
        selected_route=st.session_state.selected_route,
        vehicle_pos=vehicle_pos,
        vehicle_progress=vehicle_progress,
        danger_zones=st.session_state.danger_zones if st.session_state.show_heatmap else None,
        show_heatmap=st.session_state.show_heatmap,
    )
    st.session_state.map_html = map_to_html(m)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="safar-header">
    <div class="header-logo">🧭 SAFAR</div>
    <div class="header-tagline">Smart AI Navigation & Safety</div>
    <div class="live-dot" style="margin-left:auto;margin-right:12px;">LIVE</div>
    <div class="user-chip">
        <div class="user-avatar">{st.session_state.user_initials}</div>
        {st.session_state.username.split()[0]}
    </div>
</div>
""", unsafe_allow_html=True)


left_col, right_col = st.columns([1, 2.5], gap="small")

# ══════════════════════════════════════════════════════════
# LEFT PANEL
# ══════════════════════════════════════════════════════════
with left_col:
    st.markdown("""
    <div style="background:#0D1421;border-right:1px solid rgba(255,255,255,0.07);
         min-height:calc(100vh - 60px);padding:20px 16px;">
    """, unsafe_allow_html=True)

    # ── Route Planning ────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">📍 Plan Route</div>', unsafe_allow_html=True)

    start_input = st.text_input(
        "Starting Point",
        value=st.session_state.start_name,
        placeholder="Connaught Place, Delhi",
        key="start_field",
    )

    # GPS capture button (HTML component in the left panel)
    st.components.v1.html("""
    <style>
    body { background: transparent; margin: 0; padding: 0; }
    </style>
    <div id="gps-status" style="font-size:11px;color:#6EE7B7;min-height:16px;padding:2px 0 4px;font-family:Outfit,sans-serif;"></div>
    <button onclick="captureGPS()" style="
        background:rgba(16,185,129,0.08);
        border:1px solid rgba(16,185,129,0.25);
        border-radius:10px; color:#6EE7B7;
        padding:9px 14px; font-size:12px; font-weight:600;
        cursor:pointer; font-family:Outfit,sans-serif; width:100%;
        transition:all 0.2s; margin-bottom:4px;
    " onmouseover="this.style.background='rgba(16,185,129,0.16)'"
       onmouseout="this.style.background='rgba(16,185,129,0.08)'">
        📍 Use My Current Location
    </button>
    <script>
    function captureGPS() {
        var st = document.getElementById('gps-status');
        if (!navigator.geolocation) { st.textContent = '❌ Geolocation not supported'; return; }
        st.textContent = '⏳ Acquiring GPS...';
        navigator.geolocation.getCurrentPosition(function(pos) {
            var lat = pos.coords.latitude.toFixed(5);
            var lon = pos.coords.longitude.toFixed(5);
            var acc = Math.round(pos.coords.accuracy);
            st.textContent = '✅ ' + lat + '°N, ' + lon + '°E  (±' + acc + 'm)';
        }, function(err) {
            st.textContent = '❌ ' + err.message;
        }, { enableHighAccuracy: true, timeout: 10000 });
    }
    </script>
    """, height=65, scrolling=False)

    end_input = st.text_input(
        "Destination",
        value=st.session_state.end_name,
        placeholder="Hauz Khas, Delhi",
        key="end_field",
    )

    # Quick-pick chips
    all_places = sorted([k.title() for k in KNOWN_LOCATIONS.keys() if k != "india"])
    chips = "".join(f'<span class="sug-chip">{p}</span>' for p in all_places[:12])
    st.markdown(
        f'<div style="font-size:10px;color:#334155;margin-bottom:5px;text-transform:uppercase;letter-spacing:0.8px;">Popular Locations</div>'
        f'<div class="sug-wrap">{chips}</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    find_btn = st.button("🗺️  Find Best Routes", use_container_width=True, type="primary")

    if find_btn:
        if not start_input.strip() or not end_input.strip():
            st.error("Please enter both starting point and destination.")
        else:
            with st.spinner("Calculating optimal routes..."):
                fastest, safest, status = plan_routes(start_input.strip(), end_input.strip())

            if fastest is None:
                st.error(status)
            else:
                st.session_state.fastest_route   = fastest
                st.session_state.safest_route    = safest
                st.session_state.start_name      = start_input.strip()
                st.session_state.end_name        = end_input.strip()
                st.session_state.start_coords    = fastest.coords[0]
                st.session_state.end_coords      = fastest.coords[-1]
                st.session_state.status_msg      = status
                st.session_state.route_planned   = True
                st.session_state.tracking        = None
                st.session_state.tracking_active = False
                st.session_state.sos_triggered   = False
                mid = fastest.coords[len(fastest.coords) // 2]
                st.session_state.danger_zones    = generate_danger_zones(mid)
                rebuild_map()
                st.rerun()

    if st.session_state.status_msg:
        st.markdown(f'<div class="info-banner" style="margin-top:10px;">{st.session_state.status_msg}</div>', unsafe_allow_html=True)

    # ── Route Options ─────────────────────────────────────────────────────────
    if st.session_state.route_planned:
        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">🛣️ Route Options</div>', unsafe_allow_html=True)

        fastest = st.session_state.fastest_route
        safest  = st.session_state.safest_route
        sel     = st.session_state.selected_route

        def score_color(s):
            return "#10B981" if s >= 75 else "#F59E0B" if s >= 55 else "#EF4444"

        # Fastest
        st.markdown(f"""
        <div class="route-card {'active-fast' if sel == 'fastest' else ''}">
            <div class="route-title">⚡ Fastest Route</div>
            <div class="route-stats">
                <div class="stat-box"><div class="stat-val">{fastest.distance_km}</div><div class="stat-key">km</div></div>
                <div class="stat-box"><div class="stat-val">{fastest.time_min}</div><div class="stat-key">min</div></div>
                <div class="stat-box">
                    <div class="stat-val" style="color:{score_color(fastest.safety_score)}">{fastest.safety_score}</div>
                    <div class="stat-key">safety</div>
                </div>
            </div>
            <div class="safety-tag">{fastest.safety_label}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select Fastest", use_container_width=True, key="btn_fast"):
            st.session_state.selected_route = "fastest"
            rebuild_map(); st.rerun()

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        # Safest
        st.markdown(f"""
        <div class="route-card {'active-safe' if sel == 'safest' else ''}">
            <div class="route-title">🛡️ Safest Route</div>
            <div class="route-stats">
                <div class="stat-box"><div class="stat-val">{safest.distance_km}</div><div class="stat-key">km</div></div>
                <div class="stat-box"><div class="stat-val">{safest.time_min}</div><div class="stat-key">min</div></div>
                <div class="stat-box">
                    <div class="stat-val" style="color:{score_color(safest.safety_score)}">{safest.safety_score}</div>
                    <div class="stat-key">safety</div>
                </div>
            </div>
            <div class="safety-tag">{safest.safety_label}</div>
        </div>
        <div style="font-size:11px;color:#475569;margin-top:6px;padding:0 4px;line-height:1.5;">💡 {safest.safety_explanation}</div>
        """, unsafe_allow_html=True)
        if st.button("Select Safest", use_container_width=True, key="btn_safe"):
            st.session_state.selected_route = "safest"
            rebuild_map(); st.rerun()

        # Map Options
        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">🗺️ Map Options</div>', unsafe_allow_html=True)

        show_heat = st.toggle("Show Danger Heatmap", value=st.session_state.show_heatmap)
        if show_heat != st.session_state.show_heatmap:
            st.session_state.show_heatmap = show_heat
            rebuild_map(); st.rerun()

        # Live Tracking
        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">🚗 Live Tracking</div>', unsafe_allow_html=True)

        offline_mode = st.toggle("Offline / Dead Reckoning", value=st.session_state.offline_mode)
        if offline_mode != st.session_state.offline_mode:
            st.session_state.offline_mode = offline_mode

        tracking        = st.session_state.tracking
        tracking_active = st.session_state.tracking_active

        if not tracking_active:
            if st.button("▶  Start Journey Simulation", use_container_width=True):
                selected = (st.session_state.fastest_route if st.session_state.selected_route == "fastest"
                            else st.session_state.safest_route)
                st.session_state.tracking = init_tracking(selected)
                st.session_state.tracking_active = True
                st.rerun()
        else:
            if st.button("⏹  Stop Simulation", use_container_width=True):
                st.session_state.tracking_active = False
                st.session_state.tracking = None
                rebuild_map(); st.rerun()

        if tracking and tracking_active:
            progress = tracking.progress_pct
            pos      = tracking.current_position
            mode_lbl = "📡 Offline — Dead Reckoning" if st.session_state.offline_mode else "📶 Online — GPS Simulation"

            st.markdown(f"""
            <div class="track-box">
                <div class="track-header">
                    <span class="label">{mode_lbl}</span>
                    <span class="pct">{progress}%</span>
                </div>
                <div class="prog-bar">
                    <div class="prog-fill" style="width:{progress}%;"></div>
                </div>
                <div class="track-pos">📍 {pos[0]:.5f}°N, {pos[1]:.5f}°E</div>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.offline_mode:
                predicted = predict_next_offline(tracking)
                rebuild_map(vehicle_pos=predicted, vehicle_progress=progress)
            else:
                tracking.advance(steps=2)
                rebuild_map(vehicle_pos=tracking.current_position, vehicle_progress=tracking.progress_pct)

            if not tracking.is_active:
                st.success("🏁 You've arrived at your destination!")
                st.session_state.tracking_active = False
            else:
                time.sleep(0.8)
                st.rerun()

        # Emergency SOS
        st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">🆘 Emergency SOS</div>', unsafe_allow_html=True)

        st.markdown("""
        <div style="background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.2);
             border-radius:14px;padding:14px 16px;text-align:center;margin-bottom:8px;">
            <div style="font-family:'Syne',sans-serif;font-size:15px;font-weight:800;color:#EF4444;letter-spacing:2px;">
                SOS  ●  EMERGENCY
            </div>
            <div style="font-size:11px;color:rgba(239,68,68,0.6);margin-top:4px;">
                Instantly alerts all emergency services
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚨 TRIGGER SOS ALERT", use_container_width=True):
            pos = None
            if st.session_state.tracking:
                pos = st.session_state.tracking.current_position
            elif st.session_state.start_coords:
                pos = st.session_state.start_coords
            st.session_state.sos_triggered = True
            st.session_state.sos_response  = trigger_sos(pos)

        if st.session_state.sos_triggered and st.session_state.sos_response:
            resp = st.session_state.sos_response
            st.markdown(f"""
            <div class="sos-response">
                <div style="font-family:'Syne',sans-serif;font-size:13px;font-weight:800;color:#EF4444;margin-bottom:6px;">
                    🚨 SOS Alert Sent — {resp['timestamp']}
                </div>
                <div style="font-size:11px;color:#FCA5A5;margin-bottom:8px;">📍 {resp['location']}</div>
                <div style="font-size:12px;color:#FCA5A5;margin-bottom:10px;">{resp['message']}</div>
            """, unsafe_allow_html=True)
            for name, info in resp["contacts"].items():
                st.markdown(f"""
                <div class="sos-contact">
                    {info['icon']} <b>{name}</b> &nbsp;·&nbsp; {info['number']} &nbsp;·&nbsp; ETA: {info['eta']}
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if st.button("✖ Dismiss SOS"):
                st.session_state.sos_triggered = False
                st.session_state.sos_response  = None
                st.rerun()

    # Sign Out
    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    if st.button("← Sign Out", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# RIGHT PANEL — MAP
# ══════════════════════════════════════════════════════════
with right_col:
    if st.session_state.map_html:
        # Inject Recentre + Live GPS controls into map HTML
        controls_html = """
        <div id="map-controls" style="
            position:fixed; top:80px; right:20px; z-index:99999;
            display:flex; flex-direction:column; gap:8px;
            font-family:Outfit,sans-serif;
        ">
            <button onclick="recenterMap()" style="
                background:rgba(8,12,20,0.9); backdrop-filter:blur(16px);
                border:1px solid rgba(255,255,255,0.15); border-radius:10px;
                color:white; padding:10px 16px; font-size:13px; font-weight:600;
                cursor:pointer; font-family:Outfit,sans-serif;
                display:flex; align-items:center; gap:7px;
                box-shadow:0 4px 24px rgba(0,0,0,0.5);
                transition:all 0.2s;
            " onmouseover="this.style.background='rgba(59,130,246,0.3)'"
               onmouseout="this.style.background='rgba(8,12,20,0.9)'">
                🎯 Recentre
            </button>
            <button id="gps-btn" onclick="toggleLiveGPS()" style="
                background:rgba(8,12,20,0.9); backdrop-filter:blur(16px);
                border:1px solid rgba(16,185,129,0.3); border-radius:10px;
                color:#6EE7B7; padding:10px 16px; font-size:13px; font-weight:600;
                cursor:pointer; font-family:Outfit,sans-serif;
                display:flex; align-items:center; gap:7px;
                box-shadow:0 4px 24px rgba(0,0,0,0.5);
                transition:all 0.2s;
            ">
                📍 Live GPS
            </button>
        </div>
        <div id="gps-toast" style="
            display:none; position:fixed; bottom:28px; left:50%;
            transform:translateX(-50%); z-index:99999;
            background:rgba(8,12,20,0.92); backdrop-filter:blur(16px);
            border:1px solid rgba(16,185,129,0.3); border-radius:99px;
            padding:8px 22px; font-size:12px; color:#6EE7B7; font-weight:600;
            font-family:Outfit,sans-serif; box-shadow:0 4px 24px rgba(0,0,0,0.5);
            transition:all 0.3s;
        ">📍 Tracking your location...</div>

        <script>
        var gpsActive = false, gpsWatchId = null, gpsMarker = null, gpsCircle = null;

        function getMap() {
            var candidates = Object.keys(window).filter(function(k){
                try { return window[k] && window[k].setView && window[k]._container; } catch(e){ return false; }
            });
            return candidates.length ? window[candidates[0]] : null;
        }

        function recenterMap() {
            if (!navigator.geolocation) { alert('Geolocation not supported by your browser.'); return; }
            navigator.geolocation.getCurrentPosition(function(pos) {
                var map = getMap();
                if (map) map.setView([pos.coords.latitude, pos.coords.longitude], 15);
            }, function(e){ alert('Location error: ' + e.message); }, { enableHighAccuracy: true });
        }

        function toggleLiveGPS() {
            gpsActive = !gpsActive;
            var btn = document.getElementById('gps-btn');
            var toast = document.getElementById('gps-toast');
            if (gpsActive) {
                btn.style.background = 'rgba(16,185,129,0.18)';
                btn.style.color = '#10B981';
                btn.textContent = '🟢 GPS Active';
                toast.style.display = 'block';
                startWatch();
            } else {
                btn.style.background = 'rgba(8,12,20,0.9)';
                btn.style.color = '#6EE7B7';
                btn.textContent = '📍 Live GPS';
                toast.style.display = 'none';
                stopWatch();
            }
        }

        function startWatch() {
            if (!navigator.geolocation) return;
            gpsWatchId = navigator.geolocation.watchPosition(function(pos) {
                placeGPSMarker(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy);
            }, null, { enableHighAccuracy: true });
        }

        function stopWatch() {
            if (gpsWatchId !== null) { navigator.geolocation.clearWatch(gpsWatchId); gpsWatchId = null; }
            var map = getMap();
            if (map) {
                if (gpsMarker) { map.removeLayer(gpsMarker); gpsMarker = null; }
                if (gpsCircle) { map.removeLayer(gpsCircle); gpsCircle = null; }
            }
        }

        function placeGPSMarker(lat, lon, acc) {
            var map = getMap();
            if (!map || typeof L === 'undefined') return;
            if (gpsMarker) {
                gpsMarker.setLatLng([lat, lon]);
                if (gpsCircle) gpsCircle.setLatLng([lat, lon]).setRadius(acc);
            } else {
                gpsCircle = L.circle([lat, lon], { radius: acc, color: '#3B82F6', fillColor: '#3B82F6', fillOpacity: 0.08, weight: 1 }).addTo(map);
                gpsMarker = L.circleMarker([lat, lon], {
                    radius: 10, fillColor: '#3B82F6', color: '#fff', weight: 3, opacity: 1, fillOpacity: 0.95
                }).addTo(map).bindPopup('<b>📍 You are here</b><br>Accuracy: ±' + Math.round(acc) + 'm');
            }
            map.setView([lat, lon], Math.max(map.getZoom(), 14));
        }
        </script>
        """

        enhanced_map = st.session_state.map_html.replace("</body>", controls_html + "</body>")

        st.components.v1.html(enhanced_map, height=870, scrolling=False)

    else:
        st.markdown("""
        <div style="
            height:calc(100vh - 60px);
            display:flex; flex-direction:column;
            align-items:center; justify-content:center;
            background:radial-gradient(ellipse at 50% 40%, rgba(59,130,246,0.05) 0%, transparent 60%);
            gap:18px;
        ">
            <div style="font-size:88px; opacity:0.15; animation:float 4s ease infinite;">🗺️</div>
            <div style="font-family:'Syne',sans-serif; font-size:28px; font-weight:800; color:#1E293B; letter-spacing:-1px;">
                Your Journey Starts Here
            </div>
            <div style="font-size:14px; color:#334155; text-align:center; max-width:320px; line-height:1.8;">
                Enter your <b style="color:#475569;">starting point</b> and
                <b style="color:#475569;">destination</b> in the panel,
                then tap <b style="color:#475569;">Find Best Routes</b>.
            </div>
            <div style="display:flex; gap:10px; flex-wrap:wrap; justify-content:center; margin-top:12px;">
                <div style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:99px;padding:8px 18px;font-size:12px;color:#475569;font-weight:500;">⚡ Fastest Route</div>
                <div style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:99px;padding:8px 18px;font-size:12px;color:#475569;font-weight:500;">🛡️ Safest Route</div>
                <div style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:99px;padding:8px 18px;font-size:12px;color:#475569;font-weight:500;">📍 Real GPS</div>
                <div style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:99px;padding:8px 18px;font-size:12px;color:#475569;font-weight:500;">🚨 SOS Alert</div>
                <div style="background:#111827;border:1px solid rgba(255,255,255,0.08);border-radius:99px;padding:8px 18px;font-size:12px;color:#475569;font-weight:500;">🌡️ Danger Zones</div>
            </div>
        </div>
        <style>
        @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-12px)} }
        </style>
        """, unsafe_allow_html=True)
