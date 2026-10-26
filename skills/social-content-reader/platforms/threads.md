# Threads (Meta)

**Status:** Partial — public post text when oEmbed / public HTML works. Video Understanding needs a local file ([shared video recipe](_video-body.md)).

## URL patterns

- `https://www.threads.net/@{user}/post/{id}`
- `https://www.threads.com/@{user}/post/{id}` (alias host)

## Video and graphics

The post text is the post. An attached video is not understood from that text. Acquire a file (user save, or `yt-dlp` when the user asked to read that public video and it downloads without a login bypass), then frames + OCR + host vision + ASR. If acquire fails, say the video was not watched. Keep any caption in `caption`.

## Prefer (in order)

1. **Host Meta / Threads connector** if present.
2. **Public oEmbed** when Meta exposes it for the URL:
   `GET https://www.threads.net/oembed?url=<urlencoded post url>`
   (If the endpoint 404s for a given post, fall through — do not invent private Graph calls.)
3. **WebFetch / curl** of the public post URL with a browser-like UA; extract visible post text only from the returned HTML/JSON-LD when present. Stop on login walls.
4. User paste of the post text.
5. For video posts: the [media pipeline](_video-body.md), not the caption.

## Fetch recipe

1. Canonicalize URL; keep `@user` and post id.
2. Try connector → oEmbed → polite public page read.
3. Set `body_kind: post_text` when full text available; note truncation.
4. Understanding of a text post comes from the post text. Video claims wait for the media pipeline.

## Honest limits

- Login-gated, restricted, or deleted posts → unavailable.
- No cookie dumping, login bypass, or unofficial private Graph scrapers.
- Threads and Instagram share Meta ToS — respect rate limits; prefer user paste when blocked.

## Codex prompt sketch

```text
Follow platforms/threads.md. URL: <URL>
Return ContentRecord + short understanding. Flag login walls honestly.
```

## References

- Meta oEmbed / Threads help docs for embedding public posts
