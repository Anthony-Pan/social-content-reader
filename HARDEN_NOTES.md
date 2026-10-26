# social-content-reader v0.3.0 hardening notes

Updated 2026-10-26 ~15:35 Asia/Shanghai.

## ASR install on Anthony-Alien (completed)

| Item | Result |
| --- | --- |
| Python for ASR | **Official CPython 3.12** via `py -3.12` (`C:\Users\aw\AppData\Local\Programs\Python\Python312\python.exe`) |
| MinGW `python` on PATH | **Cannot** install `av` wheels (`--only-binary` → none). Do not use for faster-whisper. |
| `faster-whisper` | **1.2.1** installed for py3.12 (with `av` 19.0.2 wheels) |
| FFmpeg | **9.0.2 essentials** at `C:\Tools\ffmpeg\ffmpeg-9.0.2-essentials_build\bin\ffmpeg.exe` (User PATH updated). `winget` was not usable in the agent shell; zip install from gyan.dev used instead. |
| `asr_local.py --help` | OK under `py -3.12` |
| Tiny dry-run | See smoke section below / STATUS.md |

Invoke ASR with:

```powershell
py -3.12 skills\social-content-reader\scripts\asr_local.py --media <file> --language auto --backend faster-whisper --model base
```


### ASR dry-run (Alien, 2026-10-26)

- Sine-tone WAV: empty transcript (expected) after fixing av pin.
- Windows SAPI speech WAV → `asr_local.py --backend faster-whisper --model tiny` →
  `ok: true`, text approximately: "Hello from social content reader version 0.3".
- **Pin:** `av>=11,<14` (av 19.0.2 caused `TypeError: open() got unexpected keyword argument 'metadata_errors'` with faster-whisper 1.2.1). See `scripts/requirements-asr.txt`.

## v0.3 platform expansion

Added honest recipes (connector → public API/oEmbed/CC → user paste → user-media ASR):

**Overseas:** TikTok, Threads, Reddit, LinkedIn, Facebook, Telegram public, Vimeo, Twitch VODs/clips  
**Chinese:** Douyin, Bilibili, 小红书/RedNote  
**Existing hardened docs kept:** YouTube, X, Instagram, 公众号, 视频号

Also updated: `normalize_url.py` detect table, `SKILL.md` / `README.md` / `ARCHITECTURE.md` matrices (overseas first-class), `INSTALL_OWN.md`.

## Still weak / needs Anthony

- LinkedIn / 小红书 / many Facebook personal posts: paste or OAuth
- Douyin / 视频号 / IG Reels speech: user media file (remote blocked)
- Twitch long VODs: chunking time/disk; Helix tokens if metadata wanted (`TWITCH_CLIENT_ID` / `TWITCH_ACCESS_TOKEN`)
- Optional: `OPENAI_API_KEY` for API ASR fallback; `YOUTUBE_API_KEY` / Meta Graph tokens as licensed
- First Whisper model download on Alien may take time/disk on first real speech file

---

# social-content-reader v0.2.0 hardening notes

Implemented 2026-10-26 in the Windows repository. Changes are uncommitted; no commit, push, platform login, media download, or paid transcription call was performed. The pre-existing untracked `_codex_brief_v02.txt` was preserved.

## What changed

- `skills/social-content-reader/scripts/asr_local.py`: local-file ASR CLI with `--media`, `--language zh|en|auto`, `--model`, and `--backend auto|faster-whisper|openai-whisper|openai-api`. Selection prefers faster-whisper, then openai-whisper, then the official OpenAI Whisper API when its SDK/key are available. Local processing uses CPU; API uses `whisper-1` and reports the actual model.
- One JSON record on stdout: `ok`, `text`, `language`, `backend`, `model`, `media_path`, and `error` on failure. Operational failures exit 1 with Windows setup hints; help exits 0 and argument errors exit 2. Progress/diagnostics go to stderr. Unicode speech survives JSON decoding on Windows.
- No download/login behavior in the helper, no automatic package installation, no runtime fallback to cloud after inference fails, and no automatic API retry. API errors omit raw request/credential details. Oversized/unsupported API input is rejected before upload; empty speech is a failure.
- `platforms/instagram.md`: ordered transcript → user export/file + ASR → explicitly approved per-URL yt-dlp → authorized Business/Creator Graph API route. oEmbed remains embed/metadata only. Official integration environment names are documented without secrets or a claimed API implementation.
- `platforms/wechat-channels.md`: primary user file/paste → ASR → `body_text` route. Remote URL-only fetching remains blocked, including the historically observed `errCode 10012` response. Creator 视频号助手 integration environment names are documentation only.
- `platforms/wechat-article.md`: public short-link WebFetch/curl recipe, browser-like UA, substantive-body checks, at most two extra transient-error retries (2/5 seconds), structured outcomes, and immediate user assistance on verification. Never invent a short ID from a long link's `sn`.
- `SKILL.md`: metadata version `0.2.0`, local-file discovery, ASR pipeline, updated hard rules/matrix. Agent Skills YAML frontmatter + Markdown are retained.
- `README.md`: v0.2.0 matrix/pipeline and updated layout. `ARCHITECTURE.md`: new fetch-method values and file-input routing. `scripts/README.md`: setup, CLI/JSON contract, API limits/conversion and verification commands.
- `scripts/tests/test_asr_local.py`: standard-library behavior checks with stubs, no heavyweight testing dependency or real backend calls.

