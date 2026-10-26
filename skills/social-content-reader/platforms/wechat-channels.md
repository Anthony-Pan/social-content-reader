# WeChat 视频号 (Channels)

**Status:** Media required. `weixin.qq.com/sph/<id>` WebFetch can return a caption, date, and thumbnail. That text is metadata, not the video. Speech, burned-in text, and graphics need a local file and [the shared video recipe](_video-body.md). `channels.weixin.qq.com` feed paths remain blocked (`errCode 10012`).

## URL patterns

- Share links (preferred): `https://weixin.qq.com/sph/<id>` and `https://www.weixin.qq.com/sph/<id>`.
  `normalize_url.py` sets `platform: wechat-channels`, `canonical_id` to the sph id, `canonical_url` to `https://weixin.qq.com/sph/<id>`, and `link_form: sph_share`.
- `channels.weixin.qq.com` web/feed paths and in-app 视频号 cards. These are not sph share links. The [earlier network smoke](../../../SMOKE_RESULTS.md) got a homepage shell and feed response `errCode: 10012`, `errMsg: Illegal request`. Those responses contain no video body or transcript. Do not keep probing undocumented endpoints.

## Video and graphics

Default success is a local file: `extract_frames.py`, `ocr_frames.py`, the host vision/video tool, and `asr_local.py` ([_video-body.md](_video-body.md)). There is no general public 视频号 file URL and yt-dlp is not a working acquire path here. Ask the user to Save/export from WeChat, or to supply a file they already have. A share card, bookmark, sph link, or article embed is not a media file.

If the file cannot be acquired, set `body_kind: unavailable` and `fetch_method: acquire_failed` or `blocked`. Say the video was not watched. The sph caption may be stored in `caption` as a labeled side note. Do not summarize that caption as what the video shows or says.

## Caption metadata from an sph share link

Prefer **WebFetch** (or another host fetch that returns page text) on the canonical `https://weixin.qq.com/sph/<id>` URL.

Measured 2026-10-26: WebFetch of `https://weixin.qq.com/sph/AAZ3p39sQm` returned caption/description text (about Codex token waste / ChatGPT brainstorm then Codex exec), date `2026年9月2日`, and a thumbnail. It did **not** return the spoken video body. Raw curl of the same URL often returns the SPA shell only, so a curl shell is not proof the caption is missing. Use WebFetch or an equivalent host fetch that returns page text.

On a caption fetch (metadata only, not Understanding):

- `caption`: the caption/description (include the visible date when present).
- `body_kind` stays `unavailable` until a media file is read. Do not set `body_kind: caption` as a successful video read.
- `fetch_method` for the caption note: `webfetch` (ContentRecord alias `public_webfetch` — the same host page-text fetch, not a private API). The video record stays `acquire_failed` / `blocked` until the file exists.
- Keep the thumbnail URL in `media_notes` when it is useful. Do not pretend the thumbnail was watched as the video.
- `limits`: state that the caption was not used as the video body.

If WebFetch returns only an empty shell, set `body_kind: unavailable` and `fetch_method: blocked` for that caption attempt, then continue with the speech path below. Do not rotate user agents, replay challenges, or call private APIs.

## Read the file

A caption is not the video. To understand what is shown and said:

1. Accept a pasted transcript. Store supplied speech in `body_text`, `body_kind: transcript`, `fetch_method: user_paste`. On-screen text that is not speech stays caption or notes.
2. Otherwise ask the user to share/export/save an **actual video/audio file** using supported WeChat/creator controls or an authorized browser workflow. A share card, bookmark, sph link, or article containing a 视频号 embed is not a media file. If no export is offered, ask for text or a user-provided authorized copy. Do not introduce unofficial downloaders.
3. Run frames, OCR, and ASR on the local file. Describe the frames with the host vision tool.

   Windows:

   ```powershell
   py -3.12 skills\social-content-reader\scripts\extract_frames.py --media "C:\Media\channels.mp4" --mode fps --fps 1 --max-frames 24
   py -3.12 skills\social-content-reader\scripts\ocr_frames.py --frames-json frames.json
   py -3.12 skills\social-content-reader\scripts\asr_local.py --media "C:\Media\channels.mp4" --language zh --backend auto --model base
   ```

   Mac / Linux:

   ```bash
   python3 skills/social-content-reader/scripts/extract_frames.py --media "$HOME/Media/channels.mp4" --mode fps --fps 1 --max-frames 24
   python3 skills/social-content-reader/scripts/ocr_frames.py --frames-json frames.json
   python3 skills/social-content-reader/scripts/asr_local.py --media "$HOME/Media/channels.mp4" --language zh --backend auto --model base
   ```

   Resolve the helper relative to `SKILL.md` when installed elsewhere. Use `--language auto` for unknown speech language. See [setup and backend behavior](../scripts/README.md).
4. Check exit codes and `ok`. Copy ASR JSON `text` into `speech_text`, OCR text into `visual_text`, and the host vision notes into `visual_description`. Set `body_kind: media_understanding` and `fetch_method: media_pipeline` when pictures and speech were both read. ASR alone is `body_kind: transcript` with a limit that graphics were not read. Record backend/model/language in `media_notes`/`limits`. Keep the original sph share URL when known; do not invent one for a file-only request.
5. Summarize, translate, or answer from visuals + OCR + transcript. ASR does not establish silent visuals. A WebFetch caption may be quoted only as a labeled side note in `caption`.

`channels.weixin.qq.com` feed URLs stay `fetch_method: blocked` / `body_kind: unavailable` for remote deep-read. Ask for a media file or pasted speech. An sph link can add caption metadata; it does not replace the file.

## Creator 视频号助手 APIs (documentation only)

Official creator/merchant capabilities require account authorization and capability-specific access; they do not provide a general consumer API for arbitrary 视频号 speech. Consult the user's applicable [official WeChat documentation](https://developers.weixin.qq.com/) and enabled capabilities.

Suggested environment names for a separate creator integration:

- `WECHAT_CHANNELS_APP_ID`
- `WECHAT_CHANNELS_APP_SECRET`
- `WECHAT_CHANNELS_ACCESS_TOKEN`
- `WECHAT_CHANNELS_CREATOR_ID` (only if required by that capability)

Names only: never commit or echo secrets. These are integration conventions, not implemented API coverage and not inputs to `asr_local.py`. Do not promise media/transcript retrieval unless the specific official authorized capability supports it. A user-provided cross-post/mirror URL can also use its platform recipe.

## Hard limits

No login bypass, captcha defeat, cookie dumping/theft, private API scrapers, or reverse-engineering encrypted streams. Do not treat a caption, or a remote fetch failure, as proof that a user-provided video cannot be understood. Local ASR is preferred; API ASR uploads require user authorization as described in the ASR pipeline.

## Success criteria

- Video: local file read with frames and speech (`body_kind: media_understanding`), or an honest `transcript` / `visual` gap. A caption alone is not success.
- sph share link: caption may be stored in `caption` via WebFetch. It is not `body_text` for the video.
- `channels.weixin.qq.com` feed paths: remain blocked (`errCode 10012`). Ask for a file or pasted speech.
