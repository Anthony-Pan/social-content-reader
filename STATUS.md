# STATUS — social-content-reader

**Version:** 0.5.4
**Updated:** 2026-10-29 — local-file Understanding

v0.5.0 saved **13** video-platform sample files; 小红书 and 视频号 remain
blocked within allowed public paths. **v0.5.1** hardens 公众号 article
acquire. **v0.5.2** resolves a Reddit **post URL** to that post's own
v.redd.it DASH file when public embed HTML (or the `.json` listing) includes
it. **v0.5.3** acquires a public Twitch clip, a VOD of at most 600 seconds,
or one `--section` of at most 600 seconds, via yt-dlp with no cookies. A
longer VOD is refused. It is not trimmed to a silent prefix. **v0.5.4**
reads a validated local file (frames, OCR, host vision notes, local ASR)
and will not sell a caption or title as the body. Listing a platform is
not a claim of unrestricted access. Understanding is claimed only when
`understand_media.py` returns evidence from that file.

## Shipped (0.5.4)

- `scripts/understand_media.py`: ffprobe gate, then `extract_frames.py`,
  `ocr_frames.py`, and local `asr_local.py`. Optional `--speech-file` for an
  official track and `--visual-description-file` for host notes of the frames.
  No URL download, no cookie, no vision model, no API upload unless
  `--asr-backend openai-api` is explicit.
- ContentRecord `body_text` is only pictures, on-screen text, and speech.
  Caption and title stay in their own fields. Text that merely repeats them
  is dropped. `ok` requires a real channel. `complete` requires pictures and
  speech. Missing OCR/ASR is `engine: none` and `blocked` when nothing else
  was read.
- Offline tests cover URL refusal, undecodable files, engine none, caption
  rejection, silent video, audio-only, official tracks, and frame reuse.
  A generated lavfi file on this box is the smoke in SMOKE_RESULTS. The
  v0.5.0 platform samples were not on this disk, so they were not re-read.

## Shipped (0.5.3)

- `scripts/acquire_twitch.py`: public clip and `/videos/{id}` via yt-dlp
  `--ignore-config`. No cookies, netrc, or Helix token. Channel, live, list,
  and collection URLs fail before a download.
- Full file and `--section` are each capped at 600 seconds. Over that, the
  error names the real duration and does not save a prefix. `?t=` is recorded
  as an unapplied bookmark.
- A padded size estimate (about 220 KB/s at 480p, 900 KB/s at 1080p) must fit
  `--max-mb` or nothing is downloaded. An oversize file is deleted.
- ffprobe still requires positive duration and a video stream. A section's
  duration must match the window. Receipts carry `twitch_kind`, `twitch_id`,
  `twitch_full`, and `twitch_source_duration_sec`. No title or chat as body.
- Live box: the known clip matches the v0.5.0 bytes and SHA-256. A 402s
  source-only VOD saved with `--max-mb 400` and was refused at the default
  128 MB cap before download. Two 20s windows of a 15434s VOD saved 480p
  files. See SMOKE_RESULTS v0.5.3 addendum.

## Shipped (0.5.2)

- `scripts/resolve_reddit.py`: public post `.json` first; `embed.reddit.com`
  when the listing is an HTTP block. Matches `t3_{id}` only. Crosspost
  screenview URL and a single gallery video are accepted. Two hosted videos
  are refused. Signed player queries are dropped. No cookie jar.
- `acquire_media.py` downloads the resulting unsigned `DASHPlaylist.mpd` with
  the existing yt-dlp path and ffprobe gate. Direct `v.redd.it` URLs skip the
  resolver. Method `reddit_post_embed` or `reddit_post_json`.
- Offline fixtures: exact post vs comment/recommendation, crosspost, gallery,
  image/off-site, quarantine (no cookie opt-in), short-link 403, token leak.
- Live box smoke: three post URLs saved valid files (one matches the v0.5.0
  CDN bytes). `redd.it`, bare `/comments/{id}`, and a two-video post fail
  closed. See SMOKE_RESULTS v0.5.2 addendum.

## Evidence

- Matrix (video): [SMOKE_RESULTS.md](SMOKE_RESULTS.md) / Mac
  `~/Developer/scr-proof/matrix-2026-10-26/`
- 公众号 harden: `/workspace/scr-proof/wechat-gzh-2026-10-26/` (box)
- Reddit post URLs: [references/reddit-post-2026-10-29.json](skills/social-content-reader/references/reddit-post-2026-10-29.json)
- Twitch clip / VOD sections: [references/twitch-vod-2026-10-29.json](skills/social-content-reader/references/twitch-vod-2026-10-29.json)
- Unit suite: `python3 -m unittest discover -s skills/social-content-reader/scripts/tests`

## Remaining work

- 小红书 / 视频号: no successful general public media route.
- 公众号 embed media: public player often returns 「视频不存在」 from some
  networks; Mac historically saved one sample — not claimed universal.
- Reddit: `www`/`old` listing JSON and `redd.it` redirects are HTTP 403 on
  this box; post URLs need a subreddit or user in the path when JSON is
  blocked; multi-video posts are refused; quarantined subs are not opted into.
- Twitch: a VOD longer than 600s is not acquired whole. One `--section` of
  at most 600s can be, when it fits `--max-mb`. Subscriber-only media was
  not given a live sample; login/subscription errors stop with no cookie
  fallback. `?t=` does not seek.
- Understanding engines: this box has ffmpeg and tesseract. It does not have
  faster-whisper or openai-whisper, so speech stays `asr_engine: none`.
  No vision model is bundled; a human or host tool has to look at the frames
  and pass notes. The 13 acquired platform files were not on this box.

## Locations

- GitHub: https://github.com/Anthony-Pan/social-content-reader
- Mac clone: `~/Developer/social-content-reader`
- Windows clone: `C:\Users\aw\source\repos\social-content-reader`
- Box checkout: `/workspace/social-content-reader`
