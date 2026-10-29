# STATUS — social-content-reader

**Version:** 0.5.2
**Updated:** 2026-10-29 — Reddit post URL → hosted media

v0.5.0 saved **13** video-platform sample files; 小红书 and 视频号 remain
blocked within allowed public paths. **v0.5.1** hardens 公众号 article
acquire. **v0.5.2** resolves a Reddit **post URL** to that post's own
v.redd.it DASH file when public embed HTML (or the `.json` listing) includes
it. Listing a platform is not a claim of unrestricted access or completed
Understanding.

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
- Unit suite: `python3 -m unittest discover -s skills/social-content-reader/scripts/tests`

## Remaining work

- 小红书 / 视频号: no successful general public media route.
- 公众号 embed media: public player often returns 「视频不存在」 from some
  networks; Mac historically saved one sample — not claimed universal.
- Reddit: `www`/`old` listing JSON and `redd.it` redirects are HTTP 403 on
  this box; post URLs need a subreddit or user in the path when JSON is
  blocked; multi-video posts are refused; quarantined subs are not opted into.
- Long Twitch VODs.
- Speech/vision Understanding on acquired samples as requested.

## Locations

- GitHub: https://github.com/Anthony-Pan/social-content-reader
- Mac clone: `~/Developer/social-content-reader`
- Windows clone: `C:\Users\aw\source\repos\social-content-reader`
- Box checkout: `/workspace/social-content-reader`
