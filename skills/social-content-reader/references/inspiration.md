# Inspiration & references (not plagiarism)

This skill’s *ideas* draw from public docs and open projects. Do not copy their code verbatim into this repo without respecting their licenses; link instead.

## Agent Skills format

- https://agentskills.io/specification
- https://agentskills.io/skill-creation/quickstart
- https://cursor.com/docs/skills

## YouTube transcripts for agents

- YouTube Data API (metadata only): https://developers.google.com/youtube/v3
- Open MCP / transcript services discussed in public blogs (Captapi, YTAPI, opspresso/mcp-youtube) — prefer whatever connector the host already has.

## X

- Public embed/oEmbed via `publish.x.com/oembed` (single public posts; truncation possible)
- Official X API Post lookup when the user has developer credentials

## Instagram

- Meta Instagram oEmbed: https://developers.facebook.com/docs/instagram-platform/oembed/
- Tokenless Meta oEmbed announcement (2026-06-15): embed use only; not a content-analytics API

## WeChat

- Public 公众号 URL realities (`mp.weixin.qq.com/s/...`); captcha walls on long links
- Open-source WeChat article helpers (examples to evaluate, not vendored here): wechat-reader, weixin-articles-mcp, wechat-article-fetcher
- 视频号: official 视频号助手 APIs are creator/merchant scoped — https://developers.weixin.qq.com/doc/channels/api/

## Host connectors (when present, prefer them)

- YouTube research MCP tools already attached to the agent
- X public-read MCP / plugin tools already attached to the agent
