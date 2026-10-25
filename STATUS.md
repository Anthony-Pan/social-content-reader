# STATUS — social-content-reader

**Updated:** 2026-10-26 ~07:17 Asia/Shanghai (CST)  
**Owner draft by:** Dev (Grok Bot)  
**Product:** public GitHub Agent Skill — `social-content-reader`  
**Runtime:** **Windows-first + Codex CLI** (Anthony course-correct)

## Done

- [x] Agent Skills package (`SKILL.md` + platform recipes + `normalize_url.py`)
- [x] README + MIT LICENSE + ARCHITECTURE
- [x] Box git repo + Windows clone at `C:\Users\aw\source\repos\social-content-reader`
- [x] Codex on Anthony-Alien: `codex-cli 0.163.0`
- [x] **Live smoke tests** (2026-10-26 morning) → `SMOKE_RESULTS.md`
- [x] Public GitHub publish decision: **yes** — name `social-content-reader` (Anthony 2026-10-26)

## Platform matrix (design vs measured)

| Platform | Design | Measured (2026-10-26 CST) | One-liner |
| --- | --- | --- | --- |
| YouTube | ✅ Works | ✅ **pass** | TubeAlfred metadata + transcript on `jNQXAC9IVRw` |
| X/Twitter | ✅ Partial | ✅ **partial** | `x` MCP post text+metrics; oEmbed OK; threads/media limited |
| Instagram | ⚠️ / deep-read blocked | ⚠️ **partial / deep-read blocked** | oEmbed embed HTML only; no speech/transcript fields |
| WeChat 公众号 | ⚠️ Partial | ⚠️ **partial** | WebFetch got full body once; raw curl often `未知错误`/verify |
| WeChat 视频号 | ❌ Blocked | ❌ **fail (blocked)** | feed `errCode 10012 Illegal request`; no consumer transcript API |

## Windows-first layout

| Item | Value |
| --- | --- |
| Machine | Anthony-Alien (`bdd40551-6cec-4473-a698-185f52a35435`) |
| Codex | `codex-cli 0.163.0` |
| Project path | `C:\Users\aw\source\repos\social-content-reader` |
| Box path | `/workspace/social-content-reader/` |

## Repo / publish

- Box path: `/workspace/social-content-reader`
- GitHub: `Anthony-Pan/social-content-reader` (public) — see latest commit after publish
- `gh` on **box**: logged in as **Anthony-Pan** (used for create+push)
- `gh` on Windows Anthony-Alien: **not logged in** at smoke/publish time (sync via git pull after remote exists)

### Invoke pattern

```powershell
cd C:\Users\aw\source\repos\social-content-reader
codex exec --full-auto "Follow skills/social-content-reader for URL <URL>. Return ContentRecord JSON + understanding summary."
```

## Morning-brief blurb (post-smoke)

```text
📌 social-content-reader — live smokes done + public repo publish
• Measured: YouTube✅ · X partial✅ · IG oEmbed-only⚠️ · 公众号 partial⚠️ · 视频号❌
• Evidence: SMOKE_RESULTS.md (2026-10-26 ~07:17 Asia/Shanghai)
• Public: https://github.com/Anthony-Pan/social-content-reader
• Windows: C:\Users\aw\source\repos\social-content-reader (pull after publish)
```
