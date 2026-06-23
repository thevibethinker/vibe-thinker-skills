---
created: 2026-06-23
last_edited: 2026-06-23
version: 1.0
provenance: con_AHh3DteQbAZmeZWk
---

# zo.space Krisp Webhook Route Template

Use `templates/zo-space-krisp-webhook.ts` as the full source for a zo.space API route.

Recommended route path:

```text
/api/krisp-webhook
```

Security:

- Save `KRISP_WEBHOOK_SECRET` in Zo [Settings > Advanced](/?t=settings&s=advanced).
- Configure Krisp to send `Authorization: Bearer <secret>`.
- API routes are public at the network layer, so the bearer check is required.

Behavior:

- Writes raw payloads to `Personal/Integrations/krisp-meeting-blocks/incoming/`.
- Spawns `python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py import <payload> --process` for `transcript_created` events.
- Logs received/unauthorized/bad JSON events to `Personal/Integrations/krisp-meeting-blocks/webhook.log`.
