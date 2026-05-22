import { useCallback, useEffect, useRef, useState } from "react";

const WS_BASE = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

export default function useIncidentsWebSocket() {
  const wsRef = useRef(null);
  const [isLive, setIsLive] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsLive(false);
  }, []);

  const connect = useCallback(() => {
    disconnect();

    const ws = new WebSocket(`${WS_BASE}/ws/incidents`);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsLive(true);
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
      setIsLive(false);
    };
  }, [disconnect]);

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
