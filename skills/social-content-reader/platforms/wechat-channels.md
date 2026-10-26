# WeChat 视频号

**v0.5.0 status:** Documented automatic attempt; blocked on this Mac. **Mac 2026-10-26: NO; QR / app-only page.** This is file acquisition evidence, not a claim that the video has been understood.

## Automatic acquire first

Prefer a configured authorized connector if it returns permitted media. Otherwise run:

```bash
python3 skills/social-content-reader/scripts/acquire_media.py \
  'https://weixin.qq.com/sph/AAZ3p39sQm' --out-dir "$HOME/Media/wechat-channels"
```

Replace the sample with the requested public URL. Resolve ordinary short-link redirects automatically before passing a canonical URL when needed; never ask the user to export as the first step.

**Method:** Public sph page → video src (attempted). The helper uses a fresh browser context or ignores local yt-dlp config. It does not read user browser profiles, solve captchas, call private app APIs or decrypt media. Require exit 0, `ok: true`, a real `path`, positive duration and `has_video: true`. Check `has_audio`; video-only evidence cannot establish speech.

## Live result and remaining wall

The public page rendered caption/date/thumbnail and a QR prompt, with no video element or playable file. Historical feed errCode 10012 is not a media route. Creator assistant requires an authorized account and was not configured/tested. No general public file path verified.

Research boundary (not working recipes): wx-downloader describes Yuanbao login plus a separate link-resolution client (https://github.com/QinGeneral/wx-downloader); WechatVideoDL describes Yuanbao/cookie integrations (https://github.com/topgptus/WechatVideoDL). These are not documented general public WeChat media APIs, and were not installed or run. Certificate interception, private API replay and encrypted CDN download/decrypt paths are outside this task. A creator-authorized integration or a genuinely playing public page would be the next automatic route; neither was available for this sample.

Evidence: [SMOKE_RESULTS.md](../../../SMOKE_RESULTS.md); local files and receipts in `~/Developer/scr-proof/matrix-2026-10-26/wechat-channels/`. A single public success is not universal platform access.

## Read the media

Follow [_video-body.md](_video-body.md): frames → OCR → host vision → official speech track or local ASR. A post caption, oEmbed title, description, thumbnail, chat or comment stream remains metadata. Only actual post/article text can be a written body; it does not stand in for an attached video.

If the automatic acquire returns a login, captcha, risk, app-only, deleted, DRM or missing-file result, record the exact failure and stop that route. Set `body_kind: unavailable`, `fetch_method: acquire_failed` (or `blocked`), and say the video was not watched. Use an already authorized connector or official account integration when available. User Save/export is **last resort after documented automatic attempts fail**, never the default. Do not write Understanding from the caption.
