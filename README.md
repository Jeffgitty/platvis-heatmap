# 🐟 Platvis Heatmap Vis-Advies App

Realtime viskans-heatmap voor platvis (schol, schar, tong, bot) op de Nederlandse kust.  
Toont een smooth kriging-geïnterpoleerde heatmap op Leaflet (OpenStreetMap, gratis), op basis van getij, weer, bathymetrie en lichtcondities.

**Live:** `https://<jouw-github-username>.github.io/platvis-heatmap/`  
**API:**  `https://platvis-api.onrender.com`

---

## Setup (eerste keer)

### 1. Repository op GitHub zetten

```bash
cd platvis-heatmap
git init
git add .
git commit -m "init: platvis heatmap MVP"
git remote add origin https://github.com/<jouw-username>/platvis-heatmap.git
git push -u origin main
```

### 3. GitHub Pages inschakelen

1. Ga naar je repo → Settings → Pages
2. Source: **GitHub Actions**

### 4. GitHub Secrets instellen

Ga naar repo → Settings → Secrets and variables → Actions → **New repository secret**:

| Naam | Waarde |
|------|--------|
| `VITE_API_URL` | `https://platvis-api.onrender.com` (zie stap 4) |

### 5. Backend deployen op Render.com

1. Ga naar https://render.com/ → Log in met GitHub
2. **New** → **Web Service** → kies jouw `platvis-heatmap` repo
3. Render detecteert automatisch `render.yaml` → klik **Deploy**
4. Na deploy: kopieer de URL (bv. `https://platvis-api.onrender.com`)
5. Plak deze URL in het `VITE_API_URL` secret (stap 4)

### 6. Frontend deployen

Push naar main → GitHub Actions bouwt en deployt automatisch:

```bash
git add .
git commit -m "deploy"
git push
```

---

## Lokaal draaien

### Vereisten
- Python 3.11+
- Node.js 18+

### Eénmalige installatie

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
cp .env.example .env
# Vul VITE_API_URL in (http://localhost:8000 voor lokaal)
```

### Starten (Windows)

```
start.bat
```

### Starten (Mac/Linux)

```bash
chmod +x start.sh
./start.sh
```

Open http://localhost:5173 in je browser.

---

## Architectuur

```
┌─────────────────────────────────────────────────────┐
│  Browser (Mapbox GL JS + React)                     │
│  ┌──────────────┐  ┌─────────────────────────────┐  │
│  │ Kaart        │  │ AdviesPanel                 │  │
│  │ Kriging PNG  │  │ Score / Getij / Wind / Temp │  │
│  │ overlay      │  │ Uitleg / Offline badge      │  │
│  └──────────────┘  └─────────────────────────────┘  │
└──────────────────────┬──────────────────────────────┘
                       │ GET /heatmap (5 min cache)
                       ▼
┌─────────────────────────────────────────────────────┐
│  FastAPI (Render.com)                               │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐ │
│  │ Grid     │  │ Vismodel │  │ Kriging (PyKrige)  │ │
│  │ 858 pnt  │  │ 0-100    │  │ Spherical → PNG   │ │
│  └──────────┘  └──────────┘  └───────────────────┘ │
│         │              │                            │
│  ┌──────▼──────┐  ┌────▼────────────┐              │
│  │ Open-Meteo  │  │ Getij (mock)    │              │
│  │ live weer   │  │ 12.4h sinus     │              │
│  └─────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────┘
```

## Vismodel

| Factor | Condities | Effect op multiplier |
|--------|-----------|----------------------|
| **Getij** | opkomend | +0.35 |
| | hoog water | +0.18 |
| | afgaand | +0.05 |
| | laag water | −0.22 |
| **Diepte** | 5–10m | basis 85 (optimum) |
| | 3–5m | basis 50–70 |
| | <2m | basis <25 |
| | >20m | basis <50 |
| **Wind** | Bft 3–6 | +0.15 |
| | Bft >7 | −0.10 |
| **Licht** | schemer | +0.22 |
| | bewolkt | +0.08 |
| | zon | −0.12 |
| **Seizoen** | lente/herfst | +0.10 |
| | winter | −0.05 |

Score = `depth_base × condition_multiplier`, geclamped 0–100.

## Offline mode

Als er geen internet is, gebruikt de app de laatste gecachte heatmap (max 10 min oud) en toont een "Offline" badge met −10 penalty op de score.
