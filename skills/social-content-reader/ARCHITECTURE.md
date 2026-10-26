# Architecture

Adapter pattern for social content understanding.

```text
URL or local file
  │
  ▼
┌─────────────────┐
│ 1. Detect       │  hostname + path patterns → platform id
└────────┬────────┘
         ▼
┌─────────────────┐
│ 2. Classify     │  video/graphics  vs  written post/article
└────────┬────────┘
         ▼
┌──────────────────────────────┐
│ 3a. Video: acquire local file │  platform helper (Douyin playwm), yt-dlp
│     or honest acquire_failed  │  only where a file was saved, user file.
└────────┬─────────────────────┘
         ▼
┌─────────────────┐
│ 3b. Read media  │  frames → OCR → host vision → ASR or official transcript
└────────┬────────┘
         ▼
┌─────────────────┐
│ 4. Normalize    │  speech + visuals. Caption is a side field, not the body.
└────────┬────────┘
         ▼
┌─────────────────┐
│ 5. Understand   │  from pictures, burned-in text, and speech
└─────────────────┘
```

Written posts and articles (Reddit selftext, 公众号, X text, and similar) still fetch the written body. An attached video joins the media path. The shared steps live in [platforms/_video-body.md](platforms/_video-body.md).

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
  "body_text": "labeled join of visuals, OCR, and speech — or the article/post body",
  "body_kind": "media_understanding|transcript|visual|article|post_text|unavailable",
  "speech_text": "ASR or official transcript; empty when speech was not read",
  "visual_text": "OCR of burned-in text; empty when OCR did not run or found nothing",
  "visual_description": "host vision notes of the frames/video; empty when not looked at",
  "caption": "share caption or description, metadata only",
  "media_notes": "frame dir, ASR backend/model, OCR engine, truncation",
  "fetch_method": "media_pipeline|host_connector|oembed|public_api|webfetch|public_webfetch|public_curl|user_paste|user_export|user_media_asr|acquire_failed|blocked",
  "confidence": "high|medium|low",
  "limits": ["..."]
}
```

`body_kind: caption` is not a successful video read. Older notes may still say `caption` or `caption_only`; treat those values as metadata, not Understanding.

`body_kind: media_understanding` requires evidence from the file: `visual_description` and/or `visual_text`, plus `speech_text` (or an explicit speech-only / picture-only kind instead). A share caption does not qualify.

`fetch_method: acquire_failed` means no local file and no official speech track. Say the video was not watched.

## Path priority (every video)

Platform docs name the acquire tool that actually works. The shared order:

1. **Platform acquire helper** when that platform’s doc makes it the default. Douyin: `scripts/acquire_douyin.py` (mobile share `<video>` → playwm → mp4). Run it without asking the user to export.
2. **A file the user already attached.** Read it. Do not ask for an export before step 1 has been tried.
3. **yt-dlp** when the user asked to read the video and a run on that platform has saved a file (YouTube, Mac 2026-10-26). Stop on login, captcha, DRM, IP block, or HTTP 412. TikTok and Bilibili file download are not verified.
4. **Host connector** when it returns a real transcript and/or permitted media. Official CC (YouTube, Bilibili, Vimeo text tracks) fills `speech_text` only.
5. **Read the file:** `extract_frames.py` → `ocr_frames.py` → host vision/video tool → `asr_local.py` when speech is still missing.
6. **Acquire failed:** stop. `body_kind: unavailable`. Do not substitute the share caption. User export is a fallback only after the documented player returns no media URL.

For a file that is already on disk, start at step 5. A successful full read uses `body_kind: media_understanding` and `fetch_method: media_pipeline`. ASR-only is `transcript` / `user_media_asr` and must say graphics were not read.

Written posts and articles use their platform fetch (connector, oEmbed text, public JSON, WebFetch). That text is the post. It does not describe an attached video.

`webfetch` and `public_webfetch` both mean a host page-text fetch (WebFetch or equivalent).

## Runtimes

- Skill docs live in-repo under `skills/social-content-reader/`.
- Windows 24/7 is fine for heavy `codex exec` jobs. Mac and Linux fully support Codex skill load, fetch, ffmpeg frames, and local ASR. See [INSTALL_OWN.md](../../INSTALL_OWN.md).
- Keep secrets out of git; pass API keys via environment only when using official APIs.

## Extensibility

New platform = new `platforms/<id>.md` + one row in `SKILL.md` matrix + URL patterns here + `normalize_url.py` detect branch. Video platforms point at `_video-body.md`. No need to change the normalize schema if `body_kind` / `limits` stay honest.
