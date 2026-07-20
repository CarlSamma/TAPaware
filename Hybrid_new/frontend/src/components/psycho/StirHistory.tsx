import { useState, useEffect } from 'react';
import { LineChart, Line, ResponsiveContainer, Tooltip, YAxis, XAxis } from 'recharts';
import { useWebSocket } from '../../hooks/useWebSocket';
import { api } from '../../hooks/useApi';
import type { StirEntry } from '../../types/tap';

export function StirHistory() {
  const [history, setHistory] = useState<StirEntry[]>([]);
  const { on } = useWebSocket();

  useEffect(() => {
    api.stir().then(setHistory);
  }, []);

  useEffect(() => {
    return on('stir_evaluated', (data) => {
      setHistory(prev => [...prev, data as unknown as StirEntry].slice(-50));
    });
  }, [on]);

  const chartData = history.map((e, i) => ({
    i,
    stir: e.stir_percentage,
    label: new Date(e.timestamp).toLocaleTimeString('it-IT', {
      hour: '2-digit',
      minute: '2-digit',
    }),
  }));

  const latest = history[history.length - 1];

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-semibold text-[var(--text-muted)] uppercase tracking-wider">
          STIR History
        </h3>
        {latest && (
          <span
            className={`text-lg font-bold ${
              latest.stir_percentage >= 40
                ? 'text-[var(--accent-green)]'
                : latest.stir_percentage >= 20
                ? 'text-[var(--accent-yellow)]'
                : 'text-[var(--accent-red)]'
            }`}
          >
            {latest.stir_percentage.toFixed(1)}%
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={80}>
        <LineChart data={chartData}>
          <YAxis domain={[0, 100]} hide />
          <XAxis dataKey="label" hide />
          <Line
            type="monotone"
            dataKey="stir"
            stroke="var(--accent-yellow)"
            dot={false}
            strokeWidth={2}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-card)',
              border: '1px solid var(--bg-border)',
              fontSize: 11,
            }}
            formatter={(v: number) => [`${v.toFixed(1)}%`, 'STIR']}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}