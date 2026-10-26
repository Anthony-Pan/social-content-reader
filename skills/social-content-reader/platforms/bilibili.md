# Bilibili 哔哩哔哩

**Status:** Speech often works when uploader CC exists. A file download is **not** verified. Mac, 2026-10-26: `yt-dlp` returned **HTTP 412**. Public playurl still needs a recipe that has actually saved a file. Graphics need that file. The description is not the video.

## URL patterns

- `https://www.bilibili.com/video/BV{id}`
- `https://www.bilibili.com/video/av{aid}`
- `https://b23.tv/{short}` (resolve redirects)
- Bangumi / cheese (course) URLs may be paywalled — handle as unavailable without access

## Video and graphics

Uploader CC / subtitles are **speech** (`speech_text`). Default video Understanding also runs frames, OCR, and host vision on a local file ([_video-body.md](_video-body.md)). Do not claim `yt-dlp` or a public playurl gets that file: on Anthony’s Mac, 2026-10-26, `yt-dlp` returned HTTP 412. `desc` stays in `caption`. Danmaku is not speech unless the user asks for comment analysis. If there is no CC and no file, say the video was not watched.

## Prefer (in order)

1. **Host Bilibili connector / MCP** if present (metadata + subtitles).
2. **Public view API + player subtitle endpoints** commonly used by third-party clients for *public* videos (no login). Typical flow:
   - Resolve bvid/aid
   - `https://api.bilibili.com/x/web-interface/view?bvid=BV…` for title/owner/desc
   - Obtain subtitle list from the player/subtitle API associated with the `cid` when the uploader provided CC
   - Use browser-like Referer `https://www.bilibili.com` when required by the API
3. If no subtitles: a local file the user already has → `asr_local.py` (`--language zh` or `auto`) plus frames. `yt-dlp` / public playurl is not a verified acquire until a run saves a video file. HTTP 412 means stop and say the file was not acquired.
4. Description (`desc`) alone is not speech and not the picture. Store it in `caption` and set `body_kind: unavailable` until media or CC is read.

## Fetch recipe

1. Normalize b23 short links; extract BV id (`normalize_url.py`).
2. Fetch view metadata; then subtitles when available.
3. Set `body_kind: media_understanding` when CC/ASR and frames were both read. CC without frames is `transcript` (graphics unread). Desc-only is `unavailable` plus `caption`.
4. Summarize from speech + visuals; credit UP main; note danmaku is optional and not the same as speech.

## Honest limits

- 大会员 / paywalled / region-locked content → unavailable without authorization.
- Respect Bilibili ToS; polite rates; no login bypass.
- Danmaku (bullet comments) ≠ video speech unless the user asks for comment analysis.

## Codex prompt sketch

```text
Follow platforms/bilibili.md and platforms/_video-body.md. URL: <URL>
Subtitles or ASR for speech. Frames for graphics. desc is metadata.
If both are missing, say the video was not watched.
```

## References

- Bilibili open web APIs (view / player) used for public metadata and CC
