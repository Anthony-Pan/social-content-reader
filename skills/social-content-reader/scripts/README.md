# scripts/

Small URL/ASR helpers; no platform downloader, login automation, or private API scraper.

| Script | Purpose |
| --- | --- |
| `normalize_url.py` | Detect platform + canonical id/url from a link (no network) |
| `acquire_douyin.py` | Save a Douyin mp4 from the mobile share `<video>` playwm URL (Playwright). No caption body. |
| `acquire_media.py` | Public social media acquire (validated file) or WeChat 公众号 article body via `fetch_wechat_article`. |
| `fetch_wechat_article.py` | Fetch/parse 公众号 article HTML (stdlib HTTPS, Chrome UA). Body OK without ffmpeg; optional mpvideo embed media. |
| `extract_frames.py` | ffmpeg keyframes (`--mode fps` or `--mode scene`); JSON with paths and `timestamp_sec`. No URL download. |
| `ocr_frames.py` | OCR local frames with tesseract, or macOS Vision (`ocr_vision.swift`) when `swiftc` exists. `engine: none` if neither is installed. |
| `asr_local.py` | Transcribe a user-provided audio/video file using local Whisper or the official OpenAI Whisper API; JSON stdout |
| `understand_media.py` | Join a validated local file to frames, OCR, host vision notes, and speech. Caption and title stay metadata. |

Run:

```bash
python3 skills/social-content-reader/scripts/normalize_url.py "https://weixin.qq.com/sph/AAZ3p39sQm"
```

```powershell
python skills\social-content-reader\scripts\normalize_url.py "https://youtu.be/dQw4w9WgXcQ"
```

`weixin.qq.com/sph/<id>` (optional `www`) returns `platform: wechat-channels`, `link_form: sph_share`, and `canonical_url: https://weixin.qq.com/sph/<id>`. `channels.weixin.qq.com` stays `wechat-channels` without an sph id.

Heavy fetch/summarize belongs in Codex tasks guided by `platforms/*.md`, or in host MCP connectors — not in brittle scrapers checked into this folder. Video Understanding of a file already on disk is `understand_media.py` (frames + OCR + host vision notes + local ASR). See [platforms/_video-body.md](../platforms/_video-body.md).


## WeChat 公众号 article fetch

Stdlib HTTPS only. Fixed Chrome desktop UA. No cookies or profiles.

```bash
python3 skills/social-content-reader/scripts/fetch_wechat_article.py \
  'https://mp.weixin.qq.com/s/Rsa54LdbyhXIHheJYO6gkw' --out-dir /tmp/gzh
python3 skills/social-content-reader/scripts/acquire_media.py \
  'https://mp.weixin.qq.com/s/aNmLs3qJVhFGcgtGxAVlig' --out-dir /tmp/gzh
```

Success JSON includes `body_text`, `body_chars`, `embeds[]` (`vid`, `player_url`).
`--no-embed-media` skips the optional first-embed player attempt. `--html-file`
parses offline HTML (unit tests / user export). Captcha / `环境异常` shells
return `status: captcha_required`. See [platforms/wechat-article.md](../platforms/wechat-article.md).

## Douyin acquire

Optional Playwright path. It does not read the share caption.

```bash
python3 -m pip install playwright && python3 -m playwright install chromium
python3 skills/social-content-reader/scripts/acquire_douyin.py "https://v.douyin.com/2qulGbSTiRI/" --out-dir "$HOME/Media"
```

The first argument is a URL or a bare aweme id. The helper visits `https://www.douyin.com/` in Chromium (mobile UA), then `https://m.douyin.com/share/video/{aweme_id}`, reads `<video>.currentSrc` (playwm), and GETs it with that browser's cookies, the share page as Referer, and redirects followed. It writes `{out-dir}/douyin_{aweme_id}.mp4`. Success JSON is `ok`, `path`, `bytes`, `content_type`, `aweme_id`, `play_url`. iesdouyin pages that say 「请尝试在抖音内观看」 are not this player. If the mobile page has no video src, `ok` is false and `body_snip` is a page excerpt, not Understanding. Mac is the approved machine for a live run. See [INSTALL_OWN.md](../../../INSTALL_OWN.md).

Windows: `py -3.12 -m pip install playwright` then `py -3.12 -m playwright install chromium`.

## Frames

Requires `ffmpeg` and `ffprobe` on PATH. Refuses `http://` / `https://` inputs.

