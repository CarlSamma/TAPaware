import { useEffect, useRef, useCallback, useState } from 'react';
import type { WsEvent } from '../types/tap';

type EventHandler = (data: Record<string, unknown>) => void;

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const handlers = useRef<Map<string, EventHandler[]>>(new Map());
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const [connected, setConnected] = useState(false);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Route through same host — Vite proxy forwards /ws to the API
    const url = `${protocol}//${window.location.host}/ws/live`;
    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      setConnected(true);
      // keepalive ping ogni 20s
      const ping = setInterval(() => {
        if (ws.current?.readyState === WebSocket.OPEN) {
          ws.current.send('ping');
        }
      }, 20000);
      ws.current!.onclose = () => {
        clearInterval(ping);
        setConnected(false);
        // reconnect after 3s
        reconnectTimer.current = setTimeout(connect, 3000);
      };
    };

    ws.current.onmessage = (e: MessageEvent) => {
      try {
        const msg: WsEvent = JSON.parse(e.data);
        const cbs = handlers.current.get(msg.event) ?? [];
        cbs.forEach(cb => cb(msg.data));
        // wildcard handlers
        (handlers.current.get('*') ?? []).forEach(cb =>
          cb({ event: msg.event, ...msg.data })
        );
      } catch {
        /* ignore parse errors */
      }
    };

    ws.current.onerror = () => ws.current?.close();
  }, []);

  useEffect(() => {
    connect();
    return () => {
      ws.current?.close();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    };
  }, [connect]);

  const on = useCallback((event: string, handler: EventHandler) => {
    const list = handlers.current.get(event) ?? [];
    handlers.current.set(event, [...list, handler]);
    return () => {
      handlers.current.set(
        event,
        (handlers.current.get(event) ?? []).filter(h => h !== handler)
      );
    };
  }, []);

  return { connected, on };
}