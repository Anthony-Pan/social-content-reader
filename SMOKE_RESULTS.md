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
| WeChat 视频号 | ⚠️ partial | sph WebFetch caption; `channels.weixin.qq.com` feed blocked | Feed path `errCode 10012` (no transcript). Sph share `…/sph/AAZ3p39sQm` WebFetch returns caption/date/thumbnail, not speech — addendum §7 |

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

- **Result:** normalize pass for sph share links; caption WebFetch partial; speech still user-media ASR

## Honesty notes

- No captcha solving, cookie dumps, or login bypass.
- Instagram oEmbed used only to confirm embed-preview capability; skill must still refuse “what are they saying in the Reel?” without user transcript.
- 公众号 success via WebFetch does not imply every article works from every IP.

## Follow-ups (optional, not blockers for v0 publish)

- Harden 公众号 recipe with structured `ok | captcha_required | rate_limited` statuses
- Add X thread-walk recipe test
- Document IG oEmbed response shape (no caption field in v26 tokenless response observed tonight)
