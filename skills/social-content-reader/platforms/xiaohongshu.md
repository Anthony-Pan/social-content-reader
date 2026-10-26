# 小红书 / RedNote (Xiaohongshu)

**Status:** Partial — note text sometimes via share link / user paste; media speech via user media + ASR. Remote deep-read frequently login-walled.

## URL patterns

- `https://www.xiaohongshu.com/explore/{id}`
- `https://www.xiaohongshu.com/discovery/item/{id}`
- `https://xhslink.com/{short}` (resolve redirects)

## Prefer (in order)

1. Host Xiaohongshu connector if user installed an authorized one.
2. Resolve short links; try public WebFetch of the note URL once — use note body only if returned without login.
3. **User paste** of the note text (most reliable).
4. Image OCR: user screenshots + host vision/OCR tools (optional).
5. Video notes: user-exported media + ASR (`--language zh`).

## Fetch recipe

1. Canonicalize to explore/item id when possible.
2. Prefer paste/connector over brittle HTML.
3. Set `body_kind: post_text` for note body; `transcript` after ASR; `caption_only` for title-only cards.
4. Understanding from note body; disclose when only a share card was available.

## Honest limits

- 小红书 commonly forces app/login for full content. Honest default: **ask the user to paste**.
- No captcha defeat, app API reverse-engineering, or cookie theft.
- Shopping / live modules are out of scope unless text is pasted.

## Codex prompt sketch

```text
Follow platforms/xiaohongshu.md. URL: <URL>
Prefer paste/connector; one polite public fetch; else user media+ASR for video notes.
```
