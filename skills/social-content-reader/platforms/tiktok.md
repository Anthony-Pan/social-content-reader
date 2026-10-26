# TikTok (global)

**Status:** Media required for video Understanding. oEmbed caption is metadata only.

**Goal:** Read what the clip shows and what is spoken. Follow [the shared video recipe](_video-body.md).

## URL patterns

- `https://www.tiktok.com/@{user}/video/{id}`
- `https://www.tiktok.com/t/{short}` (resolve redirects first)
- `https://vm.tiktok.com/{short}` (resolve redirects)
- Regional hosts that redirect to `tiktok.com` video pages

## Video and graphics

Default success is a local file run through frames, OCR, host vision, and ASR ([_video-body.md](_video-body.md)). The oEmbed caption may be stored in `caption`. It is not Understanding. If acquire fails, say the video was not watched.

## Prefer (in order)

1. A file the user already saved from TikTok.
2. **yt-dlp** when the user asked to read the video and the public URL downloads without a login bypass:
   `yt-dlp --no-playlist -o "%(id)s.%(ext)s" "<tiktok url>"`
   Stop on login, captcha, or region block.
3. Host TikTok connector when it returns the media file or a real transcript (not a caption alone).
4. Frames + OCR + host vision + ASR on the local file:

   ```bash
   python3 skills/social-content-reader/scripts/extract_frames.py --media "$HOME/Media/tiktok.mp4" --mode fps --fps 1 --max-frames 24
   python3 skills/social-content-reader/scripts/ocr_frames.py --frames-json frames.json
   python3 skills/social-content-reader/scripts/asr_local.py --media "$HOME/Media/tiktok.mp4" --language auto --backend auto --model base
   ```

   Windows: `py -3.12` and `C:\Media\tiktok.mp4`.
5. Public oEmbed for **metadata only**:
   `GET https://www.tiktok.com/oembed?url=<urlencoded video url>`
   Author, caption, thumbnail → `caption` / `fetch_method: oembed`. Never `body_kind: media_understanding`.

## Fetch recipe

1. Normalize to a canonical `tiktok.com/@…/video/{id}` URL when possible (`normalize_url.py`).
2. Acquire the file (user save or yt-dlp). Then run the media pipeline.
3. Set `body_kind: media_understanding` and `fetch_method: media_pipeline` when pictures and speech were both read. Use `transcript` or `visual` with a limit when only one side was read.
4. If there is no file, set `body_kind: unavailable` and `fetch_method: acquire_failed`. Keep oEmbed text in `caption` if it was fetched.

## Honest limits

- oEmbed is not a watched video. Do not invent dialogue or on-screen graphics from a caption.
- Private, region-blocked, or deleted videos → unavailable.
- No login bypass, captcha defeat, cookie theft, or unofficial private API scrapers.
- TikTok ToS restricts automated bulk access. One yt-dlp acquire the user asked for, or a user-saved file, is the path. Do not bulk-scrape.

## Codex prompt sketch

```text
Follow platforms/tiktok.md and platforms/_video-body.md. URL: <URL>
Acquire the mp4, then frames + OCR + vision + ASR.
oEmbed caption is a side note. If acquire fails, say the video was not watched.
```

## References

- TikTok oEmbed (embed metadata, not the video body): https://developers.tiktok.com/doc/embed-videos
