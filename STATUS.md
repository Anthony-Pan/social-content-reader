# STATUS — overnight draft (Asia/Shanghai)

**Date:** 2026-10-25 night → for **2026-10-26 morning brief**  
**Owner draft by:** Dev (Grok Bot)  
**Product:** public GitHub Agent Skill — `social-content-reader`  
**Runtime decision (Anthony course-correct):** **Windows-first + Codex CLI**, not Linux-box-only.

## Done tonight

- [x] Agent Skills–format package (`SKILL.md` + YAML `name` / `description`)
- [x] Architecture adapter doc (detect → connector/public path → normalize → understand)
- [x] Platform recipes: YouTube, X, Instagram, WeChat 公众号, WeChat 视频号 (honest limits)
- [x] Keyless `scripts/normalize_url.py`
- [x] README (install, Windows layout, matrix, ToS honesty)
- [x] MIT LICENSE
- [x] Local git repo initialized + initial commit on the box
- [x] Probed **Anthony-Alien** Windows PC: `codex` on PATH (`codex-cli 0.163.0`); no existing `social-content-reader` clash

## Partial / not done

- [ ] Copy/sync tree onto Windows suggested path (ready; may need Anthony/Dev to finish if CopyFromBox not run)
- [ ] Create **public** GitHub repo under `Anthony-Pan` + push (gh on box is auth’d as Anthony-Pan — **waiting Anthony publish yes/name**)
- [ ] End-to-end live fetch tests per platform (overnight scaffold only; Instagram/视频号 expected weak/blocked)
- [ ] Optional paid transcript API wiring (env-based) — intentionally not hardcoded

## Windows-first layout

| Item | Value |
| --- | --- |
| Machine | Anthony-Alien (`bdd40551-6cec-4473-a698-185f52a35435`) |
| Codex | `C:\Users\aw\AppData\Roaming\npm\codex.cmd` · `codex-cli 0.163.0` |
| **Suggested project path** | `C:\Users\aw\source\repos\social-content-reader` |
| Alternatives (empty name) | `C:\Users\aw\dev\social-content-reader`, `E:\Dev\social-content-reader` |
| Box draft path | `/workspace/social-content-reader/` |

**Invoke pattern:**

```powershell
cd C:\Users\aw\source\repos\social-content-reader
codex exec --full-auto "Follow skills/social-content-reader for URL <URL>. Return ContentRecord JSON + understanding summary."
```

## Platform matrix (honest)

| Platform | Status | One-liner |
| --- | --- | --- |
| YouTube | ✅ Works | Transcript/captions → real understanding; prefer host YouTube connector |
| X/Twitter | ✅ Partial | Host X tools or `publish.x.com/oembed`; threads/media limited |
| Instagram | ⚠️ Partial / deep-read blocked | oEmbed = embed preview only (Meta ToS); Reels speech needs user paste/ASR |
| WeChat 公众号 | ⚠️ Partial | Short public links often OK; captcha/long `__biz` common; no login bypass |
| WeChat 视频号 | ❌ Blocked | No general consumer transcript API; creator APIs only / user paste |

## Repo readiness

- Box path: `/workspace/social-content-reader`
- Git: initialized; see latest commit SHA below after commit
- GitHub remote: **not created yet** (pending Anthony decisions)
- `gh` on box: logged in as **Anthony-Pan** (can publish when approved)

### Publish steps (when Anthony says yes)

```bash
cd /workspace/social-content-reader
gh repo create Anthony-Pan/social-content-reader --public --source=. --remote=origin --push \
  --description "Agent Skill: read/understand social posts & videos beyond captions (YouTube, X, Instagram, WeChat)"
```

Or rename first if he picks another public name.

### Sync to Windows (when ready)

```powershell
# after files land at suggested path
cd C:\Users\aw\source\repos\social-content-reader
# optional: install as user skill
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills" | Out-Null
# copy or junction skills\social-content-reader → ~/.agents/skills/social-content-reader
```

## Anthony next decisions (morning)

1. **Public repo name?** default `social-content-reader` — or prefer `agent-social-reader` / other?
2. **Publish now?** `gh repo create --public` + push (gh already Anthony-Pan)
3. **Windows home path OK?** `C:\Users\aw\source\repos\social-content-reader`
4. **Priority platforms to harden first?** Recommend YouTube + X + 公众号; treat IG Reels + 视频号 as “honest blocked / user-assist”
5. Any **must-have** hosts (TikTok, Bilibili, RedNote) for v0.2?

## Morning-brief blurb (paste-ready)

```text
📌 social-content-reader (overnight) — public Agent Skill draft ready on box
• Goal: agents understand social videos/posts (transcripts/bodies), not just captions
• Format: Agent Skills SKILL.md + platform docs; MIT; Windows+Codex-first
• Probed Anthony-Alien: Codex 0.163.0 on PATH; suggested path C:\Users\aw\source\repos\social-content-reader
• Matrix: YouTube✅ · X partial✅ · Instagram deep-read⚠️/blocked · 公众号 partial⚠️ · 视频号❌
• GitHub public push: waiting your yes + final repo name (gh auth OK as Anthony-Pan)
• Path on box: /workspace/social-content-reader — ask Dev to sync→Windows + publish when you decide
```

## Commit

_Filled after `git commit`:_

- SHA: _(see git log)_
- Files: README, LICENSE, STATUS, skills/social-content-reader/** 
