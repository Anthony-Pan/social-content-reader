# Douyin 抖音

**Status:** Partial — share-link caption sometimes available; speech via user media + ASR. Remote deep-read often blocked.

## URL patterns

- `https://www.douyin.com/video/{id}`
- `https://v.douyin.com/{short}` (resolve redirects)
- `https://www.iesdouyin.com/share/video/{id}`

## Prefer (in order)

1. Host Douyin/ByteDance connector if the user installed one with authorized access.
2. Resolve short links (`curl.exe -I -L`) to a canonical video URL; attempt public share-page caption extraction via WebFetch — only if real caption text appears without login.
3. User paste of caption / on-screen text.
4. **User-exported video + ASR** (primary path for speech):
   ```powershell
   python skills/social-content-reader/scripts/asr_local.py --media "C:\Media\douyin.mp4" --language zh --backend auto --model base
   ```
5. Optional approved download for a user-owned/explicitly approved URL — never login bypass.

## Fetch recipe

1. Normalize short links to `douyin.com/video/{id}` when possible.
2. Caption from share page / paste → `caption_only`.
3. Speech → ASR → `transcript` + `user_media_asr`.
4. If remote fetch yields empty/verification page, skip retries beyond a single polite attempt and ask for media/text.

## Honest limits

- Douyin aggressively blocks anonymous scrapers. Honest default for speech: **user media + ASR**.
- No captcha defeat, cookie dumping, or private API reverse-engineering.
- Same corporate family as TikTok — do not assume TikTok oEmbed works for Douyin URLs.

## Codex prompt sketch

```text
Follow platforms/douyin.md. URL: <URL>
Prefer user media+ASR for speech; caption-only if share page gives text.
```
