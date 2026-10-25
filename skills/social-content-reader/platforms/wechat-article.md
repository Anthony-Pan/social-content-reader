# WeChat 公众号 articles

**Status:** ⚠️ Partial (public articles; captcha / UA walls common)

**Goal:** Read the **article body**, not only the title card.

## URL patterns

- Short (preferred): `https://mp.weixin.qq.com/s/<id>`
- Long: `https://mp.weixin.qq.com/s?__biz=...&mid=...&idx=...&sn=...` (often triggers verification)

## Prefer (in order)

1. **Dedicated WeChat-article MCP / CLI** the user already trusts (examples that exist in the open ecosystem — cite, don’t vendorsecretly fork): browser-session readers, `wxfetch`-style public fetchers, Playwright cleaners. Prefer tools that return structured `ok | captcha_required | rate_limited` instead of silent empty HTML.
2. **Codex on Windows** with a local browser the user can unlock if captcha appears — agent should **request user action**, not solve captchas automatically.
3. **User paste / Save-as-HTML**: user opens the article on their phone/PC, pastes Markdown, or saves HTML for local parse.
4. Plain `curl`/`WebFetch` from a datacenter IP: frequently returns blank or verification pages — treat failure as expected, not as “article empty”.

## Fetch recipe

1. Prefer short `/s/<id>` links. If only a long `__biz=` link exists, warn that verification is likely.
2. Fetch via chosen tool; require real body text under the title.
3. Normalize: title, account name, publish time (Asia/Shanghai when present), Markdown body, image list (URLs only unless user asked to download).
4. `body_kind: article`. Summarize arguments from the body.
5. On `captcha_required`: stop and tell the user which URL to open.

## Honest limits

- Login-only, paywalled, fan-only, deleted, or violation-takedown articles: unavailable — do not bypass.
- Heavy JS widgets / 视频号 cards inside articles may not appear in static HTML.
- Rate-limit politely (human reading pace). No flood scraping.
- Respect copyright; personal/research use framing; no redistribution pipeline in this skill.

## Codex prompt sketch

```text
Follow platforms/wechat-article.md. URL: <URL>
Fetch public article body if possible. If captcha/verification, return status captcha_required and instructions for the user. Summarize from body only.
```
