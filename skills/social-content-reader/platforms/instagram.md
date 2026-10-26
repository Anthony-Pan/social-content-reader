# Instagram

**Status:** Works with user media + ASR. oEmbed = metadata/embed ONLY; URL-only speech understanding is unavailable.

Captions and embed previews do not establish what a Reel says. Prefer an existing authorized host connector when it returns a real transcript or permitted media; otherwise use this order.

## URL patterns

- `https://www.instagram.com/p/{code}/`
- `https://www.instagram.com/reel/{code}/` (also `/reels/{code}/`)
- `https://www.instagram.com/tv/{code}/`

## Reel understanding path (in order)

1. **User paste:** accept the user's transcript as `body_text`, `body_kind: transcript`, `fetch_method: user_paste`. A caption alone stays `caption_only`.
2. **User-provided media:** have the user use Instagram's Share → Download/Save video option where offered, an official account export, or an authorized browser download. Menu wording and availability vary; Save/bookmark alone may only save a reference. Obtain an actual local audio/video file, then run:

   ```powershell
   python skills/social-content-reader/scripts/asr_local.py --media "C:\Media\reel.mp4" --language auto --backend auto --model base
   ```

   For an installed skill, resolve the script relative to its `SKILL.md`. Check exit code and `ok`; copy JSON `text` into `body_text`, set `body_kind: transcript`, `fetch_method: user_media_asr`, and record backend/model/language in `media_notes`. Summarize speech from this text. See [ASR setup](../scripts/README.md).
3. **Optional yt-dlp:** only if the user explicitly approved using that download tool for **this exact URL**. A request to summarize a Reel is not download-tool permission. After that approval, an example is `yt-dlp --no-playlist --output "reel.%(ext)s" "<approved Reel URL>"`; locate the saved file and run ASR as above. Do not extract browser cookies, request credentials, use private API plugins, or retry behind login/captcha. If access is blocked, return to user paste/export. yt-dlp is neither bundled nor the default path.
4. **Official Instagram Graph API:** for user-owned or explicitly authorized Business/Creator accounts with required permissions. Retrieve only media the official API authorizes for that account; if it supplies a permitted downloadable media URL, process the saved file with ASR. Do not imply arbitrary public Reels have transcripts in Graph API responses.

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
- Use `body_kind: unavailable` for missing speech, or `caption_only` only when an actual caption was separately provided. Report `fetch_method: oembed` and the limitation.
- Authentication/version/rate requirements can change; no tokenless availability or quota guarantee is made here.

## Limits and stopping conditions

No login bypass, captcha defeat, cookie theft/dumping, session hijack, DRM bypass, or unofficial private API scrapers. URL-only private/inactive/restricted posts and Stories have no supported general fetch path here. An authorized user file or paste can still be understood regardless of its original share-link format. ASR covers speech, not silent visual actions or on-screen text; request screenshots/text when needed. Never claim ASR/OCR that was not run.

If all you have is a link/caption, mark speech unavailable and request a transcript or file. If a file exists, try ASR and report dependency/error details instead of declaring Instagram speech inherently unreadable.
