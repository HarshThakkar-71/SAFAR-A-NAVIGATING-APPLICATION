"""
safar_core.py - Core logic for SAFAR: routing, safety scoring, simulation, SOS
"""

import math
import random
import time
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from geo_utils import geocode_with_retry
from graph_loader import (
    load_graph, get_nearest_node, get_shortest_path_nodes,
    nodes_to_coords, path_length_km
)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RouteInfo:
    name: str
    coords: List[Tuple[float, float]]
    distance_km: float
    time_min: float
    safety_score: float          # 0–100
    safety_label: str
    safety_explanation: str
    color: str = "#2563EB"


@dataclass
class TrackingState:
    route_coords: List[Tuple[float, float]] = field(default_factory=list)
    current_index: int = 0
    is_active: bool = False
    offline_mode: bool = False
    last_known: Optional[Tuple[float, float]] = None

    @property
    def current_position(self):
        if not self.route_coords:
            return self.last_known
        idx = min(self.current_index, len(self.route_coords) - 1)
        return self.route_coords[idx]

    @property
    def progress_pct(self):
        if not self.route_coords:
            return 0
        return int(100 * self.current_index / max(len(self.route_coords) - 1, 1))

    def advance(self, steps: int = 1):
        if self.is_active and self.route_coords:
            self.current_index = min(
                self.current_index + steps,
                len(self.route_coords) - 1
            )
            self.last_known = self.current_position
            if self.current_index >= len(self.route_coords) - 1:
                self.is_active = False


# ---------------------------------------------------------------------------
# Safety scoring helpers
# ---------------------------------------------------------------------------

SAFETY_ZONES = {
    # high safety coords (approximate bounding boxes omitted for simplicity)
    # Score modifiers will be computed pseudo-randomly but deterministically
}

SAFETY_REASONS_HIGH = [
    "Well-lit main roads with heavy traffic",
    "Passes through commercial and busy areas",
    "Avoids isolated or poorly-lit stretches",
    "High police patrol frequency in this corridor",
    "Well-covered by CCTV surveillance",
]

SAFETY_REASONS_MEDIUM = [
    "Mix of busy streets and quieter lanes",
    "Some sections have limited lighting at night",
    "Moderate pedestrian activity throughout",
    "Partially covered by traffic cameras",
]

SAFETY_REASONS_LOW = [
    "Passes through low-lit residential areas",
    "Some isolated road sections at night",
    "Lower patrol density on this route",
    "Limited CCTV coverage on certain stretches",
]


def _deterministic_score(coords: list, seed_offset: float = 0) -> float:
    """Generate a deterministic but realistic safety score from route coords."""
    if not coords:
        return 70.0
    mid = coords[len(coords) // 2]
    raw = (abs(math.sin(mid[0] * 1000 + seed_offset)) * 35) + 55
    return round(min(max(raw, 45), 97), 1)


def compute_safety(coords: list, route_type: str = "fastest") -> Tuple[float, str, str]:
    """
    Returns (score, label, explanation).
    Safest route gets a bonus.
    """
    base = _deterministic_score(coords, seed_offset=0 if route_type == "fastest" else 42)
    if route_type == "safest":
        base = min(base + 12, 98)

    if base >= 80:
        label = "🟢 High Safety"
        explanation = random.choice(SAFETY_REASONS_HIGH)
    elif base >= 60:
        label = "🟡 Moderate Safety"
        explanation = random.choice(SAFETY_REASONS_MEDIUM)
    else:
        label = "🔴 Lower Safety"
        explanation = random.choice(SAFETY_REASONS_LOW)

    return round(base, 1), label, explanation


# ---------------------------------------------------------------------------
# Route interpolation (straight-line fallback)
# ---------------------------------------------------------------------------

def _interpolate_route(
    start: Tuple[float, float],
    end: Tuple[float, float],
    n_points: int = 40,
    variance: float = 0.003
) -> List[Tuple[float, float]]:
    """
    Create a smooth curved route between two points with slight randomness.
    Used as fallback when OSMnx graph is unavailable.
    """
    points = []
    rng = random.Random(hash((round(start[0], 3), round(end[0], 3))))

    for i in range(n_points + 1):
        t = i / n_points
        lat = start[0] + t * (end[0] - start[0])
        lon = start[1] + t * (end[1] - start[1])
        # Add gentle curve
        if 0 < i < n_points:
            lat += rng.uniform(-variance, variance) * math.sin(math.pi * t)
            lon += rng.uniform(-variance, variance) * math.sin(math.pi * t)
        points.append((lat, lon))
    return points


def _haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    R = 6371
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(h))


def _total_distance(coords: list) -> float:
    if len(coords) < 2:
        return 0.0
    return sum(_haversine_km(coords[i], coords[i+1]) for i in range(len(coords)-1))


# ---------------------------------------------------------------------------
# Main routing function
# ---------------------------------------------------------------------------

