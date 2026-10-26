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

### Overseas / global

| Pattern | Platform id |
| --- | --- |
| `youtube.com`, `youtu.be`, `youtube.com/shorts` | `youtube` |
| `x.com/*/status/*`, `twitter.com/*/status/*` | `x` |
| `instagram.com/p/`, `/reel/`, `/reels/`, `/tv/` | `instagram` |
| `tiktok.com/@*/video/*`, `vm.tiktok.com`, `tiktok.com/t/` | `tiktok` |
| `threads.net/@*/post/*`, `threads.com/@*/post/*` | `threads` |
| `reddit.com/r/*/comments/*`, `redd.it/*` | `reddit` |
| `linkedin.com/posts/`, `/pulse/`, `/feed/update/` | `linkedin` |
| `facebook.com`, `fb.watch` | `facebook` |
| `t.me/{channel}/{id}`, `t.me/s/{channel}/{id}` | `telegram` |
| `vimeo.com/{id}`, `player.vimeo.com/video/{id}` | `vimeo` |
| `twitch.tv/videos/*`, `clips.twitch.tv/*` | `twitch` |

### Chinese

| Pattern | Platform id |
| --- | --- |
| `bilibili.com/video/BV*`, `b23.tv/*` | `bilibili` |
| `douyin.com/video/*`, `v.douyin.com/*` | `douyin` |
| `xiaohongshu.com/explore/*`, `xhslink.com/*` | `xiaohongshu` |
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
  "fetch_method": "host_connector|oembed|public_api|public_webfetch|public_curl|user_paste|user_export|user_media_asr|blocked",
  "confidence": "high|medium|low",
  "limits": ["..."]
}
```

## Path priority (every platform)

For user-supplied files, run the [ASR pipeline](SKILL.md#asr-pipeline) directly; a working remote URL is not required. Short-form video speech (IG / TikTok / Douyin / 视频号) can be understood this way even when remote fetching is blocked. A successful ASR record uses `body_kind: transcript`, copies ASR `text` into `body_text`, and records backend/model/language in `media_notes`. Platform-specific ordering takes precedence over the generic list below.

1. **Host connector / MCP** already attached to the agent (best).
2. **Official public API or oEmbed** documented by the platform.
3. **Transcript / caption endpoints** meant for accessibility (YouTube, Bilibili CC, Vimeo text tracks).
4. **User-assisted**: user opens page, pastes text, or exports media.
5. **User media + ASR** for speech when remote transcript is unavailable.
6. **Blocked**: stop. Do not invent scrapers that fight ToS or auth walls.

## Windows + Codex placement

- Skill docs live in-repo under `skills/social-content-reader/`.
- Long fetch + summarize jobs: `codex exec` from the Windows clone.
- Keep secrets out of git; pass API keys via environment only when using official APIs.

## Extensibility

New platform = new `platforms/<id>.md` + one row in `SKILL.md` matrix + URL patterns here + `normalize_url.py` detect branch. No need to change the normalize schema if `body_kind` / `limits` stay honest.
