import { useEffect, useRef, useState, useCallback } from "react";
import { WS_BASE_URL } from "../config/runtime";

const WS_BASE = WS_BASE_URL;

/**
 * useAgentWebSocket
 *
 * Connects to the configured API websocket endpoint for a run trace.
 * and streams LangGraph step events in real time.
 *
 * Returns:
 *   steps      — array of step state objects for AgentTraceStepper
 *   isLive     — true while the WebSocket is open
 *   runStatus  — "idle" | "running" | "complete" | "failed"
 *   lastMessage— the raw last event received
 *   connect(runId) — call this to start watching a run
 *   disconnect()   — call this to close the connection
 */

const STEP_NAMES = ["detection", "reasoning", "parser", "reporting"];

function buildInitialSteps() {
  return STEP_NAMES.map((name, i) => ({
    step_index: i,
    step_name: name,
    status: "pending",   // pending | running | done | error
    message: "",
    log_type: "action",
  }));
}

export default function useAgentWebSocket() {
  const wsRef = useRef(null);
  const [steps, setSteps] = useState(buildInitialSteps());
  const [isLive, setIsLive] = useState(false);
  const [runStatus, setRunStatus] = useState("idle"); // idle | running | complete | failed
  const [lastMessage, setLastMessage] = useState(null);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsLive(false);
  }, []);

  const connect = useCallback((runId) => {
    // Close any existing connection
    disconnect();

    // Reset step states for the new run
    setSteps(buildInitialSteps());
    setRunStatus("running");
    setLastMessage(null);

    const url = `${WS_BASE}/ws/agent-trace/${runId}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsLive(true);
      console.log(`[WS] Connected to agent-trace/${runId}`);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Ignore heartbeat pings
        if (data.event === "ping" || data.event === "connected") return;
        setLastMessage(data);

        if (data.event === "step_update") {
          setSteps((prev) =>
            {
              let changed = false;

              const next = prev.map((step) => {
                if (step.step_index !== data.step_index) return step;
                if (step.status === data.status && step.message === data.message) return step;

                changed = true;
                return { ...step, status: data.status, message: data.message };
              });

              return changed ? next : prev;
            }
          );
        }

        if (data.event === "run_complete") {
          setRunStatus("complete");
          // Mark any still-pending steps as done for safety
          setSteps((prev) =>
            {
              let changed = false;

              const next = prev.map((step) => {
                if (step.status === "pending" || step.status === "running") {
                  changed = true;
                  return { ...step, status: "done" };
                }

                return step;
              });

              return changed ? next : prev;
            }
          );
          setIsLive(false);
        }

        if (data.event === "run_failed") {
          setRunStatus("failed");
          // Mark the currently running step as error
          setSteps((prev) =>
            {
              let changed = false;

              const next = prev.map((step) => {
                if (step.status === "running") {
                  changed = true;
                  return { ...step, status: "error" };
                }

                return step;
              });

              return changed ? next : prev;
            }
          );
          setIsLive(false);
        }
      } catch {
        // Non-JSON message — ignore
      }
    };

    ws.onerror = (err) => {
      console.warn("[WS] WebSocket error:", err);
    };

    ws.onclose = () => {
      setIsLive(false);
      console.log(`[WS] Disconnected from agent-trace/${runId}`);
    };
  }, [disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    steps,
    isLive,
    runStatus,
    lastMessage,
    connect,
    disconnect,
  };
}
