# Incidents and Realtime

This workstream covers run-level incident grouping and live UI behavior.

---

## Delivered

- detailed data-quality and drift incidents still exist as evidence
- incidents are grouped by run through `incident_groups`
- one primary incident becomes the top-level alert for the incident list and Slack
- incident WebSocket reconnect behavior was hardened
- grouped incidents now refresh without a manual page reload
- navbar notification updates now use the incident WebSocket for unread count changes
- notification dropdown context shows recent incident alerts and external delivery paths

---

## UI Model

### Top-level list

- `GET /incidents/` returns grouped representative incidents
- each top-level card or row represents one run-level alert

### Drill-down

- `GET /incidents/{incident_id}/children` returns the underlying incident evidence inside the group

### Live updates

- `WS /ws/incidents` refreshes the grouped list and navbar notification state
- `WS /ws/agent-trace/{run_id}` powers the live RCA stepper

### Navbar notifications

- the topbar bell connects to `WS /ws/incidents`
- `incident_created` and `incident_updated` events trigger an incident refresh
- notification details are loaded through tenant-scoped REST APIs before display
- read/unread state is scoped per tenant and user in browser storage
- periodic refresh remains as a fallback if the WebSocket is unavailable

---

## Production Value

This reduces alert noise in two ways:

- the UI is centered on one run-level alert instead of dozens of child findings
- Slack can stay human-readable without losing the underlying evidence model
- the navbar gives users immediate in-app visibility even if they are not watching Slack

---

## Production Hardening

The current UI renders tenant-safe data by refetching incidents through authenticated tenant-scoped APIs before display. For public multi-tenant production, the WebSocket transport should also be tenant-authenticated and tenant-scoped. Prefer tenant-specific Redis channels such as `incidents:{tenant_id}` or server-side filtering before sending events to browsers.

---

## Related Docs

- [realtime_tracing.md](./realtime_tracing.md)
- [notifications.md](./notifications.md)
- [database_schema.md](./database_schema.md)
- [api_reference.md](./api_reference.md)
