# Bilibili 哔哩哔哩

**Status:** ✅ Works often — official/community subtitle tracks + public video metadata; else user media + ASR.

## URL patterns

- `https://www.bilibili.com/video/BV{id}`
- `https://www.bilibili.com/video/av{aid}`
- `https://b23.tv/{short}` (resolve redirects)
- Bangumi / cheese (course) URLs may be paywalled — handle as unavailable without access

## Prefer (in order)

1. **Host Bilibili connector / MCP** if present (metadata + subtitles).
2. **Public view API + player subtitle endpoints** commonly used by third-party clients for *public* videos (no login). Typical flow:
   - Resolve bvid/aid
   - `https://api.bilibili.com/x/web-interface/view?bvid=BV…` for title/owner/desc
   - Obtain subtitle list from the player/subtitle API associated with the `cid` when the uploader provided CC
   - Use browser-like Referer `https://www.bilibili.com` when required by the API
3. If no subtitles: user media / approved download → `asr_local.py` (`--language zh` or `auto`).
4. Description (`desc`) alone is **not** a transcript — say so if that is all you have.

## Fetch recipe

1. Normalize b23 short links; extract BV id (`normalize_url.py`).
2. Fetch view metadata; then subtitles when available.
3. Set `body_kind: transcript` for CC/ASR; `caption_only` for desc-only.
4. Summarize from transcript; credit UP main; note danmaku is optional and not the same as speech.

## Honest limits

- 大会员 / paywalled / region-locked content → unavailable without authorization.
- Respect Bilibili ToS; polite rates; no login bypass.
- Danmaku (bullet comments) ≠ video speech unless the user asks for comment analysis.

## Codex prompt sketch

```text
Follow platforms/bilibili.md. URL: <URL>
Prefer official subtitles; else user media+ASR. Do not treat desc as speech.
```

## References

- Bilibili open web APIs (view / player) used for public metadata and CC
