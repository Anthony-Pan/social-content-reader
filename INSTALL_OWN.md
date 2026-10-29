# Install on Anthony’s own computers / agents

How **Anthony’s bots** should load and invoke `social-content-reader` (v0.5.0+).

Windows 24/7 is fine for heavy extract/summarize jobs. Mac and Linux are fully supported for Codex skill load, fetch, ffmpeg frames, OCR, and ASR.

## Canonical clone

| Machine | Path |
| --- | --- |
| Mac | `~/Developer/social-content-reader` |
| Anthony-Alien (Windows) | `C:\Users\aw\source\repos\social-content-reader` |
| Grok Bot box (Linux) | `/workspace/social-content-reader` |

Keep these on `origin/main` (`git pull --ff-only`).

```bash
git clone https://github.com/Anthony-Pan/social-content-reader.git ~/Developer/social-content-reader
```

## User-level skill install (Mac)

Codex and Cursor user skills resolve from the home directory. Point both at the skill package inside the clone (symlink, so `git pull` shows up immediately):

```bash
SRC="$HOME/Developer/social-content-reader/skills/social-content-reader"
mkdir -p "$HOME/.agents/skills" "$HOME/.cursor/skills"
ln -sfn "$SRC" "$HOME/.agents/skills/social-content-reader"
ln -sfn "$SRC" "$HOME/.cursor/skills/social-content-reader"
```

A desktop Linux checkout uses the same two symlinks; only `SRC` changes.

## User-level skill install (Windows)

Codex / Cursor user skills resolve under the profile:

```powershell
$src = 'C:\Users\aw\source\repos\social-content-reader\skills\social-content-reader'
$agents = Join-Path $env:USERPROFILE '.agents\skills\social-content-reader'
$cursor = Join-Path $env:USERPROFILE '.cursor\skills\social-content-reader'
New-Item -ItemType Directory -Force (Split-Path $agents) | Out-Null
New-Item -ItemType Directory -Force (Split-Path $cursor) | Out-Null
# Junction so updates in the clone appear immediately
cmd /c mklink /J "$agents" "$src"
cmd /c mklink /J "$cursor" "$src"
```

If junctions fail (permissions), robocopy instead and re-copy after pulls:

```powershell
robocopy $src $agents /MIR /NFL /NDL /NJH /NJS
robocopy $src $cursor /MIR /NFL /NDL /NJH /NJS
```

## User-level skill install (box / Linux agents)

```bash
SRC=/workspace/social-content-reader/skills/social-content-reader
mkdir -p /home/box/.agents/skills
rm -rf /home/box/.agents/skills/social-content-reader
ln -s "$SRC" /home/box/.agents/skills/social-content-reader

# Optional mirror for loaders that scan managed-skills (copy, not symlink into managed tree if policy prefers copies)
mkdir -p /home/box/sand-data/managed-skills/skills
rm -rf /home/box/sand-data/managed-skills/skills/social-content-reader
cp -a "$SRC" /home/box/sand-data/managed-skills/skills/social-content-reader
```

Grok Bot parent agents should `Skill` load `social-content-reader` by name once the package is on a scanned skills path.

## Automatic acquire (Mac)

Install browser dependencies in a dedicated environment (no browser profile or
saved-cookie access):

```bash
cd ~/Developer/social-content-reader
python3 -m venv .venv-acquire
.venv-acquire/bin/pip install -r skills/social-content-reader/scripts/requirements-acquire.txt
.venv-acquire/bin/playwright install chromium
# ffmpeg/ffprobe and yt-dlp must also be installed and on PATH.
.venv-acquire/bin/python -B skills/social-content-reader/scripts/acquire_media.py \
  'https://www.tiktok.com/@scout2015/video/6718335390845095173' --out-dir "$HOME/Media"
```

Use the venv Python above, or activate it before using the `python3` examples
in the platform docs. Windows uses the corresponding venv `Scripts/python.exe`
and `Scripts/playwright.exe`; the live matrix here was run on this Mac.

Require exit 0, `ok: true`, actual video `path`, positive duration and its
SHA-256 receipt. Check `has_audio`. Then read frames, OCR, host vision and
speech. Acquisition is not Understanding. See [SMOKE_RESULTS.md](SMOKE_RESULTS.md)
for 13 verified video-platform samples and the explicit remaining walls.

The dedicated `acquire_douyin.py URL_OR_ID --out-dir DIR` still supports
`https://v.douyin.com/2qulGbSTiRI/` and aweme `7696098282904259850`. It uses
ordinary mobile Chromium, `https://www.douyin.com/` then
`https://m.douyin.com/share/video/{id}`, and its playing `/aweme/v1/playwm` URL.
It now requires HTTP 200 and ffprobe video validation as well as size checks.
No webdriver masking or saved browser cookies are used. `body_snip` on failure
is diagnosis, not Understanding. User export is last resort after automatic
acquisition fails.

## Media tools (Mac and Linux)

