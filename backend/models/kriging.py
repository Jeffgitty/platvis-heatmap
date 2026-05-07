import base64
import io
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image
from pykrige.ok import OrdinaryKriging

# Output raster resolutie (pixels)
N_LAT = 80
N_LON = 120


def run_kriging(
    points: List[Dict],
    bounds: Tuple[float, float, float, float],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Ordinary Kriging interpolatie op NL kustgrid.

    bounds = (lat_min, lat_max, lon_min, lon_max)
    Returns: (z_pred, grid_lat, grid_lon)
    """
    lat_min, lat_max, lon_min, lon_max = bounds

    lons = np.array([p["lon"] for p in points], dtype=float)
    lats = np.array([p["lat"] for p in points], dtype=float)
    scores = np.array([p["score"] for p in points], dtype=float)

    grid_lat = np.linspace(lat_min, lat_max, N_LAT)
    grid_lon = np.linspace(lon_min, lon_max, N_LON)

    # Expliciete variogram parameters zodat kriging goede ruimtelijke
    # interpolatie geeft ook bij dataconcentratie langs de kust.
    # psill = data-variantie, range = ~1 graad (~111 km), nugget klein.
    psill = float(np.var(scores))
    if psill < 1.0:
        psill = 50.0  # fallback als alle scores gelijk zijn
    vparams = [psill, 1.0, psill * 0.05]  # [psill, range_deg, nugget]

    OK = OrdinaryKriging(
        lons,
        lats,
        scores,
        variogram_model="spherical",
        variogram_parameters=vparams,
        verbose=False,
        enable_plotting=False,
    )
    z_pred, _ = OK.execute("grid", grid_lon, grid_lat)
    return z_pred, grid_lat, grid_lon


def scores_to_png(z: np.ndarray) -> str:
    """Converteer 2D score-array naar base64 PNG met kleurcodering.

    Kleurschema: rood (laag) → geel → groen (hoog).
    Afbeelding wordt verticaal gespiegeld: rij 0 = noord (voor Mapbox image overlay).
    """
    z_norm = np.clip(z, 0.0, 100.0)

    # HSV-benadering: hue 0° (rood) → 120° (groen) via score 0→100
    hue_deg = z_norm / 100.0 * 120.0  # 0–120 graden
    H = hue_deg / 60.0  # 0–2
    hi = H.astype(int) % 6
    f = H - np.floor(H)

    v = 0.90
    s = 0.85
    p = v * (1 - s)
    q = v * (1 - s * f)
    t_val = v * (1 - s * (1 - f))

    # hi==0: rood-geel, hi==1: geel-groen (enige twee zones in 0–120°)
    r = np.where(hi == 0, v, q)
    g = np.where(hi == 0, t_val, v)
    b = np.full_like(z_norm, p)

    r_u8 = np.clip(r * 255, 0, 255).astype(np.uint8)
    g_u8 = np.clip(g * 255, 0, 255).astype(np.uint8)
    b_u8 = np.clip(b * 255, 0, 255).astype(np.uint8)
    a_u8 = np.full(z.shape, 165, dtype=np.uint8)

    rgba = np.stack([r_u8, g_u8, b_u8, a_u8], axis=-1)
    img = Image.fromarray(rgba, "RGBA")
    img = img.transpose(Image.FLIP_TOP_BOTTOM)  # rij 0 = noord

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()
