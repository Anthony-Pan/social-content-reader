# Facebook

**Status:** Partial — public Page posts via authorized Graph API or user paste; personal posts usually unavailable. Reels and videos need a media file.

## URL patterns

- `https://www.facebook.com/{page}/posts/{id}`
- `https://www.facebook.com/watch/?v={id}`
- `https://fb.watch/{short}`
- `https://www.facebook.com/reel/{id}`
- Share links that redirect to the above

## Video and graphics

Page post text from Graph, oEmbed, or a paste is the **post** (`body_kind: post_text`). A Reel or video is not understood from that caption. Acquire a file (user save, or `yt-dlp` when the user asked to read that public video and it downloads without a login bypass), then follow [_video-body.md](_video-body.md). If acquire fails, say the video was not watched.

## Prefer (in order)

1. **Meta Graph API** with a Page/User token the user authorized (host connector preferred).
2. **Public oEmbed** for some public URLs:
   `GET https://www.facebook.com/plugins/post/oembed.json?url=<urlencoded>`
   (Availability varies; treat failures as normal.)
3. **User paste** of the post text. A Reel caption goes in `caption`, not video Understanding.
4. Reels/video: local file via Save/export, or `yt-dlp` when the user asked to read that public URL. Then the [media pipeline](_video-body.md). Never a login bypass. Other ToS-sensitive downloaders need explicit approval for that URL.

## Fetch recipe

1. Canonicalize share short-links when possible.
2. For a text post: Graph connector → oEmbed → user paste. For a Reel or video: acquire a file, then the media pipeline. Do not stop at the caption.
3. Set honest `body_kind` (`post_text` for the post, `media_understanding` / `transcript` / `visual` after a real media read, `unavailable` when the video was not acquired).
4. Understanding of a video comes from frames, OCR, and speech. The caption stays in `caption`.

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
