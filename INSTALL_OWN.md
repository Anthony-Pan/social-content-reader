# Install on Anthony’s own computers / agents

How **Anthony’s bots** should load and invoke `social-content-reader` (v0.3.2+).

Windows 24/7 is fine for heavy extract/summarize jobs. Mac and Linux are fully supported for Codex skill load, fetch, and ASR.

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

## ASR runtime (Mac and Linux)

Python 3.11 or 3.12 is preferred so `faster-whisper` can use `av` wheels.

```bash
brew install ffmpeg   # macOS; on Linux install distro ffmpeg the same way you install other packages
python3 -m pip install faster-whisper "av>=11,<14"
# or: python3 -m pip install -r skills/social-content-reader/scripts/requirements-asr.txt
python3 skills/social-content-reader/scripts/asr_local.py --help
```

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
codex exec --full-auto "Use skill social-content-reader on <URL>. Return ContentRecord JSON + 8-line understanding. Public caption or post text is enough; use user media + python3 scripts/asr_local.py only for spoken-verbatim or an empty caption."
```

**Codex (Windows, heavy lift):**

```powershell
cd C:\Users\aw\source\repos\social-content-reader
codex exec --full-auto "Use skill social-content-reader on <URL>. Return ContentRecord JSON + 8-line understanding. Public caption or post text is enough; use user media + asr_local.py via py -3.12 only for spoken-verbatim or an empty caption."
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

1. Skill folder exists under `~/.agents/skills/social-content-reader/SKILL.md` (version `0.3.2` in frontmatter). On Mac that path is a symlink to `~/Developer/social-content-reader/skills/social-content-reader`.
2. `normalize_url.py` detects YouTube, Reddit, TikTok, Bilibili, and `weixin.qq.com/sph/<id>` (`link_form: sph_share`).
3. `python3 ... asr_local.py --help` (Mac/Linux) or `py -3.12 ... asr_local.py --help` (Windows) exits 0 after deps install.
