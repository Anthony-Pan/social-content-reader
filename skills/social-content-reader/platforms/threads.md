# Threads (Meta)

**Status:** Partial — public post text when oEmbed / public HTML works; media speech via user media + ASR.

## URL patterns

- `https://www.threads.net/@{user}/post/{id}`
- `https://www.threads.com/@{user}/post/{id}` (alias host)

## Prefer (in order)

1. **Host Meta / Threads connector** if present.
2. **Public oEmbed** when Meta exposes it for the URL:
   `GET https://www.threads.net/oembed?url=<urlencoded post url>`
   (If the endpoint 404s for a given post, fall through — do not invent private Graph calls.)
3. **WebFetch / curl** of the public post URL with a browser-like UA; extract visible post text only from the returned HTML/JSON-LD when present. Stop on login walls.
4. User paste of the post text.
5. For video/audio posts: user media + ASR (`asr_local.py`).

## Fetch recipe

1. Canonicalize URL; keep `@user` and post id.
2. Try connector → oEmbed → polite public page read.
3. Set `body_kind: post_text` when full text available; note truncation.
4. Understanding from post text; media needs ASR or paste.

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
