# Reddit

**v0.5.2 status:** A normal `reddit.com` / `old.reddit.com` **post URL** can resolve to that post's own hosted video when the public embed page includes it. Direct `v.redd.it` DASH still works. This is file acquisition, not Understanding, and not a claim that every Reddit URL is reachable.

## Automatic acquire first

Prefer a configured authorized connector if it returns permitted media. Otherwise run:

```bash
python3 skills/social-content-reader/scripts/acquire_media.py \
  'https://www.reddit.com/r/aww/comments/90bu6w/heat_index_was_110_degrees_so_we_offered_him_a/' \
  --out-dir "$HOME/Media/reddit"
```

A direct media URL still works:

```bash
python3 skills/social-content-reader/scripts/acquire_media.py \
  'https://v.redd.it/gyh95hiqc0b11' --out-dir "$HOME/Media/reddit"
```

**Method:**

1. Classify the URL. `v.redd.it/{media_id}` is already the media. A post URL is `/r/{sub}/comments/{id}`, `/user/{name}/comments/{id}`, or the same path on `old.reddit.com` / `www.redditmedia.com`. `redd.it/{id}` and `/r/{sub}/s/{code}` need a public redirect to a comments URL first.
2. GET `https://www.reddit.com{path}/.json?raw_json=1&limit=1` with a fixed browser User-Agent and no cookie jar. Read only the first listing's `t3` whose `id` is the requested post. Hosted media is `media` / `secure_media` `reddit_video`, else that post's `v.redd.it` URL, else `crosspost_parent_list`, else one gallery `RedditVideo`. Comment listings are ignored.
3. If that listing is an HTTP block page, GET `https://embed.reddit.com{path}/`. Use the `shreddit-player` whose `post-id` is `t3_{id}` (`src` only). A crosspost with no player uses that same post's screenview `url` when it is `https://v.redd.it/{media_id}`. Players for other post ids are ignored.
4. Build `https://v.redd.it/{media_id}/DASHPlaylist.mpd` (or `v.redd.it/link/{post}/asset/{asset}/DASHPlaylist.mpd` for an inline asset on that same post). Drop signed HLS/MP4 query strings. Download with yt-dlp (`--ignore-config`, no cookies) and require ffprobe: positive duration and a video stream.

The helper does not read browser profiles, solve captchas, call private APIs, opt into quarantined or gated subs with cookies, or decrypt media. Require exit 0, `ok: true`, a real `path`, positive duration, and `has_video: true`. Check `has_audio`. A video-only manifest cannot establish speech. `reddit_post_id` and `reddit_media_id` on the receipt are how you tell a post-URL acquire from a URL someone already knew on the CDN.

Captions, oEmbed titles, posters, and `selftext` are metadata. They are never `body_text`.

## Live result (box, 2026-10-29) and remaining walls

`www.reddit.com` and `old.reddit.com` post HTML and `.json` returned **HTTP 403 Blocked** from this box. `embed.reddit.com` did not. Three post URLs then saved ffprobe-valid files (ffmpeg decode exit 0):

| Post URL | Media id | File check | Audio |
| --- | --- | --- | --- |
| `/r/aww/comments/90bu6w/` | `gyh95hiqc0b11` | 7,478,923 bytes, 13.7s, SHA-256 `5dcd1844…` (same file as the v0.5.0 direct CDN sample) | no |
| `/r/videos/comments/6rrwyj/` | `zv89llsvexdz` | 3,733,550 bytes, 11.797s, h264+aac | yes |
| `/r/dumbfuckers_club/comments/zjjw82/` (crosspost) | `a1oneun6pa5a1` | 1,867,580 bytes, 16.063s, h264+aac, `reddit_kind: crosspost` | yes |

Still failing here, on purpose:

- `redd.it/90bu6w` and `www` share links: redirect **HTTP 403**. The helper does not invent a media id. A unit test covers a redirect that does land on a comments URL.
- `www.reddit.com/comments/90bu6w` (no subreddit/user): listing JSON blocked, and the public embed shell did not include that post.
- A text post with two inline videos (`/r/KamenRider/comments/wzqkxp/`) exposes two hosted videos and is refused rather than picking one. Gallery JSON with two videos does the same. One gallery video beside an image resolves to that video (offline fixture). Live `www` listing JSON was blocked, so a gallery page was not saved as its own sample.
- Quarantined, private, or gated listings stop. No `over18` or opt-in cookie is set.
- Off-site links and `i.redd.it` images are not hosted video. No file is saved.

Evidence: [SMOKE_RESULTS.md](../../../SMOKE_RESULTS.md) v0.5.2 addendum. Receipts without media bytes: [reddit-post-2026-10-29.json](../references/reddit-post-2026-10-29.json). A few public successes are not universal platform access.

## Read the media

Follow [_video-body.md](_video-body.md): frames → OCR → host vision → official speech track or local ASR. A post caption, oEmbed title, description, thumbnail, chat or comment stream remains metadata. Only actual post/article text can be a written body; it does not stand in for an attached video.

If the automatic acquire returns a login, captcha, risk, app-only, deleted, DRM or missing-file result, record the exact failure and stop that route. Set `body_kind: unavailable`, `fetch_method: acquire_failed` (or `blocked`), and say the video was not watched. Use an already authorized connector or official account integration when available. User Save/export is **last resort after documented automatic attempts fail**, never the default. Do not write Understanding from the caption.
