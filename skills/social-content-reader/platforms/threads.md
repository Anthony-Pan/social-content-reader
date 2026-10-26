# Threads

**v0.5.0 status:** Verified public sample. **Mac 2026-10-26: Yes; audio + video.** This is file acquisition evidence, not a claim that the video has been understood.

## Automatic acquire first

Prefer a configured authorized connector if it returns permitted media. Otherwise run:

```bash
python3 skills/social-content-reader/scripts/acquire_media.py \
  'https://www.threads.com/@nasa/post/DeMqtuYgkaL' --out-dir "$HOME/Media/threads"
```

Replace the sample with the requested public URL. Resolve ordinary short-link redirects automatically before passing a canonical URL when needed; never ask the user to export as the first step.

**Method:** Public page JSON → matching code → video_versions. The helper uses a fresh browser context or ignores local yt-dlp config. It does not read user browser profiles, solve captchas, call private app APIs or decrypt media. Require exit 0, `ok: true`, a real `path`, positive duration and `has_video: true`. Check `has_audio`; video-only evidence cannot establish speech.

## Live result and remaining wall

Text-only posts are not video failures. The tested embed did not expose video; use the public post. Match exact code to exclude replies, quoted posts and recommendations.

Evidence: [SMOKE_RESULTS.md](../../../SMOKE_RESULTS.md); local files and receipts in `~/Developer/scr-proof/matrix-2026-10-26/threads/`. A single public success is not universal platform access.

## Read the media

Follow [_video-body.md](_video-body.md): frames → OCR → host vision → official speech track or local ASR. A post caption, oEmbed title, description, thumbnail, chat or comment stream remains metadata. Only actual post/article text can be a written body; it does not stand in for an attached video.

If the automatic acquire returns a login, captcha, risk, app-only, deleted, DRM or missing-file result, record the exact failure and stop that route. Set `body_kind: unavailable`, `fetch_method: acquire_failed` (or `blocked`), and say the video was not watched. Use an already authorized connector or official account integration when available. User Save/export is **last resort after documented automatic attempts fail**, never the default. Do not write Understanding from the caption.
