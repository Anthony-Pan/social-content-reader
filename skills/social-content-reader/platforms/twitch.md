# Twitch

**v0.5.3 status:** Public clips, short VODs, and an explicit time range of a long VOD can save an ffprobe-valid file. This is acquisition, not Understanding. It is not whole-broadcast support. A VOD longer than **600 seconds** is refused unless `--section START-END` names a window of at most 600 seconds. The helper does not download a silent prefix.

## Automatic acquire first

Prefer a configured authorized connector if it returns permitted media. Otherwise run:

```bash
python3 skills/social-content-reader/scripts/acquire_media.py \
  'https://clips.twitch.tv/FaintLightGullWholeWheat' --out-dir "$HOME/Media/twitch"
```

A finished public VOD or highlight:

```bash
python3 skills/social-content-reader/scripts/acquire_media.py \
  'https://www.twitch.tv/videos/2128758214' --out-dir "$HOME/Media/twitch" --max-mb 400
```

One window of a long VOD (this sample is 15434s / 4:17:14; the command keeps 20 seconds at 1:00:00):

```bash
python3 skills/social-content-reader/scripts/acquire_media.py \
  'https://www.twitch.tv/videos/2096474672' --section '1:00:00-1:00:20' \
  --out-dir "$HOME/Media/twitch"
```

`--section` accepts seconds (`0-20`), `MM:SS`, `H:MM:SS`, or `1h2m3s`. It is Twitch-only.

**Method:** stock `yt-dlp` with `--ignore-config`, no cookies, no netrc, no browser profile, and no Helix token. Clips and `/videos/{id}` (including `player.twitch.tv/?video=`, `/{channel}/v/{id}`, and `m.twitch.tv`) are canonicalized. The helper picks a public video format at or below 480p when one exists, otherwise 720p, otherwise the lowest video. A clip's progressive MP4 may omit codec names in the metadata; the saved file is still ffprobe-checked. Before download, a padded size estimate (about 220 KB/s at 480p, 900 KB/s at 1080p, from this box's samples) must fit `--max-mb` (default 128). If the estimate is over the cap, nothing is downloaded. A file that still comes back larger is deleted. Neither case returns a shortened file as success. ffprobe must show a positive duration and a video stream. For a full file, duration must match the public metadata. For `--section`, it must match that window, not the rest of the VOD. `twitch_source_duration_sec` is the full media length. `twitch_full: false` means the file is only the section.

`?t=` on a VOD URL is a player bookmark. It is stored as `twitch_bookmark_sec` with `twitch_bookmark_applied: false`. It does not seek and it does not trim. Pass `--section`.

Channel pages, live URLs, `/videos` lists, `/clips` lists, and collections are not one media file. Live streams are not recorded. Chat and title are not speech and are not `body_text`.

The helper does not read user browser profiles, solve captchas, call a private app API of its own, or decrypt media. Require exit 0, `ok: true`, a real `path`, positive duration, and `has_video: true`. Check `has_audio`. Video-only evidence cannot establish speech.

## Live result (box, 2026-10-29) and remaining wall

yt-dlp 2026.10.26, ffmpeg 6.1.1. No cookies. Each saved file decoded with `ffmpeg -f null` exit 0.

| URL | Result |
| --- | --- |
| [clip FaintLightGullWholeWheat](https://clips.twitch.tv/FaintLightGullWholeWheat) | **FILE OK**, full clip. 16,299,328 bytes, 32.099s, h264+aac, SHA-256 `9d3021eae0ac932a…`. Same file as the v0.5.0 public-player sample. |
| [VOD 2128758214](https://www.twitch.tv/videos/2128758214) (402s, source 1080p only) | **FILE OK** with `--max-mb 400`. 256,357,852 bytes, 401.932s, aac+h264. Default `--max-mb 128` refused **before** download (estimate 361,800,000 bytes). |
| Same VOD `--section 10-25` | **FILE OK**. 11,068,048 bytes, 15.134s, 1080p, not the other 387 seconds. |
| [VOD 2096474672](https://www.twitch.tv/videos/2096474672) (15434s) | **FAIL** with no section. Error names 15434s and tells you to pass `--section`. No prefix file. |
| Same VOD `--section 0-20` | **FILE OK**. 3,407,834 bytes, 20.025s, 480p, h264+aac. Source duration on the receipt stays 15434. |
| Same VOD `--section 1:00:00-1:00:20` | **FILE OK**. 3,557,056 bytes, 20.019s, 480p. Not the opening of the VOD. |
| Same VOD `?t=1h2m3s` and no `--section` | **FAIL**. Bookmark 3723s ignored. Not acquired. |
| Same VOD `--section 0-601` | **FAIL**. Over 600s. Nothing downloaded. |
| `/videos/1` | **FAIL**. Does not exist. |
| `twitch.tv/twitch` (channel) | **FAIL** before any downloader. Not a clip or VOD. |

Still failing, on purpose:

- Any VOD longer than 600s, unless one `--section` of at most 600s is passed. The helper does not download a silent prefix and does not claim the section is the broadcast.
- A window whose padded estimate, or whose saved file, exceeds `--max-mb`.
- Subscriber-only or login-gated media. Not given a live sample here. A downloader message that asks for a login or subscription stops. No cookie or credential fallback.
- Deleted IDs, live channels, and list/collection URLs.
- `?t=` alone.

For authorized broadcaster/editor integrations, Twitch documents `GET /helix/clips/downloads` with scoped tokens. This was researched, not run; no token is configured. Reference: https://dev.twitch.tv/docs/api/reference/#get-clips-download

Evidence: [SMOKE_RESULTS.md](../../../SMOKE_RESULTS.md) v0.5.3 addendum. Receipts without media bytes: [twitch-vod-2026-10-29.json](../references/twitch-vod-2026-10-29.json). A few public successes are not universal platform access.

## Read the media

Follow [_video-body.md](_video-body.md): frames → OCR → host vision → official speech track or local ASR. A post caption, oEmbed title, description, thumbnail, chat or comment stream remains metadata. Only actual post/article text can be a written body; it does not stand in for an attached video. A `--section` file is that window only.

If the automatic acquire returns a login, captcha, risk, app-only, deleted, DRM or missing-file result, record the exact failure and stop that route. Set `body_kind: unavailable`, `fetch_method: acquire_failed` (or `blocked`), and say the video was not watched. Use an already authorized connector or official account integration when available. User Save/export is **last resort after documented automatic attempts fail**, never the default. Do not write Understanding from the caption.
