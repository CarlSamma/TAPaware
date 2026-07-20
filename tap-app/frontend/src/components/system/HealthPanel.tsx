import { useState, useEffect } from 'react';
import { api } from '../../hooks/useApi';
import type { HealthStatus } from '../../types/tap';

const STATUS_COLOR: Record<string, string> = {
  healthy: 'text-[var(--accent-green)]',
  degraded: 'text-[var(--accent-yellow)]',
  unhealthy: 'text-[var(--accent-red)]',
};

export function HealthPanel() {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    const poll = () => api.health().then(setHealth).catch(() => {});
    poll();
    const id = setInterval(poll, 10000);
    return () => clearInterval(id);
  }, []);

  if (!health)
    return <div className="text-xs text-[var(--text-muted)]">Health loading...</div>;

  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center">
        <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
          System Health
        </span>
        <span
          className={`text-xs font-bold uppercase ${STATUS_COLOR[health.status] ?? ''}`}
        >
          {health.status}
        </span>
      </div>
      {Object.entries(health.components).map(([name, comp]) => {
        const obj = comp as Record<string, unknown>;
        const st =
          typeof obj?.status === 'string'
            ? obj.status
            : obj?.connected
            ? 'connected'
            : 'unknown';
        const color =
          st === 'healthy' || st === 'connected'
            ? STATUS_COLOR.healthy
            : st === 'degraded'
            ? STATUS_COLOR.degraded
            : STATUS_COLOR.unhealthy;
        return (
          <div key={name} className="flex justify-between text-xs">
            <span className="text-[var(--text-muted)] capitalize">
              {name.replace(/_/g, ' ')}
            </span>
            <span className={color}>{st}</span>
          </div>
        );
      })}
      {health.components.engine && (
        <div className="flex justify-between text-xs">
          <span className="text-[var(--text-muted)]">Cicli eseguiti</span>
          <span className="text-[var(--text-primary)]">
            {health.components.engine.cycle_count}
          </span>
        </div>
      )}
      <div className="text-xs text-[var(--text-muted)] mt-1">
        v{health.version}
      </div>
    </div>
  );
}