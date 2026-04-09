"""
graph_loader.py - Map graph loading using OSMnx with caching and fallbacks
"""

import os
import pickle
import hashlib
import streamlit as st

try:
    import osmnx as ox
    import networkx as nx
    OSMNX_AVAILABLE = True
except ImportError:
    OSMNX_AVAILABLE = False

CACHE_DIR = ".safar_cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_key(lat: float, lon: float, dist: int) -> str:
    raw = f"{lat:.4f}_{lon:.4f}_{dist}"
    return hashlib.md5(raw.encode()).hexdigest()


def load_graph(lat: float, lon: float, dist: int = 3000):
    """
    Load a walkable/drivable OSM graph around a point.
    Uses disk cache to avoid re-downloading. Falls back gracefully.
    Returns (graph, error_message).
    """
    if not OSMNX_AVAILABLE:
        return None, "OSMnx not installed. Install with: pip install osmnx"

    key = _cache_key(lat, lon, dist)
    cache_path = os.path.join(CACHE_DIR, f"graph_{key}.pkl")

    # Try loading from cache
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                G = pickle.load(f)
            return G, None
        except Exception:
            pass  # Corrupt cache, re-download

    # Download from OSM
    try:
        ox.settings.log_console = False
        ox.settings.use_cache = True
        G = ox.graph_from_point((lat, lon), dist=dist, network_type="drive")
        # Save to cache
        with open(cache_path, "wb") as f:
            pickle.dump(G, f)
        return G, None
    except Exception as e:
        return None, f"Graph download failed: {str(e)}"


def get_nearest_node(G, lat: float, lon: float):
    """Get nearest OSM node to a lat/lon coordinate."""
    if not OSMNX_AVAILABLE or G is None:
        return None
    try:
        import osmnx as ox
        return ox.distance.nearest_nodes(G, lon, lat)
    except Exception:
        return None


def get_shortest_path_nodes(G, origin_node, dest_node, weight="length"):
    """Return list of nodes in shortest path or None."""
    if G is None or origin_node is None or dest_node is None:
        return None
    try:
        import networkx as nx
        return nx.shortest_path(G, origin_node, dest_node, weight=weight)
    except nx.NetworkXNoPath:
        return None
    except Exception:
        return None


def nodes_to_coords(G, node_list: list) -> list:
    """Convert list of OSM node IDs to list of (lat, lon) tuples."""
    if G is None or not node_list:
        return []
    coords = []
    for node in node_list:
        data = G.nodes[node]
        coords.append((data["y"], data["x"]))
    return coords


def path_length_km(G, node_list: list) -> float:
    """Compute total path length in km."""
    if not OSMNX_AVAILABLE or G is None or not node_list or len(node_list) < 2:
        return 0.0
    try:
        import osmnx as ox
        length_m = sum(
            ox.utils_graph.get_route_edge_attributes(G, node_list, "length")
        )
        return length_m / 1000.0
    except Exception:
        return 0.0
