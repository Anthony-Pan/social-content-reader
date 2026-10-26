# Install on Anthony’s own computers / agents

How **Anthony’s bots** should load and invoke `social-content-reader` (v0.3+).

## Canonical clone

| Machine | Path |
| --- | --- |
| Anthony-Alien (Windows) | `C:\Users\aw\source\repos\social-content-reader` |
| Grok Bot box | `/workspace/social-content-reader` |

Keep these on `origin/main` (`git pull --ff-only`).

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

## ASR runtime (Windows)

MinGW `python` on PATH often **cannot** install `av` wheels. Use official CPython:

```powershell
py -3.12 -m pip install faster-whisper "av>=11,<14"
# or: py -3.12 -m pip install -r skills/social-content-reader/scripts/requirements-asr.txt
# ffmpeg.exe on User PATH (e.g. C:\Tools\ffmpeg\...\bin) — see HARDEN_NOTES.md
py -3.12 skills\social-content-reader\scripts\asr_local.py --help
```

## Invoke one-liners

**Codex (heavy lift):**

```powershell
cd C:\Users\aw\source\repos\social-content-reader
codex exec --full-auto "Use skill social-content-reader on <URL>. Return ContentRecord JSON + 8-line understanding. Prefer connectors; for speech-only platforms use user media + asr_local.py via py -3.12."
```

**Cursor / Claude / Grok agent:**

> Load skill `social-content-reader` and understand this URL: `<URL>`

**Normalize only (no network):**

```powershell
py -3.12 skills\social-content-reader\scripts\normalize_url.py "<URL>"
```

## Success check

1. Skill folder exists under `~/.agents/skills/social-content-reader/SKILL.md` (version `0.3.0` in frontmatter).
2. `normalize_url.py` detects YouTube, Reddit, TikTok, Bilibili, etc.
3. `py -3.12 ... asr_local.py --help` exits 0 after deps install.
