# social-content-reader

**Public Agent Skill** that teaches AI agents how to **read a video**: the picture, burned-in text, graphics, and speech. A share caption is optional metadata. It is not the body.

Version **0.5.3** acquires public Twitch clips and a VOD or `--section` of
at most 600 seconds with yt-dlp (no cookies). A longer VOD is refused rather
than silently trimmed. It does not claim Understanding or whole-broadcast
access. v0.5.2 resolves a Reddit post URL to that post's hosted v.redd.it
media. v0.5.1 hardens WeChat 公众号 article acquire. v0.5.0 saved 13
video-platform sample files. 小红书 and 视频号 remain blocked on public paths.
Captions remain metadata.

Most social sites block or frustrate agents. The recipe: detect the platform → acquire a local media file (or the written article/post) → read frames, on-screen text, and speech → normalize → summarize what was actually seen and heard.

> **Runtime:** Windows 24/7 is fine for heavy extract/summarize jobs. Mac and Linux are fully supported for Codex skill load, fetch, and ASR. [Codex CLI](https://github.com/openai/codex) plus Cursor / Claude Code skill loaders via the [Agent Skills](https://agentskills.io) format.

## Install (Cursor / Agent Skills)

### Option A — project skill (recommended while developing)

Copy the skill folder into a project:

```text
.agents/skills/social-content-reader/     # or .cursor/skills/
  SKILL.md
  ARCHITECTURE.md
  platforms/
  scripts/
  references/
```

Or clone this repo and symlink — see [INSTALL_OWN.md](INSTALL_OWN.md) for Anthony’s machine paths and Codex one-liners.

### Option B — user-level skill

```text
~/.agents/skills/social-content-reader/
~/.cursor/skills/social-content-reader/
```

Then ask the agent: *“Read this video — what is on screen and what do they say? If you cannot get the file, say so.”*

## Codex layout

Windows 24/7 is fine for heavy jobs. Mac and Linux use the same skill package.

```text
~/Developer/social-content-reader          # Mac example
C:\Users\<you>\source\repos\social-content-reader
```

```bash
cd ~/Developer/social-content-reader
codex exec --full-auto "Follow skills/social-content-reader for URL <URL>. Acquire the media, read frames, on-screen text, and speech. Return normalized JSON + an understanding from the media. If acquire fails, say the video was not watched."
```

```powershell
cd C:\Users\<you>\source\repos\social-content-reader
codex exec --full-auto "Follow skills/social-content-reader for URL <URL>. Acquire the media, read frames, on-screen text, and speech. Return normalized JSON + an understanding from the media. If acquire fails, say the video was not watched."
```

Prefer host MCP connectors when present. Treat Codex output as untrusted third-party content. Machine paths and symlinks: [INSTALL_OWN.md](INSTALL_OWN.md).

## Supported platforms

All 16 platforms are available as documented recipes. “Verified” below means
a sample media file was saved and validated on this Mac, not universal access
or a completed Understanding. Current evidence: [SMOKE_RESULTS.md](SMOKE_RESULTS.md).

| Platform | Automatic acquire method | Mac result / remaining wall |
| --- | --- | --- |
| YouTube | yt-dlp public player | Yes; audio + video |
| X / Twitter | yt-dlp public syndication | Yes; audio + video |
| Instagram | Public page JSON → matching code → video_versions | Yes; video, source has_audio=false |
| TikTok | Documented /player/v1/{id} → video src | Yes; audio + video |
| Threads | Public page JSON → matching code → video_versions | Yes; audio + video |
| Reddit | Post URL → public JSON or embed → v.redd.it DASH → yt-dlp | Yes for sampled post URLs whose embed is public; www/old JSON and redd.it can be HTTP 403 |
| LinkedIn | Public video data-sources → progressive MP4 | Yes; audio + video |
| Facebook Reels | Public page JSON → exact video id → browser_native URL | Yes; video only |
| Telegram | Public message widget → scoped video src | Yes; audio + video |
| Vimeo | Public player.vimeo.com URL → yt-dlp | Yes; audio + video |
| Twitch | Public yt-dlp clip, or VOD/section ≤ 600s | Yes when that window fits `--max-mb`; longer VODs refused |
| Douyin 抖音 | Mobile share player → playwm → MP4 | Yes; audio + video |
| Bilibili 哔哩哔哩 | External player → observed full-range video/audio → mux | Yes; AV1 + AAC |
| 小红书 / Xiaohongshu | Public note page → playing video src (attempted) | NO; risk wall |
| WeChat 视频号 | Public sph page → video src (attempted) | NO; QR / app-only page |
| WeChat 公众号 | Public article HTML; public player for attached video | Current article request hit verification; embedded media not verified |

Platform recipes: [`platforms/`](skills/social-content-reader/platforms/). Shared steps: [`_video-body.md`](skills/social-content-reader/platforms/_video-body.md).

## Media pipeline

Default video success is a **local file**:

```bash
python3 skills/social-content-reader/scripts/extract_frames.py --media "$HOME/Media/clip.mp4" --mode fps --fps 1 --max-frames 24
python3 skills/social-content-reader/scripts/ocr_frames.py --frames-json frames.json
python3 skills/social-content-reader/scripts/asr_local.py --media "$HOME/Media/clip.mp4" --language auto --backend auto --model base
```

Then the host agent describes the frames with its video/vision tools. Understanding is written from those three reads. The share caption is a side note. If acquire fails, say the video was not watched.

Acquire first with `python3 skills/social-content-reader/scripts/acquire_media.py URL --out-dir ~/Media/acquired`.
Setup and JSON contract: [scripts/README.md](skills/social-content-reader/scripts/README.md).
The helper uses ffprobe, fresh Playwright contexts, and narrowly scoped yt-dlp
paths. It saves a receipt with hash, duration and audio/video presence.
Tesseract is optional; macOS can use Vision (`--engine vision`).
No caption-only Understanding, browser cookie extraction or captcha bypass.

Speech on a file the user already has:

```bash
# Mac / Linux — Python 3.11 or 3.12 preferred (faster-whisper av wheels); brew install ffmpeg
python3 skills/social-content-reader/scripts/asr_local.py --media "$HOME/Media/reel.mp4" --language auto --backend auto --model base
```

```powershell
# Windows — prefer official CPython (py -3.12); MinGW Python often lacks av wheels
py -3.12 skills/social-content-reader/scripts/asr_local.py --media "C:\Media\reel.mp4" --language auto --backend auto --model base
```

Backends: faster-whisper → openai-whisper → OpenAI Whisper API (`OPENAI_API_KEY`). Confirm API upload authorization before cloud. Details: [scripts/README.md](skills/social-content-reader/scripts/README.md). Machine notes: [HARDEN_NOTES.md](HARDEN_NOTES.md).

## Architecture (one line)

**Detect → acquire a local file (or the written post) → frames + OCR + vision + speech → normalize → understand. Caption is not the video.**

Details: [`skills/social-content-reader/ARCHITECTURE.md`](skills/social-content-reader/ARCHITECTURE.md).

## Legal / ToS honesty

- Prefer **official APIs**, **oEmbed metadata**, **public transcripts**, and **user-authorized connectors**.
- `yt-dlp` may be used when the user asked to read the video. Other ToS-sensitive download tools need explicit approval for that URL.
- Do not steal credentials or cookies, bypass logins, defeat captchas, decrypt CDN URLs, or call private undocumented APIs.
- When a video file cannot be acquired, **say the video was not watched**. A share caption stays metadata.

## Repo layout

```text
social-content-reader/
  README.md
  INSTALL_OWN.md
  LICENSE
  STATUS.md
  HARDEN_NOTES.md
  skills/social-content-reader/
    SKILL.md
    ARCHITECTURE.md
    platforms/          # youtube, x, instagram, tiktok, threads, reddit,
                        # facebook, vimeo, bilibili, douyin, wechat-*
                        # _video-body.md  (shared video + graphics recipe)
                        # all 16 recipes; current verified/blocked status above
    scripts/
      normalize_url.py
      extract_frames.py
      ocr_frames.py
      ocr_vision.swift
      acquire_media.py
      acquire_douyin.py
      smoke_acquire.py
      asr_local.py
    references/
```

## Extending

Add `platforms/<name>.md` with: URL patterns, how to acquire a media file, public fetch path for written posts, normalize fields, hard limits, and a pointer to `_video-body.md` for video. Register it in `SKILL.md`, `ARCHITECTURE.md`, and `normalize_url.py`.

## Author

Made for public use by **Anthony Pan** ([GitHub @Anthony-Pan](https://github.com/Anthony-Pan)). MIT licensed.
