const TIDE_NL = {
  rising: 'Opkomend',
  high: 'Hoog water',
  falling: 'Afgaand',
  low: 'Laag water',
};

function scoreClass(s) {
  if (s >= 70) return 'score-goed';
  if (s >= 40) return 'score-matig';
  return 'score-slecht';
}

function ScoreMeter({ score }) {
  const pct = Math.round(score);
  return (
    <div className="score-meter-wrap">
      <div className="score-meter-bar">
        <div className="score-meter-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="panel">
      <div className="panel-header">🐟 PLATVIS ADVIES</div>
      <div className="skeleton-block" style={{ height: 48, marginBottom: 12 }} />
      <div className="skeleton-block" style={{ height: 20, marginBottom: 8 }} />
      <div className="skeleton-block" style={{ height: 20, marginBottom: 8 }} />
      <div className="skeleton-block" style={{ height: 20 }} />
    </div>
  );
}

export default function AdviesPanel({ data, loading, offline }) {
  if (loading) return <Skeleton />;
  if (!data) return null;

  const score = data.best_score ?? 0;
  const best = data.points?.[0];
  const tide = data.tide ?? {};
  const weather = data.weather ?? {};

  const tideLabel = TIDE_NL[tide.state] ?? 'Onbekend';
  const beaufort = msToBeaufort(weather.wind_speed ?? 0);

  return (
    <div className="panel">
      {offline && (
        <div className="offline-badge">📵 Offline – laatste gecachte data (–10 penalty)</div>
      )}

      <div className="panel-header">🐟 PLATVIS ADVIES</div>

      <div className={`score-display ${scoreClass(score)}`}>
        <span className="score-number">{Math.round(score)}</span>
        <span className="score-max">/100</span>
      </div>
      <ScoreMeter score={score} />

      <div className="panel-grid">
        <Row icon="📍" label="Beste zone">
          {best ? `${best.lat.toFixed(2)}°N ${best.lon.toFixed(2)}°E` : '—'}
        </Row>
        <Row icon="🌊" label="Diepte">
          {best ? `${best.depth_m?.toFixed(0)}m` : '—'}
        </Row>
        <Row icon="🌙" label="Getij">
          {tideLabel} ({tide.height?.toFixed(1)}m)
        </Row>
        <Row icon="💨" label="Wind">
          {weather.wind_speed?.toFixed(1)} m/s (Bft {beaufort})
        </Row>
        <Row icon="🌡️" label="Temperatuur">
          {weather.temperature?.toFixed(0)}°C
        </Row>
        <Row icon="☁️" label="Bewolking">
          {weather.cloud_cover}%
        </Row>
      </div>

      <div className="panel-explain">
        {data.explanation ?? '—'}
      </div>

      <div className="panel-footer">
        Gemiddelde kust: {data.avg_score?.toFixed(0)}/100 ·
        {' '}{new Date(data.timestamp + 'Z').toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })}
      </div>
    </div>
  );
}

function Row({ icon, label, children }) {
  return (
    <div className="panel-row">
      <span className="row-icon">{icon}</span>
      <span className="row-label">{label}</span>
      <span className="row-value">{children}</span>
    </div>
  );
}

function msToBeaufort(ms) {
  const t = [0.3, 1.5, 3.3, 5.5, 7.9, 10.7, 13.8, 17.1, 20.7, 24.4, 28.4, 32.6];
  for (let i = 0; i < t.length; i++) if (ms < t[i]) return i;
  return 12;
}
