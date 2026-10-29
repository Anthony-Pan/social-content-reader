# v0.5.2 hardening — Reddit post URL → media (box, 2026-10-29)

- `resolve_reddit.py` reads a public post listing `.json` (first `t3` only).
  When that response is an HTTP block page, it reads `embed.reddit.com` for
  the same path. No cookie jar, no `over18` / gated opt-in, no private API,
  no captcha solver, no IP rotation.
- The player `src` or crosspost screenview `url` must belong to `t3_{id}`.
  Other posts, posters, caption VTT, and oEmbed titles are not the file.
  Signed HLS queries are discarded. The download URL is unsigned
  `DASHPlaylist.mpd`, then yt-dlp `--ignore-config`. ffprobe must see a
  positive duration and a video stream.
- One gallery video is kept. Two hosted videos are refused. Quarantine /
  private / gated JSON stops instead of trying the embed.
- Live: `www` and `old` post pages and `.json` are still HTTP 403 Blocked.
  Embed resolved `/r/aww/comments/90bu6w/` to `gyh95hiqc0b11` and saved the
  same 7,478,923-byte file as the v0.5.0 direct CDN sample (`has_audio:
  false`). `/r/videos/comments/6rrwyj/` and crosspost `zjjw82` saved files
  with AAC. `redd.it/90bu6w`, bare `/comments/90bu6w`, and a two-video post
  failed closed. See SMOKE_RESULTS v0.5.2 addendum.
- Acquisition is not Understanding. A caption is still metadata.

---

# v0.5.1 hardening — WeChat 公众号 (box, 2026-10-26 Asia/Shanghai)

- New `fetch_wechat_article.py`: stdlib-only HTTPS GET with a fixed Chrome
  desktop User-Agent. No cookies, profiles, captcha defeat, IP rotation, or
  private APIs.
- Substantive body gate (≥40 letters/digits/CJK) on `#js_content` /
  `#js_article_content` / `.rich_media_content` / `[itemprop=articleBody]`.
- Accept WeChat SSR `visibility:hidden;opacity:0` on `#js_content`; reject
  `display:none` and `环境异常` / captcha shells (`captcha_required`).
- Extract `mpvideo` iframe embeds (`action=mpvideo&vid=wxv_…`). Optional
  first-embed media via public player when Playwright + acquire_media helpers
  exist; article success is independent of embed media and ffmpeg.
- `acquire_media.py` routes `wechat-article` before the ffmpeg requirement.
- Live box smoke: Rsa + Anm bodies OK; Anm embed media unavailable on this
  network; 视频号 still FAIL. See SMOKE_RESULTS v0.5.1 addendum.

---

# v0.5.0 hardening — Mac, 2026-10-26

Automatic public media acquire now precedes user export. See
[SMOKE_RESULTS.md](SMOKE_RESULTS.md) for exact live evidence: 13 video
platform sample files saved; 小红书 and 视频号 remain blocked; 公众号
verification and Reddit post-resolution limits remain explicit.

- Fresh Playwright contexts only; no persistent profile, saved cookie
  file, browser-cookie extraction, captcha solver, private API client,
  certificate interception or decryption. Douyin's prior webdriver-hiding
  flags/script were removed and the ordinary mobile player was re-tested.
- TikTok uses its documented public embed. Bilibili observes media requests
  the public external player actually makes, preserves normal request headers,
  downloads the full unencrypted tracks, and muxes video+audio with ffmpeg.
  Unverified Bilibili multipart requests are rejected instead of substituting part 1.
- HTTP status alone never establishes success. ffprobe must find a positive
  duration and video stream. Complete HTTP 206 requires matching Content-Range
  and actual byte length; error.mp4 placeholders and HTML are rejected.
- Meta page media is selected by exact requested post code/video id. Tests
  exclude recommendations. Telegram uses its exact public message widget,
  not the first media on a multi-message preview.
- yt-dlp uses `--ignore-config`, no credentials, no retries, and bounded socket
  timeout. X explicitly selects public syndication. Vimeo uses a public
  player URL. Reddit direct CDN success does not imply post resolution.
- Downloads stage in temporary folders; only validated output is published.
  Receipts include source URL, hash, bytes, duration, codecs and audio/video
  presence. Exceptions do not print raw browser/downloader signed media URLs.
- `has_audio: false` stays explicit (Instagram, Facebook and Reddit samples).
  No caption is returned as body_text, and acquisition never claims
  Understanding. No cloud ASR or other upload was run for this matrix.

Validation: 55 unit tests passed; every one of the 13 counted files decoded
end to end with FFmpeg exit 0 and no error output. Replay is explicit via
`smoke_acquire.py`; network tests are not part of CI's unit suite. Current
receipts are committed under `references/acquire-matrix-2026-10-26.json`.

Remaining limitations: browser/player markup changes, fixed public-page
load allowance (adjustable 1–60 seconds), local disk/memory for downloads,
no generic blob/HLS capture or arbitrary long Twitch VOD acquisition.
`--max-mb` limits accepted outputs/tracks, not all page network traffic.
The full all-platform acquisition goal is still partially unmet.

---

# Historical hardening notes — earlier release snapshots

# social-content-reader v0.4.0 media-first notes

Updated 2026-10-26.

## What changed

Video Understanding now requires a local media file (or an official speech track **plus** frames when graphics are in scope). Helpers:

