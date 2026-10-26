# Telegram (public posts)

**Status:** Partial — public channel posts via `t.me/s/` preview pages. Video and voice notes need a file. Private chats/channels are unavailable without a user export.

## URL patterns

- Public channel post: `https://t.me/{channel}/{message_id}`
- Preview form: `https://t.me/s/{channel}/{message_id}`
- Invite links (`t.me/+…`, `joinchat`) → **not** publicly readable

## Video and graphics

Preview text is the message (`body_kind: post_text`). A video file follows [_video-body.md](_video-body.md) (frames, OCR, host vision, ASR). A voice note is speech-only: `asr_local.py`, `body_kind: transcript`, and a limit that there is no picture. The message caption is not the video. If the file cannot be acquired, say so.

## Prefer (in order)

1. **Host Telegram connector / Bot API** if the bot is already a member and authorized.
2. **Public preview page** `https://t.me/s/{channel}/{id}` via WebFetch/curl — extract the post text from the preview HTML when the channel is public.
3. User forward/export/paste of the message text.
4. Voice notes: user-exported audio + ASR (speech only). Video: user-exported file + the [media pipeline](_video-body.md).

## Fetch recipe

1. If URL is `/s/` missing, try constructing `https://t.me/s/{channel}/{id}` for public channels only.
2. Fetch preview; parse visible message text; set `body_kind: post_text`, `fetch_method: public_webfetch`.
3. If preview requires join/login or returns empty, stop — ask for paste or bot access.
4. Understanding of a text message comes from the message text. Video claims wait for the media pipeline.

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
