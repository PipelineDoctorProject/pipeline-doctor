# Slack

Slack integration provides workspace-level alert delivery for production incidents. The current design is intentionally centered on one top-level run alert instead of one message for every low-level finding.

---

## Goals

- connect one Slack workspace per OpsSight tenant
- let admins choose a default alert channel
- verify channel readiness before delivery
- avoid alert floods by sending one run-level incident alert
- keep detailed evidence available in OpsSight instead of posting huge payloads to Slack

---

## Delivery Model

```text
Pipeline run creates findings
    |
Incident group is created
    |
Primary run-level incident is selected
    |
Slack notification is sent once for the run-level incident
    |
User opens OpsSight for full child evidence, RCA, and remediation
```

This design keeps Slack human-readable while preserving full evidence in the UI and database.

---

## Channel Readiness

### Public channels

Public channels can be made ready automatically when the Slack app has the required scopes.

Recommended scopes:

- `chat:write`
- `chat:write.public`
- `channels:read`
- `channels:join`
- `groups:read`

### Private channels

Private channels require inviting the bot manually.

Example:

```text
/invite @opssight
```

---

## UI Behavior

The Slack page should show:

- connected workspace status
- expected workspace name or Slack team ID before OAuth starts
- default channel
- channel readiness
- action-required warnings
- disconnect/reconnect controls

When admins manage multiple Slack workspaces, the expected workspace field prevents an accidental install into whichever Slack workspace is active in the browser. If the exact Slack team ID is known, pass it to Slack's `team` parameter so Slack can target that workspace during OAuth.

The sidebar uses the Slack icon for the Slack integration page.

---

## Production Expectations

- Configure `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET`, and `SLACK_REDIRECT_URI` in the backend runtime.
- Register the same `SLACK_REDIRECT_URI` in the Slack app OAuth redirect URLs.
- Store Slack tokens securely.
- Never print full Slack payloads or tokens in terminal logs.
- Send concise alerts with links back to OpsSight.
- Send one alert per incident group/run.
- Use retry/backoff for transient Slack API failures.
- Keep channel-readiness validation separate from alert sending.

---

## Related Docs

- [incidents_and_realtime.md](./incidents_and_realtime.md)
- [api_reference.md](./api_reference.md)
- [setup.md](./setup.md)
