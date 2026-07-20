import { useState } from 'react';
import { clsx } from 'clsx';

export interface SteeringVector {
  name: string;
  layerIdx: number;
  alpha: number;
  isActive: boolean;
}

interface Props {
  vectors?: SteeringVector[];
  interferenceScore?: number;
  onAddVector?: (name: string, layer: number, alpha: number) => void;
  onRemoveVector?: (name: string) => void;
  onToggleVector?: (name: string) => void;
}

function getLayerDotColor(layerIdx: number): string {
  const colors = [
    'bg-blue-400',
    'bg-green-400',
    'bg-yellow-400',
    'bg-purple-400',
    'bg-red-400',
    'bg-cyan-400',
    'bg-orange-400',
    'bg-pink-400',
  ];
  return colors[layerIdx % colors.length];
}

function getInterferenceColor(score: number): string {
  if (score < 0.3) return 'text-[var(--accent-green)]';
  if (score <= 0.6) return 'text-[var(--accent-yellow)]';
  return 'text-[var(--accent-red)]';
}

function getInterferenceBarColor(score: number): string {
  if (score < 0.3) return 'bg-[var(--accent-green)]';
  if (score <= 0.6) return 'bg-[var(--accent-yellow)]';
  return 'bg-[var(--accent-red)]';
}

function getInterferenceLabel(score: number): string {
  if (score < 0.3) return 'bassa';
  if (score <= 0.6) return 'media';
  return 'alta';
}

export function SteeringControl({
  vectors = [],
  interferenceScore = 0,
  onAddVector = () => {},
  onRemoveVector = () => {},
  onToggleVector = () => {},
}: Props) {
  const [name, setName] = useState('');
  const [layer, setLayer] = useState(1);
  const [alpha, setAlpha] = useState(1.0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    onAddVector(name.trim(), layer, alpha);
    setName('');
    setLayer(1);
    setAlpha(1.0);
  };

  return (
    <div className="space-y-3">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
        Steering Control
      </h3>

      {/* Interference indicator */}
      <div className="p-2.5 rounded border border-[var(--bg-border)] bg-[#1a1f2e]">
        <div className="flex items-center justify-between text-xs mb-1.5">
          <span className="text-[var(--text-muted)]">Interferenza</span>
          <span className={clsx('font-medium', getInterferenceColor(interferenceScore))}>
            {interferenceScore.toFixed(2)} ({getInterferenceLabel(interferenceScore)})
          </span>
        </div>
        <div className="h-1.5 rounded-full bg-[var(--bg-border)] overflow-hidden">
          <div
            className={clsx('h-full rounded-full transition-all duration-500', getInterferenceBarColor(interferenceScore))}
            style={{ width: `${Math.min(100, interferenceScore * 100)}%` }}
          />
        </div>
      </div>

      {/* Active vectors list */}
      {vectors.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wide">
            Vettori attivi ({vectors.filter(v => v.isActive).length}/{vectors.length})
          </span>
          {vectors.map((vec) => (
            <div
              key={vec.name}
              className={clsx(
                'flex items-center gap-2 p-2 rounded border text-xs',
                vec.isActive
                  ? 'border-[var(--bg-border)] bg-[#1a1f2e]'
                  : 'border-[var(--bg-border)] bg-[var(--bg-card)] opacity-50'
              )}
            >
              <span className={clsx('w-2 h-2 rounded-full shrink-0', getLayerDotColor(vec.layerIdx))} />
              <span className="text-[var(--text-primary)] font-medium truncate min-w-0">{vec.name}</span>
              <span className="text-[var(--text-muted)] shrink-0">L{vec.layerIdx}</span>
              <span className="text-[var(--text-muted)] shrink-0">α{vec.alpha.toFixed(1)}</span>
              <button
                onClick={() => onToggleVector(vec.name)}
                className={clsx(
                  'ml-auto shrink-0 w-5 h-5 rounded flex items-center justify-center transition-colors',
                  vec.isActive
                    ? 'bg-[var(--accent-green)]/20 text-[var(--accent-green)]'
                    : 'bg-[var(--bg-border)] text-[var(--text-muted)]'
                )}
                title={vec.isActive ? 'Disattiva' : 'Attiva'}
              >
                {vec.isActive ? '✓' : '○'}
              </button>
              <button
                onClick={() => onRemoveVector(vec.name)}
                className="shrink-0 w-5 h-5 rounded flex items-center justify-center bg-[var(--accent-red)]/10 text-[var(--accent-red)] hover:bg-[var(--accent-red)]/20 transition-colors"
                title="Rimuovi"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {vectors.length === 0 && (
        <div className="text-xs text-[var(--text-muted)] text-center py-2">
          Nessun vettore attivo
        </div>
      )}

      {/* Add vector form */}
      <form onSubmit={handleSubmit} className="space-y-2 p-2.5 rounded border border-[var(--bg-border)] bg-[#1a1f2e]">
        <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wide">
          Aggiungi Vettore
        </span>

        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Nome vettore"
          className="w-full px-2.5 py-1.5 rounded border border-[var(--bg-border)] bg-[var(--bg-card)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[var(--accent-blue)] transition-colors"
        />

        <div className="flex gap-2">
          <div className="flex-1">
            <label className="block text-[10px] text-[var(--text-muted)] mb-0.5">Layer</label>
            <input
              type="number"
              value={layer}
              onChange={(e) => setLayer(Math.max(1, Math.min(100, Number(e.target.value) || 1)))}
              min={1}
              max={100}
              className="w-full px-2.5 py-1.5 rounded border border-[var(--bg-border)] bg-[var(--bg-card)] text-[var(--text-primary)] text-xs focus:outline-none focus:border-[var(--accent-blue)] transition-colors"
            />
          </div>
          <div className="flex-1">
            <label className="block text-[10px] text-[var(--text-muted)] mb-0.5">Alpha: {alpha.toFixed(1)}</label>
            <input
              type="range"
              min={0}
              max={3}
              step={0.1}
              value={alpha}
              onChange={(e) => setAlpha(parseFloat(e.target.value))}
              className="w-full accent-[var(--accent-blue)] mt-1"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={!name.trim()}
          className={clsx(
            'w-full py-1.5 rounded text-xs font-medium transition-colors',
            name.trim()
              ? 'bg-[var(--accent-blue)]/20 text-[var(--accent-blue)] hover:bg-[var(--accent-blue)]/30 border border-[var(--accent-blue)]/30'
              : 'bg-[var(--bg-border)] text-[var(--text-muted)] cursor-not-allowed border border-[var(--bg-border)]'
          )}
        >
          Aggiungi Vettore
        </button>
      </form>
    </div>
  );
}
