---
created: 2026-06-23
last_edited: 2026-06-23
version: 1.0
provenance: con_AHh3DteQbAZmeZWk
---
# zo.space Route Install Notes

1. Create a new zo.space API route at `/api/krisp-webhook`.
2. Paste the full code from `templates/zo-space-krisp-webhook.ts`.
3. In Zo Settings → Advanced, add `KRISP_WEBHOOK_SECRET`.
4. Configure Krisp to send `Authorization: Bearer <KRISP_WEBHOOK_SECRET>`.
5. Send a test webhook and check:

```bash
ls -la Personal/Integrations/krisp-meeting-blocks/incoming
python3 Skills/krisp-meeting-blocks/scripts/krisp_blocks.py status
```

The route is an API route and is publicly reachable. Do not deploy it without bearer authentication.
