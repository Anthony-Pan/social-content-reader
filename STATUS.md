# STATUS — social-content-reader

**Version:** 0.3.1  
**Updated:** 2026-10-26 ~16:10 Asia/Shanghai

## Locations

- GitHub: https://github.com/Anthony-Pan/social-content-reader (public)
- Box clone: `/workspace/social-content-reader`
- Mac clone: `~/Developer/social-content-reader`
- Windows clone: `C:\Users\aw\source\repos\social-content-reader`
- User skill (Mac/Linux): `~/.agents/skills/social-content-reader` and `~/.cursor/skills/social-content-reader` → skill package
- User skill (Windows): `%USERPROFILE%\.agents\skills\social-content-reader` (+ `.cursor\skills\…`)
- User skill (box): `/home/box/.agents/skills/social-content-reader` (+ managed-skills copy)

## v0.3.1

- `weixin.qq.com/sph/<id>` (and `www`) normalizes to `wechat-channels`, `link_form: sph_share`, canonical `https://weixin.qq.com/sph/<id>`.
- Sph share WebFetch returns caption/description (measured: `AAZ3p39sQm`), not spoken video. Speech still needs user media + `asr_local.py`.
- `channels.weixin.qq.com` feed paths remain blocked (`errCode 10012`).
- Mac/Linux Codex skill install documented next to Windows. Windows 24/7 remains fine for heavy jobs.

## Matrix (honest)

See README / SKILL — 16 platforms. Overseas majors are first-class alongside Chinese.

## ASR (Alien)

- `py -3.12` + faster-whisper 1.2.1 + ffmpeg 9.0.2 essentials — installed
- Prefer `py -3.12` over MinGW python for ASR
- Pin `av>=11,<14` with faster-whisper 1.2.x
- Dry-run: SAPI speech WAV → ok:true (tiny model)

## Next

- Real speech E2E on a user Reel/视频号/TikTok file when Anthony supplies one
- Optional API keys for Graph / Helix / YouTube Data as needed