- `scripts/extract_frames.py` — ffmpeg `--mode fps` or `--mode scene`. JSON frame paths and timestamps. Refuses URLs.
- `scripts/ocr_frames.py` — Tesseract when installed; macOS Vision via `ocr_vision.swift` when `swiftc` is available. `engine: none` when neither exists. Does not invent text.
- `platforms/_video-body.md` — shared acquire + read recipe. Platform docs point here. Captions stay metadata.
- Skill version **0.4.0**. `normalize_url.py` and `asr_local.py` kept.

`yt-dlp` is documented as a public acquire CLI when the user asked to read the video **and** a run has saved a file. Mac, 2026-10-26: YouTube saved a file; the TikTok sample was IP-blocked; Bilibili returned HTTP 412. Those last two are not file recipes. No cookie theft, login bypass, captcha defeat, CDN decrypt, or private API client was added.

## Douyin acquire (2026-10-26)

Share `https://v.douyin.com/2qulGbSTiRI/` → aweme **7696098282904259850**.

Two different pages:

- **iesdouyin / desktop curl.** Redirects `v.douyin.com` → `www.iesdouyin.com/share/video/7696098282904259850/` → `www.douyin.com/video/7696098282904259850`. Datacenter curl returns a JavaScript shell. That share surface often says **「请尝试在抖音内观看」**. It is not the player.
- **Working path (Mac, repeated).** `scripts/acquire_douyin.py` is the helper that re-downloaded this aweme from `https://v.douyin.com/2qulGbSTiRI/`. CLI is positional (`URL` or bare id) plus `--out-dir`. It writes `douyin_{aweme_id}.mp4`. Playwright Chromium, mobile UA. Open `https://www.douyin.com/` for cookies in that browser, then `https://m.douyin.com/share/video/7696098282904259850`. Read `<video>.src` / `currentSrc` (`https://m.douyin.com/aweme/v1/playwm/?…&video_id=v0…`). GET it with the same context and `Referer` = the share page. Follows to a CDN `video/mp4` (~8MB, 1280×720, H.264+AAC, ~49s). Then `extract_frames.py`, `asr_local.py`, and the host video tool. Success JSON uses `ok: true`.

Default goal is that automatic file. User export is the fallback only when the mobile share page has no `<video>` src. The helper does not write cookies to disk, solve captchas, or return a caption as the body. A share caption is not a substitute. `body_snip` on failure is a page excerpt, not Understanding.

## Mac file matrix (2026-10-26)

| Platform | Observed | Documented as a file recipe |
| --- | --- | --- |
| Douyin | `acquire_douyin.py` saved ~8MB, repeatedly | Yes |
| YouTube | `yt-dlp` saved a file | Yes, for the file only. Frames and speech still required. |
| TikTok | Sample `yt-dlp` IP-blocked | No |
| Bilibili | `yt-dlp` HTTP 412; public playurl did not save a file | No. Uploader CC can still be speech. |

## Tests

`python3 -B -m unittest discover -s skills/social-content-reader/scripts/tests -v`

Includes a generated lavfi sample (testsrc plus a red/blue scene cut) when ffmpeg is on PATH. GitHub Actions (`.github/workflows/tests.yml`) installs ffmpeg and runs the same suite. OCR tests stub Tesseract and assert a missing engine returns `ok: false`.

---

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
- `platforms/wechat-article.md` + `scripts/fetch_wechat_article.py` (v0.5.1): Chrome UA HTTPS body, SSR visibility:hidden accepted, mpvideo embed extraction, optional embed media; captcha_required on 环境异常. Never invent a short ID from a long link's `sn`.
- `SKILL.md`: metadata version `0.2.0`, local-file discovery, ASR pipeline, updated hard rules/matrix. Agent Skills YAML frontmatter + Markdown are retained.
- `README.md`: v0.2.0 matrix/pipeline and updated layout. `ARCHITECTURE.md`: new fetch-method values and file-input routing. `scripts/README.md`: setup, CLI/JSON contract, API limits/conversion and verification commands.
- `scripts/tests/test_asr_local.py`: standard-library behavior checks with stubs, no heavyweight testing dependency or real backend calls.

Platform/script paths above are relative to `skills/social-content-reader/` unless otherwise qualified. The PowerShell wrapper was optional and is not needed: invoke Python directly. `normalize_url.py` is unchanged. `SMOKE_RESULTS.md` and `STATUS.md` retain their earlier URL-fetch observations; those historical remote limitations do not describe the new user-file ASR capability.

## Capability matrix (v0.2.0 snapshot)

This table records the v0.2.0 harden. Current recipes are SKILL.md **0.4.0**: Understanding comes from frames, OCR, vision, and speech. A public caption, including a 视频号 sph WebFetch, is metadata.

| Platform | v0.2.0 status | Evidence/input needed |
| --- | --- | --- |
| YouTube | Works | Existing connector/transcript path |
| X/Twitter | Partial | Public post text; thread/media limitations remain |
| Instagram | Works with user media + ASR (oEmbed meta-only) | Actual user-provided speech file or pasted transcript |
| WeChat 视频号 | Works with user media + ASR (remote fetch blocked) | Actual user-provided speech file or pasted transcript |
| WeChat 公众号 | Body OK via Chrome UA HTTPS (v0.5.1); embed media best-effort | Accessible `/s/<id>` `#js_content`; user action if verified/blocked; embed file not guaranteed |

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
