# SMOKE_RESULTS — live platform checks

**When:** 2026-10-26 ~07:15–07:17 Asia/Shanghai (CST, UTC+8)  
**Runner:** Grok Bot on box `/workspace/social-content-reader`  
**Purpose:** Measure claim vs reality before public GitHub publish. No login bypass.

## Summary matrix (measured)

| Platform | Measured | Method | Evidence (one line) |
| --- | --- | --- | --- |
| `normalize_url.py` | ✅ pass | local Python | Correct platform/id for YT, X, IG, 公众号 short, 视频号, bare YT id |
| YouTube | ✅ pass | TubeAlfred `youtube_video_get` + `youtube_video_transcript` | `jNQXAC9IVRw` (“Me at the zoo”) metadata + English manual transcript (6 cues) |
| X / Twitter | ✅ partial | host `x` MCP `get_posts_by_id` + `publish.twitter.com/oembed` | Post `2112722684710719913` (@X) text+metrics; oEmbed HTML OK; thread/media still limited |
| Instagram | ⚠️ partial / deep-read blocked | Meta `graph.facebook.com/v26.0/instagram_oembed` | Real post `fA9uwTtkSN` → embed HTML only (`html`,`provider_*`,`type`,`width`); **no** caption/transcript fields; speech understanding blocked |
| WeChat 公众号 | ⚠️ partial | WebFetch vs raw curl | Short URL `…/s/Rsa54LdbyhXIHheJYO6gkw` → full article body via WebFetch; raw datacenter `curl` often `未知错误`/redirect — captcha/UA walls real |
| WeChat 视频号 | ⚠️ caption metadata only | sph WebFetch caption; `channels.weixin.qq.com` feed blocked | Feed path `errCode 10012` (no transcript). Sph share `…/sph/AAZ3p39sQm` WebFetch returns caption/date/thumbnail, not the video — addendum §7 |
| Douyin | ⚠️ iesdouyin curl blocked; Mac player worked | curl of the short link; separate Mac Playwright run | Share `v.douyin.com/2qulGbSTiRI` → aweme `7696098282904259850`. iesdouyin curl is a JS shell / in-app wall. Mobile share after homepage cookies played — addendum §8 |

## Detail

### 1. normalize_url.py

Command: `python3 skills/social-content-reader/scripts/normalize_url.py <url>`

| Input | platform | canonical_id / notes |
| --- | --- | --- |
| `https://youtu.be/jNQXAC9IVRw` | youtube | `jNQXAC9IVRw` |
| `https://twitter.com/elonmusk/status/1519480761749016577` | x | `1519480761749016577` |
| `https://www.instagram.com/reel/C123abcDEF/` | instagram | kind=`reel`, id=`C123abcDEF` |
| `https://mp.weixin.qq.com/s/AbCdEfGhIjKlMnOp` | wechat-article | short form |
| `https://channels.weixin.qq.com/web/pages/live?finderUsername=test` | wechat-channels | limits: no general public consumer fetch |
| `https://weixin.qq.com/sph/AAZ3p39sQm` | wechat-channels | `canonical_id` `AAZ3p39sQm`, `link_form` `sph_share`, canonical `https://weixin.qq.com/sph/AAZ3p39sQm` (v0.3.1; see addendum) |
| `https://www.weixin.qq.com/sph/AAZ3p39sQm` | wechat-channels | same canonical id/url; `www` stripped |
| bare `dQw4w9WgXcQ` | youtube | OK |

**Result:** pass

### 2. YouTube

- URL: `https://www.youtube.com/watch?v=jNQXAC9IVRw`
- Method: TubeAlfred MCP
- Metadata: title “Me at the zoo”; channel `@jawed`; duration 00:19; publish 2005-04-24
- Transcript (`language=en`, manual):  
  “All right, so here we are, in front of the elephants … really really long trunks … and that's pretty much all there is to say”
- **Result:** pass — body/transcript understanding possible

### 3. X / Twitter

