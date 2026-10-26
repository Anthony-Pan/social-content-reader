# Instagram

**Status:** Works for understanding when a public caption or post text is available. Tokenless oEmbed often returns embed HTML only (no caption). Spoken ASR is optional: use it when the user wants verbatim speech, or the caption is empty/useless. Do not ask for a file before summarizing a caption you already have.

## URL patterns

- `https://www.instagram.com/p/{code}/`
- `https://www.instagram.com/reel/{code}/` (also `/reels/{code}/`)
- `https://www.instagram.com/tv/{code}/`

## Default path: caption or post text → understand

1. **Host connector** when it returns a real caption, post text, or transcript. Use that text as `body_text`.
2. **Public oEmbed** for a preview of public posts. If the response includes the actual caption or post copy, store it as `body_text`, `body_kind: caption`, `fetch_method: oembed`, and write Understanding (claims, topic, tone) from it.
3. The repository's [earlier smoke](../../../SMOKE_RESULTS.md) of tokenless `instagram_oembed` for `fA9uwTtkSN` returned embed HTML and provider fields only, with chrome text “View this post on Instagram”. That is not a caption. Set `body_kind: unavailable` for that response. Do not invent speech from stripped embed HTML.
4. A nonempty caption is a successful understanding path. Finish the normalized record and the 5–12 line Understanding. Do not ask the user to save the Reel first.

## Optional: spoken transcript

Use this only when the user asks what was said verbatim, or step 2–3 produced no usable caption.

1. **User paste:** accept a transcript as `body_text`, `body_kind: transcript`, `fetch_method: user_paste`.
2. **User-provided media:** Instagram Share → Download/Save video where offered, an official account export, or an authorized browser download. Menu wording varies; a bookmark alone may only save a reference. With an actual local audio/video file, run:

   ```powershell
   python skills/social-content-reader/scripts/asr_local.py --media "C:\Media\reel.mp4" --language auto --backend auto --model base
   ```

   Mac / Linux: `python3` and `"$HOME/Media/reel.mp4"`. Resolve the script relative to `SKILL.md`. Check exit code and `ok`; copy JSON `text` into `body_text`, set `body_kind: transcript`, `fetch_method: user_media_asr`, and record backend/model/language in `media_notes`. See [ASR setup](../scripts/README.md).
3. **Optional yt-dlp:** only if the user explicitly approved that download tool for **this exact URL**. A request to summarize a Reel is not download-tool permission. After approval, an example is `yt-dlp --no-playlist --output "reel.%(ext)s" "<approved Reel URL>"`; then ASR the saved file. Do not extract browser cookies, request credentials, use private API plugins, or retry behind login/captcha. yt-dlp is neither bundled nor the default path.
4. **Official Instagram Graph API:** for user-owned or explicitly authorized Business/Creator accounts with required permissions. Retrieve only media the official API authorizes. If it supplies a permitted caption, understand that caption. If it supplies a permitted downloadable media URL and the user asked for speech, process the saved file with ASR. Do not imply arbitrary public Reels have transcripts in Graph API responses.

## Official account configuration (documentation only)

Environment names for a separately configured official integration:

- `IG_ACCESS_TOKEN` — user-authorized token, never a committed value.
- `IG_USER_ID` — authorized Business/Creator account ID.
- `IG_APP_ID`, `IG_APP_SECRET` — app credentials when required by the chosen official login flow.
- `IG_GRAPH_API_VERSION` — supported version selected for that app.

These are suggested integration names, **not variables consumed by `asr_local.py`**. Permissions, host and token type depend on the official login flow; follow [Meta's Instagram platform documentation](https://developers.facebook.com/docs/instagram-platform/). Do not print tokens or persist token-bearing media URLs in normalized records.

## oEmbed honesty

- oEmbed is a public embed/preview, not an analytics corpus. Observe [Meta's oEmbed terms and requirements](https://developers.facebook.com/docs/instagram-platform/oembed/).
- Use caption text when the response actually contains it. Embed chrome with no caption is `body_kind: unavailable`, `fetch_method: oembed`.
- Authentication/version/rate requirements can change; no tokenless availability or quota guarantee is made here.

## Limits and stopping conditions

No login bypass, captcha defeat, cookie theft/dumping, session hijack, DRM bypass, or unofficial private API scrapers. URL-only private/inactive/restricted posts and Stories have no supported general fetch path here. ASR covers speech, not silent visual actions or on-screen text; request screenshots/text when the user needs those and they are not in the caption. Never claim ASR/OCR that was not run.

## Success criteria

- Nonempty public caption or post text → normalized record + Understanding, with no ask for a file.
- Tokenless oEmbed that is only embed chrome → unavailable for that URL. ASR is then optional, not a demand before you report the gap.
- Spoken transcript: ASR `ok: true` from user media, or a user-pasted transcript, only when that was the task.
