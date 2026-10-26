# Threads (Meta)

**Status:** Works when public post text is available via oEmbed or the public page. ASR is optional for spoken video, not a step before summarizing text you already have.

## URL patterns

- `https://www.threads.net/@{user}/post/{id}`
- `https://www.threads.com/@{user}/post/{id}` (alias host)

## Prefer (in order)

1. **Host Meta / Threads connector** if present and it returns post text.
2. **Public oEmbed** when Meta exposes it for the URL:
   `GET https://www.threads.net/oembed?url=<urlencoded post url>`
   (If the endpoint 404s for a given post, fall through — do not invent private Graph calls.)
3. **WebFetch / curl** of the public post URL with a browser-like UA; extract visible post text only from the returned HTML/JSON-LD when present. Stop on login walls.
4. User paste of the post text, only when the public fetch returned nothing usable.
5. For video/audio, user media + ASR (`asr_local.py`) only when the user asks for spoken words or the post text is empty.

## Fetch recipe

1. Canonicalize URL; keep `@user` and post id.
2. Try connector → oEmbed → polite public page read.
3. Set `body_kind: post_text` when the post text is available; note truncation. `body_kind: caption` is fine when the text is a short video caption.
4. Write Understanding from that text (claims, topic, tone). Do not ask for a file or a paste before summarizing text you already fetched.
5. Login-walled or empty responses: say so. Paste and ASR are the follow-ups, not the default.

## Honest limits

- Login-gated, restricted, or deleted posts → unavailable.
- No cookie dumping, login bypass, or unofficial private Graph scrapers.
- Threads and Instagram share Meta ToS — respect rate limits.

## Codex prompt sketch

```text
Follow platforms/threads.md. URL: <URL>
Public post text → understand. ASR only for spoken-verbatim or empty text.
Return ContentRecord + short understanding. Flag login walls honestly.
```

## References

- Meta oEmbed / Threads help docs for embedding public posts
