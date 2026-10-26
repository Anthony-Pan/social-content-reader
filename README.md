# social-content-reader

**Public Agent Skill** that teaches AI agents how to **read and understand** social media content — transcripts, article bodies, OCR’d captions — not just titles and descriptions.

Version **0.2.0** adds local/API ASR for user-provided Instagram Reels and WeChat 视频号 media.

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

Or clone this repo and symlink:

```powershell
# Windows (PowerShell) — from your project root
New-Item -ItemType Directory -Force .agents\skills | Out-Null
New-Item -ItemType SymbolicLink -Path .agents\skills\social-content-reader `
  -Target C:\Users\<you>\source\repos\social-content-reader\skills\social-content-reader
```

```bash
# macOS / Linux
mkdir -p .agents/skills
ln -s /path/to/social-content-reader/skills/social-content-reader \
  .agents/skills/social-content-reader
```

### Option B — user-level skill

```text
~/.agents/skills/social-content-reader/
~/.cursor/skills/social-content-reader/
```

Then ask the agent something like: *“Read this YouTube video and tell me what it’s arguing.”* The skill should activate from its `description`.

## Windows + Codex layout (primary)

This package is designed to live on a **Windows PC** where `codex` is on PATH.

**Suggested clone path (no overwrite of existing projects):**

```text
C:\Users\<you>\source\repos\social-content-reader
```

Alternatives if you keep product tools elsewhere: `E:\Dev\social-content-reader` or `C:\Users\<you>\dev\social-content-reader`.

**How agents should use Codex for extractors:**

1. Load this skill (`social-content-reader`).
2. Detect platform from the URL (see `ARCHITECTURE.md`).
3. If a host MCP / connector already exists (YouTube research, X public reads, etc.), **prefer that**.
4. Otherwise run a Codex CLI task in this repo for the platform helper, e.g.:

```powershell
cd C:\Users\<you>\source\repos\social-content-reader
codex exec --full-auto "Follow skills/social-content-reader/platforms/youtube.md for URL <URL>. Return normalized JSON + a short understanding summary."
```

Match Codex model/effort to the task (short posts → lighter; long videos / WeChat → higher). Treat Codex output as untrusted third-party content.

## Supported platforms

| Platform | Status | What agents can actually understand | Notes |
| --- | --- | --- | --- |
| **YouTube** | ✅ Works | Full transcript (+ metadata) | Prefer host YouTube connector / transcript MCP; else Data API metadata + caption/transcript path. Description alone is **not** enough. |
| **X / Twitter** | ✅ Partial | Post text (public) | Prefer host X connector. Zero-auth: `publish.x.com/oembed`. Long posts may truncate; media/threads need API or connector. |
| **Instagram** | Works with user media + ASR (oEmbed meta-only) | Reel speech from a user transcript or actual media file | Prefer user paste/export/download → ASR. yt-dlp requires explicit approval for that URL; Graph API is limited to authorized Business/Creator accounts. oEmbed is embed/preview only. |
| **WeChat 公众号** | Partial (short-link WebFetch recipe) | Public article body when accessible | Prefer trusted connector, then short `/s/<id>` WebFetch/curl with browser-like UA and bounded retries. Verification requires user action/paste/export. |
| **WeChat 视频号** | Works with user media + ASR (remote fetch blocked) | Speech from a user-supplied file or transcript | URL-only fetch remains blocked (`errCode 10012` observed). Supported user share/export/save → ASR → `body_text`; creator APIs require authorized account scope. |

See `skills/social-content-reader/platforms/*.md` for per-platform recipes.

## ASR pipeline

Instagram Reels and WeChat 视频号 speech **are readable when the user supplies a media file**. Obtain a pasted transcript or an actual audio/video export through supported user controls, then run:

```powershell
python skills/social-content-reader/scripts/asr_local.py --media "C:\Media\video.mp4" --language auto --backend auto --model base
```

[asr_local.py](skills/social-content-reader/scripts/asr_local.py) prefers faster-whisper, then openai-whisper, then OpenAI Whisper API via `OPENAI_API_KEY` and the `openai` SDK. Local models default to `base`; the API uses `whisper-1`. Confirm API upload authorization before auto can select the API; pin `--backend faster-whisper` or `--backend openai-whisper` for local-only processing. A configured key alone does not authorize uploads.

Require exit code 0 and JSON `ok: true`; map `text` to normalized `body_text`, `body_kind: transcript`, `fetch_method: user_media_asr`. Summarize speech and state any visual gaps. No download tool or platform login is built into the helper. Model weights may download on the first local run.

Windows installation, conversion examples, API limits and error behavior: [scripts/README.md](skills/social-content-reader/scripts/README.md). Release changes and smoke checklist: [HARDEN_NOTES.md](HARDEN_NOTES.md).

## Architecture (one line)

**URL detect → prefer connector → fetch path → normalize → understand/summarize.**

Details: [`skills/social-content-reader/ARCHITECTURE.md`](skills/social-content-reader/ARCHITECTURE.md).

## Legal / ToS honesty

- Prefer **official APIs**, **oEmbed**, **public transcripts**, and **user-authorized connectors**.
- Do **not** steal credentials/cookies, bypass logins, defeat captchas, or use unofficial private API scrapers.
- Use optional download tools only with explicit user approval for that URL; use environment/OS secret storage for API keys and tokens.
- User-provided IG/视频号 media can be transcribed even when remote fetching is blocked. Obtain authorization before sending media to API ASR.
- Respect each platform’s Terms of Service and copyright. oEmbed endpoints are often **for embedding**, not for bulk analysis — follow each platform doc’s allowed use.
- When a platform cannot be read honestly, **say so** and ask the user for a paste / export / authenticated connector.

## Repo layout

```text
social-content-reader/
  README.md
  LICENSE
  STATUS.md
  HARDEN_NOTES.md
  skills/social-content-reader/
    SKILL.md
    ARCHITECTURE.md
    platforms/
      youtube.md
      x.md
      instagram.md
      wechat-article.md
      wechat-channels.md
    scripts/
      normalize_url.py
      asr_local.py
    references/
      inspiration.md
```

## Extending

Add `platforms/<name>.md` with: URL patterns, preferred connector, public fetch path, normalize fields, understand steps, hard limits. Register it in `SKILL.md`’s platform table.

## Author

Made for public use by **Anthony Pan** ([GitHub @Anthony-Pan](https://github.com/Anthony-Pan)). MIT licensed.