Platform/script paths above are relative to `skills/social-content-reader/` unless otherwise qualified. The PowerShell wrapper was optional and is not needed: invoke Python directly. `normalize_url.py` is unchanged. `SMOKE_RESULTS.md` and `STATUS.md` retain their earlier URL-fetch observations; those historical remote limitations do not describe the new user-file ASR capability.

## Capability matrix (v0.2.0 snapshot)

This table records the v0.2.0 harden. Current recipes are SKILL.md **0.3.2**: a public caption (including 视频号 sph WebFetch) is enough to understand the post. Do not read the rows below as a requirement to ask for a file.

| Platform | v0.2.0 status | Evidence/input needed |
| --- | --- | --- |
| YouTube | Works | Existing connector/transcript path |
| X/Twitter | Partial | Public post text; thread/media limitations remain |
| Instagram | Works with user media + ASR (oEmbed meta-only) | Actual user-provided speech file or pasted transcript |
| WeChat 视频号 | Works with user media + ASR (remote fetch blocked) | Actual user-provided speech file or pasted transcript |
| WeChat 公众号 | Partial (short-link WebFetch recipe) | Accessible `/s/<id>` article body; user action if verified/blocked |

“Works with user media + ASR” describes the implemented route with dependencies configured. It is not a claim that real speech was transcribed on this machine during this release check.

## How an agent now reads an Instagram Reel

1. Prefer an authorized host connector with actual transcript/media, or accept the user's pasted transcript. Do not treat a caption as speech.
2. Otherwise obtain an actual file supplied by the user via Instagram's supported Download/Save video option, account export, or authorized browser download. A saved bookmark or share URL alone is insufficient. Feature availability varies.
3. If the user explicitly approved yt-dlp for the exact Reel URL, the optional documented download may supply the file. Stop if login/captcha/access controls intervene; do not extract browser cookies. A general request to summarize is not that permission.
4. If appropriate for an account the user owns/authorized, a separate official Graph integration may supply permitted media. Documented env names: `IG_ACCESS_TOKEN`, `IG_USER_ID`, `IG_APP_ID`, `IG_APP_SECRET`, `IG_GRAPH_API_VERSION`; the helper does not consume them.
5. Check ASR dependencies. Prefer local processing. Use `--backend faster-whisper` or `--backend openai-whisper` when API uploads are not authorized. Before API/auto can upload, ensure the user authorized sending the file to OpenAI; a key alone is not upload consent.
6. From the repository root, run:

   ```powershell
   python skills/social-content-reader/scripts/asr_local.py --media "C:\Media\reel.mp4" --language auto --backend faster-whisper --model base
   ```

7. Require exit 0, `ok: true`, and nonempty `text`; copy `text` into normalized `body_text`, set `body_kind: transcript`, `fetch_method: user_media_asr`, and retain backend/model/language, known source URL, and speech-only limitations. Summarize/translate from that text. On failure, report the JSON error rather than inventing speech from oEmbed.

For an installed skill, locate the helper relative to its `SKILL.md` instead of assuming a repo checkout.

## How an agent now reads WeChat 视频号

1. A remote 视频号 URL alone remains blocked; the historical `10012` feed response and HTML shell are not content. Avoid further undocumented endpoint probing.
2. Accept pasted text, or ask the user to share/export/save the actual video/audio using supported WeChat/creator controls or an authorized browser workflow. If those controls do not offer a file, request text or an authorized user copy. Do not ship an unofficial downloader/private API scraper.
3. Run the same helper, for example:

   ```powershell
   python skills/social-content-reader/scripts/asr_local.py --media "C:\Media\channels.mp4" --language zh --backend faster-whisper --model base
   ```

4. Map successful ASR JSON into `body_text`/`body_kind: transcript`/`fetch_method: user_media_asr`, then summarize the speech. Use `auto` language if uncertain. Silent visuals/on-screen text need user screenshots/text or an authorized vision tool.
5. Creator APIs remain separately configured, capability-specific account integrations. Suggested env names only: `WECHAT_CHANNELS_APP_ID`, `WECHAT_CHANNELS_APP_SECRET`, `WECHAT_CHANNELS_ACCESS_TOKEN`, `WECHAT_CHANNELS_CREATOR_ID`. No general arbitrary-channel transcript API is promised.

## Windows installation and blockers

Observed here: Python is available; **faster-whisper, openai-whisper, the openai SDK, ffmpeg on PATH, and OPENAI_API_KEY are absent**. No heavy ASR packages or model weights were installed. Actual end-to-end speech decoding is therefore pending setup and a real user speech file.

