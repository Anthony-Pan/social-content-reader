# Facebook

**Status:** Partial — public Page posts via authorized Graph API or user paste; personal posts usually unavailable.

## URL patterns

- `https://www.facebook.com/{page}/posts/{id}`
- `https://www.facebook.com/watch/?v={id}`
- `https://fb.watch/{short}`
- `https://www.facebook.com/reel/{id}`
- Share links that redirect to the above

## Prefer (in order)

1. **Meta Graph API** with a Page/User token the user authorized (host connector preferred).
2. **Public oEmbed** for some public URLs:
   `GET https://www.facebook.com/plugins/post/oembed.json?url=<urlencoded>`
   (Availability varies; treat failures as normal.)
3. **User paste** of the post text / Reel caption.
4. Reels/video speech: user media + ASR (`asr_local.py`).
5. Optional approved download of a *public* video URL the user owns or explicitly approves — never login bypass.

## Fetch recipe

1. Canonicalize share short-links when possible.
2. Try Graph connector → oEmbed → user paste/ASR.
3. Set honest `body_kind` (`post_text`, `caption_only`, `transcript`, `unavailable`).
4. Understanding only from obtained body text.

## Honest limits

- Personal profiles and most non-public posts are not agent-readable without authorization.
- No scraping facebook.com HTML while logged in via stolen cookies.
- Graph API permissions are narrowly scoped; document `FACEBOOK_ACCESS_TOKEN` / Page id as env conventions only.

## Codex prompt sketch

```text
Follow platforms/facebook.md. URL: <URL>
Prefer Graph connector or paste; oEmbed if public. No auth bypass.
```

## References

- Meta Graph API — Pages / Video
- Facebook oEmbed / plugins documentation
