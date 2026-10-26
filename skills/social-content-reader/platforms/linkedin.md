# LinkedIn

**Status:** Partial — public post text sometimes available; most deep content needs user paste or authorized API.

## URL patterns

- `https://www.linkedin.com/posts/{slug}`
- `https://www.linkedin.com/feed/update/urn:li:activity:{id}`
- `https://www.linkedin.com/pulse/{slug}` (articles)

## Prefer (in order)

1. **Host LinkedIn connector** with user-authorized OAuth (Marketing / Community Management APIs as licensed).
2. **User paste** of the post or article (most reliable for agents without OAuth).
3. **WebFetch** of a *public* post/article URL — only use visible text if the page returns it without login. Many posts redirect to login → stop and ask for paste.
4. Pulse articles: try public WebFetch; if paywall/login, ask for export/paste.
5. Video posts: user media + ASR.

## Fetch recipe

1. Detect posts vs Pulse articles.
2. Try connector → public page → user paste.
3. Set `body_kind: post_text` or `article`; `fetch_method` accordingly.
4. Never claim understanding from an Open Graph title card alone.

## Honest limits

- LinkedIn aggressively login-walls content. Honest default: **ask the user to paste**.
- No cookie theft, session hijacking, or unofficial scrapers.
- Official APIs require app review and member authorization — document env names only (`LINKEDIN_ACCESS_TOKEN`), do not commit secrets.

## Codex prompt sketch

```text
Follow platforms/linkedin.md. URL: <URL>
If login-walled, return unavailable + ask for paste. Do not bypass auth.
```

## References

- LinkedIn Developer docs (Posts / Articles APIs)