```bash
python3 skills/social-content-reader/scripts/extract_frames.py --media "$HOME/Media/clip.mp4" --mode fps --fps 1 --max-frames 24 --out-dir /tmp/scr-frames
python3 skills/social-content-reader/scripts/extract_frames.py --media "$HOME/Media/clip.mp4" --mode scene --scene-threshold 0.3 --max-frames 24
```

```powershell
py -3.12 skills\social-content-reader\scripts\extract_frames.py --media "C:\Media\clip.mp4" --mode fps --fps 1 --max-frames 24
```

`--mode fps` samples evenly. `--mode scene` keeps the first frame plus scene changes. `--max-frames` defaults to 24 (1–300). When the cap is hit, `truncated` is true. `--out-dir` must not already contain `frame_*.jpg`; the default is a new temp directory. Stdout is one JSON object: `ok`, `frames[].path`, `frames[].timestamp_sec`, `duration_sec`, `error`.

macOS: `brew install ffmpeg`. Windows: `winget install --id Gyan.FFmpeg --exact`. Linux: the distro ffmpeg package.

## OCR

Optional. Missing engines exit 1 with `ok: false`, `engine: none`, and install hints. Empty OCR text with `ok: true` means the engine ran and found no burned-in words.

```bash
python3 skills/social-content-reader/scripts/ocr_frames.py --frames-json frames.json
python3 skills/social-content-reader/scripts/ocr_frames.py --dir /tmp/scr-frames --lang chi_sim+eng
```

Tesseract languages fall back from `chi_sim+eng` to `eng` when Chinese data is not installed. macOS Vision: `--engine vision` compiles `ocr_vision.swift` with `swiftc` (Xcode). The host agent's vision tool is still required for a description of the picture; OCR is only the burned-in string.

macOS: `brew install tesseract tesseract-lang`. Windows: `winget install --id UB-Mannheim.TesseractOCR --exact`. Linux: `tesseract-ocr` and, for Chinese, `tesseract-ocr-chi-sim`.

## Understanding a local file

`understand_media.py` is the join for a file that acquire (or the user) already saved. It does not download. `ffprobe` must see a positive duration and an audio or video stream. A URL, an empty file, or an undecodable file is `blocked` and is not described from the caption.

```bash
python3 skills/social-content-reader/scripts/understand_media.py \
  --media "$HOME/Media/clip.mp4" \
  --caption "share text, metadata only" \
  --visual-description-file "$HOME/Media/vision.txt" \
  --out-dir "$HOME/Media/understood"
```

```powershell
py -3.12 skills\social-content-reader\scripts\understand_media.py --media "C:\Media\clip.mp4" --caption "share text, metadata only" --visual-description-file "C:\Media\vision.txt" --out-dir "C:\Media\understood"
```

Stdout is one JSON object:

- `record` is the ContentRecord. `body_text` is a labeled join of pictures, on-screen text, and speech. `caption` and `title` are not copied into `body_text`, `speech_text`, `visual_text`, or `visual_description`.
- `understanding` is a short summary of those same fields. When `ok` is true and a caption was passed, the caption appears only on a line marked metadata.
- `ok: true` means at least one real channel produced evidence. `complete: true` means `body_kind: media_understanding` (pictures and speech). Speech-only is `transcript`. Picture-only is `visual`.
- `ocr_engine` and `asr_engine` are `none` when that engine did not run. `evidence.ocr.reason` / `evidence.asr.reason` say `engine_missing`, `no_audio`, `no_frames`, or `official_track`. A missing engine does not become guessed text.
- `--asr-backend` defaults to `local` and never calls the OpenAI API. `--asr-backend openai-api` uploads only when set. `--speech-file` supplies an official track and skips ASR. Text that matches the caption or the title is rejected as metadata.
- `--visual-description-file` is host notes of the frames. It is ignored when no frames were read. This script does not ship a vision model.
- `evidence.frames_json` is the extract receipt. A second pass can pass `--frames-json` for the same `--media` after the host has looked at the frames.
- `has_audio: false` skips ASR. Speech stays empty.

Exit 0 when `ok` is true. Exit 1 when the file was not validated or when no channel produced evidence (`blocked: true`).

## ASR usage and output

From the repo root (adjust paths for a copied/installed skill):

