# Douyin 抖音

**Status:** Works when a public share caption is present. Understand from that caption. ASR is optional. Empty or verification pages stay blocked.

## URL patterns

- `https://www.douyin.com/video/{id}`
- `https://v.douyin.com/{short}` (resolve redirects)
- `https://www.iesdouyin.com/share/video/{id}`

## Prefer (in order)

1. Host Douyin/ByteDance connector if the user installed one with authorized access and it returns caption or post text.
2. Resolve short links (`curl.exe -I -L`, or the platform equivalent) to a canonical video URL. WebFetch the public share page. When real caption text appears without login, that caption is the body: `body_kind: caption`, `fetch_method: webfetch`. Write Understanding from it. Do not ask for a file.
3. User paste only when the share page has no usable caption.
4. **User-exported video + ASR** only when the user asks for spoken words, or the caption is empty/useless:

   ```powershell
   python skills/social-content-reader/scripts/asr_local.py --media "C:\Media\douyin.mp4" --language zh --backend auto --model base
   ```

   Mac / Linux: `python3` and `"$HOME/Media/douyin.mp4"`.
5. Optional approved download for a user-owned or explicitly approved URL — never login bypass. A request to summarize is not download approval.

## Fetch recipe

1. Normalize short links to `douyin.com/video/{id}` when possible.
2. Caption from the share page → `body_text`, `body_kind: caption`, then Understanding (claims, tips, topic).
3. Speech → ASR → `transcript` + `user_media_asr` only for the optional cases above.
4. If remote fetch yields an empty or verification page, skip retries beyond a single polite attempt and say the caption is unavailable. Offer paste or ASR only if the user still wants spoken words.

## Honest limits

- Douyin often blocks anonymous scrapers. When the share caption is present, use it. When it is not, say the fetch is blocked.
- No captcha defeat, cookie dumping, or private API reverse-engineering.
- Same corporate family as TikTok — do not assume TikTok oEmbed works for Douyin URLs.

## Codex prompt sketch

```text
Follow platforms/douyin.md. URL: <URL>
Share caption → understand. ASR only for spoken-verbatim or an empty caption.
```
