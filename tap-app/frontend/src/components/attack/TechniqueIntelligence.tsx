import { clsx } from 'clsx';
import type { AttackTechnique } from '../../types/tap';
import { ScoringBreakdown } from './ScoringBreakdown';

interface Props {
  technique: AttackTechnique;
  onApply: () => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  incremental: 'bg-blue-500',
  persuasion: 'bg-purple-500',
  roleplay: 'bg-pink-500',
  priming: 'bg-orange-500',
  injection: 'bg-red-500',
  reasoning: 'bg-cyan-500',
  multimodal: 'bg-teal-500',
  optimization: 'bg-yellow-500',
  agentic: 'bg-green-500',
};

function computeTotalScore(tech: AttackTechnique): number {
  const synergy = Math.min(1, (tech.asr + tech.stealth) / 2 * 1.1);
  const platformFit = tech.tags.length >= 3 ? 0.85 : tech.tags.length >= 2 ? 0.7 : 0.55;
  const base = 0.35 * tech.asr + 0.25 * tech.stealth + 0.20 * synergy + 0.10 * platformFit;

  let bonus = 0;
  if (synergy > 0.8) bonus += base * 0.15;
  if (tech.tags.some(t => ['measurement', 'citation', 'data-driven'].includes(t.toLowerCase()))) {
    bonus += base * 0.12;
  }

  return Math.min(1, base + bonus);
}

export function TechniqueIntelligence({ technique, onApply }: Props) {
  const totalScore = computeTotalScore(technique);
  const catColor = CATEGORY_COLORS[technique.category] || 'bg-gray-500';

  return (
    <div
      className={clsx(
        'rounded-lg border border-[var(--bg-border)] bg-[var(--bg-card)] p-4',
        'transition-all duration-200 hover:border-[var(--accent-blue)] hover:shadow-lg hover:shadow-blue-900/20'
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <span className={clsx('w-3 h-3 rounded-full', catColor)} />
          <div>
            <h3 className="text-sm font-semibold text-[var(--text-primary)]">{technique.name}</h3>
            <span className="text-xs text-[var(--text-muted)] uppercase tracking-wide">
              {technique.category}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className={clsx(
            'text-lg font-bold',
            totalScore >= 0.7 ? 'text-[var(--accent-green)]' :
            totalScore >= 0.4 ? 'text-[var(--accent-yellow)]' :
            'text-red-400'
          )}>
            {Math.round(totalScore * 100)}
          </div>
          <span className="text-xs text-[var(--text-muted)]">score</span>
        </div>
      </div>

      {/* Quick stats */}
      <div className="flex gap-3 mb-3 text-xs">
        <div className="flex items-center gap-1">
          <span className="text-[var(--accent-green)]">ASR</span>
          <span className="text-[var(--text-primary)]">{Math.round(technique.asr * 100)}%</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-[var(--accent-yellow)]">Stealth</span>
          <span className="text-[var(--text-primary)]">{Math.round(technique.stealth * 100)}%</span>
        </div>
        {technique.cost_usd !== undefined && (
          <div className="flex items-center gap-1">
            <span className="text-[var(--text-muted)]">Costo</span>
            <span className="text-[var(--text-primary)]">${technique.cost_usd.toFixed(2)}</span>
          </div>
        )}
        {technique.avg_turns !== undefined && (
          <div className="flex items-center gap-1">
            <span className="text-[var(--text-muted)]">Turni</span>
            <span className="text-[var(--text-primary)]">{technique.avg_turns}</span>
          </div>
        )}
      </div>

      {/* Tags */}
      <div className="flex gap-1 flex-wrap mb-3">
        {technique.tags.map(tag => (
          <span
            key={tag}
            className="text-xs px-1.5 py-0.5 rounded bg-[var(--bg-border)] text-[var(--text-muted)]"
          >
            {tag}
          </span>
        ))}
      </div>

      {/* Burned warning */}
      {technique.burned && (
        <div className="mb-3 text-xs px-2 py-1 rounded bg-red-900/30 border border-red-800 text-red-400">
          Tecnica compromessa — potrebbe essere rilevata
        </div>
      )}

      {/* Scoring breakdown */}
      <div className="mb-3 pt-3 border-t border-[var(--bg-border)]">
        <ScoringBreakdown technique={technique} />
      </div>

      {/* Apply button */}
      <button
        onClick={onApply}
        className={clsx(
          'w-full py-2 px-4 rounded text-sm font-medium transition-all',
          'bg-[var(--accent-blue)] text-white',
          'hover:opacity-90 hover:shadow-md',
          'disabled:opacity-40 disabled:cursor-not-allowed'
        )}
        disabled={technique.burned}
      >
        Applica Tecnica
      </button>
    </div>
  );
}
