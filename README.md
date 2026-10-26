# social-content-reader

**Public Agent Skill** that teaches AI agents how to **read a video**: the picture, burned-in text, graphics, and speech. A share caption is optional metadata. It is not the body.

Version **0.4.0** makes the media file the default success path. Agents extract frames (`extract_frames.py`), OCR burned-in text when Tesseract or macOS Vision is available (`ocr_frames.py`), describe frames with the host vision/video tool, and transcribe speech with `asr_local.py` or an official transcript track. If the file cannot be acquired, the agent says the video was not watched. **0.3.1** still documents WeChat 视频号 `weixin.qq.com/sph/<id>` caption metadata. **0.3.0** expanded coverage across major **overseas** and **Chinese** platforms.

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

### Overseas / global

| Platform | Status | What counts as reading it | Notes |
| --- | --- | --- | --- |
| **YouTube** | Works with transcript + frames | Speech from official captions or ASR; graphics from frames | Description is metadata. Mac, 2026-10-26: `yt-dlp` acquired a YouTube file. That file is not Understanding by itself. |
| **X / Twitter** | Post text works; video needs a file | Public post text. Attached video → media pipeline | Host X connector → `publish.x.com/oembed` for the post only. |
| **Instagram** | Media required for a Reel | Frames + OCR + vision + ASR on a local file | oEmbed is an embed preview, not the Reel. |
| **TikTok** | Media required | A local file, then the media pipeline | oEmbed caption is metadata. Mac, 2026-10-26: the sample `yt-dlp` tried was IP-blocked. That is not a verified file recipe. |
| **Threads** | Post text when public; video needs a file | Public post text. Video → media pipeline | Login walls → ask for paste or a file. |
| **Reddit** | Public text works; video needs a file | OP selftext. `v.redd.it` → media pipeline | Public `.json` append or host connector. |
| **Facebook** | Page post when authorized; Reel needs a file | Graph/paste for the post. Reel → media pipeline | Personal posts usually unavailable. |
| **Vimeo** | Works when text tracks or a file are read | Text tracks = speech. Frames = graphics | oEmbed description is metadata. |

### Chinese

| Platform | Status | What counts as reading it | Notes |
| --- | --- | --- | --- |
| **Bilibili** | Speech when uploader CC exists; graphics need a file | CC = speech. Frames = graphics, and only after a real file | `desc` is metadata. Mac, 2026-10-26: `yt-dlp` returned HTTP 412. Public playurl is not a verified file recipe. |
| **Douyin 抖音** | Media required; auto-acquire works | mp4 from `acquire_douyin.py`, then frames + OCR + vision + ASR | Mac, 2026-10-26: short link `v.douyin.com/2qulGbSTiRI` → aweme `7696098282904259850` re-downloaded repeatedly (~8MB). iesdouyin 「请尝试在抖音内观看」 is not the player. Caption is not the video. |
| **WeChat 公众号** | Article body on short `/s/<id>` links | Article HTML. Embedded 视频号 → media file | Verification → user paste. Do not solve captchas. |
| **WeChat 视频号** | Media required | User export/save, then the media pipeline | sph WebFetch caption is metadata. Feed paths stay blocked (`errCode 10012`). |

See `skills/social-content-reader/platforms/*.md`. Shared video steps: [`platforms/_video-body.md`](skills/social-content-reader/platforms/_video-body.md).

Platform recipes for LinkedIn / 小红书 / Telegram / Twitch still exist under `platforms/` but are not listed as supported.

## Media pipeline

Default video success is a **local file**:

```bash
python3 skills/social-content-reader/scripts/extract_frames.py --media "$HOME/Media/clip.mp4" --mode fps --fps 1 --max-frames 24
python3 skills/social-content-reader/scripts/ocr_frames.py --frames-json frames.json
python3 skills/social-content-reader/scripts/asr_local.py --media "$HOME/Media/clip.mp4" --language auto --backend auto --model base
```

Then the host agent describes the frames with its video/vision tools. Understanding is written from those three reads. The share caption is a side note. If acquire fails, say the video was not watched.

`ffmpeg` is required for frames. `yt-dlp` is the documented public acquire CLI when the user asked to read a video and a run on that URL has actually saved a file. As of Mac 2026-10-26 that is YouTube; TikTok was IP-blocked and Bilibili returned HTTP 412, so those are not verified file recipes. Tesseract is optional; OCR fails honestly when it is missing. macOS can use Vision via `swiftc` (`--engine vision`).

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
                        # linkedin, telegram, twitch, xiaohongshu stay on disk, unlisted
    scripts/
      normalize_url.py
      extract_frames.py
      ocr_frames.py
      ocr_vision.swift
      acquire_douyin.py
      asr_local.py
    references/
```

## Extending

Add `platforms/<name>.md` with: URL patterns, how to acquire a media file, public fetch path for written posts, normalize fields, hard limits, and a pointer to `_video-body.md` for video. Register it in `SKILL.md`, `ARCHITECTURE.md`, and `normalize_url.py`.

## Author

Made for public use by **Anthony Pan** ([GitHub @Anthony-Pan](https://github.com/Anthony-Pan)). MIT licensed.
