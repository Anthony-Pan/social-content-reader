# STATUS — social-content-reader

**Version:** 0.5.1
**Updated:** 2026-10-26 Asia/Shanghai — WeChat 公众号 harden

v0.5.0 saved **13** video-platform sample files; 小红书 and 视频号 remain
blocked within allowed public paths. **v0.5.1** hardens 公众号 article
acquire: Chrome desktop UA + stdlib HTTPS returns substantive `#js_content`
(SSR `visibility:hidden;opacity:0` accepted). Embedded `mpvideo` vids are
extracted; playable embed files remain best-effort / network-dependent.
视频号 sph still has no public media URL.

Listing a platform is not a claim of unrestricted access or completed
Understanding.

## Shipped (0.5.1)

- `scripts/fetch_wechat_article.py`: stdlib HTTPS, fixed Chrome UA, substantive
  body gate, captcha/`环境异常` rejection, mpvideo embed extraction, optional
  first-embed media attempt. Article ok without ffmpeg.
- `acquire_media.py` routes `mp.weixin.qq.com` → fetch_wechat_article.
- Offline fixtures + unit tests for SSR body, captcha shell, display:none,
  embed ids, and acquire wiring without ffmpeg.
- Docs: `platforms/wechat-article.md`, this STATUS, SMOKE_RESULTS addendum,
  HARDEN_NOTES, scripts/README, SKILL metadata `0.5.1`.

## Evidence

- Matrix (video): [SMOKE_RESULTS.md](SMOKE_RESULTS.md) / Mac
  `~/Developer/scr-proof/matrix-2026-10-26/`
- 公众号 harden: `/workspace/scr-proof/wechat-gzh-2026-10-26/` (box) with live
  receipts for Rsa + Anm articles.
- Unit suite: run `python3 -m unittest discover -s skills/social-content-reader/scripts/tests`

## Remaining work

- 小红书 / 视频号: no successful general public media route.
- 公众号 embed media: public player often returns 「视频不存在」 from some
  networks; Mac historically saved one sample — not claimed universal.
- Reddit post-to-media resolution; long Twitch VODs.
- Speech/vision Understanding on acquired samples as requested.

## Locations

- GitHub: https://github.com/Anthony-Pan/social-content-reader
- Mac clone: `~/Developer/social-content-reader`
- Windows clone: `C:\Users\aw\source\repos\social-content-reader`
- Box checkout: `/workspace/social-content-reader`
