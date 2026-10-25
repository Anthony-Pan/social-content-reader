# Architecture

Adapter pattern for social content understanding.

```text
URL
  │
  ▼
┌─────────────────┐
│ 1. Detect       │  hostname + path patterns → platform id
└────────┬────────┘
         ▼
┌─────────────────┐
│ 2. Resolve path │  connector? → public API/oEmbed/transcript? → user-assist?
└────────┬────────┘
         ▼
┌─────────────────┐
│ 3. Fetch        │  only documented / allowed methods
└────────┬────────┘
         ▼
┌─────────────────┐
│ 4. Normalize    │  common ContentRecord schema
└────────┬────────┘
         ▼
┌─────────────────┐
│ 5. Understand   │  summarize / Q&A over body_text (not captions alone)
└─────────────────┘
```

## Platform detection (order matters)

| Pattern | Platform id |
| --- | --- |
| `youtube.com`, `youtu.be`, `youtube.com/shorts` | `youtube` |
| `x.com/*/status/*`, `twitter.com/*/status/*` | `x` |
| `instagram.com/p/`, `/reel/`, `/reels/`, `/tv/` | `instagram` |
| `mp.weixin.qq.com/s` | `wechat-article` |
| `channels.weixin.qq.com`, 视频号 share links | `wechat-channels` |
| Unknown | `unknown` → ask user or try generic web read with honesty |

Optional helper: `scripts/normalize_url.py` (canonical id extraction only).

## ContentRecord (normalize target)

```json
{
  "platform": "youtube",
  "url": "https://www.youtube.com/watch?v=...",
  "canonical_id": "dQw4w9WgXcQ",
  "title": "...",
  "author": "...",
  "published_at": "2026-...",
  "language": "en",
  "body_text": "full transcript or article body",
  "body_kind": "transcript|article|post_text|caption_only|unavailable",
  "media_notes": "has video; transcript from captions",
  "fetch_method": "host_connector|oembed|public_api|user_paste|blocked",
  "confidence": "high|medium|low",
  "limits": ["..."]
}
```

## Path priority (every platform)

1. **Host connector / MCP** already attached to the agent (best).
2. **Official public API or oEmbed** documented by the platform.
3. **Transcript / caption endpoints** meant for accessibility (YouTube).
4. **User-assisted**: user opens page, pastes text, or exports.
5. **Blocked**: stop. Do not invent scrapers that fight ToS or auth walls.

## Windows + Codex placement

- Skill docs live in-repo under `skills/social-content-reader/`.
- Long fetch + summarize jobs: `codex exec` from the Windows clone.
- Keep secrets out of git; pass API keys via environment (e.g. `YOUTUBE_API_KEY`) only when using official APIs.

## Extensibility

New platform = new `platforms/<id>.md` + one row in `SKILL.md` matrix + URL patterns here. No need to change the normalize schema if `body_kind` / `limits` stay honest.
