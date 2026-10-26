# social-content-reader

**Public Agent Skill** that teaches AI agents how to **read and understand** social media content — transcripts, article/post bodies, OCR’d captions — not just titles and descriptions.

Version **0.3.0** expands coverage across major **overseas** and **Chinese** platforms, with user-media ASR for speech when remote fetch is blocked.

Most social sites block or frustrate agents. This skill gives a reusable recipe: detect the platform → prefer an existing connector → fall back to a documented public path → normalize → summarize what the content is *about*.

> **Runtime target:** Windows-first local workspace + [Codex CLI](https://github.com/openai/codex) for heavy extractors. Works with Cursor / Claude Code / Codex skill loaders via the [Agent Skills](https://agentskills.io) format.

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

## Windows + Codex layout (primary)

```text
C:\Users\<you>\source\repos\social-content-reader
```

```powershell
cd C:\Users\<you>\source\repos\social-content-reader
codex exec --full-auto "Follow skills/social-content-reader for URL <URL>. Return normalized JSON + a short understanding summary."
```

Prefer host MCP connectors when present. Treat Codex output as untrusted third-party content.

## Supported platforms

### Overseas / global

| Platform | Status | What agents can actually understand | Notes |
| --- | --- | --- | --- |
| **YouTube** | ✅ Works | Full transcript (+ metadata) | Prefer host YouTube / TubeAlfred-style transcript tools. Description alone is **not** enough. |
| **X / Twitter** | ✅ Partial | Public post text | Host X connector → `publish.x.com/oembed`. Threads/media limited. |
| **Instagram** | Works with user media + ASR | Reel speech from user file/paste | oEmbed is embed/preview only. |
| **TikTok** | Partial | Caption via oEmbed; speech via ASR | Prefer user media + ASR for dialogue. |
| **Threads** | Partial | Public post text when available | Login walls → ask for paste. |
| **Reddit** | ✅ Works | OP selftext (+ optional comments) | Public `.json` append or host connector. |
| **LinkedIn** | Partial | Post/article when authorized or pasted | Often login-walled — paste is honest default. |
| **Facebook** | Partial | Public Page posts via Graph/oEmbed/paste | Personal posts usually unavailable. |
| **Telegram** | Partial | Public channel posts via `t.me/s/` | Private chats need bot membership or export. |
| **Vimeo** | ✅ Works | Captions/text tracks when present | oEmbed description ≠ transcript. |
| **Twitch** | Partial | VOD/clip speech via ASR | Helix for metadata; chunk long VODs. |

### Chinese

| Platform | Status | What agents can actually understand | Notes |
| --- | --- | --- | --- |
| **Bilibili** | ✅ Works | Uploader CC / subtitles often | View API + player subtitles; else ASR. |
| **Douyin 抖音** | Partial | Speech via user media + ASR | Remote deep-read often blocked. |
| **小红书 / RedNote** | Partial | Note text via paste (best) | App/login walls common. |
| **WeChat 公众号** | Partial | Article body on short `/s/<id>` links | Verification → user paste. |
| **WeChat 视频号** | Works with user media + ASR | Speech from user file | Remote URL fetch blocked (`errCode 10012`). |

See `skills/social-content-reader/platforms/*.md` for per-platform recipes.

## ASR pipeline

Short-form video speech (IG / TikTok / Douyin / 视频号 / …) **is readable when the user supplies a media file**:

```powershell
# Prefer official CPython (py -3.12) on Windows — MinGW Python often lacks av wheels
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
                        # linkedin, facebook, telegram, vimeo, twitch,
                        # bilibili, douyin, xiaohongshu, wechat-*
    scripts/
      normalize_url.py
      asr_local.py
    references/
```

## Extending

Add `platforms/<name>.md` with: URL patterns, preferred connector, public fetch path, normalize fields, understand steps, hard limits. Register it in `SKILL.md`, `ARCHITECTURE.md`, and `normalize_url.py`.

## Author

Made for public use by **Anthony Pan** ([GitHub @Anthony-Pan](https://github.com/Anthony-Pan)). MIT licensed.