```powershell
python skills/social-content-reader/scripts/asr_local.py --help
python skills/social-content-reader/scripts/asr_local.py --media "C:\Media\reel.mp4" --language auto --model base --backend auto
python skills/social-content-reader/scripts/asr_local.py --media "C:\Media\channels.mp4" --language zh --model small --backend faster-whisper
```

`--language` accepts `zh`, `en`, or `auto` (default). `--model` selects a local model such as `tiny`, `base` (default), `small`, `medium`, or `large-v3`; English-only `.en` models suit English speech only. Both local backends use CPU to avoid a CUDA setup requirement; faster-whisper uses int8. First use may download weights and take time/disk space. After weights are cached, local transcription can work offline.

`--backend auto` tries importable **faster-whisper**, then **openai-whisper**, then **OpenAI API** if the `openai` SDK and `OPENAI_API_KEY` are available. Import/dependency failures allow selection of the next candidate. Once selected, model-loading/inference/upload errors stop with a JSON error; they do not trigger a cloud fallback. Explicit backends never switch. Before auto can upload, ensure the user authorized API processing; having a key is not upload consent. Pin a local backend for local-only processing.

The API backend always uses **`whisper-1`**, regardless of local `--model`, and reports that actual model in JSON. It sends media to the official OpenAI endpoint using `OPENAI_API_KEY` from the environment; it does not use a custom `OPENAI_BASE_URL`. Never put keys in arguments/files or echo them. API uploads may incur charges; no upload or billed call is made by `--help` or the unit tests. No third-party transcript service is bundled.

Example result (illustrative, not a recorded transcription):

```json
{"ok": true, "text": "Hello from the video.", "language": "en", "backend": "faster-whisper", "model": "base", "media_path": "C:\\Media\\reel.mp4"}
```

Check exit code 0 and `ok: true`, then map `text` → `speech_text`. Together with frames, OCR, and host vision this is `body_kind: media_understanding`, `fetch_method: media_pipeline`. ASR alone is `body_kind: transcript`, `fetch_method: user_media_asr`, and the record must say graphics were not read. Record language/backend/model. ASR does not extract silent visuals or guarantee exact names/numbers. Empty transcription fails. Do not copy the share caption into `speech_text`.

Operational failures return the same keys, `ok: false`, an `error`, and exit code 1. Missing files, empty files, missing dependencies/ffmpeg, unsupported API formats, oversized API uploads and backend errors are actionable failures. Help uses normal CLI text/exit 0; invalid arguments use argparse diagnostics/exit 2. Diagnostics/progress go to stderr; operational stdout is one ASCII-safe JSON object (Unicode text round-trips through JSON decoding on Windows).

## Mac / Linux installation

Python 3.11 or 3.12 is preferred so `faster-whisper` can install `av` wheels. On macOS, `brew install ffmpeg`. On Linux, install distro `ffmpeg`. Then:

```bash
python3 -m pip install faster-whisper "av>=11,<14"
python3 skills/social-content-reader/scripts/asr_local.py --help
```

Windows 24/7 is fine for heavy jobs. Mac and Linux fully support skill load, fetch, and this ASR helper. See [INSTALL_OWN.md](../../../INSTALL_OWN.md).

## Windows installation

**Important (Anthony-Alien):** the MinGW `python` on PATH cannot install binary `av` wheels. Use official CPython:

```powershell
py -3.12 -m pip install faster-whisper "av>=11,<14"
py -3.12 skills/social-content-reader/scripts/asr_local.py --help
```

FFmpeg: if `winget` is unavailable, install essentials to `C:\Tools\ffmpeg\...\bin` and add that bin dir to the User PATH (see HARDEN_NOTES.md).


Use your chosen Python environment. Install **one** local engine; these commands are setup instructions, not automatically executed by the helper:

```powershell
# Preferred local engine (PyAV bundles FFmpeg decoding libraries)
python -m pip install faster-whisper "av>=11,<14"
# or: py -3.12 -m pip install -r skills/social-content-reader/scripts/requirements-asr.txt

# Alternative local engine (can pull large PyTorch dependencies)
python -m pip install openai-whisper

# Required by openai-whisper and manual media conversion
winget install --id Gyan.FFmpeg --exact
# Reopen PowerShell so PATH refreshes, then verify:
ffmpeg -version

# Optional API backend; provision OPENAI_API_KEY via environment/secret store
python -m pip install openai
```

