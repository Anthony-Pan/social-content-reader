# v0.5.0 acquisition matrix — Mac, 2026-10-26

> **Also see the [v0.5.1 公众号 addendum](#v051-addendum--wechat-公众号-harden-box-2026-10-26-asiashanghai), the [v0.5.2 Reddit post-URL addendum](#v052-addendum--reddit-post-url--media-box-2026-10-29), the [v0.5.3 Twitch addendum](#v053-addendum--twitch-clip-and-bounded-vod-box-2026-10-29), and the [v0.5.4 Understanding addendum](#v054-addendum--local-file-understanding-box-2026-10-29) below.** The table in this section is the v0.5.0 Mac matrix. Its Reddit row is the direct CDN sample. Post-URL behavior is the later addendum. The Twitch row is the clip file; VOD limits are the v0.5.3 addendum.

**Fresh live results (v0.5.0 Mac):** 13 saved video files across 15 video
platforms; 小红书 and 视频号 did not yield media. 公众号 is an article
platform: its then-current article fetch hit verification and embedded video
was not acquired. Reddit's v0.5.0 pass starts from a known public CDN id.
**v0.5.2** (box) resolves sampled post URLs via the public embed when `www`
listing JSON is HTTP 403; that does not make every Reddit URL work. This
remains a partial all-platform goal, not 16 working fetches.

Proof root: `~/Developer/scr-proof/matrix-2026-10-26/` (including exploratory
artifacts). `matrix.json` and each platform's `PASS.json` or `FAIL.txt` identify
the authoritative outcome. `POST-RESOLUTION-FAIL.txt` preserves Reddit's wall.
The Bilibili `REJECTED-error-placeholder.mp4` is deliberately excluded from
success; exploratory `player-*` downloads and failed raw tracks are not the
counted media. Every counted file has a SHA-256 receipt, ffprobe stream/duration
validation, a decoded proof frame and a full FFmpeg decode with exit 0 and no
error output. The file names below select the actual evidence.

Environment: macOS arm64, Python 3.15.1, Playwright 1.64.1 / Chromium 156,
FFmpeg/ffprobe 9.0.2, yt-dlp 2026.10.21. Browser work used a new venv under
`~/Developer/scr-proof/acquire-venv/`; the pre-existing `.venv-asr/` was preserved.
No user profile cookies, captcha defeat, private API clients or CDN decrypt.
No ASR/Understanding was claimed in this acquisition matrix.

| Platform | Actual source / method | Saved file | Bytes | Seconds | Audio | Remaining wall |
| --- | --- | --- | ---: | ---: | --- | --- |
| youtube | [watch](https://www.youtube.com/watch?v=jNQXAC9IVRw); yt_dlp | `youtube/youtube_488c5108c18e9ac4.mp4` | 475989 | 19.014 | yes | Public sample only; gated/deleted URLs can still fail. |
| x | [1577855540407197696](https://x.com/oshtru/status/1577855540407197696); yt_dlp_syndication | `x/x_8500828fc95e473b.mp4` | 893919 | 30.036875 | yes | Public sample only; gated/deleted URLs can still fail. |
| instagram | [](https://www.instagram.com/reel/Chunk8-jurw/); public_page_media | `instagram/instagram_7a956bbb30f3fa04.mp4` | 918120 | 4.966667 | no | Source reports has_audio=false; visual evidence only. |
| tiktok | [6718335390845095173](https://www.tiktok.com/@scout2015/video/6718335390845095173); public_page_media | `tiktok/tiktok_d2899f4428fa4c46.mp4` | 2953029 | 10.495011 | yes | Old yt-dlp IP wall bypass not attempted; official player worked. Alternate 7206382937372134662 unavailable. |
| threads | [DeMqtuYgkaL](https://www.threads.com/@nasa/post/DeMqtuYgkaL); public_page_media | `threads/threads_8f063507f698a30d.mp4` | 11169291 | 89.470708 | yes | Public sample only; gated/deleted URLs can still fail. |
| reddit | [gyh95hiqc0b11](https://v.redd.it/gyh95hiqc0b11); yt_dlp | `reddit/reddit_5dcd184489f41800.mp4` | 7478923 | 13.7 | no | v0.5.0 Mac used a known CDN id (post page blocked). v0.5.2 resolves the post URL when `embed.reddit.com` is public; `www` JSON can still be HTTP 403. See addendum. |
| linkedin | [the-mathworks_2_what-is-mathworks-cloud-center-activity-7151241570371948544-4Gu7](https://www.linkedin.com/posts/the-mathworks_2_what-is-mathworks-cloud-center-activity-7151241570371948544-4Gu7); public_page_media | `linkedin/linkedin_496e0813b1cc2178.mp4` | 5316468 | 161.866009 | yes | Public sample only; gated/deleted URLs can still fail. |
| facebook | [1195289147628387](https://www.facebook.com/reel/1195289147628387); public_page_media | `facebook/facebook_cc12fd22535bfa0d.mp4` | 622802 | 9.566667 | no | Target DASH manifest has video representations only; visual evidence only. |
| telegram | [402](https://t.me/telegram/402); public_page_media | `telegram/telegram_2604a7144d849a8e.mp4` | 1408169 | 8.0 | yes | Public sample only; gated/deleted URLs can still fail. |
| vimeo | [22439234](https://vimeo.com/22439234); yt_dlp | `vimeo/vimeo_b7b62529f65a3d07.mp4` | 20561134 | 185.877333 | yes | 76979871 login/DRM rejected; alternate 22439234 saved. |
| twitch | [FaintLightGullWholeWheat](https://clips.twitch.tv/FaintLightGullWholeWheat); public_page_media on Mac, `twitch_ytdlp_public` on the v0.5.3 box (same SHA-256) | `twitch/twitch_9d3021eae0ac932a.mp4` | 16299328 | 32.099 | yes | Clip matches v0.5.0. A VOD longer than 600s is refused unless `--section` names a window that fits `--max-mb`. See the v0.5.3 addendum. |
| douyin | [7696098282904259850](https://www.douyin.com/video/7696098282904259850); douyin_mobile_player | `douyin/douyin_2d5c9591cdc9468a.mp4` | 8382047 | 48.833333 | yes | Public sample only; gated/deleted URLs can still fail. |
| bilibili | [BV17x411w7KC](https://www.bilibili.com/video/BV17x411w7KC); browser_media_tracks | `bilibili/bilibili_ee02d4fb68da3725.mp4` | 6445696 | 199.319433 | yes | Main/view API HTTP 412. External player works for valid sample. error.mp4 for BV1GJ411x7h7 rejected. |
| xiaohongshu | [6411cf99000000001300b6d9](https://www.xiaohongshu.com/explore/6411cf99000000001300b6d9); public page attempt | **FAIL** | — | — | — | Two public notes returned IP-risk 300031/300012; stopped. |
| wechat-channels | [AAZ3p39sQm](https://weixin.qq.com/sph/AAZ3p39sQm); public page attempt | **FAIL** | — | — | — | sph page has caption/QR but no video; no compliant public auto-acquire established. |
| wechat-article | [Rsa54LdbyhXIHheJYO6gkw](https://mp.weixin.qq.com/s/Rsa54LdbyhXIHheJYO6gkw); Chrome UA HTTPS body (v0.5.1) | **BODY OK** (article) | — | — | — | v0.5.0 bare-UA verification FAIL superseded by v0.5.1 Chrome UA body. Embeds: see Anm addendum. |

## What changed the hard-wall outcomes

- TikTok: [its documented embed player](https://developers.tiktok.com/docs/en/embed-player)
  `/player/v1/6718335390845095173?autoplay=1` exposed a real video src;
  same-context GET saved 2,953,029 bytes. No TikTok yt-dlp challenge/app API path
  was used in this run.
- Bilibili: main/view API 412 did not describe the public external player.
  For BV17x411w7KC the external player played normally. Its unencrypted .m4s
  responses were fetched with the observed Origin/Referer/User-Agent and
  `Range: bytes=0-`. Complete Content-Range/body coverage was required, then
  AV1+AAC tracks were muxed locally (6,445,696 bytes, 199.319433 seconds). A
  final canonical-player recheck with `--wait-seconds 12` saved the identical
  SHA-256 again. Multipart parts after 1 remain unverified and are rejected
  rather than silently substituted. A simple GET with different request headers returned 567, and a different
  sample played the site's 17-second error.mp4; neither counts as success.
- Meta: public HTML carries matching post codes/ids and progressive media
  URLs. Instagram/Threads match `code` plus `video_versions`; Facebook matches
  numeric video id plus browser-native URL. Unrelated recommendations are
  excluded. Instagram's source reports no audio; the selected Facebook source
  manifest has no audio representation. No claim of acquired speech is made.
- Telegram: the [public post widget](https://core.telegram.org/widgets/post)
  isolates message 402. The `/s/` preview returns nearby messages; downloading
  its first video would give the wrong post.
- X: yt-dlp explicitly selects public syndication rather than its private
  GraphQL path. LinkedIn reads public video `data-sources`. Twitch on this Mac
  read the public clip's video src. v0.5.3 saves that same clip with public
  yt-dlp and uses the same downloader for a bounded VOD section. Vimeo uses
  its public embedded player.

## Remaining walls / researched routes

- 小红书: explore/6411cf99000000001300b6d9 and
  discovery/item/674051740000000007027a15 (with supplied xsec_token) both
  returned `安全限制 / IP存在风险`, codes `300031/300012`. No signatures, app
  APIs, cookie extraction, IP switching or captcha workarounds were attempted.
- 视频号: sph/AAZ3p39sQm rendered public caption/date and a QR prompt, no
  video element. Native WeChat availability was inspected, but no reproducible
  public-link-to-file path was established; no messages or exports were sent.
  Creator assistant is an authorized-account avenue, not a verified arbitrary
  video API here. [wx-downloader](https://github.com/QinGeneral/wx-downloader)
  and [WechatVideoDL](https://github.com/topgptus/WechatVideoDL) were researched,
  not executed: their Yuanbao/cookie clients are outside a documented public
  player route. Interception/private API replay/CDN decryption are excluded.
- Reddit (v0.5.0 Mac): post URL, JSON via yt-dlp, and redditmedia embed were
  blocked. The media id `gyh95hiqc0b11` is mapped to post `90bu6w` by the
  [public yt-dlp test fixture](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/reddit.py).
  Its public DASH manifest saved a video-only file. That CDN pass alone was
  not a post resolver. **v0.5.2** resolves the post URL on a network where
  `embed.reddit.com` is reachable; see the addendum. `www` listing JSON can
  still be HTTP 403.
- 公众号: current curl of /s/Rsa54LdbyhXIHheJYO6gkw returned `环境异常 /
  当前环境异常，完成验证后即可继续访问`, not `#js_content`. A host web open also
  failed. Historical body-reading results below remain historical.
- Twitch's [official clips download API](https://dev.twitch.tv/docs/api/reference/#get-clips-download)
  is an additional authorized broadcaster/editor route, researched but not
  executed without scoped tokens. **v0.5.3** acquires public clips and a VOD
  or `--section` of at most 600 seconds with uncredentialed yt-dlp. A longer
  VOD is refused. See the addendum.

## Validation and replay

`python3 -B -m unittest discover -s skills/social-content-reader/scripts/tests -q`
passed **55 tests** on this Mac, including acquisition provenance, placeholder
rejection, complete ranges, failure cleanup, no-cookie downloader options, and
the media-first doc contract. All 13 counted files also decoded completely.

```bash
# Explicit network replay of one sample, using the acquire venv:
~/Developer/scr-proof/acquire-venv/bin/python -B skills/social-content-reader/scripts/smoke_acquire.py --platform tiktok --proof-dir ~/Developer/scr-proof/recheck
# --all opts into all 16 sample attempts (公众号 is an embedded video probe).
```

Receipts committed without media or signed CDN URLs:
[`acquire-matrix-2026-10-26.json`](skills/social-content-reader/references/acquire-matrix-2026-10-26.json).

---

# Historical smoke results (v0.4.0 and earlier; not current acquisition claims)

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

---

# v0.5.1 addendum — WeChat 公众号 harden (box, 2026-10-26 Asia/Shanghai)

Helper: `skills/social-content-reader/scripts/fetch_wechat_article.py` (stdlib
HTTPS, fixed Chrome desktop UA, no cookies/profiles). Wired through
`acquire_media.py` for `mp.weixin.qq.com` (article body may succeed without
ffmpeg).

Proof: `/workspace/scr-proof/wechat-gzh-2026-10-26/`.

| Sample | Result | Notes |
| --- | --- | --- |
| [Rsa54Ld…](https://mp.weixin.qq.com/s/Rsa54LdbyhXIHheJYO6gkw) | **BODY OK** | Title 一个错误，让我客户痛苦失去200万; substantive `#js_content` (~1500+ chars); SSR `visibility:hidden;opacity:0` accepted. No embeds. |
| [aNmLs3…](https://mp.weixin.qq.com/s/aNmLs3qJVhFGcgtGxAVlig) | **BODY OK** + embeds listed | Title 这，才是下一个5年的工作操作系统; 3 mpvideo vids `wxv_4683490097843765252`, `wxv_4683473112590647297`, `wxv_4683357298663309319`. |
| Anm first embed public player | **MEDIA FAIL** (this box) | Player UI: 「当前视频不存在，暂无法观看」; `get_mp_video_play_url` returns empty. Mac earlier saved one ~2.8MB public embed mp4 — not reproduced here. Article still OK. |
| [sph AAZ3…](https://weixin.qq.com/sph/AAZ3p39sQm) 视频号 | **FAIL** (unchanged) | No public media URL; QR/app-only. |

Hard rules unchanged: no captcha defeat, IP rotation, stolen cookies, private
APIs, or CDN decrypt. Captions remain metadata; Understanding needs a real
media file for video.

---

# v0.5.2 addendum — Reddit post URL → media (box, 2026-10-29)

Helper: `skills/social-content-reader/scripts/resolve_reddit.py`, called from
`acquire_media.py` for a Reddit post URL (no media id yet). Fixed browser
User-Agent, no cookie jar. `www.reddit.com` and `old.reddit.com` post HTML and
`.json` were **HTTP 403 Blocked**. `embed.reddit.com` for the same path
returned the post's `shreddit-player` or, for a crosspost, that post's
screenview `v.redd.it` URL. Signed player queries were dropped. yt-dlp
downloaded unsigned `DASHPlaylist.mpd` with `--ignore-config`. ffprobe required
a positive duration and a video stream. `ffmpeg -f null` decode exit 0 on each
saved file. Media files were not committed.

Receipts: [`reddit-post-2026-10-29.json`](skills/social-content-reader/references/reddit-post-2026-10-29.json).

| Sample | Result | Notes |
| --- | --- | --- |
| [/r/aww/comments/90bu6w/](https://www.reddit.com/r/aww/comments/90bu6w/heat_index_was_110_degrees_so_we_offered_him_a/) | **FILE OK** | `reddit_post_embed` → `gyh95hiqc0b11`. 7,478,923 bytes, 13.7s, h264, `has_audio: false`. SHA-256 `5dcd184489f41800edfafd60dbab966226cbc262421cf92c8385f271aaf84e97`, the same file as the v0.5.0 direct CDN sample. |
| [/r/videos/comments/6rrwyj/](https://www.reddit.com/r/videos/comments/6rrwyj/that_small_heart_attack/) | **FILE OK** | `zv89llsvexdz`. 3,733,550 bytes, 11.797s, h264+aac, `has_audio: true`. |
| [/r/dumbfuckers_club/comments/zjjw82/](https://www.reddit.com/r/dumbfuckers_club/comments/zjjw82/cringe/) | **FILE OK** (crosspost) | `a1oneun6pa5a1`, `reddit_kind: crosspost`. 1,867,580 bytes, 16.063s, h264+aac. |
| [/r/KamenRider/comments/wzqkxp/](https://www.reddit.com/r/KamenRider/comments/wzqkxp/finale_kamen_rider_revice_episode_50_family_to/) | **FAIL** | Two inline hosted videos; refused to choose one. No file. |
| [redd.it/90bu6w](https://redd.it/90bu6w) | **FAIL** | Short-link redirect HTTP 403. Media id not invented. |
| [/comments/90bu6w](https://www.reddit.com/comments/90bu6w) | **FAIL** | Listing JSON blocked and the embed shell did not include the post. |
| `www` `/r/aww/s/…` | **FAIL** | Share redirect HTTP 403 on this box. A redirect that reaches a comments URL is covered by a unit test, not by this live code. |

Gallery JSON (one video beside an image; two videos refused) is an offline
fixture. This box never received listing JSON, so a gallery page was not saved
as its own sample. Quarantine / private / gated reasons stop without an opt-in
cookie. oEmbed on a full post URL returned title and author only; that was not
used as the file or as `body_text`.

This does not mean every Reddit URL works, and it is not Understanding.

---

# v0.5.3 addendum — Twitch clip and bounded VOD (box, 2026-10-29)

Helper: `skills/social-content-reader/scripts/acquire_twitch.py`, called from
`acquire_media.py` for a Twitch clip or `/videos/{id}` URL. yt-dlp 2026.10.26
with `--ignore-config`. No cookies, netrc, or Helix token. ffmpeg 6.1.1.
Success required ffprobe (positive duration and a video stream) and
`ffmpeg -f null` exit 0. Media files were not committed. A window longer
than 600 seconds is refused and is not saved as a prefix.

Receipts: [`twitch-vod-2026-10-29.json`](skills/social-content-reader/references/twitch-vod-2026-10-29.json).

| Sample | Result | Notes |
| --- | --- | --- |
| [clip FaintLightGullWholeWheat](https://clips.twitch.tv/FaintLightGullWholeWheat) | **FILE OK** | `twitch_ytdlp_public`, full clip, 1080p. 16,299,328 bytes, 32.099s, h264+aac. SHA-256 `9d3021eae0ac932a520b5ebedf995ec14901d882d97b27eeccbbb5b9440a4317`, the same file as the v0.5.0 public-player sample. |
| [VOD 2128758214](https://www.twitch.tv/videos/2128758214) | **FILE OK** with `--max-mb 400` | 402s highlight, source 1080p only. 256,357,852 bytes, 401.932s, aac+h264, `twitch_full: true`. |
| Same VOD, default `--max-mb 128` | **FAIL** before download | Estimate 361,800,000 bytes at 1080p. No file. |
| Same VOD `--section 10-25` | **FILE OK** | 11,068,048 bytes, 15.134s, 1080p. `twitch_source_duration_sec` stays 402. |
| [VOD 2096474672](https://www.twitch.tv/videos/2096474672) | **FAIL** | 15434s (4:17:14). Refused. No prefix. |
| Same VOD `--section 0-20` | **FILE OK** | 3,407,834 bytes, 20.025s, 480p, h264+aac. |
| Same VOD `--section 1:00:00-1:00:20` | **FILE OK** | 3,557,056 bytes, 20.019s, 480p. Not the opening of the VOD. |
| Same VOD `?t=1h2m3s` | **FAIL** | Bookmark 3723s ignored. Still over 600s. |
| Same VOD `--section 0-601` | **FAIL** | Over 600s. Nothing downloaded. |
| `/videos/1` | **FAIL** | Does not exist. |
| `twitch.tv/twitch` | **FAIL** | Channel/live URL. Not recorded. |

Subscriber-only VODs were not live-sampled. A login or subscription error
stops; there is no cookie fallback. This does not mean every Twitch URL
works, a section is not the whole VOD, and none of this is Understanding.

---

# v0.5.4 addendum — local-file Understanding (box, 2026-10-29)

Helper: `skills/social-content-reader/scripts/understand_media.py`. No
download, cookie, or API upload. ffmpeg 6.1.1, ffprobe, tesseract 5.3.4
(`eng`; `chi_sim` not installed). `faster-whisper` and `openai-whisper` are
not installed. No acquired platform sample from the v0.5.0 matrix was on
this disk (`~/Developer/scr-proof` is not this box), so this smoke uses a
one-second generated file, not a YouTube/Twitch/Douyin sample.

```bash
ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=10 \
  -f lavfi -i sine=frequency=440:duration=1 \
  -map 0:v -map 1:a -shortest -pix_fmt yuv420p /tmp/scr-understand-smoke/sample.mp4
python3 -B skills/social-content-reader/scripts/understand_media.py \
  --media /tmp/scr-understand-smoke/sample.mp4 \
  --out-dir /tmp/scr-understand-smoke/out --max-frames 4 --fps 1 \
  --caption "CAPTION_SENTINEL_share_text" --title "TITLE_SENTINEL_upload_name"
```

| Check | Result |
| --- | --- |
| ffprobe | duration 1.0s, h264 + aac, `has_video` and `has_audio` true. SHA-256 `3af5ba4c56ba7cb91e66bfcb850ea683c75fa53ec4925990b5ca1757506bcef1`. |
| Frames | 1 JPEG. The frame is a color-bar circle, a rainbow stripe, and a white numeral 0. |
| OCR | `ocr_engine: tesseract`, language `eng`, text `[0.00s] On`. That fragment does not match the numeral. It was kept as OCR output, not corrected into a story. |
| ASR | `asr_engine: none`, reason `engine_missing`. `speech_text` empty. No model download and no API call. |
| Caption / title | Stored on `caption` and `title`. Absent from `body_text`, `speech_text`, `visual_text`, and `visual_description`. |
| First pass, no vision notes | `ok: true`, `complete: false`, `blocked: false`, `body_kind: visual`, `fetch_method: media_pipeline`. Understanding says pictures only and `ASR engine: none`. |
| Second pass | `--frames-json` reused the same frames (`reason: reused`). Host notes described the color bars and the numeral 0 after looking at `frame_0001.jpg`. `visual_description` is those notes. `complete` stays false because speech was not read. |

`body_text` on the second pass is the picture notes plus the OCR line. It does
not contain the caption sentinel. The media file was not committed.

A machine without tesseract and without a Whisper package gets `ocr_engine:
none`, `asr_engine: none`, `blocked: true`, and an understanding that does
not quote the caption. That path is the unit test
`test_missing_engines_are_none_and_caption_is_not_the_body`, and it is what
GitHub Actions will hit until those packages are installed. CI installs
ffmpeg only.


