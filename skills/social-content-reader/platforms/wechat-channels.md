# WeChat 视频号 (Channels)

**Status:** Works with user media + ASR (remote URL-only fetch blocked).

## URL patterns and observed network limit

- `channels.weixin.qq.com` share links and in-app 视频号 cards.
- The repository's [earlier network smoke](../../../SMOKE_RESULTS.md) got a homepage shell and feed response `errCode: 10012`, `errMsg: Illegal request`. These contain no video body/transcript. Treat remote URL-only fetching as blocked; do not keep probing undocumented endpoints.

## Primary path: user text or saved/exported video

Prefer an existing authorized host connector if it actually returns a transcript or permitted media. Otherwise:

1. Accept a pasted transcript/on-screen text. Store supplied speech in `body_text`, `body_kind: transcript`, `fetch_method: user_paste`; label caption-only material accordingly.
2. If speech understanding is needed, ask the user to share/export/save an **actual video/audio file** using supported WeChat/creator controls or an authorized browser workflow. A share card, bookmark, or article containing a 视频号 embed is not a media file. If no export is offered, ask for text or a user-provided authorized copy; do not introduce unofficial downloaders.
3. Run ASR on the local file:

   ```powershell
   python skills/social-content-reader/scripts/asr_local.py --media "C:\Media\channels.mp4" --language zh --backend auto --model base
   ```

   Resolve the helper relative to `SKILL.md` when installed elsewhere. Use `--language auto` for unknown speech language. See [setup and backend behavior](../scripts/README.md).
4. Check exit code and `ok`. On success, copy JSON `text` into `body_text`, set `body_kind: transcript`, `fetch_method: user_media_asr`, and record backend/model/language plus speech-only limitations in `media_notes`/`limits`. Keep the original share URL when known; do not invent one for a file-only request.
5. Summarize, translate, or answer from the transcript. ASR is speech evidence; it does not establish visual details or guarantee perfect names/numbers. Request screenshots or pasted on-screen text for silent content.

If only the remote URL is available, return `fetch_method: blocked`, `body_kind: unavailable`, empty `body_text`, and ask for a file or text. When the user supplies media, switch to ASR instead of continuing to report a platform-wide block.

## Creator 视频号助手 APIs (documentation only)

Official creator/merchant capabilities require account authorization and capability-specific access; they do not provide a general consumer API for arbitrary 视频号 speech. Consult the user's applicable [official WeChat documentation](https://developers.weixin.qq.com/) and enabled capabilities.

Suggested environment names for a separate creator integration:

- `WECHAT_CHANNELS_APP_ID`
- `WECHAT_CHANNELS_APP_SECRET`
- `WECHAT_CHANNELS_ACCESS_TOKEN`
- `WECHAT_CHANNELS_CREATOR_ID` (only if required by that capability)

Names only: never commit or echo secrets. These are integration conventions, not implemented API coverage and not inputs to `asr_local.py`. Do not promise media/transcript retrieval unless the specific official authorized capability supports it. A user-provided cross-post/mirror URL can also use its platform recipe.

## Hard limits

No login bypass, captcha defeat, cookie dumping/theft, private API scrapers, or reverse-engineering encrypted streams. Do not treat remote fetch failure as proof that a user-provided video cannot be understood. Local ASR is preferred; API ASR uploads require user authorization as described in the ASR pipeline.

## Success criteria

- User media ASR `ok: true` or pasted transcript; remote URL-only → `blocked` + ask for file/text.
