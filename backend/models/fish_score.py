from datetime import datetime
from typing import Dict


def ms_to_beaufort(ms: float) -> int:
    """Windsnelheid m/s → Beaufort schaal."""
    thresholds = [0.3, 1.5, 3.3, 5.5, 7.9, 10.7, 13.8, 17.1, 20.7, 24.4, 28.4, 32.6]
    for i, t in enumerate(thresholds):
        if ms < t:
            return i
    return 12


def _depth_base(depth_m: float) -> float:
    """Ruimtelijke basisscore op basis van diepte (0–90).

    Dit is de enige ruimtelijk varierende factor; conditie-factoren
    werken hier als vermenigvuldiger, zodat kriging zinvolle variatie ziet.
    """
    d = depth_m
    if d < 1.0:
        return 5.0 + d * 10.0                          # 5–15
    if d < 3.0:
        return 15.0 + (d - 1.0) * 17.5                 # 15–50
    if d <= 10.0:
        return 50.0 + (d - 3.0) / 7.0 * 35.0           # 50–85 (optimum)
    if d <= 20.0:
        return 85.0 - (d - 10.0) * 3.5                 # 85–50
    return max(10.0, 50.0 - (d - 20.0) * 1.5)         # 50→ afnemend


def _light_mult(dt: datetime, cloud_cover: float) -> float:
    """Lichtcorrectie als vermenigvuldigingsfactor-delta."""
    hour = dt.hour
    if hour in (5, 6, 20, 21):    # Schemer
        return 0.22
    if hour < 5 or hour > 21:    # Nacht
        return 0.05
    if hour in (7, 8, 18, 19):   # Vroeg/laat dag
        return 0.10 + (0.08 if cloud_cover > 70 else 0.0)
    # Volle dag
    if cloud_cover > 70:
        return 0.08
    if cloud_cover < 30:
        return -0.12
    return 0.0


def calculate_fish_score(
    depth_m: float,
    dist_km: float,
    tide: Dict,
    weather: Dict,
    dt: datetime | None = None,
) -> float:
    """Bereken platvis-activiteitsscore 0–100 voor één gridpunt.

    Architectuur:  score = depth_base(d) * condition_multiplier
    - depth_base: 5–85, ruimtelijk variabel → kriging-input
    - condition_mult: 0.35–1.65, uniform per moment
    """
    if dt is None:
        dt = datetime.utcnow()

    base = _depth_base(depth_m)

    # --- Conditie-vermenigvuldiger ---
    mult = 1.0

    # Getij (grootste factor)
    mult += {"rising": 0.35, "high": 0.18, "falling": 0.05, "low": -0.22}.get(
        tide.get("state", ""), 0.0
    )

    # Wind
    beaufort = ms_to_beaufort(weather.get("wind_speed", 5.0))
    if 3 <= beaufort <= 6:
        mult += 0.15
    elif beaufort > 7:
        mult -= 0.10
    elif beaufort <= 1:
        mult -= 0.05

    # Licht
    mult += _light_mult(dt, float(weather.get("cloud_cover", 50)))

    # Seizoen
    month = dt.month
    if month in (3, 4, 5, 9, 10, 11):
        mult += 0.10
    elif month in (12, 1, 2):
        mult -= 0.05

    mult = max(0.35, min(1.65, mult))
    score = base * mult

    return max(0.0, min(100.0, score))


def get_score_explanation(score: float, best: Dict, tide: Dict, weather: Dict) -> str:
    """Genereer korte Nederlandse uitleg van de score."""
    parts = []

    tide_nl = {
        "rising": "Opkomend tij",
        "high": "Hoog water",
        "falling": "Afgaand tij",
        "low": "Laag water",
    }.get(tide.get("state", ""), "Onbekend getij")
    parts.append(tide_nl)

    depth = best.get("depth_m", 0)
    if 5 <= depth <= 10:
        parts.append(f"uitstekende diepte ({depth:.0f}m)")
    elif 3 <= depth <= 15:
        parts.append(f"goede diepte ({depth:.0f}m)")
    elif depth < 2:
        parts.append(f"erg ondiep ({depth:.1f}m)")
    elif depth > 20:
        parts.append(f"te diep ({depth:.0f}m)")

    bft = ms_to_beaufort(weather.get("wind_speed", 5.0))
    parts.append(f"wind Bft {bft}")

    cloud = weather.get("cloud_cover", 50)
    if cloud > 70:
        parts.append("bewolkt (gunstig)")
    elif cloud < 30:
        parts.append("helder (ongunstig)")

    return " · ".join(parts)
