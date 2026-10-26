# WeChat 视频号 (Channels)

**Status:** Works for understanding from a public `weixin.qq.com/sph/<id>` share caption. WebFetch the share page, put the caption in `body_text`, and always write the Understanding section from that text. Spoken ASR is optional. `channels.weixin.qq.com` feed paths stay blocked (`errCode 10012`).

## URL patterns

- Share links (preferred): `https://weixin.qq.com/sph/<id>` and `https://www.weixin.qq.com/sph/<id>`.
  `normalize_url.py` sets `platform: wechat-channels`, `canonical_id` to the sph id, `canonical_url` to `https://weixin.qq.com/sph/<id>`, and `link_form: sph_share`.
- `channels.weixin.qq.com` web/feed paths and in-app cards that are not sph share links. The [earlier network smoke](../../../SMOKE_RESULTS.md) got a homepage shell and feed response `errCode: 10012`, `errMsg: Illegal request`. Those responses contain no caption. Do not keep probing undocumented endpoints. Ask for an sph share URL when the user only has a feed link.

## Primary path: sph share caption → understand

For a typical 视频号 post, the share caption **is** the publishable copy. It is enough to understand what the video is about: claims, tips, and topic. Produce the Understanding section from that caption. Do not stop at "caption only", and do not ask the user to save media for "what is this about?".

**Recipe:** WebFetch `https://weixin.qq.com/sph/<id>` → `body_text` = caption, `body_kind: caption`, `fetch_method: webfetch` → Understanding (5–12 lines) from `body_text`.

Prefer **WebFetch** (or another host fetch that extracts share-page text). Bare curl of the same URL is often a JS shell without the caption, so a curl shell is not proof the caption is missing. Do not use raw curl as the caption fetch.

Measured 2026-10-26: WebFetch of `https://weixin.qq.com/sph/AAZ3p39sQm` returned a Chinese caption about Codex token waste — brainstorm the task in ChatGPT first, then hand the conversation to Codex — plus date `2026年9月2日` and a thumbnail. That URL is the caption→understand example. Expected themes: Codex token waste; brainstorm in ChatGPT first.

On success:

- `body_text`: the caption/description (include the visible date when present).
- `body_kind: caption`
- `fetch_method: webfetch` (ContentRecord alias `public_webfetch` — the same host page-text fetch, not a private API).
- Keep the thumbnail URL in `media_notes` when it is useful. Do not download or decrypt the video.
- **Understanding:** 5–12 lines from `body_text` covering what the post argues, the practical tip, and the topic. For `AAZ3p39sQm`, cover Codex token waste and brainstorming in ChatGPT before handing work to Codex.
- `limits`: the record is the publishable caption, which is enough to understand the post. A spoken transcript was not requested. This label does not block the Understanding section.

If WebFetch returns only an empty shell or a useless caption, set `body_kind: unavailable` and `fetch_method: blocked` for that attempt. The optional speech path below applies only in that case, or when the user asks for spoken words. Do not rotate user agents, replay challenges, or call private APIs.

## Optional: spoken transcript (user media + ASR)

ASR is not the default and is not required to answer what the video is about. Use it only when:

- the user asks for a spoken or verbatim transcript, or
- the sph caption came back empty or useless.

1. Accept a pasted transcript. Store supplied speech in `body_text`, `body_kind: transcript`, `fetch_method: user_paste`.
2. Otherwise the user may share, export, or save an **actual video/audio file** with supported WeChat or creator controls. A share card, bookmark, sph link, or article that only embeds 视频号 is not a media file. Do not introduce unofficial downloaders.
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
5. When the user asked about speech, summarize from the transcript. ASR is speech evidence; it does not establish visual details or guarantee perfect names/numbers. If both a WebFetch caption and a transcript exist, label which is which.

`channels.weixin.qq.com` feed URLs stay `fetch_method: blocked` / `body_kind: unavailable` for remote deep-read. Ask for an sph share link. A feed block is not a reason to demand a file when an sph URL is already in hand.

## Creator 视频号助手 APIs (documentation only)

Official creator/merchant capabilities require account authorization and capability-specific access; they do not provide a general consumer API for arbitrary 视频号 speech. Consult the user's applicable [official WeChat documentation](https://developers.weixin.qq.com/) and enabled capabilities.

Suggested environment names for a separate creator integration:

- `WECHAT_CHANNELS_APP_ID`
- `WECHAT_CHANNELS_APP_SECRET`
- `WECHAT_CHANNELS_ACCESS_TOKEN`
- `WECHAT_CHANNELS_CREATOR_ID` (only if required by that capability)

Names only: never commit or echo secrets. These are integration conventions, not implemented API coverage and not inputs to `asr_local.py`. Do not promise media/transcript retrieval unless the specific official authorized capability supports it. A user-provided cross-post/mirror URL can also use its platform recipe.

## Hard limits

No login bypass, captcha defeat, cookie dumping/theft, private API scrapers, CDN decrypt scrapers, unofficial video downloaders, or third-party parser APIs (AnyFetcher, Tikomni, Evil0ctal-style, and similar). A nonempty sph caption is a successful understanding path. Local ASR is optional and only for spoken-verbatim or empty-caption cases. API ASR uploads require user authorization as described in the ASR pipeline.

## Success criteria

- sph URL only: WebFetch caption in `body_text` with `body_kind: caption` and `fetch_method: webfetch`, plus a 5–12 line Understanding. No ask for a file.
- Example `https://weixin.qq.com/sph/AAZ3p39sQm`: understanding covers Codex token waste and brainstorming in ChatGPT first.
- Spoken transcript: only when the user asks, or the caption is empty/useless (user media ASR `ok: true`, or a pasted transcript).
- `channels.weixin.qq.com` feed paths: remain blocked (`errCode 10012`).
