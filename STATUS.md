# STATUS — social-content-reader

**Version:** 0.5.3
**Updated:** 2026-10-29 — Twitch clip / bounded VOD section

v0.5.0 saved **13** video-platform sample files; 小红书 and 视频号 remain
blocked within allowed public paths. **v0.5.1** hardens 公众号 article
acquire. **v0.5.2** resolves a Reddit **post URL** to that post's own
v.redd.it DASH file when public embed HTML (or the `.json` listing) includes
it. **v0.5.3** acquires a public Twitch clip, a VOD of at most 600 seconds,
or one `--section` of at most 600 seconds, via yt-dlp with no cookies. A
longer VOD is refused. It is not trimmed to a silent prefix. Listing a
platform is not a claim of unrestricted access or completed Understanding.

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
- Speech/vision Understanding on acquired samples as requested.

## Locations

- GitHub: https://github.com/Anthony-Pan/social-content-reader
- Mac clone: `~/Developer/social-content-reader`
- Windows clone: `C:\Users\aw\source\repos\social-content-reader`
- Box checkout: `/workspace/social-content-reader`
