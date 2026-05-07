import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from models.data_fetchers import fetch_tide, fetch_weather
from models.fish_score import calculate_fish_score, get_score_explanation
from models.grid import distance_to_coast, estimate_depth, generate_coastal_grid
from models.kriging import run_kriging, scores_to_png

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("platvis")

CACHE_TTL = 300  # seconden
BOUNDS = (51.2, 53.7, 3.0, 7.5)  # lat_min, lat_max, lon_min, lon_max

_grid: list = []
_cache: dict = {"data": None, "ts": 0.0}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _grid
    log.info("Kustgrid genereren...")
    _grid = generate_coastal_grid(resolution=0.07)
    log.info(f"Grid klaar: {len(_grid)} kustpunten")
    yield


app = FastAPI(title="Platvis Heatmap API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "points": len(_grid)}


@app.get("/heatmap")
async def get_heatmap():
    global _cache

    now = time.time()
    if _cache["data"] and (now - _cache["ts"]) < CACHE_TTL:
        log.info("Cache hit")
        return _cache["data"]

    log.info("Heatmap berekenen...")
    t0 = time.time()

    weather, tide = await asyncio.gather(fetch_weather(), fetch_tide())
    dt = datetime.utcnow()

    # Score elk kustpunt
    scored: list[dict] = []
    for p in _grid:
        s = calculate_fish_score(
            depth_m=p["depth_m"],
            dist_km=p["dist_km"],
            tide=tide,
            weather=weather,
            dt=dt,
        )
        scored.append({**p, "score": round(s, 1)})

    # Kriging interpolatie → PNG
    try:
        z, _, _ = run_kriging(scored, BOUNDS)
        png_b64 = scores_to_png(z)
    except Exception as exc:
        log.warning(f"Kriging mislukt: {exc} — geen surface beschikbaar")
        png_b64 = None

    # Top 5 beste punten
    top5 = sorted(scored, key=lambda x: x["score"], reverse=True)[:5]
    avg = sum(p["score"] for p in scored) / len(scored) if scored else 0

    result = {
        "surface": {
            "image_b64": png_b64,
            "bounds": {
                "north": BOUNDS[1],
                "south": BOUNDS[0],
                "west": BOUNDS[2],
                "east": BOUNDS[3],
            },
        },
        "points": top5,
        "weather": weather,
        "tide": tide,
        "avg_score": round(avg, 1),
        "best_score": round(top5[0]["score"], 1) if top5 else 0,
        "explanation": get_score_explanation(avg, top5[0] if top5 else {}, tide, weather),
        "timestamp": dt.isoformat(),
    }

    _cache = {"data": result, "ts": now}
    log.info(f"Heatmap klaar in {time.time() - t0:.1f}s | beste score: {result['best_score']}")
    return result


@app.get("/score")
async def get_score(
    lat: float = Query(..., ge=50.0, le=54.5),
    lon: float = Query(..., ge=2.0, le=8.0),
):
    """Bereken viskans voor één aangeklikte locatie."""
    dist_km = distance_to_coast(lat, lon)

    if dist_km > 60:
        raise HTTPException(status_code=400, detail="Locatie te ver van de Nederlandse kust")

    depth_m = estimate_depth(dist_km)
    dt = datetime.utcnow()

    # Hergebruik gecachte weer/getij indien beschikbaar
    if _cache["data"]:
        tide = _cache["data"]["tide"]
        weather = _cache["data"]["weather"]
    else:
        weather, tide = await asyncio.gather(fetch_weather(lat, lon), fetch_tide())

    score = calculate_fish_score(depth_m, dist_km, tide, weather, dt)
    explanation = get_score_explanation(score, {"depth_m": depth_m}, tide, weather)

    return {
        "lat": round(lat, 4),
        "lon": round(lon, 4),
        "score": round(score, 1),
        "depth_m": round(depth_m, 1),
        "dist_km": round(dist_km, 1),
        "explanation": explanation,
        "tide": tide,
        "weather": weather,
    }
