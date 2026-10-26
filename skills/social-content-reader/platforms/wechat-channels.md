# WeChat 视频号 (Channels)

**Status:** Partial. `weixin.qq.com/sph/<id>` share links expose caption/description (often with a date and thumbnail) via WebFetch. That text is not the spoken video. Speech still needs user media + `asr_local.py`. `channels.weixin.qq.com` feed paths remain blocked (`errCode 10012`) for remote deep-read.

## URL patterns

- Share links (preferred): `https://weixin.qq.com/sph/<id>` and `https://www.weixin.qq.com/sph/<id>`.
  `normalize_url.py` sets `platform: wechat-channels`, `canonical_id` to the sph id, `canonical_url` to `https://weixin.qq.com/sph/<id>`, and `link_form: sph_share`.
- `channels.weixin.qq.com` web/feed paths and in-app 视频号 cards. These are not sph share links. The [earlier network smoke](../../../SMOKE_RESULTS.md) got a homepage shell and feed response `errCode: 10012`, `errMsg: Illegal request`. Those responses contain no video body or transcript. Do not keep probing undocumented endpoints.

## Caption from an sph share link

Prefer **WebFetch** (or another host fetch that returns page text) on the canonical `https://weixin.qq.com/sph/<id>` URL.

Measured 2026-10-26: WebFetch of `https://weixin.qq.com/sph/AAZ3p39sQm` returned caption/description text (about Codex token waste / ChatGPT brainstorm then Codex exec), date `2026年9月2日`, and a thumbnail. It did **not** return the spoken video body. Raw curl of the same URL often returns the SPA shell only, so a curl shell is not proof the caption is missing. Use WebFetch or an equivalent host fetch that returns page text.

On success:

- `body_text`: the caption/description (include the visible date when present).
- `body_kind: caption`
- `fetch_method: webfetch` (ContentRecord alias `public_webfetch` — the same host page-text fetch, not a private API).
- Keep the thumbnail URL in `media_notes` when it is useful. Do not download the video.
- `limits`: state that the caption/description is not speech.

If WebFetch returns only an empty shell, set `body_kind: unavailable` and `fetch_method: blocked` for that caption attempt, then continue with the speech path below. Do not rotate user agents, replay challenges, or call private APIs.

## Spoken understanding: user media + ASR

Caption is not speech. To understand what is said:

1. Accept a pasted transcript. Store supplied speech in `body_text`, `body_kind: transcript`, `fetch_method: user_paste`. On-screen text that is not speech stays caption or notes.
2. Otherwise ask the user to share/export/save an **actual video/audio file** using supported WeChat/creator controls or an authorized browser workflow. A share card, bookmark, sph link, or article containing a 视频号 embed is not a media file. If no export is offered, ask for text or a user-provided authorized copy. Do not introduce unofficial downloaders.
3. Run ASR on the local file.

   Windows:

   ```powershell
   python skills/social-content-reader/scripts/asr_local.py --media "C:\Media\channels.mp4" --language zh --backend auto --model base
   ```

   Mac / Linux:

   ```bash
   python3 skills/social-content-reader/scripts/asr_local.py --media "$HOME/Media/channels.mp4" --language zh --backend auto --model base
   ```

   Resolve the helper relative to `SKILL.md` when installed elsewhere. Use `--language auto` for unknown speech language. See [setup and backend behavior](../scripts/README.md).
4. Check exit code and `ok`. On success, copy JSON `text` into `body_text`, set `body_kind: transcript`, `fetch_method: user_media_asr`, and record backend/model/language plus speech-only limitations in `media_notes`/`limits`. Keep the original sph share URL when known; do not invent one for a file-only request.
5. Summarize, translate, or answer from the transcript when the user asked about speech. ASR is speech evidence; it does not establish visual details or guarantee perfect names/numbers. Request screenshots or pasted on-screen text for silent content. Quote a WebFetch caption beside a transcript only when you label which is which.

If the user asked what the video is about and only the caption was fetched, answer from the caption and say the spoken body was not read.

`channels.weixin.qq.com` feed URLs stay `fetch_method: blocked` / `body_kind: unavailable` for remote deep-read. Ask for an sph share link (caption), a media file, or pasted text.

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

- sph share link: WebFetch caption/description in `body_text` with `body_kind: caption` and `fetch_method: webfetch`, or an honest unavailable/blocked caption attempt.
- Speech: user media ASR `ok: true`, or a pasted transcript. A caption alone is not a transcript.
- `channels.weixin.qq.com` feed paths: remain blocked (`errCode 10012`). Ask for an sph share link, a file, or text.
