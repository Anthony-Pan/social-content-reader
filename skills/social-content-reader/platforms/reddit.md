# Reddit

**v0.5.0 status:** Verified public sample. **Mac 2026-10-26: Yes; video only; post URL blocked.** This is file acquisition evidence, not a claim that the video has been understood.

## Automatic acquire first

Prefer a configured authorized connector if it returns permitted media. Otherwise run:

```bash
python3 skills/social-content-reader/scripts/acquire_media.py \
  'https://v.redd.it/gyh95hiqc0b11' --out-dir "$HOME/Media/reddit"
```

Replace the sample with the requested public URL. Resolve ordinary short-link redirects automatically before passing a canonical URL when needed; never ask the user to export as the first step.

**Method:** Public v.redd.it DASH manifest → yt-dlp. The helper uses a fresh browser context or ignores local yt-dlp config. It does not read user browser profiles, solve captchas, call private app APIs or decrypt media. Require exit 0, `ok: true`, a real `path`, positive duration and `has_video: true`. Check `has_audio`; video-only evidence cannot establish speech.

## Live result and remaining wall

The media id is independently known from the public yt-dlp Reddit test fixture for post 90bu6w. That post page/JSON and redditmedia embed were blocked on this Mac. CDN success does not prove arbitrary post-to-media resolution. No audio track in this sample manifest.

For a post URL, prefer an authorized connector, then public post HTML / `.json` to obtain its actual `reddit_video.dash_url` or media id. This network blocked that step: the helper cannot invent a CDN id from a post id. With an already public `v.redd.it/{media_id}` URL, the helper reads `DASHPlaylist.mpd`, downloads video plus audio when present, and validates the result. Public source of this test mapping: https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/reddit.py

Evidence: [SMOKE_RESULTS.md](../../../SMOKE_RESULTS.md); local files and receipts in `~/Developer/scr-proof/matrix-2026-10-26/reddit/`. A single public success is not universal platform access.

## Read the media

Follow [_video-body.md](_video-body.md): frames → OCR → host vision → official speech track or local ASR. A post caption, oEmbed title, description, thumbnail, chat or comment stream remains metadata. Only actual post/article text can be a written body; it does not stand in for an attached video.

If the automatic acquire returns a login, captcha, risk, app-only, deleted, DRM or missing-file result, record the exact failure and stop that route. Set `body_kind: unavailable`, `fetch_method: acquire_failed` (or `blocked`), and say the video was not watched. Use an already authorized connector or official account integration when available. User Save/export is **last resort after documented automatic attempts fail**, never the default. Do not write Understanding from the caption.
