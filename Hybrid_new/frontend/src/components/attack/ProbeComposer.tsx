import { useState } from 'react';
import { api } from '../../hooks/useApi';
import { FollowUpCard } from './FollowUpCard';
import { TechniqueSelector } from './TechniqueSelector';
import type { FollowUpState } from '../../types/tap';

export function ProbeComposer({ isRunning }: { isRunning: boolean }) {
  const [followUpState, setFollowUpState] = useState<FollowUpState | null>(null);
  const [selectedTechniqueId, setSelectedTechniqueId] = useState<string | null>(null);
  const [customPrompt, setCustomPrompt] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTechniqueSelect = async (techniqueId: string, custom?: string) => {
    setSelectedTechniqueId(techniqueId);
    setCustomPrompt(custom);
    try {
      await api.selectTechnique(techniqueId, custom);
    } catch (e) {
      console.error('Failed to select technique:', e);
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      // Select technique first if chosen
      if (selectedTechniqueId) {
        await api.selectTechnique(selectedTechniqueId, customPrompt);
      }
      await api.generateOptions();
      const state = await api.followup();
      setFollowUpState(state);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Errore sconosciuto');
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (choice: 'A' | 'B') => {
    await api.selectOption(choice);
    setFollowUpState(prev =>
      prev
        ? {
            ...prev,
            selected_probe:
              choice === 'A' ? prev.followup!.option_a : prev.followup!.option_b,
          }
        : null
    );
  };

  const handlePost = async () => {
    setLoading(true);
    try {
      await api.postSelected();
      setFollowUpState(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Post fallito');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    await api.resetEngine();
    setFollowUpState(null);
    setError(null);
    setSelectedTechniqueId(null);
    setCustomPrompt(undefined);
  };

  return (
    <div className="space-y-4">
      {/* Technique Selector */}
      <div className="bg-[var(--bg-card)] rounded-lg p-3 border border-[var(--bg-border)]">
        <TechniqueSelector
          onSelect={handleTechniqueSelect}
          selectedTechniqueId={selectedTechniqueId}
        />
      </div>

      {/* Selected technique indicator */}
      {selectedTechniqueId && (
        <div className="flex items-center gap-2 px-3 py-2 rounded bg-[var(--accent-blue)]/10 border border-[var(--accent-blue)]/30 text-sm">
          <span className="text-[var(--accent-blue)]">Tecnica attiva:</span>
          <span className="font-medium text-[var(--text-primary)]">{selectedTechniqueId}</span>
          {customPrompt && (
            <span className="text-xs text-[var(--text-muted)] ml-auto" title={customPrompt}>
              + custom prompt
            </span>
          )}
        </div>
      )}

      {/* Generate button */}
      <div className="flex gap-2">
        <button
          onClick={handleGenerate}
          disabled={isRunning || loading}
          className="flex-1 py-2 px-4 rounded bg-[var(--accent-blue)] text-white text-sm font-medium disabled:opacity-40 hover:opacity-90 transition-opacity"
        >
          {loading ? 'Generazione...' : 'Genera Probe A/B'}
        </button>
        <button
          onClick={handleReset}
          className="py-2 px-3 rounded bg-[var(--bg-border)] text-[var(--text-muted)] text-sm hover:bg-red-900 hover:text-white transition-colors"
          title="Force Reset Engine"
        >
          ↺
        </button>
      </div>

      {error && (
        <p className="text-xs text-[var(--accent-red)] bg-red-950 rounded p-2">{error}</p>
      )}

      {isRunning && (
        <div className="flex items-center gap-2 text-sm text-[var(--accent-yellow)] bg-yellow-950 rounded p-2">
          <span className="animate-pulse">●</span> Ciclo in esecuzione...
        </div>
      )}

      {followUpState?.followup && !isRunning && (
        <FollowUpCard
          followup={followUpState.followup}
          selected={followUpState.selected_probe}
          onSelect={handleSelect}
          onPost={handlePost}
          loading={loading}
        />
      )}
    </div>
  );
}