def plan_routes(
    start_name: str,
    end_name: str,
    use_graph: bool = True
) -> Tuple[Optional[RouteInfo], Optional[RouteInfo], str]:
    """
    Returns (fastest_route, safest_route, status_message).
    Both routes may be None on failure.
    """
    # Geocode
    start_coords = geocode_with_retry(start_name)
    if not start_coords:
        return None, None, f"❌ Could not find location: '{start_name}'. Try a more specific name."

    end_coords = geocode_with_retry(end_name)
    if not end_coords:
        return None, None, f"❌ Could not find location: '{end_name}'. Try a more specific name."

    if _haversine_km(start_coords, end_coords) < 0.05:
        return None, None, "❌ Start and destination are the same (or too close). Please choose different locations."

    graph_used = False
    fastest_coords = None
    safest_coords = None

    # Try OSMnx graph routing
    if use_graph:
        mid_lat = (start_coords[0] + end_coords[0]) / 2
        mid_lon = (start_coords[1] + end_coords[1]) / 2
        dist_km = _haversine_km(start_coords, end_coords)
        graph_dist = min(int(dist_km * 1000 * 1.5) + 2000, 8000)

        G, err = load_graph(mid_lat, mid_lon, dist=graph_dist)
        if G is not None:
            origin_node = get_nearest_node(G, *start_coords)
            dest_node = get_nearest_node(G, *end_coords)

            fast_nodes = get_shortest_path_nodes(G, origin_node, dest_node, weight="length")
            if fast_nodes:
                fastest_coords = nodes_to_coords(G, fast_nodes)
                graph_used = True

            # Safest = slightly longer path (travel_time weight or length with detour)
            # Simulate by taking a slightly perturbed graph route
            safe_nodes = get_shortest_path_nodes(G, origin_node, dest_node, weight="travel_time")
            if safe_nodes:
                safest_coords = nodes_to_coords(G, safe_nodes)
            elif fastest_coords:
                safest_coords = fastest_coords  # fallback same

    # Fallback to interpolated routes
    if not fastest_coords:
        fastest_coords = _interpolate_route(start_coords, end_coords, n_points=50, variance=0.002)

    if not safest_coords:
        # Safest route takes a slight detour
        safest_coords = _interpolate_route(start_coords, end_coords, n_points=60, variance=0.004)

    # Compute distances
    fast_dist = _total_distance(fastest_coords)
    safe_dist = _total_distance(safest_coords)

    # Estimate time: avg 35 km/h urban
    fast_time = round(fast_dist / 35 * 60, 1)
    safe_time = round(safe_dist / 35 * 60, 1)

    # Safety scores
    fast_score, fast_label, fast_exp = compute_safety(fastest_coords, "fastest")
    safe_score, safe_label, safe_exp = compute_safety(safest_coords, "safest")

    status = "✅ Routes planned using real road network." if graph_used else "✅ Routes planned (estimated path — install osmnx for real roads)."

    fastest_route = RouteInfo(
        name="Fastest Route",
        coords=fastest_coords,
        distance_km=round(fast_dist, 2),
        time_min=fast_time,
        safety_score=fast_score,
        safety_label=fast_label,
        safety_explanation=fast_exp,
        color="#2563EB",
    )

    safest_route = RouteInfo(
        name="Safest Route",
        coords=safest_coords,
        distance_km=round(safe_dist, 2),
        time_min=safe_time,
        safety_score=safe_score,
        safety_label=safe_label,
        safety_explanation=safe_exp,
        color="#16A34A",
    )

    return fastest_route, safest_route, status


# ---------------------------------------------------------------------------
# Live tracking simulation
# ---------------------------------------------------------------------------

def init_tracking(route: RouteInfo) -> TrackingState:
    return TrackingState(
        route_coords=route.coords,
        current_index=0,
        is_active=True,
        last_known=route.coords[0] if route.coords else None,
    )


def predict_next_offline(state: TrackingState) -> Tuple[float, float]:
    """Dead reckoning: predict next position when offline."""
    if not state.route_coords or state.current_index >= len(state.route_coords) - 1:
        return state.last_known or (0, 0)
    # Return next point on route as prediction
    return state.route_coords[min(state.current_index + 2, len(state.route_coords) - 1)]


# ---------------------------------------------------------------------------
# Emergency SOS
# ---------------------------------------------------------------------------

EMERGENCY_CONTACTS = {
    "Police": {"number": "100", "eta": "8-12 minutes", "icon": "🚔"},
    "Ambulance": {"number": "108", "eta": "10-15 minutes", "icon": "🚑"},
    "Fire Brigade": {"number": "101", "eta": "12-18 minutes", "icon": "🚒"},
    "Women Helpline": {"number": "1091", "eta": "Immediate call", "icon": "📞"},
    "Disaster Mgmt": {"number": "1078", "eta": "15-20 minutes", "icon": "🆘"},
}

def trigger_sos(current_position: Optional[Tuple[float, float]] = None) -> dict:
    """Simulate SOS response."""
    loc_str = (
        f"{current_position[0]:.4f}°N, {current_position[1]:.4f}°E"
        if current_position else "Unknown"
    )
    return {
        "timestamp": time.strftime("%H:%M:%S"),
        "location": loc_str,
        "contacts": EMERGENCY_CONTACTS,
        "message": "Emergency alert sent! Help is on the way. Stay calm and stay where you are.",
    }


# ---------------------------------------------------------------------------
# Danger heatmap simulation
# ---------------------------------------------------------------------------

def generate_danger_zones(center: Tuple[float, float], n: int = 8) -> List[dict]:
    """Generate simulated danger hotspots around a center point."""
    rng = random.Random(hash((round(center[0], 2), round(center[1], 2))))
    zones = []
    for _ in range(n):
        lat = center[0] + rng.uniform(-0.025, 0.025)
        lon = center[1] + rng.uniform(-0.025, 0.025)
        intensity = rng.choice(["low", "medium", "high"])
        zones.append({
            "lat": lat, "lon": lon,
            "intensity": intensity,
            "radius": rng.randint(150, 400),
        })
    return zones
