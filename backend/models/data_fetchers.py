import math
from datetime import datetime
from typing import Dict

import httpx


async def fetch_weather(lat: float = 52.5, lon: float = 4.5) -> Dict:
    """Haal huidig weer op via Open-Meteo (gratis, geen API key)."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=wind_speed_10m,temperature_2m,cloud_cover"
            f"&wind_speed_unit=ms"
        )
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            current = r.json()["current"]
            return {
                "wind_speed": current.get("wind_speed_10m", 5.0),
                "temperature": current.get("temperature_2m", 12.0),
                "cloud_cover": current.get("cloud_cover", 50),
                "source": "live",
            }
    except Exception:
        return _mock_weather()


async def fetch_tide() -> Dict:
    """Getijstatus op basis van sinusoïdaal 12.4-uursmodel (mock).

    Rijkswaterstaat Waterinfo API vereist complexe POST-structuur;
    voor MVP gebruiken we een realistische benadering.
    """
    return _mock_tide()


def _mock_weather() -> Dict:
    return {
        "wind_speed": 5.5,
        "temperature": 13.0,
        "cloud_cover": 60,
        "source": "mock",
    }


def _mock_tide() -> Dict:
    """Getij op basis van tijd: sinusoïde met periode 12.4 uur."""
    now = datetime.utcnow()
    t_hours = now.hour + now.minute / 60.0

    # Getijperiode ~12.4 uur, fase willekeurig verankerd
    phase = (t_hours / 12.4) * 2 * math.pi
    height = math.sin(phase)          # -1 .. +1
    rate = math.cos(phase)            # afgeleid (stijgend/dalend)

    if abs(height) > 0.85:
        state = "high" if height > 0 else "low"
    elif rate > 0:
        state = "rising"
    else:
        state = "falling"

    return {
        "state": state,
        "height": round(height * 1.0 + 1.0, 2),  # 0–2 m schaal
        "source": "mock",
    }
