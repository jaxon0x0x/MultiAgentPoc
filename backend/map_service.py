import geocoder
import folium
import os
import time
from typing import List, Optional

MAP_FILENAME = "map.html"


def _save_map(m: folium.Map) -> str:
    map_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "public"))
    os.makedirs(map_dir, exist_ok=True)
    map_path = os.path.join(map_dir, MAP_FILENAME)
    m.save(map_path)
    return f"/{MAP_FILENAME}?t={int(time.time())}"


def create_map() -> Optional[dict]:
    g = geocoder.ip("me")
    if not g.latlng:
        return None

    latlng = g.latlng
    m = folium.Map(location=latlng, zoom_start=13, tiles="OpenStreetMap")
    folium.Marker(latlng, popup="Your Location", tooltip="Current location").add_to(m)
    map_url = _save_map(m)

    return {
        "map_url": map_url,
        "latlng": latlng,
        "source": "ip",
    }


# def create_map_with_coords(latlng: List[float]) -> Optional[dict]:
#     if not latlng or len(latlng) != 2:
#         return None
#
#     m = folium.Map(location=latlng, zoom_start=15, tiles="OpenStreetMap")
#     folium.Marker(latlng, popup="Precise Location", tooltip="User provided location").add_to(m)
#     map_url = _save_map(m)
#
#     return {
#         "map_url": map_url,
#         "latlng": latlng,
#         "source": "user",
#     }


