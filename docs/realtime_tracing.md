# Realtime Tracing

PipelineDoctor uses WebSockets plus Redis Pub/Sub for two live experiences:

- live RCA step updates while the doctor agent is running
- live grouped-incident refresh on the incidents page

---

## Current Realtime Architecture

```mermaid
flowchart LR
    A[Celery doctor or incident publisher] --> B[(Redis Pub/Sub)]
    B --> C[FastAPI WebSocket endpoints]
    C --> D[React hooks]
    D --> E[Incident drawer RCA stepper]
    D --> F[Incidents page grouped refresh]
```

---

## Endpoints

### `WS /ws/agent-trace/{run_id}`

Used by the incident drawer to stream live RCA execution for a run.

Common event types:

- `connected`
- `ping`
- `step_update`
- `run_complete`
- `run_failed`

### `WS /ws/incidents`

Used by the incidents page to refresh when incidents are created or updated.

Common event types:

- `connected`
- `ping`
- `incident_created`
- `incident_updated`

---

## Current UI Behavior

### Agent trace

The drawer:

1. loads stored `agent_runs`
2. loads stored `agent_step_logs`
3. connects to `WS /ws/agent-trace/{run_id}` when the run is still active
4. shows live progress until reporting finishes
5. reveals the final RCA card only after reporting is complete

### Incidents page

The incidents page:

1. loads grouped top-level incidents
2. connects to `WS /ws/incidents`
3. refreshes the grouped incident list when live events arrive
4. fetches children separately when the drawer opens

---

## Reliability Notes

Recent hardening changed two important runtime behaviors:

- the incident WebSocket hook now reconnects after unexpected socket closure
- the incident list is centered on run-level grouped alerts, not every raw child incident

---

## Related Files

- `backend/fastapi/app/api/routes/agent_trace.py`
- `backend/fastapi/app/services/websocket/connection_manager.py`
- `backend/fastapi/app/services/incidents/live_events.py`
- `frontend/src/hooks/useAgentWebSocket.js`
- `frontend/src/hooks/useIncidentsWebSocket.js`
- `frontend/src/pages/incidents/IncidentsPage.jsx`
