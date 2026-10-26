# STATUS — social-content-reader

**Version:** 0.5.0
**Updated:** 2026-10-26, Mac acquisition matrix

All 16 platforms are listed again, with documented automatic attempts and
explicit failures. **13 video platforms saved real sample media.** 小红书
(IP-risk wall) and 视频号 (QR/app-only share surface) remain unsolved within
the allowed public acquisition paths. 公众号's current article request hit
verification; embedded media was not acquired. Reddit's public CDN file is
verified, while arbitrary post-to-media resolution is still blocked.

The full all-platform goal remains partially unmet; listing a platform is not
a claim of unrestricted access or completed Understanding.

## Shipped

- `acquire_media.py`: public players / scoped yt-dlp routes, fresh contexts,
  no user profile extraction; validated local files and SHA-256 receipts.
- TikTok official embed, Bilibili external-player full-range tracks + local
  mux, public Instagram/Threads/Facebook post-matched media, Telegram exact
  widget, LinkedIn public video sources and Twitch clips. YouTube, Douyin,
  Vimeo and independently known public Reddit CDN media are verified too.
- Existing `acquire_douyin.py` now rejects HTTP errors/non-media using
  ffprobe, removes partial files, and no longer hides webdriver. The normal
  mobile player still saved its 8,382,047-byte sample after that change.
- `smoke_acquire.py --platform NAME|--all --proof-dir DIR` replays opt-in
  public samples and records PASS/FAIL. Does not run in the unit suite.
- Media-first rule unchanged: captions/oEmbed/descriptions are metadata.
  Files feed frames + OCR + host vision + speech; acquisition alone is not
  Understanding. User export follows failed automatic paths as last resort.

## Evidence

[SMOKE_RESULTS.md](SMOKE_RESULTS.md) contains every source, file, byte count,
stream limit and remaining wall. Local proof:
`~/Developer/scr-proof/matrix-2026-10-26/` (`matrix.json`, PASS/FAIL notes,
media, hashes, decoded frames and decode logs). All 13 counted files fully
decoded without FFmpeg errors. Unit suite: 55 passed.

## Remaining work

- A legitimate public player or configured authorized media integration for
  小红书 and 视频号; no successful general route is claimed.
- Reddit post-to-media resolution on a network/account with permitted access.
- Long Twitch VOD and 公众号 embedded-video live proof.
- Speech/vision Understanding on newly acquired samples as requested; this
  release run tests acquisition and decoding, not ASR quality.

## Locations

- GitHub: https://github.com/Anthony-Pan/social-content-reader
- Mac clone: `~/Developer/social-content-reader`
- Mac installed skill: `~/.agents/skills/social-content-reader` points to
  `skills/social-content-reader/` in this checkout.
- Windows clone: `C:\Users\aw\source\repos\social-content-reader`
- Existing ASR environment `.venv-asr/` preserved.
