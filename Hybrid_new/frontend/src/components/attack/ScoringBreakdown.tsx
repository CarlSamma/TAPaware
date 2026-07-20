import { clsx } from 'clsx';
import type { AttackTechnique } from '../../types/tap';

interface Props {
  technique: AttackTechnique;
}

interface ScoreComponent {
  label: string;
  value: number;
  weight: number;
  color: string;
  bgColor: string;
}

function computeComponents(tech: AttackTechnique): ScoreComponent[] {
  // Derived values from available data
  const synergy = Math.min(1, (tech.asr + tech.stealth) / 2 * 1.1);
  const platformFit = tech.tags.length >= 3 ? 0.85 : tech.tags.length >= 2 ? 0.7 : 0.55;

  return [
    { label: 'ASR', value: tech.asr, weight: 0.35, color: 'bg-[var(--accent-blue)]', bgColor: 'bg-blue-900/40' },
    { label: 'Stealth', value: tech.stealth, weight: 0.25, color: 'bg-[var(--accent-green)]', bgColor: 'bg-green-900/40' },
    { label: 'Synergy', value: synergy, weight: 0.20, color: 'bg-purple-500', bgColor: 'bg-purple-900/40' },
    { label: 'Platform Fit', value: platformFit, weight: 0.10, color: 'bg-orange-500', bgColor: 'bg-orange-900/40' },
  ];
}

export function ScoringBreakdown({ technique }: Props) {
  const components = computeComponents(technique);
  const baseScore = components.reduce((sum, c) => sum + c.value * c.weight, 0);

  // Bonuses
  const synergyVal = components.find(c => c.label === 'Synergy')!.value;
  const hasInfoGainBonus = synergyVal > 0.8;
  const hasClaimBonus = technique.tags.some(t =>
    ['measurement', 'citation', 'data-driven'].includes(t.toLowerCase())
  );

  const infoGainBonus = hasInfoGainBonus ? baseScore * 0.15 : 0;
  const claimBonus = hasClaimBonus ? baseScore * 0.12 : 0;
  const totalScore = Math.min(1, baseScore + infoGainBonus + claimBonus);

  return (
    <div className="space-y-2.5">
      <h4 className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide">
        Scoring v2 — Breakdown
      </h4>

      {components.map(comp => {
        const contribution = comp.value * comp.weight;
        const barPct = comp.value * 100;
        return (
          <div key={comp.label} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[var(--text-primary)]">{comp.label}</span>
              <span className="text-[var(--text-muted)]">
                {Math.round(comp.value * 100)}%
                <span className="ml-1 opacity-60">×{comp.weight}</span>
                <span className="ml-1 text-[var(--text-primary)]">= {Math.round(contribution * 100)}</span>
              </span>
            </div>
            <div className={clsx('h-1.5 rounded-full overflow-hidden', comp.bgColor)}>
              <div
                className={clsx('h-full rounded-full transition-all duration-500', comp.color)}
                style={{ width: `${barPct}%` }}
              />
            </div>
          </div>
        );
      })}

      {/* Bonuses */}
      <div className="pt-1.5 border-t border-[var(--bg-border)] space-y-1">
        <div className="flex items-center justify-between text-xs">
          <span className="flex items-center gap-1.5">
            <span className={clsx(
              'w-1.5 h-1.5 rounded-full',
              hasInfoGainBonus ? 'bg-[var(--accent-yellow)]' : 'bg-gray-600'
            )} />
            <span className="text-[var(--text-muted)]">Info Gain Bonus</span>
          </span>
          <span className={clsx(hasInfoGainBonus ? 'text-[var(--accent-yellow)]' : 'text-[var(--text-muted)]')}>
            {hasInfoGainBonus ? `+${Math.round(infoGainBonus * 100)}` : '—'}
          </span>
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="flex items-center gap-1.5">
            <span className={clsx(
              'w-1.5 h-1.5 rounded-full',
              hasClaimBonus ? 'bg-cyan-400' : 'bg-gray-600'
            )} />
            <span className="text-[var(--text-muted)]">Claim Type Bonus</span>
          </span>
          <span className={clsx(hasClaimBonus ? 'text-cyan-400' : 'text-[var(--text-muted)]')}>
            {hasClaimBonus ? `+${Math.round(claimBonus * 100)}` : '—'}
          </span>
        </div>
      </div>

      {/* Total */}
      <div className="pt-1.5 border-t border-[var(--bg-border)]">
        <div className="flex items-center justify-between text-sm font-medium">
          <span className="text-[var(--text-primary)]">Score Totale</span>
          <span className={clsx(
            totalScore >= 0.7 ? 'text-[var(--accent-green)]' :
            totalScore >= 0.4 ? 'text-[var(--accent-yellow)]' :
            'text-red-400'
          )}>
            {Math.round(totalScore * 100)}
          </span>
        </div>
        <div className="mt-1 h-2 rounded-full bg-[var(--bg-border)] overflow-hidden">
          <div
            className={clsx(
              'h-full rounded-full transition-all duration-500',
              totalScore >= 0.7 ? 'bg-[var(--accent-green)]' :
              totalScore >= 0.4 ? 'bg-[var(--accent-yellow)]' :
              'bg-red-500'
            )}
            style={{ width: `${totalScore * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}
