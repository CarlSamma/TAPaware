import { useState, useEffect, useCallback, createContext, useContext } from 'react';
import type { Toast, ToastType } from '../../types/tap';
import { useWebSocket } from '../../hooks/useWebSocket';

// ---- Toast Context ----
interface ToastContextValue {
  addToast: (toast: Omit<Toast, 'id'>) => void;
}

const ToastContext = createContext<ToastContextValue>({ addToast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

// ---- Toast Provider & Container ----

let toastId = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const { on } = useWebSocket();

  const addToast = useCallback((t: Omit<Toast, 'id'>) => {
    const id = String(++toastId);
    const duration = t.duration ?? 6000;
    setToasts(prev => [...prev, { ...t, id }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(toast => toast.id !== id));
    }, duration);
  }, []);

  // Auto-toast from WebSocket events
  useEffect(() => {
    const unsubs = [
      on('cycle_timeout', (data) => {
        addToast({
          type: 'error',
          title: 'Cycle Timeout',
          message:
            (data.error as string) ||
            'Nessuna risposta ricevuta. Usa Force Reset per riprovare.',
          duration: 12000,
        });
      }),
      on('cycle_failed', (data) => {
        addToast({
          type: 'error',
          title: 'Cycle Failed',
          message: (data.error as string) || 'Errore sconosciuto durante il ciclo.',
        });
      }),
      on('cycle_status', (data) => {
        if (data.is_running === false) {
          addToast({
            type: 'success',
            title: 'Ciclo Completato',
            message: 'Il ciclo di attacco è terminato.',
          });
        }
      }),
      on('force_reset', (data) => {
        addToast({
          type: 'warning',
          title: 'Force Reset',
          message: `Engine resettato (era in esecuzione: ${data.was_running ? 'sì' : 'no'}).`,
        });
      }),
      on('property_confirmed', (data) => {
        addToast({
          type: 'success',
          title: 'Proprietà Confermata',
          message: `${data.property_key} = ${data.property_value}`,
        });
      }),
    ];
    return () => unsubs.forEach(fn => fn());
  }, [on, addToast]);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
        {toasts.map(toast => (
          <ToastItem key={toast.id} toast={toast} onDismiss={removeToast} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

// ---- Single Toast Item ----

function ToastItem({
  toast,
  onDismiss,
}: {
  toast: Toast;
  onDismiss: (id: string) => void;
}) {
  const [exiting, setExiting] = useState(false);

  const handleDismiss = () => {
    setExiting(true);
    setTimeout(() => onDismiss(toast.id), 300);
  };

  const bgColor: Record<ToastType, string> = {
    info: 'bg-[#1c2333] border-[var(--accent-blue)]',
    success: 'bg-[#1a2a1a] border-[var(--accent-green)]',
    warning: 'bg-[#2a2a1a] border-[var(--accent-yellow)]',
    error: 'bg-[#2a1111] border-[var(--accent-red)]',
  };

  const iconMap: Record<ToastType, string> = {
    info: 'ℹ️',
    success: '✅',
    warning: '⚠️',
    error: '🔴',
  };

  return (
    <div
      className={`${bgColor[toast.type]} border rounded-lg p-3 shadow-lg ${
        exiting ? 'toast-exit' : 'toast-enter'
      }`}
    >
      <div className="flex items-start gap-2">
        <span className="text-sm">{iconMap[toast.type]}</span>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-semibold text-[var(--text-primary)]">{toast.title}</p>
          {toast.message && (
            <p className="text-xs text-[var(--text-muted)] mt-0.5">{toast.message}</p>
          )}
        </div>
        <button
          onClick={handleDismiss}
          className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-xs shrink-0"
        >
          ✕
        </button>
      </div>
    </div>
  );
}