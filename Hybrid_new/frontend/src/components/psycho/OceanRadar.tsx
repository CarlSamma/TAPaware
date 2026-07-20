import { useState, useEffect } from 'react';
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Tooltip } from 'recharts';
import { useWebSocket } from '../../hooks/useWebSocket';
import { api } from '../../hooks/useApi';
import type { StirEntry } from '../../types/tap';

const LABELS = {
  O: 'Openness',
  C: 'Conscientiousness',
  E: 'Extraversion',
  A: 'Agreeableness',
  N: 'Neuroticism',
};

export function OceanRadar() {
  const [current, setCurrent] = useState<StirEntry | null>(null);
  const { on } = useWebSocket();

  useEffect(() => {
    api.stir().then(data => {
      if (data.length > 0) setCurrent(data[data.length - 1]);
    });
  }, []);

  useEffect(() => {
    return on('stir_evaluated', (data) => {
      const raw = data as unknown as StirEntry;
      if (raw.ocean && typeof raw.ocean === 'object') {
        setCurrent(raw);
      }
    });
  }, [on]);

  if (!current) return (
    <div className="flex items-center justify-center h-48 text-[var(--text-muted)]">
      Nessun dato OCEAN disponibile
    </div>
  );

  const chartData = Object.entries(current.ocean).map(([key, val]) => ({
    axis: LABELS[key as keyof typeof LABELS] ?? key,
    value: val as number,
    fullMark: 5,
  }));

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-semibold text-[var(--text-muted)] uppercase tracking-wider">
          Profilo OCEAN Target
        </h3>
        <span className="text-xs text-[var(--accent-yellow)]">
          STIR: {current.stir_percentage?.toFixed(1)}%
        </span>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <RadarChart data={chartData}>
          <PolarGrid stroke="var(--bg-border)" />
          <PolarAngleAxis dataKey="axis" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
          <Radar
            name="OCEAN"
            dataKey="value"
            stroke="var(--accent-blue)"
            fill="var(--accent-blue)"
            fillOpacity={0.25}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-card)',
              border: '1px solid var(--bg-border)',
              color: 'var(--text-primary)',
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}