# Vimeo

**Status:** ✅ Works when captions/text tracks exist; otherwise metadata + user media ASR.

## URL patterns

- `https://vimeo.com/{id}`
- `https://vimeo.com/{user}/{id}`
- `https://player.vimeo.com/video/{id}`

## Prefer (in order)

1. **Host Vimeo connector** if present.
2. **Public oEmbed**:
   `GET https://vimeo.com/api/oembed.json?url=<urlencoded>`
   → title, author, description (description ≠ transcript).
3. **Official Vimeo API** text tracks / transcripts when the user has an access token and the video exposes captions (`VIMEO_ACCESS_TOKEN` env).
4. If no captions: user-approved download or user-supplied file → `asr_local.py`.
5. Never treat the description as spoken content.

## Fetch recipe

1. Extract numeric video id (`normalize_url.py`).
2. oEmbed for metadata; API or connector for text tracks.
3. Set `body_kind: transcript` only when real captions/ASR exist.
4. Summarize from transcript; flag auto-caption uncertainty.

## Honest limits

- Private / password / domain-restricted videos need authorization.
- oEmbed description alone is **not** understanding.
- Respect Vimeo ToS; no login bypass.

## Codex prompt sketch

```text
Follow platforms/vimeo.md. URL: <URL>
Prefer captions/transcript over description. Else user media+ASR.
```

## References

- Vimeo oEmbed: https://developer.vimeo.com/api/oembed
- Vimeo API text tracks