Frames need `ffmpeg`. Acquire uses `yt-dlp` when the user asked to read a video and the platform doc allows it. OCR is optional.

```bash
brew install ffmpeg yt-dlp
brew install tesseract tesseract-lang   # optional; Chinese burned-in text needs the language data
python3 -m pip install playwright && python3 -m playwright install chromium   # Douyin mobile-share acquire
# Linux: distro packages ffmpeg, yt-dlp, and tesseract-ocr (plus tesseract-ocr-chi-sim when wanted)
python3 skills/social-content-reader/scripts/extract_frames.py --help
python3 skills/social-content-reader/scripts/ocr_frames.py --help
```

macOS Vision OCR (only if Tesseract is not installed): Xcode `swiftc` on PATH, then `ocr_frames.py --engine vision`. The host agent's video/vision tool still describes the frames. This skill does not ship a vision model.

## ASR runtime (Mac and Linux)

Python 3.11 or 3.12 is preferred so `faster-whisper` can use `av` wheels.

```bash
python3 -m pip install faster-whisper "av>=11,<14"
# or: python3 -m pip install -r skills/social-content-reader/scripts/requirements-asr.txt
python3 skills/social-content-reader/scripts/asr_local.py --help
```

## Media tools (Windows)

```powershell
winget install --id Gyan.FFmpeg --exact
winget install --id yt-dlp.yt-dlp --exact
winget install --id UB-Mannheim.TesseractOCR --exact   # optional OCR
py -3.12 -m pip install playwright
py -3.12 -m playwright install chromium   # Douyin mobile-share acquire
# Reopen PowerShell so PATH refreshes. If winget cannot install ffmpeg, use the essentials zip in HARDEN_NOTES.md.
py -3.12 skills\social-content-reader\scripts\extract_frames.py --help
py -3.12 skills\social-content-reader\scripts\ocr_frames.py --help
yt-dlp --version
ffmpeg -version
```

Tesseract on Windows must be on PATH (`tesseract.exe`). Chinese burned-in text needs the Chinese language data selected in the UB-Mannheim installer. OCR failure is an honest `engine: none`; use the host vision tool on the frames and say OCR did not run.

## ASR runtime (Windows)

MinGW `python` on PATH often **cannot** install `av` wheels. Use official CPython:

```powershell
py -3.12 -m pip install faster-whisper "av>=11,<14"
# or: py -3.12 -m pip install -r skills/social-content-reader/scripts/requirements-asr.txt
# ffmpeg.exe on User PATH (e.g. C:\Tools\ffmpeg\...\bin) — see HARDEN_NOTES.md
py -3.12 skills\social-content-reader\scripts\asr_local.py --help
```

## Invoke one-liners

**Codex (Mac / Linux, bash):**

```bash
cd ~/Developer/social-content-reader
codex exec --full-auto "Use skill social-content-reader on <URL>. Acquire the video, then run understand_media.py on the saved file. Describe the extracted frames and pass that text as --visual-description-file. Return the helper JSON. If acquire fails, say the video was not watched. If ocr_engine or asr_engine is none, do not invent that channel."
```

**Codex (Windows, heavy lift):**

```powershell
cd C:\Users\aw\source\repos\social-content-reader
codex exec --full-auto "Use skill social-content-reader on <URL>. Acquire the video, then run understand_media.py via py -3.12 on the saved file. Describe the extracted frames and pass that text as --visual-description-file. Return the helper JSON. If acquire fails, say the video was not watched. If ocr_engine or asr_engine is none, do not invent that channel."
```

**Cursor / Claude / Grok agent:**

> Load skill `social-content-reader` and understand this URL: `<URL>`

**Normalize only (no network):**

```bash
python3 skills/social-content-reader/scripts/normalize_url.py "https://weixin.qq.com/sph/AAZ3p39sQm"
```

```powershell
py -3.12 skills\social-content-reader\scripts\normalize_url.py "<URL>"
```

The sph example should print `platform` `wechat-channels` and `canonical_id` `AAZ3p39sQm`.

## Success check

1. Skill folder exists under `~/.agents/skills/social-content-reader/SKILL.md` (version `0.5.0` in frontmatter). On Mac that path is a symlink to `~/Developer/social-content-reader/skills/social-content-reader`.
2. `normalize_url.py` detects YouTube, Reddit, TikTok, Bilibili, and `weixin.qq.com/sph/<id>` (`link_form: sph_share`).
3. `ffmpeg -version` and `extract_frames.py --help` succeed. A two-second generated sample (`ffmpeg -f lavfi -i testsrc=duration=2:size=160x120:rate=10`) extracts at least two frames with timestamps.
4. `python3 ... asr_local.py --help` (Mac/Linux) or `py -3.12 ... asr_local.py --help` (Windows) exits 0 after deps install.
5. `ocr_frames.py --help` exits 0. With Tesseract missing, a real run returns `ok: false` and `engine: none` instead of invented text.
6. `python3 -B -m unittest discover -s skills/social-content-reader/scripts/tests -v` passes.
