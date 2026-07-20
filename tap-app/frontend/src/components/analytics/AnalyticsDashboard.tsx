interface SessionStats {
  totalProbes: number;
  successfulProbes: number;
  avgAsr: number;
  totalCostUsd: number;
  infoGains: Record<string, number>;
}

interface AnalyticsDashboardProps {
  stats: SessionStats;
  onExportReport: () => void;
  onResetStats: () => void;
}

function formatUsd(value: number): string {
  return `$${value.toFixed(2)}`;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function getAsrColor(asr: number): string {
  if (asr >= 0.7) return 'text-[var(--accent-green)]';
  if (asr >= 0.4) return 'text-[var(--accent-yellow)]';
  return 'text-[var(--accent-red)]';
}

export function AnalyticsDashboard({ stats, onExportReport, onResetStats }: AnalyticsDashboardProps) {
  const successRate = stats.totalProbes > 0
    ? stats.successfulProbes / stats.totalProbes
    : 0;

  const sortedInfoGains = Object.entries(stats.infoGains)
    .sort(([, a], [, b]) => b - a);

  const maxInfoGain = sortedInfoGains.length > 0
    ? Math.max(...sortedInfoGains.map(([, v]) => v))
    : 1;

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--bg-border)] rounded-lg p-4 space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--text-muted)]">
          Attack Analytics
        </h2>
      </div>

      {/* Session Stats */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-[var(--text-muted)]">Total Probes</span>
          <span className="text-[var(--text-primary)] font-medium">{stats.totalProbes}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-[var(--text-muted)]">Successful Probes</span>
          <span className="text-[var(--text-primary)]">
            {stats.successfulProbes} <span className="text-[var(--text-muted)]">({formatPercent(successRate)})</span>
          </span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-[var(--text-muted)]">Average ASR</span>
          <span className={`font-medium ${getAsrColor(stats.avgAsr)}`}>
            {formatPercent(stats.avgAsr)}
          </span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-[var(--text-muted)]">Total Cost</span>
          <span className="text-[var(--accent-blue)] font-medium">{formatUsd(stats.totalCostUsd)}</span>
        </div>
      </div>

      {/* V-Usable Info Section */}
      {sortedInfoGains.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            V-Usable Info
          </span>
          <div className="space-y-2">
            {sortedInfoGains.map(([property, gain]) => (
              <div key={property} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-[var(--text-muted)] truncate">{property}</span>
                  <span className="text-[var(--accent-purple)] font-medium ml-2">
                    {gain.toFixed(2)} bits
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-[var(--bg-base)] overflow-hidden">
                  <div
                    className="h-full rounded-full bg-[var(--accent-purple)] transition-all duration-300"
                    style={{ width: `${(gain / maxInfoGain) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="space-y-2 pt-1">
        <button
          onClick={onExportReport}
          className="w-full px-3 py-2 text-xs font-medium rounded bg-[var(--accent-blue)] text-[var(--bg-base)] hover:opacity-90 transition-opacity"
        >
          Esporta Report
        </button>
        <button
          onClick={onResetStats}
          className="w-full px-3 py-2 text-xs font-medium rounded border border-[var(--bg-border)] text-[var(--text-primary)] hover:bg-[var(--bg-border)] transition-colors"
        >
          Reset Stats
        </button>
      </div>
    </div>
  );
}