- URL: `https://x.com/X/status/2112722684710719913`
- Method: `x.get_users_by_username` → `get_users_posts` → `get_posts_by_id`
- Text: `and for dessert, a little scroll`
- Metrics sampled: impressions ~3.0M, likes 5501, replies 873 (at smoke time)
- Fallback: `publish.twitter.com/oembed` → HTTP 200, provider X, author X, html_len 296
- Limits observed: this sample had no attachments in API payload; skill still correctly treats full thread walk + media ASR as partial
- **Result:** partial (single-post text OK; threads/media not fully exercised)

### 4. Instagram

- URL: `https://www.instagram.com/p/fA9uwTtkSN/` (Meta docs sample)
- Also OK: `https://www.instagram.com/p/DalfZ3Jn8yi/`
- Method: `GET https://graph.facebook.com/v26.0/instagram_oembed?url=…` (tokenless)
- Response keys only: `html`, `provider_name`, `provider_url`, `type`, `version`, `width`
- Stripped HTML preview: “View this post on Instagram” — **not** Reel speech
- Fake/missing codes → HTTP 400 Media Not Found (expected)
- **Result:** partial for embed preview · **deep-read / speech blocked** (do not claim understanding from oEmbed alone)

### 5. WeChat 公众号

- URL: `https://mp.weixin.qq.com/s/Rsa54LdbyhXIHheJYO6gkw`
- WebFetch: **success** — title《一个错误，让我客户痛苦失去200万》; full Chinese body returned
- Raw `curl` from box (WeChat iPhone UA): HTTP 302 / title `未知错误` on several public short links — datacenter/UA wall
- **Result:** partial — public short links sometimes readable; captcha/verify/UA failures common; no login bypass attempted

### 6. WeChat 视频号

- `https://channels.weixin.qq.com/` → HTML shell (~4.6KB), not a video transcript
- `https://channels.weixin.qq.com/web/pages/feed` → `{"desc":"非法请求","errMsg":"Illegal request","errCode":10012}`
- **Result:** fail / blocked for `channels.weixin.qq.com` feed deep-read — still true. Sph share links are a separate path; see the addendum.

### 7. Addendum (2026-10-26, v0.3.1) — 视频号 sph share links

Normalize (local, no network):

```bash
python3 skills/social-content-reader/scripts/normalize_url.py 'https://weixin.qq.com/sph/AAZ3p39sQm'
```

Expected: `platform` `wechat-channels`, `canonical_id` `AAZ3p39sQm`, `canonical_url` `https://weixin.qq.com/sph/AAZ3p39sQm`, `link_form` `sph_share`. `www.weixin.qq.com` normalizes to the same canonical URL. `channels.weixin.qq.com` stays `wechat-channels` and does not pick up `sph_share`. Covered by `scripts/tests/test_normalize_url.py`.

WebFetch (measured, do not treat as speech): `https://weixin.qq.com/sph/AAZ3p39sQm` returns caption/description text (about Codex token waste / ChatGPT brainstorm then Codex exec), date `2026年9月2日`, and a thumbnail. It does **not** return the spoken video body. Raw curl of the same URL often returns the SPA shell only. Recipe: WebFetch → `body_kind: caption`, `fetch_method: webfetch`. Spoken understanding still requires user media + `asr_local.py`.

`channels.weixin.qq.com` feed paths remain blocked (`errCode 10012`) for remote deep-read. No login bypass.

- **Result:** normalize pass for sph share links; caption WebFetch is metadata only (v0.4.0). Speech and graphics still need a local file. A caption is not Understanding.

### 8. Addendum (2026-10-26, v0.4.0) — Douyin in-app wall

Video **7696098282904259850**, share `https://v.douyin.com/2qulGbSTiRI`.

Public redirect chain measured from this environment (browser UA, no cookies, no login bypass):

1. `https://v.douyin.com/2qulGbSTiRI` → 302
2. `https://www.iesdouyin.com/share/video/7696098282904259850/...` → 302
3. `https://www.douyin.com/video/7696098282904259850?previous_page=app_code_link`

