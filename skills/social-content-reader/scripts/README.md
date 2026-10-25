# scripts/

Small **keyless** helpers only.

| Script | Purpose |
| --- | --- |
| `normalize_url.py` | Detect platform + canonical id/url from a link (no network) |

Run:

```powershell
python skills\social-content-reader\scripts\normalize_url.py "https://youtu.be/dQw4w9WgXcQ"
```

Heavy fetch/summarize belongs in Codex tasks guided by `platforms/*.md`, or in host MCP connectors — not in brittle scrapers checked into this folder.
