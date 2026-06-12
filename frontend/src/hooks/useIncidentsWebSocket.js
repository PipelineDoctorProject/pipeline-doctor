import { useCallback, useEffect, useRef, useState } from "react";
import { WS_BASE_URL } from "../config/runtime";

const WS_BASE = WS_BASE_URL;
const RECONNECT_DELAY_MS = 2000;

export default function useIncidentsWebSocket() {
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const manuallyClosedRef = useRef(false);
  const [isLive, setIsLive] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);

  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimerRef.current) {
      window.clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  const disconnect = useCallback(() => {
    manuallyClosedRef.current = true;
    clearReconnectTimer();
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsLive(false);
  }, [clearReconnectTimer]);

  const connect = useCallback(() => {
    manuallyClosedRef.current = false;
    clearReconnectTimer();

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const ws = new WebSocket(`${WS_BASE}/ws/incidents`);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsLive(true);
      clearReconnectTimer();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event === "ping" || data.event === "connected") return;
        setLastMessage(data);
      } catch {
        // Ignore malformed websocket frames.
      }
    };

    ws.onerror = () => {
      setIsLive(false);
    };

    ws.onclose = () => {
      wsRef.current = null;
      setIsLive(false);

      if (manuallyClosedRef.current) {
        return;
      }

      clearReconnectTimer();
      reconnectTimerRef.current = window.setTimeout(() => {
        connect();
      }, RECONNECT_DELAY_MS);
    };
  }, [clearReconnectTimer]);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isLive,
    lastMessage,
    connect,
    disconnect,
  };
}
