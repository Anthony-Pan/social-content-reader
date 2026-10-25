# Instagram

**Status:** ⚠️ Partial for embed metadata · ❌ Blocked for deep “what is this Reel about” without user help

**Goal:** Be honest. Captions ≠ spoken Reel content. oEmbed ≠ analytics corpus.

## URL patterns

- `https://www.instagram.com/p/{code}/`
- `https://www.instagram.com/reel/{code}/`
- `https://www.instagram.com/reels/{code}/`
- `https://www.instagram.com/tv/{code}/`

## Prefer (in order)

1. **User paste** of caption + their own transcript / description of the Reel.
2. **Instagram oEmbed** (tokenless as of Meta’s June 2026 change) for **embed HTML / basic preview metadata only**:  
   `GET https://graph.facebook.com/v26.0/instagram_oembed?url=<post url>`  
   Allowed use per Meta: provide a **front-end view** of the post. Meta prohibits consuming/extracting/persisting metadata for analytics or other non-embed purposes — agents must not treat oEmbed as a full content-intelligence API.
3. **Instagram Graph API** only for accounts the user owns / authorized (Business/Creator) — not arbitrary public scraping.
4. For spoken Reel audio: user-provided media + ASR they approve — never login-bypass downloaders.

## Fetch recipe

1. Detect post vs reel vs story (Stories: unsupported).
2. If user only needs “is this link valid / embeddable?”, oEmbed may suffice — label `body_kind: caption_only` or `unavailable` for speech.
3. If user asks “what are they saying in the Reel?”, and you only have a caption or oEmbed HTML: **say you cannot hear the video**. Ask for paste or authorized export.
4. Never claim OCR/ASR results you did not run on user-authorized media.

## Honest limits

- Private, inactive, age-restricted, embed-disabled accounts: unsupported.
- Stories: unsupported.
- oEmbed rate limits (tokenless ~1000/hour per Meta docs; higher with approved token access).
- No legitimate general-purpose “read any Instagram Reel transcript” public API for third-party agents as of this skill’s research window (2026-10).
- Do not ship credential stuffing, session hijack, or unofficial private APIs in this skill.

## Codex prompt sketch

```text
Follow platforms/instagram.md. URL: <URL>
If understanding spoken content is required and no user transcript exists, return blocked + ask user to paste. Do not scrape behind login.
```
