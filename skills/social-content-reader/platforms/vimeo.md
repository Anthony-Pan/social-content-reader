# Vimeo

**Status:** Works when text tracks or a media file are read. The oEmbed description is not the video.

## URL patterns

- `https://vimeo.com/{id}`
- `https://vimeo.com/{user}/{id}`
- `https://player.vimeo.com/video/{id}`

## Video and graphics

Text tracks are **speech**. Default video Understanding also needs frames, OCR, and host vision ([_video-body.md](_video-body.md)). The oEmbed description stays in `caption`. If the file and the text track are both missing, say the video was not watched.

## Prefer (in order)

1. **Host Vimeo connector** if it returns text tracks or the media file.
2. **Official Vimeo API** text tracks when the user has an access token and the video exposes captions (`VIMEO_ACCESS_TOKEN` env). That fills `speech_text` only.
3. **yt-dlp** when the user asked to read the video, or a file they supplied. Then frames + OCR + host vision + ASR if there is no text track. Stop on password, domain restriction, or login.
4. **Public oEmbed** for metadata only:
   `GET https://vimeo.com/api/oembed.json?url=<urlencoded>`
   Title, author, description → `caption`. Never the body.

## Fetch recipe

1. Extract numeric video id (`normalize_url.py`).
2. Text tracks or ASR → `speech_text`. Frames → `visual_text` / `visual_description`.
3. Set `body_kind: media_understanding` only when pictures and speech were both read. Text-track-only is `transcript` with graphics unread.
4. Summarize from speech + visuals. Flag auto-caption uncertainty. Description stays in `caption`.

## Honest limits

- Private / password / domain-restricted videos need authorization.
- oEmbed description alone is **not** understanding.
- Respect Vimeo ToS; no login bypass.

## Codex prompt sketch

```text
Follow platforms/vimeo.md and platforms/_video-body.md. URL: <URL>
Speech from text tracks or ASR. Frames for graphics. Description is metadata.
If acquire fails and there is no text track, say the video was not watched.
```

## References

- Vimeo oEmbed: https://developer.vimeo.com/api/oembed
- Vimeo API text tracks
