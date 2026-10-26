# Facebook

**Status:** Works when Graph or public oEmbed returns post text or a Reel caption. Understand from that text. Personal posts usually stay unavailable. ASR is optional for spoken Reels.

## URL patterns

- `https://www.facebook.com/{page}/posts/{id}`
- `https://www.facebook.com/watch/?v={id}`
- `https://fb.watch/{short}`
- `https://www.facebook.com/reel/{id}`
- Share links that redirect to the above

## Prefer (in order)

1. **Meta Graph API** with a Page/User token the user authorized (host connector preferred). Use returned post text or caption as `body_text` and write Understanding from it.
2. **Public oEmbed** for some public URLs:
   `GET https://www.facebook.com/plugins/post/oembed.json?url=<urlencoded>`
   (Availability varies; treat failures as normal.) When the payload contains the post or Reel caption, set `body_kind: caption` or `post_text`, `fetch_method: oembed`, and understand it. Do not ask for a file first.
3. **User paste** only when Graph and oEmbed return no usable text.
4. Reels speech: user media + ASR (`asr_local.py`) only when the user asks for spoken words, or the caption is empty.
5. Optional approved download of a *public* video URL the user owns or explicitly approves — never login bypass. A summarize request is not download approval.

## Fetch recipe

1. Canonicalize share short-links when possible.
2. Try Graph connector → oEmbed. Understand immediately when either returns post text or a caption.
3. Set honest `body_kind` (`post_text`, `caption`, `transcript`, `unavailable`).
4. Understanding from obtained body text (5–12 lines). Paste and ASR are follow-ups for an empty caption or a spoken-verbatim ask.

## Honest limits

- Personal profiles and most non-public posts are not agent-readable without authorization.
- No scraping facebook.com HTML while logged in via stolen cookies.
- Graph API permissions are narrowly scoped; document `FACEBOOK_ACCESS_TOKEN` / Page id as env conventions only.

## Codex prompt sketch

```text
Follow platforms/facebook.md. URL: <URL>
Public caption or post text → understand. ASR only for spoken-verbatim or an empty caption. No auth bypass.
```

## References

- Meta Graph API — Pages / Video
- Facebook oEmbed / plugins documentation
