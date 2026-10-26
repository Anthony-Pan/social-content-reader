# Video and graphics — shared recipe

**Default success** for a video is a local media file that was actually read: pictures, burned-in text, and speech. A share caption, oEmbed title, or description is **metadata**. It is never the video Understanding.

Use this recipe from every platform doc when the user asks what a video shows or says. Text posts and articles keep their own written-body recipes; an attached video still comes here.

## Pipeline

1. **Acquire** a local video (or audio, or a keyframe set the user already exported). See [Acquire](#acquire) below.
2. **Frames.** Uniform or scene-change stills:

   ```bash
   python3 skills/social-content-reader/scripts/extract_frames.py \
     --media "$HOME/Media/clip.mp4" --mode fps --fps 1 --max-frames 24
   ```

   ```powershell
   py -3.12 skills\social-content-reader\scripts\extract_frames.py --media "C:\Media\clip.mp4" --mode scene --scene-threshold 0.3 --max-frames 24
   ```

   Require `ok: true` and a non-empty `frames` array. Keep `timestamp_sec` with each path. `truncated: true` means the cap hid later frames — say so, or raise `--max-frames` / lower `--fps`.
3. **Burned-in text (OCR).** Optional engine, honest failure:

   ```bash
   python3 skills/social-content-reader/scripts/ocr_frames.py --frames-json frames.json
   ```

   Tesseract when it is on PATH (`chi_sim+eng` when language data exists, else `eng`). On macOS, `--engine vision` uses `ocr_vision.swift` via `swiftc` when Tesseract is absent. If the helper returns `engine: none`, do not invent on-screen text. Say OCR did not run.
4. **Vision / video description.** This skill does not bundle a vision model. The host agent looks at the **video file and the extracted frames** with its own video/vision tools and writes `visual_description`: people, graphics, burned-in words, cuts, on-screen claims. If the host has no vision tool, say visual description was not produced.
5. **Speech.** Official transcript/CC tracks when that platform documents them (YouTube, Bilibili CC, Vimeo text tracks, Twitch CC). Otherwise [scripts/asr_local.py](../scripts/asr_local.py) on the local file. Map ASR `text` to `speech_text`. ASR does not see pictures. A transcript-only result is speech, not full video Understanding, unless frames were also read.
6. **Write Understanding** from `visual_description` + OCR `text` + `speech_text`. Put any share caption in `caption` and mention it only as a labeled side note.
7. **Acquire failure.** If step 1 does not yield a file, stop. Set `body_kind: unavailable` and `fetch_method: acquire_failed` (or `blocked` when the platform wall is the reason). Say the video was not watched. Do not write Understanding from the caption. A caption may sit in `caption` so the user can see the share text; it must be labeled metadata.

## ContentRecord fields

| Field | Video success | Acquire failed |
| --- | --- | --- |
| `body_kind` | `media_understanding` (pictures and speech), `transcript` (speech only), or `visual` (pictures only) | `unavailable` |
| `body_text` | Labeled join of visuals, OCR, and speech | empty, or a one-line statement that the video was not read |
| `speech_text` | ASR or official transcript | empty |
| `visual_text` | OCR text | empty |
| `visual_description` | Host vision notes | empty |
| `caption` | Share caption / description, if any | same, labeled metadata |
| `fetch_method` | `media_pipeline`, `user_media_asr`, `host_connector`, or `public_api` for an official transcript | `acquire_failed` or `blocked` |
| `limits` | truncated frames, speech-only, OCR engine missing, auto-caption uncertainty | the acquire error in plain language |

`body_kind: caption` is not a successful video read.

## Acquire

Prefer a file the user already has (app Save/Download/export, screen recording they made, camera roll). When the user asked to **read the video**, the documented public CLI **yt-dlp** is an allowed way to acquire a local file only where a run has actually saved one. Mac, 2026-10-26: YouTube `yt-dlp` saved a file; the TikTok sample was IP-blocked; Bilibili `yt-dlp` returned HTTP 412 and public playurl is not a verified file recipe. Do not claim those last two until a sample saves a video. Example:

```bash
yt-dlp --no-playlist -o "%(id)s.%(ext)s" "<video url>"
```

Stop if yt-dlp hits a login wall, captcha, or DRM. Do not add cookie theft, captcha defeat, CDN decryption, or private undocumented API clients. Other optional download tools, when ToS-sensitive, still need explicit user approval **for that URL**.

**Browser cookies:** only when the user wants yt-dlp to use **their own** already-logged-in browser on their machine (`--cookies-from-browser`) because the web player actually plays. Do not export those cookies into the repo, the chat log, or another machine. If playback still does not start, cookies did not unlock it — stop.

**Browser capture:** when a normal page load actually plays the video, save that playing media. Playwright (or any browser tool) is only a way to hold a page that is already playing. It is not a way through an in-app wall.

### Per platform (honest)

| Platform | What usually yields a file | When acquire is blocked |
| --- | --- | --- |
| YouTube | Host connector media or transcript; `yt-dlp` for the file when the user asked to read the video. Mac, 2026-10-26: `yt-dlp` acquired a YouTube file on Anthony’s network. Official captions cover **speech**; frames still required for graphics. The file alone is not Understanding. | Private, members-only, age-gated, DRM. Description is not the body. |
| TikTok | A file the user already has, or in-app Save/download. `yt-dlp` only after **this** URL returns a video file. Mac, 2026-10-26: the sample tried from Anthony’s network was IP-blocked. That is not a verified file recipe. | Login, region, IP block, or deleted videos. oEmbed caption is not the body. |
| Instagram | In-app Share → Download/Save when offered; `yt-dlp` when the user asked to read that Reel and the download works without a login bypass. | Login/captcha. Stop. oEmbed HTML is not the Reel. |
| Douyin 抖音 | **Default:** `scripts/acquire_douyin.py`. Playwright Chromium (mobile UA) opens `https://www.douyin.com/` for cookies, then `https://m.douyin.com/share/video/{id}`, reads `<video>.src` / `currentSrc` (`https://m.douyin.com/aweme/v1/playwm/?…`), and GETs that URL with the same browser and the share page as Referer. The response is a CDN mp4 written as `{out-dir}/douyin_{aweme_id}.mp4`. No user export first. Mac, 2026-10-26: aweme `7696098282904259850` from `https://v.douyin.com/2qulGbSTiRI/` re-downloaded repeatedly (~8MB). | iesdouyin often shows 「请尝试在抖音内观看」 and is not the player. If the **mobile** share page has no `<video>` src, acquire failed. User export is only that fallback. Caption is not the video. |
| WeChat 视频号 | User Save/export from WeChat or a file they already have. | No general public file URL. `channels.weixin.qq.com` feed `errCode 10012`. sph WebFetch caption is not the video. |
| Bilibili | Public CC for speech when the subtitle API returns cues. Graphics need a real file. Mac, 2026-10-26: `yt-dlp` returned HTTP 412. Public playurl is not a verified file recipe. `desc` is not speech. | 大会员, region lock, paywall, HTTP 412. Stop and say the file was not acquired. |
| Vimeo | Text tracks for speech when present; `yt-dlp` or the user file for frames. | Password, domain restriction, private. oEmbed description is not the body. |
| Twitch | User file or an authorized VOD/clip download; Helix is metadata. Creator CC when the connector exposes it. | Live chat is not speech. Do not rip VODs the user did not ask to read. |
| X, Threads, Facebook, Reddit, LinkedIn, Telegram, 小红书 | Written post/article text is the **post**, not a video. For an attached video or video note: user file, or `yt-dlp` where that public URL actually downloads. | Login walls. Do not treat the post caption as the video. |
| WeChat 公众号 | Article HTML is the article. An embedded 视频号 still needs a media file. | Verification / captcha → ask for a paste. Do not solve the captcha. |

## Douyin in-app wall

Measured **2026-10-26**:

- Share: `https://v.douyin.com/2qulGbSTiRI`
- Video id: `7696098282904259850`
- Public redirect chain from this environment: `v.douyin.com` → `www.iesdouyin.com/share/video/7696098282904259850/` → `https://www.douyin.com/video/7696098282904259850?previous_page=app_code_link`
- A datacenter `curl` of that chain returns a JavaScript shell, not a media file and not a transcript. The shell does not include the spoken or visual body.
- **iesdouyin** share pages often show **「请尝试在抖音内观看」**. A datacenter curl of that chain is a JavaScript shell, not an mp4. Do not stop there.
- **Working player (Mac, 2026-10-26, repeated):** Playwright Chromium, mobile UA, visit `https://www.douyin.com/` (cookies in that browser only), then `https://m.douyin.com/share/video/7696098282904259850`. `<video>.currentSrc` was `https://m.douyin.com/aweme/v1/playwm/?…&video_id=v0…`. GET that URL with the same browser context and `Referer` set to the share page. It followed to a CDN `video/mp4` (~8MB, 1280×720, H.264+AAC, ~49s). The same helper re-downloaded this aweme from the short link. Helper: `scripts/acquire_douyin.py` (positional URL or aweme id, `--out-dir`; writes `douyin_{aweme_id}.mp4`; success JSON `ok: true`). Then frames, OCR, ASR, and the host video tool.
- If that mobile share page has no `<video>` src (wall text or a captcha), acquire is blocked. Do not solve the captcha, dump cookies, or decrypt the CDN. User export is the fallback, not the default. Do not pretend a share caption is Understanding.

## Hard limits

No captcha defeat, login bypass, cookie theft, CDN decrypt, or private undocumented API reverse-engineering. No unofficial scraper services. If acquire fails, say so.
