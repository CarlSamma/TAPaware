import { useState, useEffect } from 'react';
import { clsx } from 'clsx';
import { api } from '../../hooks/useApi';
import type { AttackTechnique, TechniqueRelations } from '../../types/tap';

interface Props {
  onSelect: (techniqueId: string, customPrompt?: string) => void;
  selectedTechniqueId: string | null;
  showScoring?: boolean;
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

export function TechniqueSelector({ onSelect, selectedTechniqueId, showScoring = true }: Props) {
  const [techniques, setTechniques] = useState<AttackTechnique[]>([]);
  const [relations, setRelations] = useState<TechniqueRelations | null>(null);
  const [customPrompt, setCustomPrompt] = useState('');
  const [showCustom, setShowCustom] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTechniques();
  }, []);

  useEffect(() => {
    if (selectedTechniqueId) {
      loadRelations(selectedTechniqueId);
    }
  }, [selectedTechniqueId]);

  const loadTechniques = async () => {
    try {
      const data = await api.getTechniques();
      setTechniques(data.techniques);
    } catch (e) {
      console.error('Failed to load techniques:', e);
    } finally {
      setLoading(false);
    }
  };

  const loadRelations = async (techniqueId: string) => {
    try {
      const data = await api.getTechniqueRelations(techniqueId);
      setRelations(data.relations);
    } catch (e) {
      console.error('Failed to load relations:', e);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    if (id) {
      onSelect(id, customPrompt || undefined);
    }
  };

  const selected = techniques.find(t => t.technique_id === selectedTechniqueId);

  // Group by category for optgroup
  const grouped = techniques.reduce((acc, t) => {
    if (!acc[t.category]) acc[t.category] = [];
    acc[t.category].push(t);
    return acc;
  }, {} as Record<string, AttackTechnique[]>);

  if (loading) {
    return (
      <div className="text-sm text-[var(--text-muted)] py-2">
        Caricamento tecniche...
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Dropdown menu a tendina */}
      <div>
        <label className="block text-xs font-medium text-[var(--text-muted)] mb-1.5 uppercase tracking-wide">
          Tecnica d'attacco
        </label>
        <select
          value={selectedTechniqueId || ''}
          onChange={handleChange}
          className="w-full px-3 py-2.5 rounded border border-[var(--bg-border)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm cursor-pointer hover:border-[var(--accent-blue)] focus:outline-none focus:border-[var(--accent-blue)] transition-colors appearance-none"
          style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center' }}
        >
          <option value="">-- Seleziona tecnica --</option>
          {Object.entries(grouped).map(([category, techs]) => (
            <optgroup key={category} label={category.toUpperCase()}>
              {techs.map(tech => (
                <option key={tech.technique_id} value={tech.technique_id}>
                  {tech.name} (ASR {Math.round(tech.asr * 100)}% | STL {Math.round(tech.stealth * 100)}%)
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </div>

      {/* Selected technique info card */}
      {selected && (
        <div className="p-3 rounded border border-[var(--bg-border)] bg-[#1a1f2e] text-sm space-y-2">
          <div className="flex items-center gap-2">
            <span className={clsx('w-2.5 h-2.5 rounded-full', CATEGORY_COLORS[selected.category] || 'bg-gray-500')} />
            <span className="font-medium text-[var(--text-primary)]">{selected.name}</span>
          </div>
          <div className="flex gap-3 text-xs">
            <span className="text-[var(--accent-green)]">ASR {Math.round(selected.asr * 100)}%</span>
            <span className="text-[var(--accent-yellow)]">Stealth {Math.round(selected.stealth * 100)}%</span>
            {selected.cost_usd !== undefined && (
              <span className="text-[var(--text-muted)]">${selected.cost_usd.toFixed(2)}</span>
            )}
          </div>
          <div className="flex gap-1 flex-wrap">
            {selected.tags.map(tag => (
              <span key={tag} className="text-xs px-1.5 py-0.5 rounded bg-[var(--bg-border)] text-[var(--text-muted)]">
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Scoring v2 preview */}
      {selected && showScoring && (
        <div className="p-3 rounded border border-[var(--bg-border)] bg-[#1a1f2e] text-sm space-y-2">
          <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide">Scoring v2</p>
          {(() => {
            const baseScore = 0.35 * selected.asr + 0.25 * selected.stealth;
            const synergy = 0.20 * 0.5; // placeholder synergy
            const platform = 0.10 * 0.8; // placeholder platform compatibility
            const totalScore = baseScore + synergy + platform;
            const scoreColor = totalScore > 0.8 ? 'text-[var(--accent-green)]'
              : totalScore >= 0.6 ? 'text-[var(--accent-yellow)]'
              : 'text-[var(--accent-red)]';
            const scoreLabel = totalScore > 0.8 ? 'Eccellente'
              : totalScore >= 0.6 ? 'Buono'
              : 'Moderato';
            return (
              <>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-[var(--text-muted)]">Base score:</span>
                  <span className="text-[var(--text-primary)]">{(baseScore * 100).toFixed(1)}%</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[var(--text-muted)] text-xs">Total score:</span>
                  <span className={clsx('font-semibold', scoreColor)}>{(totalScore * 100).toFixed(1)}%</span>
                  <span className={clsx('text-xs px-1.5 py-0.5 rounded', scoreColor, 'bg-opacity-20')}>{scoreLabel}</span>
                </div>
                <p className="text-[10px] text-[var(--text-muted)] font-mono mt-1">
                  Score = 0.35×ASR + 0.25×Stealth + 0.20×Synergy + 0.10×Platform
                </p>
              </>
            );
          })()}
        </div>
      )}

      {/* Custom prompt toggle */}
      <div>
        <button
          onClick={() => setShowCustom(!showCustom)}
          className="text-xs text-[var(--text-muted)] hover:text-[var(--accent-blue)] transition-colors"
        >
          {showCustom ? '− Nascondi prompt personalizzato' : '+ Aggiungi prompt personalizzato'}
        </button>
        {showCustom && (
          <textarea
            value={customPrompt}
            onChange={e => setCustomPrompt(e.target.value)}
            placeholder="Scrivi un prompt personalizzato per guidare la traiettoria d'attacco..."
            className="w-full mt-2 px-3 py-2 rounded border border-[var(--bg-border)] bg-[var(--bg-card)] text-[var(--text-primary)] text-sm resize-none h-20 focus:outline-none focus:border-[var(--accent-blue)]"
          />
        )}
      </div>

      {/* Related techniques */}
      {relations && selectedTechniqueId && (
        <div className="pt-2 border-t border-[var(--bg-border)] space-y-1.5">
          <p className="text-xs font-medium text-[var(--text-muted)]">Tecniche complementari:</p>
          <div className="flex flex-wrap gap-1">
            {relations.complements.map(comp => (
              <button
                key={comp.technique_id}
                onClick={() => onSelect(comp.technique_id, customPrompt || undefined)}
                className={clsx(
                  'text-xs px-2 py-1 rounded border transition-colors',
                  selectedTechniqueId === comp.technique_id
                    ? 'border-[var(--accent-green)] bg-green-900/30 text-[var(--accent-green)]'
                    : 'border-[var(--bg-border)] text-[var(--text-muted)] hover:border-[var(--accent-green)]'
                )}
              >
                {comp.technique_id} ({Math.round(comp.strength * 100)}%)
              </button>
            ))}
          </div>
          {relations.counters.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {relations.counters.map(counter => (
                <span
                  key={counter.layer_id}
                  className="text-xs px-2 py-1 rounded border border-red-800 text-red-400 opacity-70"
                  title={counter.evidence}
                >
                  counter: {counter.layer_id}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