faster-whisper normally does **not** require the standalone `ffmpeg.exe` because PyAV supplies its decoding libraries. openai-whisper requires that executable on PATH; `pip install ffmpeg`/`ffmpeg-python` does not install it. If installation lacks wheels for your Python/platform, consult the backend's supported Python versions. Do not auto-install large packages/model weights during a smoke check.

For API input, the helper accepts MP3, MP4, MPEG, MPGA, M4A, WAV and WebM, with a conservative maximum of **25,000,000 bytes** per file. It does not auto-convert or split. Use local ASR for larger videos, or extract/compress/split audio first:

```powershell
ffmpeg -i "C:\Media\video.mp4" -vn -ac 1 -ar 16000 -c:a libmp3lame -b:a 64k "C:\Media\speech.mp3"
# If still too large, split and transcribe each chunk in chronological order:
ffmpeg -i "C:\Media\speech.mp3" -f segment -segment_time 600 -c copy "C:\Media\speech-%03d.mp3"
```

Check each chunk's size; review sentence boundaries and overlap when reconstructing `body_text`. Do not assume converted/split files were read until their ASR commands succeed.

## Checks without downloading models

```powershell
python -B -m unittest discover -s skills/social-content-reader/scripts/tests -v
```

Tests use backend stubs to cover routing, JSON, failure handling and upload boundaries; they do not prove speech accuracy. Actual ASR needs installed dependencies, model weights (local) or an authorized configured API, and a real speech file. Current machine smoke results: [HARDEN_NOTES.md](../../../HARDEN_NOTES.md).

Sources: [faster-whisper usage and decoding requirements](https://github.com/SYSTRAN/faster-whisper), [openai-whisper setup/usage](https://github.com/openai/whisper), [official OpenAI transcription guide](https://developers.openai.com/api/docs/guides/speech-to-text).

## Public video acquire (v0.5.0)

`acquire_media.py URL --out-dir ~/Media/proof` tries a documented public player
or yt-dlp route in a fresh context. Requires `ffmpeg`, `ffprobe`, and `yt-dlp` for
YouTube, X, Vimeo, direct `v.redd.it` DASH, Reddit post URLs (public `.json`
or `embed.reddit.com`, then DASH), and Twitch clips/VODs. Playwright Chromium is for browser routes. Install Playwright
in a venv (`python3 -m venv .venv-acquire; .venv-acquire/bin/pip install playwright;
.venv-acquire/bin/playwright install chromium`). Use that venv Python to run the helper, or activate it before the `python3`
examples. No browser profile or cookie file is read. The existing Douyin helper is routed through the same file validation.

Success: exit 0, JSON `ok: true`, absolute `path`, `bytes`, SHA-256, duration,
`has_video`, `has_audio`, codec names, source URL and method. The same receipt
is written beside the file. Silent/video-only files have `has_audio: false`;
that is picture-only evidence until source audio absence has been checked.
No Understanding is produced by a downloader. Failure: exit 1, `ok: false`,
`body_kind: unavailable`, `fetch_method: acquire_failed`, no success path.
Partial downloads live in a temporary directory and are removed on failure.

`--max-mb 128` bounds each download and the published output; `--wait-seconds 8`
is the public player load allowance (1–60). `--section START-END` is Twitch-only
and at most 600 seconds. A longer Twitch VOD is refused; `?t=` is not a range.
Downloader calls ignore local yt-dlp configuration. Browser routes reject error.mp4 placeholders. HTTP 206
is accepted only when Content-Range and actual bytes cover the entire file.
Bilibili's unencrypted video/audio tracks are muxed locally without re-encoding.
See [the live matrix](../../../SMOKE_RESULTS.md) for actual successes and walls.

Live sample replay (network and disk use; separate from unit tests):

```bash
.venv-acquire/bin/python -B skills/social-content-reader/scripts/smoke_acquire.py --platform tiktok --proof-dir "$HOME/Developer/scr-proof/recheck"
# --all explicitly attempts all 16 sample recipes; returns 1 if any failed.
```

`PASS.json` / `FAIL.txt` describe the latest attempt; media receipts are immutable
file evidence. Reddit's sample is the public post URL
`/r/aww/comments/90bu6w/` (not a pre-known CDN id). Direct `v.redd.it` URLs
still work. `redd.it` short links fail closed when that redirect is blocked.
公众号's sample is an embedded video probe, not the article-body reader.
This runner never produces Understanding.
`--max-mb` limits accepted files; browser playback and HTTP transfers may fetch
more data before an oversize response can be rejected.
