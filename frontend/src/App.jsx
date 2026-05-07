import AdviesPanel from './components/AdviesPanel.jsx';
import Map from './components/Map.jsx';
import { useHeatmap } from './hooks/useHeatmap.js';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export default function App() {
  const { data, loading, offline } = useHeatmap(API_URL);

  return (
    <div className="app">
      <div className="map-container">
        <Map heatmapData={data} />
      </div>
      <div className="panel-container">
        <AdviesPanel data={data} loading={loading} offline={offline} />
      </div>
    </div>
  );
}
