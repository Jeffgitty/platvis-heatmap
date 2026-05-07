import { useEffect, useState } from 'react';

const CACHE_KEY = 'platvis_v1';
const CACHE_MAX_AGE = 10 * 60 * 1000; // 10 minuten
const REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minuten

export function useHeatmap(apiUrl) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    fetchHeatmap();
    const id = setInterval(fetchHeatmap, REFRESH_INTERVAL);
    return () => clearInterval(id);
  }, [apiUrl]);

  async function fetchHeatmap() {
    try {
      const res = await fetch(`${apiUrl}/heatmap`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();

      setData(json);
      setOffline(false);

      // Sla op in localStorage voor offline gebruik
      try {
        localStorage.setItem(CACHE_KEY, JSON.stringify({ data: json, ts: Date.now() }));
      } catch (_) {
        // localStorage vol of geblokkeerd — geen probleem
      }
    } catch {
      // Probeer gecachte data
      const cached = _loadCache();
      if (cached) {
        // Offline penalty: -10 op best_score
        setData({ ...cached, best_score: Math.max(0, (cached.best_score ?? 0) - 10) });
        setOffline(true);
      }
    } finally {
      setLoading(false);
    }
  }

  return { data, loading, offline };
}

function _loadCache() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const { data, ts } = JSON.parse(raw);
    if (Date.now() - ts > CACHE_MAX_AGE) return null;
    return data;
  } catch {
    return null;
  }
}
