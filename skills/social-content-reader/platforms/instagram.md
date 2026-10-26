# Instagram

**Status:** Media required for a Reel. oEmbed is an embed preview, not the video.

Captions and embed previews do not establish what a Reel shows or says. Default success is the [shared video recipe](_video-body.md): a local file, frames, burned-in text, host vision, and ASR. Prefer an existing authorized host connector when it returns permitted media or a real transcript; a transcript alone is speech, not the picture.

## URL patterns

- `https://www.instagram.com/p/{code}/`
- `https://www.instagram.com/reel/{code}/` (also `/reels/{code}/`)
- `https://www.instagram.com/tv/{code}/`

## Video and graphics

Follow [_video-body.md](_video-body.md). A pasted transcript fills `speech_text` (`body_kind: transcript`, `fetch_method: user_paste`) and must say graphics were not read unless frames were also supplied. A caption alone stays in `caption`.

## Reel understanding path (in order)

1. **User-provided media:** Instagram Share → Download/Save video where offered, an official account export, or an authorized browser download. Menu wording and availability vary; a bookmark may only save a reference. Obtain an actual local audio/video file.
2. **yt-dlp** when the user asked to read this Reel: `yt-dlp --no-playlist -o "%(id)s.%(ext)s" "<reel url>"`. Stop on login or captcha. Do not extract browser cookies, request credentials, or use private API plugins. Other ToS-sensitive downloaders still need explicit approval for that URL.
3. **On the local file**, run frames, OCR, host vision, and ASR:

   ```bash
   python3 skills/social-content-reader/scripts/extract_frames.py --media "$HOME/Media/reel.mp4" --mode fps --fps 1 --max-frames 24
   python3 skills/social-content-reader/scripts/ocr_frames.py --frames-json frames.json
   python3 skills/social-content-reader/scripts/asr_local.py --media "$HOME/Media/reel.mp4" --language auto --backend auto --model base
   ```

   Windows: `py -3.12` and `C:\Media\reel.mp4`. Resolve helpers relative to `SKILL.md`. Check exit code and `ok`. Map ASR `text` to `speech_text`, OCR text to `visual_text`, and the host vision notes to `visual_description`. Set `body_kind: media_understanding` and `fetch_method: media_pipeline` when pictures and speech were both read. See [ASR setup](../scripts/README.md).
4. **User paste of a transcript** is speech evidence only (`body_kind: transcript`). Ask for the file or screenshots when the question is about graphics.
5. **Official Instagram Graph API:** for user-owned or explicitly authorized Business/Creator accounts with required permissions. Retrieve only media the official API authorizes for that account; if it supplies a permitted downloadable media URL, save the file and run the media pipeline. Do not imply arbitrary public Reels have transcripts in Graph API responses.

## Official account configuration (documentation only)

Environment names for a separately configured official integration:

- `IG_ACCESS_TOKEN` — user-authorized token, never a committed value.
- `IG_USER_ID` — authorized Business/Creator account ID.
- `IG_APP_ID`, `IG_APP_SECRET` — app credentials when required by the chosen official login flow.
- `IG_GRAPH_API_VERSION` — supported version selected for that app.

These are suggested integration names, **not variables consumed by `asr_local.py`**. Permissions, host and token type depend on the official login flow; follow [Meta's Instagram platform documentation](https://developers.facebook.com/docs/instagram-platform/). Do not print tokens or persist token-bearing media URLs in normalized records.

## oEmbed honesty

- oEmbed is for a front-end embed/basic preview, **not** transcript extraction or an analytics corpus. Observe [Meta's oEmbed terms and requirements](https://developers.facebook.com/docs/instagram-platform/oembed/).
- The repository's [earlier smoke](../../../SMOKE_RESULTS.md) returned embed HTML/provider fields and **no speech transcript**. Do not infer speech from stripped embed HTML.
- A missing file is `body_kind: unavailable` and `fetch_method: acquire_failed`. Store a separately provided caption in `caption` with `fetch_method: oembed` on that field's source note. Do not promote it to Understanding.
- Authentication/version/rate requirements can change; no tokenless availability or quota guarantee is made here.

## Limits and stopping conditions

No login bypass, captcha defeat, cookie theft/dumping, session hijack, DRM bypass, or unofficial private API scrapers. URL-only private/inactive/restricted posts and Stories have no supported general fetch path here. An authorized user file or paste can still be understood regardless of its original share-link format. ASR covers speech, not silent visual actions or on-screen text; request screenshots/text when needed. Never claim ASR/OCR that was not run.

If all you have is a link or a caption, the Reel was not watched. Ask for a file. If a file exists, run the media pipeline and report dependency errors instead of declaring the Reel unreadable.

## Success criteria

- `body_kind: media_understanding` after frames and speech were read, or `transcript` / `visual` with that gap stated. oEmbed alone is not success.
