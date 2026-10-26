# Telegram (public posts)

**Status:** Partial — public channel posts via `t.me/s/` preview pages; private chats/channels unavailable without user export.

## URL patterns

- Public channel post: `https://t.me/{channel}/{message_id}`
- Preview form: `https://t.me/s/{channel}/{message_id}`
- Invite links (`t.me/+…`, `joinchat`) → **not** publicly readable

## Prefer (in order)

1. **Host Telegram connector / Bot API** if the bot is already a member and authorized.
2. **Public preview page** `https://t.me/s/{channel}/{id}` via WebFetch/curl — extract the post text from the preview HTML when the channel is public.
3. User forward/export/paste of the message text.
4. Voice/video notes: user-exported media + ASR.

## Fetch recipe

1. If URL is `/s/` missing, try constructing `https://t.me/s/{channel}/{id}` for public channels only.
2. Fetch preview; parse visible message text; set `body_kind: post_text`, `fetch_method: public_webfetch`.
3. If preview requires join/login or returns empty, stop — ask for paste or bot access.
4. Understanding from message text; media needs separate path.

## Honest limits

- Private channels, groups, and DMs: **no** public fetch. Use user export or an authorized bot already inside.
- Do not scrape Telegram private APIs or steal `tdata` / session files.
- Bot API requires a bot token in env (`TELEGRAM_BOT_TOKEN`) — never commit it.

## Codex prompt sketch

```text
Follow platforms/telegram.md. URL: <URL>
Try t.me/s/ preview for public channels only. Else ask for paste.
```

## References

- Telegram Bot API
- Public channel preview pages (`t.me/s/…`)
