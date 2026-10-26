# TikTok (global)

**Status:** Partial — caption/description via public oEmbed when available; speech via user media + ASR.

**Goal:** Understand what the clip *says* (speech) and/or on-screen caption text — not only the share card.

## URL patterns

- `https://www.tiktok.com/@{user}/video/{id}`
- `https://www.tiktok.com/t/{short}` (resolve redirects first)
- `https://vm.tiktok.com/{short}` (resolve redirects)
- Regional hosts that redirect to `tiktok.com` video pages

## Prefer (in order)

1. **Host TikTok / social connector** if the agent already has one that returns caption + transcript.
2. **Public oEmbed** (embed metadata; not full speech):
   `GET https://www.tiktok.com/oembed?url=<urlencoded video url>`
   Returns author, title/caption text, thumbnail. Documented embed endpoint — use for caption/`body_kind: caption_only` only.
3. **User paste** of on-screen captions / creator transcript.
4. **User-provided media + ASR** (`scripts/asr_local.py`) for spoken content:
   ```powershell
   python skills/social-content-reader/scripts/asr_local.py --media "C:\Media\tiktok.mp4" --language auto --backend auto --model base
   ```
5. Optional download tools (e.g. yt-dlp) **only** with explicit user approval for that exact URL; then ASR the file. Do not bundle scrapers here.

## Fetch recipe

1. Normalize to a canonical `tiktok.com/@…/video/{id}` URL when possible (`normalize_url.py`).
2. Try connector → oEmbed for caption text.
3. If the user needs speech understanding and oEmbed caption is insufficient, ask for export/download or approved fetch → ASR.
4. Set `body_kind: caption_only` for oEmbed-only; `transcript` + `fetch_method: user_media_asr` after ASR.
5. Summarize claims from `body_text`; note music-only / silent visual limits.

## Honest limits

- oEmbed ≠ video understanding. Do not invent dialogue from a caption.
- Private, region-blocked, or deleted videos → unavailable.
- No login bypass, captcha defeat, or unofficial private API scrapers.
- TikTok ToS restricts automated bulk access — prefer connector / user media / single oEmbed lookups.

## Codex prompt sketch

```text
Follow platforms/tiktok.md. URL: <URL>
Prefer connector → oEmbed caption → user media+ASR.
Return ContentRecord + understanding. Flag caption-only vs transcript.
```

## References

- TikTok oEmbed: https://developers.tiktok.com/doc/embed-videos
