# YouTube

**Status:** Works when speech (official transcript or ASR) **and** frames are read. The description is not the video.

**Goal:** Read what the video shows and what is spoken. Follow [the shared video recipe](_video-body.md).

## URL patterns

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`
- `https://www.youtube.com/live/VIDEO_ID`
- bare 11-char video id

## Video and graphics

Official caption tracks are **speech**, not the picture. Default video Understanding also extracts frames and reads burned-in text and graphics ([_video-body.md](_video-body.md)). The description and chapter blurbs stay in `caption`. Do not write Understanding from the description.

## Prefer (in order)

1. **Host YouTube connector / transcript MCP** if the agent already has one (e.g. TubeAlfred-style research tools, `@captapi/mcp`, `ytapi` MCP, `mcp-youtube`). Use it for **speech**. Still acquire frames for graphics unless the connector already returned frame descriptions you actually looked at.
2. **yt-dlp** when the user asked to read the video, then `extract_frames.py`, `ocr_frames.py`, host vision, and `asr_local.py` (ASR only if no official transcript). Stop on age-gate, login, or DRM. Mac, 2026-10-26: `yt-dlp` acquired a YouTube file on Anthony’s network. That is the file, not Understanding by itself.
3. **Official YouTube Data API v3** for metadata only (`videos.list`). It does not return transcript text or frames.
4. If no captions and no media file: `body_kind: unavailable`. Ask for a file or an authorized transcript. Do not invent speech or graphics from the description.

## Fetch recipe

1. Normalize to `VIDEO_ID` (`scripts/normalize_url.py` or regex).
2. Fetch the **transcript** (manual track preferred over auto-generated when both exist) into `speech_text`.
3. Acquire the file when graphics matter (they do for default video Understanding) and run `extract_frames.py` + OCR + host vision.
4. Metadata (title, channel, duration, publish date) is fine alongside the media read. Description → `caption`.
5. Set `body_kind: media_understanding` when pictures and speech were both read. A transcript with no frames is `body_kind: transcript` and must say graphics were not read.
6. Summarize from speech + visuals. Note auto-caption uncertainty. Quote timestamps from transcript cues or frame `timestamp_sec`.

## Honest limits

- Private, members-only, age-gated, or caption-disabled videos → unavailable.
- YouTube Data API alone is not understanding. The description is not the body.
- Third-party transcript APIs may be paid; do not hardcode keys in the skill.
- Auto-captions can be wrong — say “based on auto captions” when relevant.
- `yt-dlp` is the documented public acquire CLI when the user asked to read the file. No cookie theft or age-gate bypass.

## Codex prompt sketch

```text
Follow platforms/youtube.md and platforms/_video-body.md. URL: <URL>
Speech from the official transcript when it exists; frames + OCR + vision for graphics.
Description is metadata. If the file and the transcript are both missing, say the video was not watched.
```

## References

- YouTube Data API overview (metadata): https://developers.google.com/youtube/v3
- Agent Skills pattern: prefer connector over scrape

## Success criteria

- `body_kind: media_understanding` when speech and frames were both read, **or** `transcript` / `visual` with that gap stated, **or** honest `unavailable`.
- Never claim the picture or the speech from the description alone.
