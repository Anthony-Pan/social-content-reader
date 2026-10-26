# X / Twitter

**Status:** ✅ Partial (public single-post text)

**Goal:** Read what the post *says*. Media and threads need more than oEmbed.

## URL patterns

- `https://x.com/{user}/status/{id}`
- `https://twitter.com/{user}/status/{id}`
- `https://mobile.x.com/...`

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
5. Understanding: claims, links, tone. If media-only joke/meme, say text is insufficient.

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
