# Twitch VODs / clips

**Status:** Partial — metadata easy; speech needs official transcript (rare), creator VOD download authorization, or user media + ASR.

## URL patterns

- VOD: `https://www.twitch.tv/videos/{id}`
- Clip: `https://www.twitch.tv/{channel}/clip/{slug}` or `https://clips.twitch.tv/{slug}`
- Live URLs are out of scope for “read what was said” unless a VOD/clip exists

## Prefer (in order)

1. **Host Twitch connector / Helix API** with app/user token for metadata (`TWITCH_CLIENT_ID`, `TWITCH_ACCESS_TOKEN`).
2. **Clip title + creator description** via Helix or public page — caption-level only.
3. **User-supplied VOD/clip file** or explicitly approved download → `asr_local.py` (long VODs: chunk audio first; see scripts/README.md).
4. If Twitch provides creator closed captions for that VOD and the connector exposes them, use those as `body_kind: transcript`.

## Fetch recipe

1. Detect VOD vs clip; extract id/slug.
2. Fetch metadata via Helix when credentials exist; else public page title.
3. For understanding speech: require captions or ASR — do not invent dialogue from chat logs unless the user asks to analyze chat specifically (separate from VOD speech).
4. Set honest limits for multi-hour VODs (chunking, cost/time).

## Honest limits

- Live streams: no durable transcript unless recorded.
- Chat ≠ what the streamer said.
- No unauthorized VOD ripping; follow Twitch Developer Agreement.
- Very long ASR jobs belong on Windows + Codex with chunking.

## Codex prompt sketch

```text
Follow platforms/twitch.md. URL: <URL>
Metadata first; speech only via captions or user media+ASR (chunk long VODs).
```

## References

- Twitch Helix API (videos, clips)
