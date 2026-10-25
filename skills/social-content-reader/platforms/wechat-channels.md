# WeChat 视频号 (Channels)

**Status:** ❌ Blocked for general third-party agents

**Goal:** Do not pretend arbitrary 视频号 videos are readable. Document reality.

## URL patterns

- `channels.weixin.qq.com` share links
- In-app 视频号 shares (often not useful outside WeChat)

## What exists officially

WeChat documents **视频号助手** server APIs for **authorized creators / merchants** (access_token, showcase, leads, livestream data, etc.). These are **not** a public consumer API to fetch any channel’s video bytes or transcripts.

There is **no** honest, general-purpose “paste any 视频号 link → full transcript” path comparable to YouTube captions for third-party agents.

## Prefer (in order)

1. **User paste**: transcript, on-screen text, or summary they typed.
2. **Creator-owned APIs** if the user owns the channel and has 视频号助手 credentials (out of band; never store secrets in this repo).
3. If the video is also published on YouTube / X, use those platform recipes instead.
4. Otherwise: **blocked** — explain and stop.

## Fetch recipe

1. Detect 视频号 URL / mention.
2. Immediately set `fetch_method: blocked`, `body_kind: unavailable`.
3. Ask the user for: pasted text, export, or another platform mirror.
4. Do **not** document login bypass, reverse-engineering of encrypted media streams, or unofficial downloaders.

## Honest limits

- No public oEmbed-style consumer read for arbitrary channel posts (as of skill research, 2026-10).
- Official APIs require AppID/AppSecret, capability enablement, often IP allowlists — and cover operator analytics/commerce, not “read this viral video’s speech for my homework agent.”
- Embedded 视频号 cards inside 公众号 articles usually won’t yield playable/transcript content to agents.

## Codex prompt sketch

```text
Follow platforms/wechat-channels.md. URL: <URL>
Return blocked ContentRecord + clear user ask (paste transcript or provide mirror URL). No scrape/bypass attempts.
```
