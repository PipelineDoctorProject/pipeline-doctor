# Incidents and Realtime

This workstream covers run-level incident grouping and live UI behavior.

---

## Delivered

- detailed data-quality and drift incidents still exist as evidence
- incidents are grouped by run through `incident_groups`
- one primary incident becomes the top-level alert for the incident list and Slack
- incident WebSocket reconnect behavior was hardened
- grouped incidents now refresh without a manual page reload

---

## UI Model

### Top-level list

- `GET /incidents/` returns grouped representative incidents
- each top-level card or row represents one run-level alert

### Drill-down

- `GET /incidents/{incident_id}/children` returns the underlying incident evidence inside the group

### Live updates

- `WS /ws/incidents` refreshes the grouped list
- `WS /ws/agent-trace/{run_id}` powers the live RCA stepper

---

## Production Value

This reduces alert noise in two ways:

- the UI is centered on one run-level alert instead of dozens of child findings
- Slack can stay human-readable without losing the underlying evidence model

---

## Related Docs

- [realtime_tracing.md](./realtime_tracing.md)
- [database_schema.md](./database_schema.md)
- [api_reference.md](./api_reference.md)
