# X / Twitter

**Status:** ✅ Works for a public single post. Understand from the post text. ASR is optional when the post is media-only and the user wants spoken words.

**Goal:** Read what the post says, then summarize it. Reply threads and media bytes need more than oEmbed; that does not block understanding of the text you fetched.

## URL patterns

- `https://x.com/{user}/status/{id}`
- `https://twitter.com/{user}/status/{id}`
- `https://mobile.x.com/...`

## Prefer (in order)

1. **Host X connector** (official X API tools / agent X MCP) — best for full text, threads, media metadata.
2. **Public oEmbed** (no API key):  
   `GET https://publish.x.com/oembed?url=<urlencoded post url>`  
   Returns author + HTML/blockquote with post text. Documented embed endpoint; single public posts only. Nonempty text is `body_kind: post_text`, `fetch_method: oembed`. Write Understanding from it.
3. Ask the user to paste only when oEmbed fails or the extracted text is empty. A truncated post is still a body: summarize what you have and note the ellipsis.

## Fetch recipe

1. Canonicalize to `https://x.com/{user}/status/{id}`.
2. Try host connector; else oEmbed.
3. Extract plain text from connector payload or oEmbed `html` / text fields.
4. Set `body_kind: post_text` when full text available; note truncation in `limits`.
5. Understanding: claims, links, tone, in 5–12 lines. If the post is a media-only joke with no text, say the text is empty. Offer ASR only if the user wants spoken words.

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

- Nonempty post text via connector or oEmbed, with truncation flagged, plus Understanding. Ask for a paste only when that text is missing.
