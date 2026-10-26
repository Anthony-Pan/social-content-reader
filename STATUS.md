# STATUS — social-content-reader

**Version:** 0.4.0
**Updated:** 2026-10-26 ~17:45 Asia/Shanghai

## Locations

- GitHub: https://github.com/Anthony-Pan/social-content-reader (public)
- Box clone: `/workspace/social-content-reader`
- Mac clone: `~/Developer/social-content-reader`
- Windows clone: `C:\Users\aw\source\repos\social-content-reader`
- User skill (Mac/Linux): `~/.agents/skills/social-content-reader` and `~/.cursor/skills/social-content-reader` → skill package
- User skill (Windows): `%USERPROFILE%\.agents\skills\social-content-reader` (+ `.cursor\skills\…`)
- User skill (box): `/home/box/.agents/skills/social-content-reader` (+ managed-skills copy)

## v0.4.0

- Default video success is a local media file: frames (`extract_frames.py`), burned-in text (`ocr_frames.py`, Tesseract or macOS Vision), host vision description, and speech (`asr_local.py` or an official transcript).
- Share captions, oEmbed titles, and descriptions are `caption` metadata. They are not Understanding. Acquire failure is `body_kind: unavailable` / `fetch_method: acquire_failed` or `blocked`.
- `yt-dlp` is the documented public acquire CLI when the user asked to read the video and the platform doc says it can work. No cookie theft, captcha defeat, or private API client.
- Douyin share `https://v.douyin.com/2qulGbSTiRI` is aweme `7696098282904259850`. iesdouyin curl still returns a JS shell and that page often shows 「请尝试在抖音内观看」. The working acquire (Mac, 2026-10-26) is `acquire_douyin.py`: Playwright mobile UA, `www.douyin.com` for cookies, `m.douyin.com/share/video/{id}`, `<video>` playwm URL, same-context GET with Referer → CDN mp4 (~8MB, 1280×720, ~49s). User export is only the fallback when that page has no video src. Caption is not Understanding.

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

- Real speech + frame E2E on a user Reel/视频号/TikTok/Douyin file when Anthony supplies one
- Douyin `7696098282904259850` is acquired with `acquire_douyin.py` on a machine where the mobile share player exposes `<video>` src. Re-check if that page starts showing the in-app wall with no video element.
- Optional API keys for Graph / Helix / YouTube Data as needed
