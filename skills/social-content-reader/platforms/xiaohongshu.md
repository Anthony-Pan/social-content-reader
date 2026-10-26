# 小红书 / RedNote (Xiaohongshu)

**Status:** Partial. Note text is most reliable via user paste. Video notes and image graphics need media. Remote deep-read is often login-walled.

## URL patterns

- `https://www.xiaohongshu.com/explore/{id}`
- `https://www.xiaohongshu.com/discovery/item/{id}`
- `https://xhslink.com/{short}` (resolve redirects)

## Video and graphics

The note body is the written post (`body_kind: post_text`) when a paste or a public fetch actually returns it. A title card or share caption is not the note and not a video. Video notes follow [_video-body.md](_video-body.md) on a user-exported file (or `yt-dlp` only when that public URL downloads without a login bypass): frames, OCR, host vision, ASR with `--language zh`. Image notes: run `ocr_frames.py` and the host vision tool on the images the user supplied. If the pictures or the video were not acquired, say so. Do not describe unseen graphics from the title.

## Prefer (in order)

1. Host Xiaohongshu connector if the user installed an authorized one that returns the note body or the media file.
2. **User paste** of the note text (most reliable for the written post).
3. Resolve short links; one public WebFetch of the note URL — use the note body only if it is returned without login.
4. Images: user screenshots or saved images → `ocr_frames.py` and host vision.
5. Video notes: local file → the [media pipeline](_video-body.md).

## Fetch recipe

1. Canonicalize to explore/item id when possible.
2. Prefer paste/connector over brittle HTML.
3. Set `body_kind: post_text` for a real note body; `media_understanding` after a video/image read; `unavailable` for a title-only card.
4. Understanding of a video or image note comes from the media. A share card is `caption` only.

## Honest limits

- 小红书 commonly forces app/login for full content. Honest default: **ask the user to paste**.
- No captcha defeat, app API reverse-engineering, or cookie theft.
- Shopping / live modules are out of scope unless text is pasted.

## Codex prompt sketch

```text
Follow platforms/xiaohongshu.md and platforms/_video-body.md. URL: <URL>
Paste or connector for the note text. Video and images need a local file.
A title card is not Understanding. If acquire fails, say so.
```
