import { useState, useEffect } from 'react';
import { api } from './useApi';
import type { EngineStatus } from '../types/tap';

export function useEngineStatus(intervalMs = 3000) {
  const [status, setStatus] = useState<EngineStatus | null>(null);

  useEffect(() => {
    const poll = async () => {
      try {
        setStatus(await api.status());
      } catch {
        /* ignore polling errors */
      }
    };
    poll();
    const id = setInterval(poll, intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  return status;
}