The final body is a JavaScript shell (about 73KB). It is not a media file and not a transcript. The raw shell does not contain the spoken or visual body. The client-rendered share page for this video shows **「请尝试在抖音内观看」** (in-app watch wall). Web playback is not available from this fetch.

That curl is not the player. iesdouyin share pages often show **「请尝试在抖音内观看」**. Do not treat this shell as proof the video cannot be acquired, and do not treat a caption as Understanding.

No captcha solve, cookie dump, CDN decrypt, or private API call was attempted on this curl.

- **Result:** iesdouyin/datacenter curl has no media file. See §9 for the player that worked.

### 9. Addendum (2026-10-26, v0.4.0) — Douyin mobile share player

Same video: `https://v.douyin.com/2qulGbSTiRI/` → aweme **7696098282904259850**.

Measured on **Mac** (not this datacenter curl):

1. Playwright Chromium, mobile user agent.
2. Open `https://www.douyin.com/` so that browser receives cookies.
3. Open `https://m.douyin.com/share/video/7696098282904259850`.
4. `<video>.src` / `currentSrc` is `https://m.douyin.com/aweme/v1/playwm/?…&video_id=v0…`.
5. GET that playwm URL with the same browser context and `Referer` set to the share page. It follows to a CDN response `video/mp4`.

Saved file: about **8MB**, **1280×720**, H.264 + AAC, about **49 seconds**. The same helper re-downloaded this aweme from the short link on Anthony’s Mac.

Next step is the media pipeline (`extract_frames.py`, `ocr_frames.py`, `asr_local.py`, host vision / watch the file). The share caption is not the body.

Helper: `skills/social-content-reader/scripts/acquire_douyin.py`. Positional URL or aweme id plus `--out-dir`. It writes `{out-dir}/douyin_{aweme_id}.mp4` and prints JSON `ok`, `path`, `bytes`, `content_type`, `aweme_id`, `play_url`. It does not ask the user to export first. If the mobile share page has no `<video>` src, `ok` is false. `body_snip` is a page excerpt, not Understanding. A download under 20KB is `download too small`.

- **Result:** automatic playwm acquire worked repeatedly for this aweme on Mac, 2026-10-26. iesdouyin curl remains a non-player.

### 10. Addendum (2026-10-26, v0.4.0) — Mac file-acquire matrix

Measured on Anthony’s Mac, same day. Document only what saved a file.

| Platform | What happened | Claim |
| --- | --- | --- |
| Douyin `https://v.douyin.com/2qulGbSTiRI/` → `7696098282904259850` | `acquire_douyin.py` saved ~8MB mp4, more than once | Auto-acquire works. Understanding still needs frames, OCR, vision, and speech. |
| YouTube | `yt-dlp` saved a file | File acquire works. The file is not Understanding by itself. No specific video id was recorded in this note. |
| TikTok | `yt-dlp` for the sample tried was IP-blocked from that network | Not a verified file recipe. Do not document `yt-dlp` as the TikTok path until a sample saves a file. |
| Bilibili | `yt-dlp` returned HTTP 412. Public playurl did not save a file | Not a verified file recipe. Uploader CC remains a speech path when the subtitle API returns cues. Graphics still need a file. |

- **Result:** Douyin and YouTube file acquire are the verified rows. TikTok and Bilibili stay open. Caption and `desc` are still not the video.

## Honesty notes

- No captcha solving, cookie dumps, or login bypass.
- Instagram oEmbed used only to confirm embed-preview capability; skill must still refuse “what are they saying in the Reel?” without user transcript.
- 公众号 success via WebFetch does not imply every article works from every IP.

## Follow-ups (optional, not blockers for v0 publish)

- Harden 公众号 recipe with structured `ok | captcha_required | rate_limited` statuses
- Add X thread-walk recipe test
- Document IG oEmbed response shape (no caption field in v26 tokenless response observed tonight)
