"""
Inverse Distance Weighting interpolatie — vervangt PyKrige/scipy.
Geen compilatie nodig, pure numpy. Visueel vergelijkbaar resultaat.
"""
import base64
import io
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

N_LAT = 80
N_LON = 120
IDW_POWER = 2.5


def run_kriging(
    points: List[Dict],
    bounds: Tuple[float, float, float, float],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """IDW interpolatie op NL kustgrid.

    bounds = (lat_min, lat_max, lon_min, lon_max)
    Returns: (z_pred, grid_lat, grid_lon)
    """
    lat_min, lat_max, lon_min, lon_max = bounds

    lats = np.array([p["lat"] for p in points], dtype=np.float32)
    lons = np.array([p["lon"] for p in points], dtype=np.float32)
    scores = np.array([p["score"] for p in points], dtype=np.float32)

    grid_lat = np.linspace(lat_min, lat_max, N_LAT, dtype=np.float32)
    grid_lon = np.linspace(lon_min, lon_max, N_LON, dtype=np.float32)

    # Vectoriseerd IDW: (N_LAT, N_LON, N_points)
    glat, glon = np.meshgrid(grid_lat, grid_lon, indexing="ij")

    dlat = glat[:, :, np.newaxis] - lats[np.newaxis, np.newaxis, :]
    dlon = glon[:, :, np.newaxis] - lons[np.newaxis, np.newaxis, :]
    dist = np.sqrt(dlat ** 2 + dlon ** 2)
    dist = np.maximum(dist, 1e-8)

    w = 1.0 / dist ** IDW_POWER
    z = np.sum(w * scores, axis=2) / np.sum(w, axis=2)

    return z.astype(np.float64), grid_lat, grid_lon


def scores_to_png(z: np.ndarray) -> str:
    """Converteer 2D score-array naar base64 PNG (rood → geel → groen).

    Rij 0 = noord na FLIP_TOP_BOTTOM, klopt met Mapbox/Leaflet image overlay.
    """
    z_norm = np.clip(z, 0.0, 100.0).astype(np.float32)

    hue_deg = z_norm / 100.0 * 120.0
    H = hue_deg / 60.0
    hi = H.astype(np.int32) % 6
    f = H - np.floor(H)

    v, s = 0.90, 0.85
    p = v * (1 - s)
    q = (v * (1 - s * f)).astype(np.float32)
    t_val = (v * (1 - s * (1 - f))).astype(np.float32)

    r = np.where(hi == 0, v, q)
    g = np.where(hi == 0, t_val, v)
    b = np.full_like(z_norm, p)

    r_u8 = np.clip(r * 255, 0, 255).astype(np.uint8)
    g_u8 = np.clip(g * 255, 0, 255).astype(np.uint8)
    b_u8 = np.clip(b * 255, 0, 255).astype(np.uint8)
    a_u8 = np.full(z.shape, 165, dtype=np.uint8)

    rgba = np.stack([r_u8, g_u8, b_u8, a_u8], axis=-1)
    img = Image.fromarray(rgba, "RGBA").transpose(Image.FLIP_TOP_BOTTOM)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()
