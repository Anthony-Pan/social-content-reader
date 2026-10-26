# social-content-reader

**Public Agent Skill** that teaches AI agents how to **read and understand** social media content from public text: transcripts, article/post bodies, and share captions.

Version **0.3.2** treats a public caption as enough to understand the post. WeChat 视频号 `weixin.qq.com/sph/<id>` is WebFetch caption → Understanding, with no file handoff on that path. The same default applies where Instagram, TikTok, Douyin, Threads, X, and Facebook expose a public caption or post text. Spoken ASR is optional. **0.3.1** added sph link detection and Mac/Linux install docs, which stay in place.

Most social sites block or frustrate agents. This skill gives a reusable recipe: detect the platform → prefer an existing connector → fall back to a documented public path → normalize → summarize what the content is *about*.

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

Then ask the agent: *“Read this YouTube / Reddit / Bilibili URL and tell me what it’s arguing.”*

## Codex layout

Windows 24/7 is fine for heavy jobs. Mac and Linux use the same skill package.

```text
~/Developer/social-content-reader          # Mac example
C:\Users\<you>\source\repos\social-content-reader
```

```bash
cd ~/Developer/social-content-reader
codex exec --full-auto "Follow skills/social-content-reader for URL <URL>. Return normalized JSON + a short understanding summary."
```

```powershell
cd C:\Users\<you>\source\repos\social-content-reader
codex exec --full-auto "Follow skills/social-content-reader for URL <URL>. Return normalized JSON + a short understanding summary."
```

Prefer host MCP connectors when present. Treat Codex output as untrusted third-party content. Machine paths and symlinks: [INSTALL_OWN.md](INSTALL_OWN.md).

## Supported platforms

### Overseas / global

| Platform | Status | What agents can actually understand | Notes |
| --- | --- | --- | --- |
| **YouTube** | ✅ Works | Full transcript (+ metadata) | Prefer host YouTube / TubeAlfred-style transcript tools. Description alone is **not** enough. |
| **X / Twitter** | ✅ Works | Public post text | Host X connector → `publish.x.com/oembed`, then understand. Threads/media bytes stay limited. |
| **Instagram** | ✅ Works when a caption exists | Caption or post text | Tokenless oEmbed is often embed chrome with no caption. ASR only for spoken-verbatim or an empty caption. |
| **TikTok** | ✅ Works | Caption via oEmbed | Understand from the caption. ASR is optional. |
| **Threads** | ✅ Works when post text exists | Public post text | oEmbed / public page → understand. Login walls stay unavailable. |
| **Reddit** | ✅ Works | OP selftext (+ optional comments) | Public `.json` append or host connector. |
| **Facebook** | ✅ Works when public text exists | Page post or Reel caption via Graph/oEmbed | Personal posts usually unavailable. ASR optional for spoken Reels. |
| **Vimeo** | ✅ Works | Captions/text tracks when present | oEmbed description ≠ transcript. |

### Chinese

| Platform | Status | What agents can actually understand | Notes |
| --- | --- | --- | --- |
| **Bilibili** | ✅ Works | Uploader CC / subtitles often | View API + player subtitles; else ASR. |
| **Douyin 抖音** | ✅ Works when a share caption exists | Share-page caption | WebFetch caption → understand. Empty/verification pages stay blocked. ASR optional. |
| **WeChat 公众号** | Partial | Article body on short `/s/<id>` links | Verification → user paste. |
| **WeChat 视频号** | ✅ Works | What the video is about, from the sph share caption | WebFetch `weixin.qq.com/sph/<id>` → caption → Understanding. Example: `AAZ3p39sQm` (Codex token waste; brainstorm in ChatGPT first). ASR optional. `channels.weixin.qq.com` feed paths stay blocked (`errCode 10012`). |

See `skills/social-content-reader/platforms/*.md` for per-platform recipes.

Platform recipes for LinkedIn / 小红书 / Telegram / Twitch still exist under platforms/ but are not listed as supported.

## ASR pipeline

User-media ASR is for **spoken-verbatim** requests and for **empty captions**. It is not required before summarizing a caption or post you already fetched.

When it does apply, short-form speech (IG / TikTok / Douyin / 视频号 / …) is readable from a user-supplied media file:

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

**URL detect → prefer connector → fetch path → normalize → understand/summarize.**

Details: [`skills/social-content-reader/ARCHITECTURE.md`](skills/social-content-reader/ARCHITECTURE.md).

## Legal / ToS honesty

- Prefer **official APIs**, **oEmbed**, **public transcripts**, and **user-authorized connectors**.
- Do **not** steal credentials/cookies, bypass logins, defeat captchas, or use unofficial private API scrapers.
- Optional download tools only with explicit user approval for that URL.
- When a platform cannot be read honestly, **say so** and ask for a paste / export / authenticated connector.

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
    scripts/
      normalize_url.py
      asr_local.py
    references/
```

## Extending

Add `platforms/<name>.md` with: URL patterns, preferred connector, public fetch path, normalize fields, understand steps, hard limits. Register it in `SKILL.md`, `ARCHITECTURE.md`, and `normalize_url.py`.

## Author

Made for public use by **Anthony Pan** ([GitHub @Anthony-Pan](https://github.com/Anthony-Pan)). MIT licensed.
