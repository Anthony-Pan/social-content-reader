# Video and graphics — shared recipe

**Default success** for a video is a local media file that was actually read: pictures, burned-in text, and speech. A share caption, oEmbed title, or description is **metadata**. It is never the video Understanding.

Use this recipe from every platform doc when the user asks what a video shows or says. Text posts and articles keep their own written-body recipes; an attached video still comes here.

## Pipeline

1. **Acquire** a local video (or audio, or a keyframe set the user already exported). See [Acquire](#acquire) below.
2. **Frames.** Uniform or scene-change stills:

   ```bash
   python3 skills/social-content-reader/scripts/extract_frames.py \
     --media "$HOME/Media/clip.mp4" --mode fps --fps 1 --max-frames 24
   ```

   ```powershell
   py -3.12 skills\social-content-reader\scripts\extract_frames.py --media "C:\Media\clip.mp4" --mode scene --scene-threshold 0.3 --max-frames 24
   ```

   Require `ok: true` and a non-empty `frames` array. Keep `timestamp_sec` with each path. `truncated: true` means the cap hid later frames — say so, or raise `--max-frames` / lower `--fps`.
3. **Burned-in text (OCR).** Optional engine, honest failure:

   ```bash
   python3 skills/social-content-reader/scripts/ocr_frames.py --frames-json frames.json
   ```

   Tesseract when it is on PATH (`chi_sim+eng` when language data exists, else `eng`). On macOS, `--engine vision` uses `ocr_vision.swift` via `swiftc` when Tesseract is absent. If the helper returns `engine: none`, do not invent on-screen text. Say OCR did not run.
4. **Vision / video description.** This skill does not bundle a vision model. The host agent looks at the **video file and the extracted frames** with its own video/vision tools and writes `visual_description`: people, graphics, burned-in words, cuts, on-screen claims. If the host has no vision tool, say visual description was not produced.
5. **Speech.** Official transcript/CC tracks when that platform documents them (YouTube, Bilibili CC, Vimeo text tracks, Twitch CC). Otherwise [scripts/asr_local.py](../scripts/asr_local.py) on the local file. Map ASR `text` to `speech_text`. ASR does not see pictures. A transcript-only result is speech, not full video Understanding, unless frames were also read.
6. **Write Understanding** from `visual_description` + OCR `text` + `speech_text`. Put any share caption in `caption` and mention it only as a labeled side note.
7. **Acquire failure.** If step 1 does not yield a file, stop. Set `body_kind: unavailable` and `fetch_method: acquire_failed` (or `blocked` when the platform wall is the reason). Say the video was not watched. Do not write Understanding from the caption. A caption may sit in `caption` so the user can see the share text; it must be labeled metadata.

## ContentRecord fields

| Field | Video success | Acquire failed |
| --- | --- | --- |
| `body_kind` | `media_understanding` (pictures and speech), `transcript` (speech only), or `visual` (pictures only) | `unavailable` |
| `body_text` | Labeled join of visuals, OCR, and speech | empty, or a one-line statement that the video was not read |
| `speech_text` | ASR or official transcript | empty |
| `visual_text` | OCR text | empty |
| `visual_description` | Host vision notes | empty |
| `caption` | Share caption / description, if any | same, labeled metadata |
| `fetch_method` | `media_pipeline`, `user_media_asr`, `host_connector`, or `public_api` for an official transcript | `acquire_failed` or `blocked` |
| `limits` | truncated frames, speech-only, OCR engine missing, auto-caption uncertainty | the acquire error in plain language |

`body_kind: caption` is not a successful video read.

## Acquire

Automatic acquisition is the default. Prefer an available authorized connector
that supplies actual media; otherwise run the platform's documented public path:

```bash
python3 skills/social-content-reader/scripts/acquire_media.py '<public video URL>' --out-dir "$HOME/Media/acquired"
```

Install Playwright Chromium in a venv for browser paths; ffmpeg and ffprobe are
required for file validation. yt-dlp is used for YouTube, public X syndication,
Vimeo's public player and a supplied public Reddit CDN media URL. See
[script setup](../scripts/README.md). Ordinary redirect resolution is automatic
agent work, not a reason to request a user export. Preserve owner-supplied
access parameters such as Vimeo `h` and Xiaohongshu `xsec_token`.

A download succeeds only when the helper returns exit 0 and `ok: true`, with
`path`, SHA-256, size, positive duration and a video stream. The JSON receipt is
saved beside the file. Check `has_audio` before claiming speech. A video-only
file is visual evidence; a transcript-only response is speech evidence. Neither
alone establishes both. An HTTP 200, caption, thumbnail, or playable site error
video is not the requested media. The helper rejects Bilibili error.mp4 and
partial HTTP ranges (HTTP 206 requires Content-Range and actual bytes to cover the entire file), and matches Meta post IDs rather than taking a neighbor's
video. Bilibili video/audio are downloaded from requests made by the actual
public external player and muxed without re-encoding or decryption.

No browser profile/cookie extraction (including `--cookies-from-browser`),
private API client, signed-request fabrication, captcha defeat, login bypass,
certificate interception or CDN decrypt is part of these recipes. Fresh contexts
may retain only cookies issued by their own ordinary public page loads. Stop
on an access challenge; do not rotate IPs or repeatedly retry a risk wall.

When the documented automatic route really fails, record the error and return
`body_kind: unavailable` / `fetch_method: acquire_failed` or `blocked`. A
configured authorized media connector / official account integration can be
tried next. User export is last resort after those available automatic paths
fail. Say the video was not watched; never fill the gap with a caption.

## Mac acquisition matrix — 2026-10-26

All 16 platforms have recipes. **Listed support does not mean every URL is
accessible.** Verified sample files, byte counts and hashes are in
[SMOKE_RESULTS.md](../../../SMOKE_RESULTS.md); remaining walls are explicit.

| Platform | Automatic method | Actual sample result |
| --- | --- | --- |
| [YouTube](youtube.md) | yt-dlp public player | Yes; audio + video |
| [X / Twitter](x.md) | yt-dlp public syndication | Yes; audio + video |
| [Instagram](instagram.md) | Public page JSON → matching code → video_versions | Yes; video, source has_audio=false |
| [TikTok](tiktok.md) | Documented /player/v1/{id} → video src | Yes; audio + video |
| [Threads](threads.md) | Public page JSON → matching code → video_versions | Yes; audio + video |
| [Reddit](reddit.md) | Post URL → public JSON or embed → that post's v.redd.it DASH → yt-dlp | Yes when the public embed (or listing JSON) includes that post's media. Direct CDN still works. www/old JSON and redd.it can be blocked. |
| [LinkedIn](linkedin.md) | Public video data-sources → progressive MP4 | Yes; audio + video |
| [Facebook Reels](facebook.md) | Public page JSON → exact video id → browser_native URL | Yes; video only |
| [Telegram](telegram.md) | Public message widget → scoped video src | Yes; audio + video |
| [Vimeo](vimeo.md) | Public player.vimeo.com URL → yt-dlp | Yes; audio + video |
| [Twitch](twitch.md) | Public yt-dlp clip, or VOD/section ≤ 600s | Yes when the clip, short VOD, or `--section` fits `--max-mb`. Longer VODs are refused, not silently trimmed. |
| [Douyin 抖音](douyin.md) | Mobile share player → playwm → MP4 | Yes; audio + video |
| [Bilibili 哔哩哔哩](bilibili.md) | External player → observed full-range video/audio → mux | Yes; AV1 + AAC |
| [小红书 / Xiaohongshu](xiaohongshu.md) | Public note page → playing video src (attempted) | NO; risk wall |
| [WeChat 视频号](wechat-channels.md) | Public sph page → video src (attempted) | NO; QR / app-only page |
| [WeChat 公众号](wechat-article.md) | Chrome UA HTTPS → `#js_content`; mpvideo embeds listed; optional public player | Body OK (v0.5.1). Embed media network-dependent; not Understanding without a file. |
