# Current Sprint: Slack

This workstream covers Slack connectivity, delivery readiness, and production-style alert behavior.

---

## Delivered

- Slack OAuth workspace connection is live
- admins can select a default alert channel
- default channel readiness is validated before alert delivery
- Slack delivery is centered on the primary run-level incident
- the UI now shows readiness or action-required messaging instead of failing silently

---

## Current Delivery Rules

### Public channels

- can be made auto-ready when the app has the required scopes
- recommended scopes include:
  - `chat:write`
  - `chat:write.public`
  - `channels:read`
  - `channels:join`
  - `groups:read`

### Private channels

- still require inviting the bot manually

Example:

```text
/invite @opssight
```

---

## Current UI and API

- Slack status page shows workspace connection and default-channel readiness
- the backend validates the saved channel before relying on it for alert delivery
- disconnect and reconnect flows are available from the integration page

---

## Production Value

This closes the gap between “Slack is connected” and “Slack alerts will actually deliver.”

It also avoids noisy per-finding posting by keeping alerts centered on one run-level incident.

---

## Related Docs

- [api_reference.md](./api_reference.md)
- [incidents_and_realtime.md](./incidents_and_realtime.md)
