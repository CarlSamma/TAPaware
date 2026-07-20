import { OceanRadar } from '../components/psycho/OceanRadar';
import { StirHistory } from '../components/psycho/StirHistory';
import { LiveFeed } from '../components/feed/LiveFeed';
import { ProbeComposer } from '../components/attack/ProbeComposer';
import { HealthPanel } from '../components/system/HealthPanel';
import { SsotViewer } from '../components/ssot/SsotViewer';
import { EscalationMonitor } from '../components/orchestration/EscalationMonitor';
import { SteeringControl } from '../components/steering/SteeringControl';
import { useEngineStatus } from '../hooks/useEngineStatus';

export function Dashboard() {
  const status = useEngineStatus();

  return (
    <div className="grid grid-cols-[280px_1fr_260px_280px] gap-4 h-[calc(100vh-48px)] p-4">
      {/* Colonna sinistra: controlli + health + STIR */}
      <aside className="flex flex-col gap-4 overflow-y-auto">
        <div className="bg-[var(--bg-card)] rounded-lg p-4 border border-[var(--bg-border)]">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">
            Controllo Attacco
          </h2>
          <ProbeComposer isRunning={status?.is_running ?? false} />
        </div>
        <div className="bg-[var(--bg-card)] rounded-lg p-4 border border-[var(--bg-border)]">
          <HealthPanel />
        </div>
        <div className="bg-[var(--bg-card)] rounded-lg p-4 border border-[var(--bg-border)]">
          <StirHistory />
        </div>
        <div className="bg-[var(--bg-card)] rounded-lg p-4 border border-[var(--bg-border)]">
          <SsotViewer />
        </div>
      </aside>

      {/* Colonna centrale: feed live */}
      <main className="bg-[var(--bg-card)] rounded-lg p-4 border border-[var(--bg-border)] flex flex-col">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">
          Feed Live — @HackingA0
        </h2>
        <LiveFeed />
      </main>

      {/* Colonna destra 1: OCEAN */}
      <aside className="flex flex-col gap-4 overflow-y-auto">
        <div className="bg-[var(--bg-card)] rounded-lg p-4 border border-[var(--bg-border)]">
          <OceanRadar />
        </div>
      </aside>

      {/* Colonna destra 2: Escalation + Steering */}
      <aside className="flex flex-col gap-4 overflow-y-auto">
        <div className="bg-[var(--bg-card)] rounded-lg p-4 border border-[var(--bg-border)]">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">
            Escalation Monitor
          </h2>
          <EscalationMonitor />
        </div>
        <div className="bg-[var(--bg-card)] rounded-lg p-4 border border-[var(--bg-border)]">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-3">
            Steering Control
          </h2>
          <SteeringControl />
        </div>
      </aside>
    </div>
  );
}