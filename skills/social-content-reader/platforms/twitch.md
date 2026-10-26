# Twitch VODs / clips

**Status:** Partial. Metadata is easy. Speech and graphics need creator CC or a media file. Chat is not the VOD.

## URL patterns

- VOD: `https://www.twitch.tv/videos/{id}`
- Clip: `https://www.twitch.tv/{channel}/clip/{slug}` or `https://clips.twitch.tv/{slug}`
- Live URLs are out of scope for “read what was said” unless a VOD/clip exists

## Video and graphics

Follow [_video-body.md](_video-body.md). Helix titles and descriptions are `caption`. Creator closed captions, when the connector exposes them, are `speech_text` and still need frames for graphics. A local VOD/clip file (user-supplied, or `yt-dlp` when the user asked to read that VOD/clip) gets frames, OCR, host vision, and ASR. Chunk long ASR (see scripts/README.md). If there is no CC and no file, say the VOD was not watched.

## Prefer (in order)

1. **Host Twitch connector / Helix API** with app/user token for metadata (`TWITCH_CLIENT_ID`, `TWITCH_ACCESS_TOKEN`). Metadata is not the body.
2. Creator closed captions for that VOD when the connector exposes them → `speech_text`.
3. **User-supplied VOD/clip file**, or `yt-dlp` when the user asked to read that URL. Then the media pipeline. Do not rip a VOD the user did not ask to read.
4. Clip title and creator description stay in `caption`.

## Fetch recipe

1. Detect VOD vs clip; extract id/slug.
2. Fetch metadata via Helix when credentials exist; else public page title.
3. Speech comes from CC or ASR. Graphics come from frames. Do not invent dialogue from chat unless the user asks to analyze chat separately from the VOD.
4. Set honest limits for multi-hour VODs (chunking, cost/time).

## Honest limits

- Live streams: no durable transcript unless recorded.
- Chat ≠ what the streamer said.
- No unauthorized VOD ripping; follow Twitch Developer Agreement.
- Very long ASR jobs belong on Windows + Codex with chunking.

## Codex prompt sketch

```text
Follow platforms/twitch.md and platforms/_video-body.md. URL: <URL>
Helix is metadata. Speech from CC or ASR; graphics from frames. Chat is not the VOD.
If there is no file and no CC, say the VOD was not watched.
```

## References

- Twitch Helix API (videos, clips)
