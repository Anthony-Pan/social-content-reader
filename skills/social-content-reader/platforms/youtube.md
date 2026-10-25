# YouTube

**Status:** ✅ Works (for videos with captions / accessible transcripts)

**Goal:** Understand what the video *says*, not what the description claims.

## URL patterns

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`
- `https://www.youtube.com/live/VIDEO_ID`
- bare 11-char video id

## Prefer (in order)

1. **Host YouTube connector / transcript MCP** if the agent already has one (e.g. TubeAlfred-style research tools, `@captapi/mcp`, `ytapi` MCP, `mcp-youtube`). Use transcript tools first; metadata second.
2. **Codex on Windows** running a transcript fetch in this repo when no connector is present.
3. **Official YouTube Data API v3** for metadata only (`videos.list`) — **does not return transcript text**. Never stop at description.
4. If no captions exist: ask the user, or use a user-approved speech-to-text path on audio they authorize — do not silently invent dialogue.

## Fetch recipe

1. Normalize to `VIDEO_ID` (`scripts/normalize_url.py` or regex).
2. Fetch **transcript / captions** (manual track preferred over auto-generated when both exist).
3. Optionally fetch metadata (title, channel, duration, publish date).
4. Set `body_kind: transcript`, `body_text` = full caption text (truncate with clear note if huge).
5. Summarize from transcript: main claim, chapters/topics, notable quotes with timestamps when available.

## Honest limits

- Private, members-only, age-gated, or caption-disabled videos → unavailable.
- YouTube Data API alone ≠ understanding.
- Third-party transcript APIs may be paid; do not hardcode keys in the skill.
- Auto-captions can be wrong — say “based on auto captions” when relevant.

## Codex prompt sketch

```text
Follow platforms/youtube.md. URL: <URL>
Return ContentRecord JSON + 8-line understanding summary from the transcript.
If no transcript, stop and list options (user paste / STT) — do not guess spoken content from the description.
```

## References

- YouTube Data API overview (metadata): https://developers.google.com/youtube/v3
- Agent Skills pattern: prefer connector over scrape
