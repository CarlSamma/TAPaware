import { useState, useEffect, useCallback } from 'react';
import { api } from '../../hooks/useApi';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useToast } from '../toast/ToastContainer';
import type { SsotSnapshot, ConfirmedProperty } from '../../types/tap';

export function SsotViewer() {
  const [ssot, setSsot] = useState<SsotSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [confirming, setConfirming] = useState<string | null>(null);
  const { on } = useWebSocket();
  const { addToast } = useToast();

  const loadSsot = useCallback(async () => {
    try {
      const data = await api.ssot();
      setSsot(data);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSsot();
  }, [loadSsot]);

  // Refresh on WebSocket property_confirmed events
  useEffect(() => {
    return on('property_confirmed', () => {
      loadSsot();
    });
  }, [on, loadSsot]);

  const handleConfirm = async (prop: { key: string; value: string }) => {
    setConfirming(prop.key);
    try {
      await api.confirmProperty(prop.key, prop.value);
      addToast({
        type: 'success',
        title: 'Proprietà Confermata Manualmente',
        message: `${prop.key} = ${prop.value}`,
      });
      await loadSsot();
    } catch (e) {
      addToast({
        type: 'error',
        title: 'Conferma Fallita',
        message: e instanceof Error ? e.message : 'Errore sconosciuto',
      });
    } finally {
      setConfirming(null);
    }
  };

  if (loading) {
    return (
      <div className="text-xs text-[var(--text-muted)] p-4">Caricamento SSOT...</div>
    );
  }

  if (!ssot) {
    return (
      <div className="text-xs text-[var(--accent-red)] p-4">
        SSOT non disponibile
      </div>
    );
  }

  const totalProps =
    (ssot.confirmed_properties?.length ?? 0) +
    (ssot.unconfirmed_properties?.length ?? 0);
  const confirmedCount = ssot.confirmed_properties?.length ?? 0;
  const progressPct = totalProps > 0 ? (confirmedCount / totalProps) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Header & Progress */}
      <div>
        <div className="flex justify-between items-center mb-1">
          <h3 className="text-sm font-semibold text-[var(--text-muted)] uppercase tracking-wider">
            SSOT — {ssot.target_handle}
          </h3>
          <span className="text-xs text-[var(--text-muted)]">
            {confirmedCount}/{totalProps} proprietà
          </span>
        </div>
        {/* Progress bar */}
        <div className="w-full h-1.5 bg-[var(--bg-base)] rounded-full overflow-hidden">
          <div
            className="h-full bg-[var(--accent-green)] rounded-full transition-all duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* Confirmed Properties */}
      {ssot.confirmed_properties && ssot.confirmed_properties.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-[var(--accent-green)] mb-2">
            ✓ Confermate ({ssot.confirmed_properties.length})
          </h4>
          <div className="space-y-1">
            {ssot.confirmed_properties.map((prop: ConfirmedProperty, i: number) => (
              <div
                key={i}
                className="flex items-center justify-between text-xs bg-[#1a2a1a] rounded p-2 border border-[var(--accent-green)] border-opacity-20"
              >
                <span className="text-[var(--text-primary)] font-mono">
                  {prop.key} = {prop.value}
                </span>
                <span className="text-[var(--accent-green)]">
                  {((prop.confidence ?? 0) * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Unconfirmed Properties — with manual confirm button */}
      {ssot.unconfirmed_properties && ssot.unconfirmed_properties.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-[var(--accent-yellow)] mb-2">
            ⚡ Non Confermate ({ssot.unconfirmed_properties.length})
          </h4>
          <div className="space-y-1">
            {ssot.unconfirmed_properties.map(
              (prop: { key: string; value: string }, i: number) => (
                <div
                  key={i}
                  className="flex items-center justify-between text-xs bg-[#2a2a1a] rounded p-2 border border-[var(--accent-yellow)] border-opacity-20"
                >
                  <span className="text-[var(--text-muted)] font-mono">
                    {prop.key} = {prop.value}
                  </span>
                  <button
                    onClick={() => handleConfirm(prop)}
                    disabled={confirming === prop.key}
                    className="text-xs px-2 py-1 rounded bg-[var(--accent-green)] text-white hover:opacity-80 disabled:opacity-40 transition-opacity"
                    title="Conferma manualmente questa proprietà (Phase 0 unlock)"
                  >
                    {confirming === prop.key ? '...' : '✓ Conferma'}
                  </button>
                </div>
              )
            )}
          </div>
        </div>
      )}

      {(!ssot.confirmed_properties || ssot.confirmed_properties.length === 0) &&
        (!ssot.unconfirmed_properties || ssot.unconfirmed_properties.length === 0) && (
          <p className="text-xs text-[var(--text-muted)] text-center py-4">
            Nessuna proprietà SSOT disponibile
          </p>
        )}
    </div>
  );
}