# STATUS — social-content-reader

**Version:** 0.4.0
**Updated:** 2026-10-26 Mac matrix

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
- `yt-dlp` is a public acquire CLI only where a run has saved a file. Mac, 2026-10-26: YouTube `yt-dlp` saved a file (that file is not Understanding by itself). The TikTok sample was IP-blocked. Bilibili `yt-dlp` returned HTTP 412; public playurl is not a verified file recipe. Uploader CC remains a speech path when the subtitle API returns cues. No cookie theft, captcha defeat, or private API client.
- Douyin share `https://v.douyin.com/2qulGbSTiRI` is aweme `7696098282904259850`. iesdouyin curl still returns a JS shell and that page often shows 「请尝试在抖音内观看」. The verified helper is `scripts/acquire_douyin.py` (positional URL or aweme id, `--out-dir`, writes `douyin_{aweme_id}.mp4`, JSON `ok` / `path` / `bytes` / `content_type` / `aweme_id` / `play_url`). Mac, 2026-10-26: it re-downloaded this aweme repeatedly (~8MB, 1280×720, ~49s) via Playwright mobile UA, `www.douyin.com` cookies, `m.douyin.com/share/video/{id}`, `<video>` playwm, same-context GET with Referer. User export is only the fallback when that page has no video src. Caption is not Understanding. A download under 20KB fails. `body_snip` is diagnosis, not the body.

## v0.3.1

- `weixin.qq.com/sph/<id>` (and `www`) normalizes to `wechat-channels`, `link_form: sph_share`, canonical `https://weixin.qq.com/sph/<id>`.
- Sph share WebFetch returns caption/description (measured: `AAZ3p39sQm`), not spoken video. Speech still needs user media + `asr_local.py`.
- `channels.weixin.qq.com` feed paths remain blocked (`errCode 10012`).
- Mac/Linux Codex skill install documented next to Windows. Windows 24/7 remains fine for heavy jobs.

## Matrix (honest, Mac 2026-10-26)

See README / SKILL — 16 platforms. Live file acquire on Anthony’s Mac that day:

| Platform | File acquire |
| --- | --- |
| Douyin `7696098282904259850` | `acquire_douyin.py` works repeatedly (~8MB mp4). |
| YouTube | `yt-dlp` saved a file. Frames and speech are still required for Understanding. |
| TikTok | Sample was IP-blocked. Not a verified file recipe. |
| Bilibili | `yt-dlp` HTTP 412. Public playurl not verified. Uploader CC can still be speech. |

## ASR (Alien)

- `py -3.12` + faster-whisper 1.2.1 + ffmpeg 9.0.2 essentials — installed
- Prefer `py -3.12` over MinGW python for ASR
- Pin `av>=11,<14` with faster-whisper 1.2.x
- Dry-run: SAPI speech WAV → ok:true (tiny model)

## Next

- Real speech + frame E2E on a user Reel/视频号/TikTok/Douyin file when Anthony supplies one
- Douyin `7696098282904259850` auto-acquire is verified on Mac. Re-check if the mobile share page starts showing the in-app wall with no video element.
- TikTok and Bilibili still need a sample that actually saves a file before any `yt-dlp` or playurl recipe is documented as working.
- Optional API keys for Graph / Helix / YouTube Data as needed