Install one local engine in your chosen Python environment:

```powershell
# Preferred local ASR; PyAV includes FFmpeg decoding libraries
python -m pip install faster-whisper

# Alternative local ASR; may install large PyTorch dependencies
python -m pip install openai-whisper

# Required by openai-whisper and manual media conversion
winget install --id Gyan.FFmpeg --exact
# Reopen PowerShell to refresh PATH, then verify
ffmpeg -version

# Optional official API backend; provision OPENAI_API_KEY securely out of band
python -m pip install openai
```

faster-whisper normally does not require standalone `ffmpeg.exe`; openai-whisper does. Installing the Python `ffmpeg`/`ffmpeg-python` package is not a replacement for the executable. Local model weights may download on first use; start with `tiny`/`base` for a setup smoke and use a suitable larger model for accuracy when resources permit.

For an authorized API run, use `--backend openai-api`; the actual model is always `whisper-1`. The helper accepts MP3/MP4/MPEG/MPGA/M4A/WAV/WebM and limits uploads conservatively to 25,000,000 bytes; it does not auto-split or convert. To extract/compress audio:

```powershell
ffmpeg -i "C:\Media\video.mp4" -vn -ac 1 -ar 16000 -c:a libmp3lame -b:a 64k "C:\Media\speech.mp3"
ffmpeg -i "C:\Media\speech.mp3" -f segment -segment_time 600 -c copy "C:\Media\speech-%03d.mp3"
```

Check chunk sizes, transcribe in chronological order, and review sentence boundaries. Setup/API behavior references: [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [openai-whisper](https://github.com/openai/whisper), [official OpenAI transcription guide](https://developers.openai.com/api/docs/guides/speech-to-text).

## Smoke results and checklist

Run from the repo root:

```powershell
python skills/social-content-reader/scripts/normalize_url.py "https://youtu.be/jNQXAC9IVRw"
python skills/social-content-reader/scripts/normalize_url.py "https://twitter.com/elonmusk/status/1519480761749016577"
python skills/social-content-reader/scripts/normalize_url.py "https://www.instagram.com/reels/C123abcDEF/?igsh=test"
python skills/social-content-reader/scripts/normalize_url.py "https://mp.weixin.qq.com/s/Rsa54LdbyhXIHheJYO6gkw"
python skills/social-content-reader/scripts/normalize_url.py "https://mp.weixin.qq.com/s?__biz=sample&mid=1&idx=1&sn=test"
python skills/social-content-reader/scripts/normalize_url.py "https://channels.weixin.qq.com/web/pages/live?finderUsername=test"
python skills/social-content-reader/scripts/normalize_url.py "dQw4w9WgXcQ"
python skills/social-content-reader/scripts/asr_local.py --help
python -B -m unittest discover -s skills/social-content-reader/scripts/tests -v
git diff --check
```

- [x] Seven normalization CLI examples passed: YT URL/bare ID, X canonicalization, IG plural Reels + tracking removal, 公众号 short/long forms, 视频号.
- [x] `asr_local.py --help` passed without optional dependencies, model downloads or network calls.
- [x] Eleven standard-library behavior tests passed: backend preference, missing key/deps/ffmpeg, lazy-segment consumption, Unicode JSON/stdout separation, CPU arguments/language, API model/file closure, format/size upload rejection, redacted runtime failure without fallback, empty speech, and missing/empty files.
- [x] Actual CLI missing-file and missing-dependency probes returned parseable `ok: false` JSON and exit 1. The dependency probe used a temporary placeholder file without decoding; no synthetic WAV or speech transcription was attempted.
- [x] Parsed Agent Skills YAML frontmatter using PyYAML installed only into a temporary directory; checked skill name, description, supported keys, retained `compatibility`, and version `0.2.0`. No global dependency was installed. The bundled legacy `skill-creator/scripts/quick_validate.py` could not pass as-is: its direct run lacked PyYAML, and the temporary-dependency run hit its default GBK decoding of UTF-8 Chinese. Its inspected key allowlist also predates the existing `compatibility` field. The release keeps that supported Agent Skills field rather than changing the package to satisfy the legacy checker.
- [x] Python syntax, changed-document local links, preserved Chinese characters, placeholder checks, and `git diff --check` passed. No generated bytecode/cache directories or temporary fixtures remain in the repository.
- [ ] Real local speech transcription after dependencies/model weights are installed. Verify recognizable speech in `text`, correct language/backend/model, then normalized `body_text` and a grounded summary.
- [ ] Optional authorized API speech smoke with SDK/key configured; verify upload consent, format/size and the actual `whisper-1` result.
- [ ] New live 公众号 article fetch. This release documents the existing `SMOKE_RESULTS.md` success, without claiming a fresh WebFetch/curl success or circumventing verification.

No login bypass, captcha solving, cookie theft, credential values, unofficial private API scrapers, or new remote platform fetch claims were introduced.
