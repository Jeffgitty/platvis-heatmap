import L from 'leaflet';
import { useEffect, useRef } from 'react';

// Fix voor Leaflet marker icons in Vite builds
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconUrl: markerIcon, iconRetinaUrl: markerIcon2x, shadowUrl: markerShadow });

const NL_CENTER = [52.5, 4.9];

const TIDE_NL = {
  rising: 'Opkomend', high: 'Hoog water',
  falling: 'Afgaand', low: 'Laag water',
};
const NL_ZOOM = 8;

const greenIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

export default function Map({ heatmapData, apiUrl }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const overlayRef = useRef(null);
  const markerRef = useRef(null);
  const apiUrlRef = useRef(apiUrl);
  useEffect(() => { apiUrlRef.current = apiUrl; }, [apiUrl]);

  useEffect(() => {
    if (mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: NL_CENTER,
      zoom: NL_ZOOM,
      maxBounds: [[50.5, 2.0], [54.2, 8.0]],
      maxBoundsViscosity: 0.8,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 18,
    }).addTo(map);

    // Klik op kaart → lokale viskans opvragen
    map.on('click', async (e) => {
      const { lat, lng } = e.latlng;
      const popup = L.popup({ maxWidth: 220 })
        .setLatLng(e.latlng)
        .setContent('<div style="padding:4px">⏳ Berekenen...</div>')
        .openOn(map);

      try {
        const res = await fetch(`${apiUrlRef.current}/score?lat=${lat.toFixed(5)}&lon=${lng.toFixed(5)}`);
        if (!res.ok) {
          popup.setContent('<div style="color:#ef4444">Buiten NL kustgebied</div>');
          return;
        }
        const d = await res.json();
        const col = d.score >= 70 ? '#22c55e' : d.score >= 40 ? '#eab308' : '#ef4444';
        popup.setContent(`
          <div style="font-size:13px;line-height:1.7">
            <div style="font-size:22px;font-weight:800;color:${col}">${Math.round(d.score)}<span style="font-size:13px;color:#94a3b8">/100</span></div>
            🌊 Diepte: <strong>${d.depth_m}m</strong><br/>
            📍 ${d.dist_km}km van kust<br/>
            🌙 Getij: ${TIDE_NL[d.tide?.state] ?? d.tide?.state}<br/>
            <hr style="border-color:#334155;margin:6px 0"/>
            <span style="font-size:11px;color:#94a3b8">${d.explanation}</span>
          </div>
        `);
      } catch {
        popup.setContent('<div style="color:#ef4444">Fout bij ophalen data</div>');
      }
    });

    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !heatmapData) return;

    const { surface, points } = heatmapData;

    // --- Kriging PNG overlay ---
    if (surface?.image_b64) {
      const url = `data:image/png;base64,${surface.image_b64}`;
      const { north, south, west, east } = surface.bounds;
      const bounds = [[south, west], [north, east]];

      if (overlayRef.current) {
        overlayRef.current.setUrl(url);
        overlayRef.current.setBounds(bounds);
      } else {
        overlayRef.current = L.imageOverlay(url, bounds, { opacity: 0.65, zIndex: 300 }).addTo(map);
      }
    }

    // --- Beste punt marker ---
    if (markerRef.current) { markerRef.current.remove(); markerRef.current = null; }

    const best = points?.[0];
    if (best) {
      markerRef.current = L.marker([best.lat, best.lon], { icon: greenIcon })
        .bindPopup(
          `<div style="font-size:13px;line-height:1.6">
            <strong>Score: ${best.score}/100</strong><br/>
            Diepte: ${best.depth_m}m<br/>
            ${best.lat.toFixed(3)}°N ${best.lon.toFixed(3)}°E
          </div>`,
          { maxWidth: 180 }
        )
        .addTo(map);
    }
  }, [heatmapData]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />
      <Legend />
    </div>
  );
}

function Legend() {
  return (
    <div className="map-legend">
      <div className="legend-title">Viskans</div>
      <div className="legend-bar" />
      <div className="legend-labels">
        <span>Laag</span>
        <span>Hoog</span>
      </div>
    </div>
  );
}
