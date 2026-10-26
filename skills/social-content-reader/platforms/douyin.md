# Douyin 抖音

**Status:** Media required. Default acquire is automatic: Playwright opens the mobile share player and saves the mp4. A share caption is metadata, not the video.

**Goal:** Read pictures, burned-in text, and speech from the file `acquire_douyin.py` saved. Follow [the shared video recipe](_video-body.md). Do not write Understanding from the caption.

## URL patterns

- `https://v.douyin.com/{short}` (resolve to an aweme id)
- `https://www.douyin.com/video/{id}`
- `https://m.douyin.com/share/video/{id}` (the page that plays)
- `https://www.iesdouyin.com/share/video/{id}` (often the in-app wall — not the player)

## Video and graphics

Default success is a local mp4, then frames, OCR, host vision, and ASR ([_video-body.md](_video-body.md)). The agent runs the acquire helper below on its own. Do not ask the user to export from the Douyin app first.

Put any share-page caption in `caption` only when a separate metadata fetch returned one. It is not Understanding. If acquire fails, set `body_kind: unavailable` and say the video was not watched.

## Prefer (in order)

1. **`scripts/acquire_douyin.py`** — the default. No user handoff. Measured on Mac, 2026-10-26, for `https://v.douyin.com/2qulGbSTiRI/` → aweme **7696098282904259850**:
   1. Playwright Chromium, mobile UA.
   2. Open `https://www.douyin.com/` so this browser receives cookies.
   3. Open `https://m.douyin.com/share/video/{id}`.
   4. Read `<video>.currentSrc` / `<video>.src`. It is a play URL of the form `https://m.douyin.com/aweme/v1/playwm/?…&video_id=v0…`.
   5. GET that playwm URL with the **same browser context** (those cookies) and `Referer` set to the mobile share page. The response follows to a CDN `video/mp4`.

   Re-downloaded on Anthony’s Mac, 2026-10-26, from that short link: about 8MB. The same helper has acquired this aweme repeatedly on that Mac. Then run the media pipeline on `path`. Do not write Understanding from the caption.

   ```bash
   python3 skills/social-content-reader/scripts/acquire_douyin.py \
     "https://v.douyin.com/2qulGbSTiRI/" --out-dir "$HOME/Media"
   python3 skills/social-content-reader/scripts/extract_frames.py \
     --media "$HOME/Media/douyin_7696098282904259850.mp4" --mode fps --fps 1 --max-frames 24
   python3 skills/social-content-reader/scripts/ocr_frames.py --frames-json frames.json
   python3 skills/social-content-reader/scripts/asr_local.py \
     --media "$HOME/Media/douyin_7696098282904259850.mp4" --language zh --backend auto --model base
   ```

   A bare aweme id works in the same position: `7696098282904259850`. The helper writes `{out-dir}/douyin_{aweme_id}.mp4` and prints JSON with `ok`, `path`, `bytes`, `content_type`, `aweme_id`, and `play_url`. Require `ok: true` and a real `path`. On failure, `body_snip` is a page excerpt for diagnosis, not Understanding. The host agent then watches the file and the frames.

   Install once: `python3 -m pip install playwright && python3 -m playwright install chromium` (Windows: `py -3.12`). See [requirements-acquire.txt](../scripts/requirements-acquire.txt).

2. A file the user already attached. Skip acquire and read that file. Do not ask for one when step 1 has not been tried.
3. **yt-dlp** only when the web detail page is already playing and step 1 did not return a file. Do not point it at stolen cookies.
4. **User export is the fallback**, only if the mobile share page has no `<video>` src (the in-app wall, a captcha, or Playwright/Chromium missing). Say acquire failed. Do not write Understanding from the caption.

## In-app wall vs the player (2026-10-26)

Share `https://v.douyin.com/2qulGbSTiRI` resolves to aweme **7696098282904259850**.

- A datacenter `curl` follows `v.douyin.com` → `www.iesdouyin.com/share/video/7696098282904259850/` → `www.douyin.com/video/7696098282904259850` and gets a JavaScript shell, not an mp4. **iesdouyin share pages often show 「请尝试在抖音内观看」.** That page is not the acquire target.
- The page that played is `https://m.douyin.com/share/video/7696098282904259850` after a Playwright visit to `https://www.douyin.com/` in the same browser. The `<video>` element exposed the playwm URL, and that URL followed to the CDN mp4.
- If `m.douyin.com/share/video/{id}` itself has no `<video>` src and shows 「请尝试在抖音内观看」 or a captcha, stop. Do not solve the captcha, do not dump cookies, do not decrypt a CDN URL, and do not call a private API. User export is then the remaining file source.

## Fetch recipe

1. Resolve a short link to the numeric aweme id (`acquire_douyin.py` does this from public redirects).
2. Run the helper. Do not stop on the iesdouyin wall before trying the mobile share page.
3. On `ok: true`, set `fetch_method: playwright_playwm`, then frames + OCR + host vision + ASR on `path`. `body_kind: media_understanding` only after pictures and speech were both read.
4. On failure, `body_kind: unavailable`, `fetch_method: acquire_failed` or `blocked`. Leave `speech_text` and `visual_description` empty. Do not write Understanding from the caption.

## Honest limits

- Cookies stay inside the Playwright context that just visited `www.douyin.com`. The helper does not write a cookie file and does not read the user's browser profile.
- No captcha defeat, login bypass, cookie theft, CDN decrypt, or private API reverse-engineering. playwm is the URL the page's own `<video>` element is playing.
- TikTok oEmbed does not read Douyin videos.
- A download under 20KB is a failure (`download too small`). Do not treat that body as the video.

## Codex prompt sketch

```text
Follow platforms/douyin.md and platforms/_video-body.md. URL: <URL>
Run acquire_douyin.py (homepage cookies, then m.douyin.com/share/video, then the <video> playwm URL).
Read frames, burned-in text, and speech from the mp4. Describe the frames with the host video tool.
Do not write Understanding from the caption.
If the mobile share page has no <video> src, say acquire failed.
```
