"""
geo_utils.py - Geocoding utilities for SAFAR with fallback, retry, and known locations
"""

import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Hardcoded known locations for reliability (India-focused)
KNOWN_LOCATIONS = {
    # Delhi
    "connaught place": (28.6315, 77.2167),
    "india gate": (28.6129, 77.2295),
    "red fort": (28.6562, 77.2410),
    "new delhi railway station": (28.6431, 77.2194),
    "delhi airport": (28.5665, 77.1031),
    "indira gandhi international airport": (28.5665, 77.1031),
    "igi airport": (28.5665, 77.1031),
    "chandni chowk": (28.6506, 77.2310),
    "lajpat nagar": (28.5700, 77.2430),
    "saket": (28.5244, 77.2167),
    "hauz khas": (28.5431, 77.2034),
    "dwarka": (28.5921, 77.0460),
    "rohini": (28.7390, 77.1308),
    "janakpuri": (28.6219, 77.0827),

    # Mumbai
    "gateway of india": (18.9220, 72.8347),
    "mumbai airport": (19.0896, 72.8656),
    "chhatrapati shivaji terminus": (18.9398, 72.8355),
    "cst station": (18.9398, 72.8355),
    "bandra": (19.0596, 72.8295),
    "andheri": (19.1136, 72.8697),
    "juhu beach": (19.0979, 72.8264),
    "marine drive": (18.9438, 72.8235),
    "dadar": (19.0176, 72.8439),
    "borivali": (19.2309, 72.8567),
    "powai": (19.1176, 72.9060),

    # Bangalore
    "majestic bangalore": (12.9766, 77.5713),
    "koramangala": (12.9352, 77.6245),
    "indiranagar": (12.9784, 77.6408),
    "whitefield": (12.9698, 77.7499),
    "electronic city": (12.8399, 77.6770),
    "marathahalli": (12.9591, 77.6974),
    "bangalore airport": (13.1986, 77.7066),
    "mg road bangalore": (12.9757, 77.6095),
    "hsr layout": (12.9116, 77.6370),
    "yelahanka": (13.1007, 77.5963),

    # Chennai
    "marina beach": (13.0500, 80.2824),
    "chennai central": (13.0827, 80.2707),
    "t nagar": (13.0418, 80.2341),
    "anna nagar": (13.0891, 80.2099),
    "chennai airport": (12.9941, 80.1709),
    "adyar": (13.0012, 80.2565),

    # Hyderabad
    "charminar": (17.3616, 78.4747),
    "hitech city": (17.4435, 78.3772),
    "banjara hills": (17.4153, 78.4480),
    "jubilee hills": (17.4310, 78.4071),
    "hyderabad airport": (17.2403, 78.4294),
    "secunderabad station": (17.4399, 78.4983),

    # Ahmedabad
    "sabarmati ashram": (23.0602, 72.5827),
    "law garden": (23.0332, 72.5560),
    "ahmedabad airport": (23.0773, 72.6347),
    "gujarat university": (23.0388, 72.5507),
    "cg road ahmedabad": (23.0368, 72.5586),
    "sg highway": (23.0013, 72.5071),

    # Pune
    "shaniwar wada": (18.5195, 73.8553),
    "pune station": (18.5280, 73.8742),
    "hinjewadi": (18.5914, 73.7380),
    "koregaon park": (18.5362, 73.8939),
    "pune airport": (18.5822, 73.9197),
    "fc road pune": (18.5237, 73.8479),

    # Kolkata
    "victoria memorial": (22.5448, 88.3426),
    "howrah station": (22.5851, 88.3425),
    "park street kolkata": (22.5535, 88.3522),
    "salt lake": (22.5841, 88.4105),
    "kolkata airport": (22.6520, 88.4463),
    "new town kolkata": (22.5841, 88.4678),

    # Generic
    "india": (20.5937, 78.9629),
}


def normalize_key(text: str) -> str:
    return text.strip().lower()


def get_known_location(place: str):
    key = normalize_key(place)
    if key in KNOWN_LOCATIONS:
        return KNOWN_LOCATIONS[key]
    # Partial match
    for known_key, coords in KNOWN_LOCATIONS.items():
        if known_key in key or key in known_key:
            return coords
    return None


def geocode_with_retry(place: str, retries: int = 3, delay: float = 1.5):
    """
    Try to geocode a place name. First checks known locations,
    then tries Nominatim with retry logic and city/India context fallback.
    Returns (lat, lon) tuple or None.
    """
    # 1. Check hardcoded known locations
    known = get_known_location(place)
    if known:
        return known

    geolocator = Nominatim(user_agent="safar_navigation_app_v1", timeout=10)

    # 2. Try exact query
    for attempt in range(retries):
        try:
            location = geolocator.geocode(place)
            if location:
                return (location.latitude, location.longitude)
            break
        except GeocoderTimedOut:
            if attempt < retries - 1:
                time.sleep(delay)
        except GeocoderServiceError:
            break

    # 3. Fallback: append ", India"
    fallback_query = f"{place}, India"
    for attempt in range(retries):
        try:
            location = geolocator.geocode(fallback_query)
            if location:
                return (location.latitude, location.longitude)
            break
        except GeocoderTimedOut:
            if attempt < retries - 1:
                time.sleep(delay)
        except GeocoderServiceError:
            break

    return None


def get_place_suggestions(partial: str) -> list:
    """Return matching known locations for autocomplete."""
    key = normalize_key(partial)
    if len(key) < 2:
        return []
    suggestions = [
        k.title() for k in KNOWN_LOCATIONS
        if key in k
    ]
    return suggestions[:8]
