# X / Twitter

**Status:** Public single-post text works. An attached video needs a media file.

**Goal:** Read what the post says. When the post is a video or a media-only joke, follow [the shared video recipe](_video-body.md). oEmbed text is the post, not a watched video.

## URL patterns

- `https://x.com/{user}/status/{id}`
- `https://twitter.com/{user}/status/{id}`
- `https://mobile.x.com/...`

## Video and graphics

Written post text is `body_kind: post_text`. A video, GIF, or image that carries the claim still needs a local file: frames, OCR, host vision, and ASR when there is speech ([_video-body.md](_video-body.md)). `yt-dlp` is allowed when the user asked to read that public video and the URL downloads without a login bypass. If the file cannot be acquired, say the video was not watched. Do not treat the post caption as the video body.

## Prefer (in order)

1. **Host X connector** (official X API tools / agent X MCP) — best for full text, threads, media metadata.
2. **Public oEmbed** (no API key):  
   `GET https://publish.x.com/oembed?url=<urlencoded post url>`  
   Returns author + HTML/blockquote with post text. Documented embed endpoint; single public posts only.
3. Ask user to paste the post if oEmbed truncates or fails.

## Fetch recipe

1. Canonicalize to `https://x.com/{user}/status/{id}`.
2. Try host connector; else oEmbed.
3. Extract plain text from connector payload or oEmbed `html` / text fields.
4. Set `body_kind: post_text` when full text available; note truncation in `limits`.
5. Understanding of a text post comes from the post text. If the post is a video or the text is insufficient for the claim, acquire the media and read it. Do not describe unseen pictures from the caption.

## Honest limits

- oEmbed: **no** reply threads, search, timelines, like counts, or media file bytes. Long posts may end with ellipsis (~280-char era truncation still appears in embeds).
- Protected, deleted, suspended, age-restricted posts → unavailable.
- Scraping syndication/guest APIs is brittle and often ToS-hostile — **do not** document exploit paths here; use connector or oEmbed.
- Quoted posts / cards: may be incomplete via oEmbed.

## Codex prompt sketch

```text
Follow platforms/x.md. URL: <URL>
Prefer host X tools if present; else publish.x.com/oembed.
Return ContentRecord + short understanding. Flag truncation.
```

## References

- X oEmbed / publish embed endpoint usage (public posts)
- Official X API Post lookup when user has developer credentials

## Success criteria

- Nonempty post text via connector or oEmbed, with truncation flagged, **or** ask user to paste.
