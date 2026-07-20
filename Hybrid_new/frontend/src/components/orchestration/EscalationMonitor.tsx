import { useState, useEffect } from 'react';
import { clsx } from 'clsx';

interface Props {
  currentLevel?: number;
  probeCount?: number;
  cooldownRemaining?: number;
  frameName?: string;
  onAdvanceLevel?: () => void;
  onReset?: () => void;
}

const LEVEL_NAMES = [
  'Benign Inquiry',
  'Academic Framing',
  'Professional',
  'Ethical Dilemma',
  'Urgency Pressure',
];

const LEVEL_COLORS = [
  'bg-[var(--accent-blue)]',
  'bg-[var(--accent-green)]',
  'bg-[var(--accent-yellow)]',
  'bg-[var(--accent-red)]',
  'bg-[var(--accent-purple)]',
];

const LEVEL_TEXT_COLORS = [
  'text-[var(--accent-blue)]',
  'text-[var(--accent-green)]',
  'text-[var(--accent-yellow)]',
  'text-[var(--accent-red)]',
  'text-[var(--accent-purple)]',
];

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export function EscalationMonitor({
  currentLevel = 1,
  probeCount = 0,
  cooldownRemaining: initialCooldown = 0,
  frameName = '',
  onAdvanceLevel = () => {},
  onReset = () => {},
}: Props) {
  const [cooldown, setCooldown] = useState(initialCooldown);

  useEffect(() => {
    setCooldown(initialCooldown);
  }, [initialCooldown]);

  useEffect(() => {
    if (cooldown <= 0) return;

    const timer = setInterval(() => {
      setCooldown((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [cooldown > 0]);

  const levelIndex = Math.max(0, Math.min(currentLevel - 1, 4));
  const nextProbeHint = currentLevel < 5 ? Math.max(1, 5 - (probeCount % 5)) : null;

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
          Escalation Status
        </h3>
        <span className="text-xs font-medium text-[var(--accent-purple)]">
          Livello {currentLevel}/5
        </span>
      </div>

      {/* Progress bar - 5 segments */}
      <div className="flex gap-1">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className={clsx(
              'h-2 flex-1 rounded-full transition-all duration-300',
              i < currentLevel ? LEVEL_COLORS[i] : 'bg-[var(--bg-border)]'
            )}
          />
        ))}
      </div>

      {/* Current level name */}
      <div className="text-center">
        <span className={clsx('text-sm font-medium', LEVEL_TEXT_COLORS[levelIndex])}>
          {LEVEL_NAMES[levelIndex]}
        </span>
      </div>

      {/* Stats section */}
      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-[var(--bg-border)]">
        <div className="text-center">
          <div className="text-lg font-bold text-[var(--text-primary)]">{probeCount}</div>
          <div className="text-xs text-[var(--text-muted)]">Probe</div>
        </div>
        <div className="text-center">
          <div className={clsx(
            'text-lg font-bold',
            cooldown > 0 ? 'text-[var(--accent-yellow)]' : 'text-[var(--text-primary)]'
          )}>
            {formatTime(cooldown)}
          </div>
          <div className="text-xs text-[var(--text-muted)]">Cooldown</div>
        </div>
        <div className="text-center">
          <div className="text-sm font-medium text-[var(--text-primary)] truncate" title={frameName}>
            {frameName || '—'}
          </div>
          <div className="text-xs text-[var(--text-muted)]">Frame</div>
        </div>
      </div>

      {/* Next level hint */}
      {nextProbeHint !== null && (
        <div className="text-xs text-center text-[var(--text-muted)]">
          Prossimo livello tra: {nextProbeHint} probe
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-2 pt-2">
        <button
          onClick={onAdvanceLevel}
          disabled={currentLevel >= 5}
          className={clsx(
            'flex-1 py-2 px-3 rounded text-sm font-medium transition-colors',
            currentLevel >= 5
              ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
              : 'bg-[var(--accent-purple)] text-white hover:opacity-90'
          )}
        >
          Avanza Livello
        </button>
        <button
          onClick={onReset}
          className="px-4 py-2 rounded text-sm font-medium bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
        >
          Reset
        </button>
      </div>
    </div>
  );
}
