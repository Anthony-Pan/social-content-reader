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
│ 2. Resolve path │  connector? → public caption/oEmbed/share text? → transcript?
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
│ 5. Understand   │  summarize / Q&A over body_text (caption, post, or transcript)
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
| `weixin.qq.com/sph/<id>`, `www.weixin.qq.com/sph/<id>` (`link_form: sph_share`) | `wechat-channels` |
| `channels.weixin.qq.com`, other 视频号 cards | `wechat-channels` |
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
  "body_kind": "transcript|article|post_text|caption|caption_only|unavailable",
  "media_notes": "has video; transcript from captions",
  "fetch_method": "host_connector|oembed|public_api|webfetch|public_webfetch|public_curl|user_paste|user_export|user_media_asr|blocked",
  "confidence": "high|medium|low",
  "limits": ["..."]
}
```

## Path priority (every platform)

For user-supplied files, run the [ASR pipeline](SKILL.md#asr-pipeline) directly; a working remote URL is not required. A successful ASR record uses `body_kind: transcript`, copies ASR `text` into `body_text`, and records backend/model/language in `media_notes`. Platform-specific ordering takes precedence over the generic list below.

On Instagram, TikTok, Douyin, Threads, X, Facebook, and WeChat 视频号, a nonempty public caption or post text is a successful understand path. ASR is optional after that.

1. **Host connector / MCP** already attached to the agent (best).
2. **Official public API, oEmbed, or share-page text** (WebFetch). A nonempty caption or post text is enough to understand the post.
3. **Transcript endpoints** when the platform publishes them (YouTube, Bilibili CC, Vimeo text tracks) or the user asked for spoken words.
4. **User media + ASR** only when the user wants a spoken/verbatim transcript, or the caption is empty/useless.
5. **Blocked**: stop. Do not invent scrapers that fight ToS or auth walls.

`caption` and `caption_only` both mean caption/description text. That text is enough for the Understanding section. It is not a spoken transcript. `webfetch` and `public_webfetch` both mean a host page-text fetch (WebFetch or equivalent). Prefer WebFetch over bare curl when the platform doc says curl returns a JS shell.

## Runtimes

- Skill docs live in-repo under `skills/social-content-reader/`.
- Windows 24/7 is fine for heavy `codex exec` jobs. Mac and Linux fully support Codex skill load, fetch, and local ASR. See [INSTALL_OWN.md](../../INSTALL_OWN.md).
- Keep secrets out of git; pass API keys via environment only when using official APIs.

## Extensibility

New platform = new `platforms/<id>.md` + one row in `SKILL.md` matrix + URL patterns here + `normalize_url.py` detect branch. No need to change the normalize schema if `body_kind` / `limits` stay honest.
