import numpy as np
from typing import List, Dict

# Vereenvoudigde NL kustlijn: (lon, lat) ankerpunten van Zeeland → Wadden
COAST_SEGMENTS = [
    (3.53, 51.38),  # Westerschelde monding
    (3.72, 51.55),  # Oosterschelde
    (3.95, 51.72),  # Goeree-Overflakkee W
    (4.05, 51.87),  # Hoek van Holland N
    (4.12, 51.98),  # Hoek van Holland
    (4.20, 52.07),  # Monster
    (4.26, 52.12),  # Kijkduin
    (4.42, 52.20),  # Katwijk
    (4.58, 52.46),  # IJmuiden
    (4.70, 52.72),  # Bergen aan Zee
    (4.75, 52.97),  # Den Helder
    (4.78, 53.02),  # Callantsoog
    (4.76, 53.12),  # Texel Z
    (4.75, 53.19),  # Texel NW
    (5.10, 53.28),  # Vlieland
    (5.40, 53.36),  # Terschelling W
    (5.80, 53.40),  # Ameland W
    (6.20, 53.46),  # Schiermonnikoog W
    (7.00, 53.47),  # Borkum richting
]


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Afstand in km tussen twee lat/lon punten."""
    R = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


def distance_to_coast(lat: float, lon: float) -> float:
    """Minimale haversine-afstand (km) tot NL kustsegmenten."""
    min_dist = float("inf")
    for i in range(len(COAST_SEGMENTS) - 1):
        lon1, lat1 = COAST_SEGMENTS[i]
        lon2, lat2 = COAST_SEGMENTS[i + 1]
        dx, dy = lon2 - lon1, lat2 - lat1
        if dx == 0 and dy == 0:
            d = haversine(lat, lon, lat1, lon1)
        else:
            t = ((lon - lon1) * dx + (lat - lat1) * dy) / (dx * dx + dy * dy)
            t = max(0.0, min(1.0, t))
            proj_lon = lon1 + t * dx
            proj_lat = lat1 + t * dy
            d = haversine(lat, lon, proj_lat, proj_lon)
        if d < min_dist:
            min_dist = d
    return min_dist


def estimate_depth(dist_km: float) -> float:
    """Schat waterdiepte (m) op basis van afstand tot kust."""
    if dist_km < 2:
        return 1.0 + dist_km * 1.5
    elif dist_km < 10:
        return 4.0 + (dist_km - 2) * 1.2
    elif dist_km < 25:
        return 14.0 + (dist_km - 10) * 0.8
    else:
        return 26.0 + (dist_km - 25) * 0.4


def generate_coastal_grid(resolution: float = 0.07) -> List[Dict]:
    """Genereer kustpunten langs NL kust (0.5–40 km offshore)."""
    lat_min, lat_max = 51.2, 53.7
    lon_min, lon_max = 3.0, 7.5

    lats = np.arange(lat_min, lat_max, resolution)
    lons = np.arange(lon_min, lon_max, resolution)

    points = []
    for lat in lats:
        for lon in lons:
            dist_km = distance_to_coast(float(lat), float(lon))
            if 0.5 <= dist_km <= 40.0:
                depth = estimate_depth(dist_km)
                points.append(
                    {
                        "lat": round(float(lat), 4),
                        "lon": round(float(lon), 4),
                        "dist_km": round(float(dist_km), 2),
                        "depth_m": round(float(depth), 1),
                    }
                )
    return points
