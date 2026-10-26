# Reddit

**Status:** Works for public posts/comments via public JSON (`.json`) and/or a host Reddit connector. Reddit-hosted video still needs a media file.

## URL patterns

- `https://www.reddit.com/r/{sub}/comments/{id}/{slug}/`
- `https://reddit.com/...`, `https://old.reddit.com/...`
- `https://www.reddit.com/comments/{id}/`
- Short: `https://redd.it/{id}`

## Video and graphics

`selftext` is the written post (`body_kind: post_text` or `article`). A `v.redd.it` video, a video link, or an image that carries the claim is not understood from the title. Acquire the file (user save, or `yt-dlp` when the user asked to read that public video), then follow [_video-body.md](_video-body.md). If acquire fails, say the video was not watched. The title and selftext stay available as the post, labeled as text.

## Prefer (in order)

1. **Host Reddit connector / MCP** if present.
2. **Public JSON append** (documented Reddit convenience for public pages):
   Append `.json` to the post URL (strip tracking query noise first), e.g.
   `https://www.reddit.com/r/{sub}/comments/{id}/{slug}.json`
   Use a descriptive User-Agent string (Reddit asks clients to identify themselves). Example:
   ```powershell
   curl.exe -L -A "social-content-reader/0.4 (by Anthony-Pan; research)" "https://www.reddit.com/r/EXAMPLE/comments/POSTID/title.json"
   ```
3. User paste if JSON is blocked (403) or the post is quarantined/NSFW-gated without access.

## Fetch recipe

1. Normalize to a canonical comments URL + id via `normalize_url.py`.
2. Fetch `.json`; take `data.children[0].data` for the submission (`title`, `selftext`, `author`, `subreddit`, `created_utc`).
3. Optionally include top-level comment bodies (mark as comments, not OP body).
4. Set `body_kind: post_text` (or `article` for long self-posts), `fetch_method: public_api` / `public_curl`.
5. For link-posts with empty `selftext`, note that the body is external — follow the linked URL with its own platform recipe when useful.
6. Understanding: OP claim + notable top comments if fetched.

## Honest limits

- Private subs, quarantined, removed, or account-gated content → unavailable without authorized access.
- Respect Reddit API Terms; identify your UA; do not hammer endpoints.
- Media (video/image) uses [_video-body.md](_video-body.md). Title-only is not a watched video.
- OAuth Reddit API is preferred for production volume; `.json` is fine for occasional agent reads of public posts.

## Codex prompt sketch

```text
Follow platforms/reddit.md. URL: <URL>
Fetch public .json; return ContentRecord (OP selftext) + understanding.
```

## References

- Reddit API rules / User-Agent requirements
- Public `.json` convenience on reddit.com pages
