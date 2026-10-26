# TikTok (global)

**Status:** Works. The public oEmbed caption is the default understanding path. ASR is an optional upgrade for spoken-verbatim, or when the caption is empty.

**Goal:** Understand what the clip is about from the public caption (claims, topic, tone). Spoken dialogue is optional.

## URL patterns

- `https://www.tiktok.com/@{user}/video/{id}`
- `https://www.tiktok.com/t/{short}` (resolve redirects first)
- `https://vm.tiktok.com/{short}` (resolve redirects)
- Regional hosts that redirect to `tiktok.com` video pages

## Prefer (in order)

1. **Host TikTok / social connector** if the agent already has one that returns caption or transcript text.
2. **Public oEmbed** (the default success path):
   `GET https://www.tiktok.com/oembed?url=<urlencoded video url>`
   Returns author, title/caption text, and thumbnail. Store the caption as `body_text`, `body_kind: caption`, `fetch_method: oembed`, then write Understanding from it. Do not ask for a media file.
3. **User paste** only when oEmbed returns no usable caption.
4. **User-provided media + ASR** (`scripts/asr_local.py`) only when the user asks for spoken words, or the caption is empty:

   ```powershell
   python skills/social-content-reader/scripts/asr_local.py --media "C:\Media\tiktok.mp4" --language auto --backend auto --model base
   ```

   Mac / Linux: `python3` and `"$HOME/Media/tiktok.mp4"`.
5. Optional download tools (e.g. yt-dlp) **only** with explicit user approval for that exact URL; then ASR the file if speech was requested. Do not bundle scrapers here.

## Fetch recipe

1. Normalize to a canonical `tiktok.com/@…/video/{id}` URL when possible (`normalize_url.py`).
2. Try connector → oEmbed for caption text.
3. When the caption is nonempty, summarize claims, tips, and topic from `body_text`. Label `body_kind: caption`. Do not invent spoken lines that are not in the caption, and do not withhold the summary because ASR was not run.
4. If the caption is empty and the user still wants to know what was said, ask for a paste or a file and use ASR. Set `body_kind: transcript` and `fetch_method: user_media_asr` only after ASR succeeds.

## Honest limits

- Private, region-blocked, or deleted videos → unavailable.
- No login bypass, captcha defeat, or unofficial private API scrapers.
- TikTok ToS restricts automated bulk access — prefer connector / single oEmbed lookups.

## Codex prompt sketch

```text
Follow platforms/tiktok.md. URL: <URL>
oEmbed caption → understand. ASR only for spoken-verbatim or an empty caption.
Return ContentRecord + understanding.
```

## References

- TikTok oEmbed: https://developers.tiktok.com/doc/embed-videos
