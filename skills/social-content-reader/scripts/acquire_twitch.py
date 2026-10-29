#!/usr/bin/env python3
"""Public Twitch clip and VOD acquire via stock yt-dlp.

No cookies, netrc, browser profile, client secret, or Helix token. yt-dlp is
invoked with --ignore-config. A VOD longer than TWITCH_MAX_WINDOW_SEC is not
downloaded and is not silently trimmed to a prefix. Pass --section START-END
(at most that window). ?t= on the URL is a player bookmark, not a range.
Success is decided by the caller with ffprobe, not by HTTP status.
"""
from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# One public bound for a full file and for one --section. Not whole-broadcast support.
TWITCH_MAX_WINDOW_SEC = 600
# Padded above observed box rates so an over-estimate refuses before download.
# 480p30 sample ~170 KB/s; 1080p source sample ~731 KB/s.
_RATE_BY_MAX_HEIGHT = (
    (160, 80_000),
    (360, 160_000),
    (480, 220_000),
    (720, 500_000),
    (1080, 900_000),
)
_RATE_ABOVE_1080 = 2_000_000

_CLIP_RE = re.compile(
    r"""(?x)
    https?://
    (?:
        clips\.twitch\.tv/(?:embed\?[^#]*\bclip=|(?:[^/?#]+/)*)
        |
        (?:(?:www|go|m)\.)?twitch\.tv/(?:[^/?#]+/)?clip/
    )
    (?P<id>[^/?#&]+)
    """,
    re.I,
)
_VOD_RE = re.compile(
    r"""(?x)
    https?://
    (?:
        (?:(?:www|go|m)\.)?twitch\.tv/(?:[^/?#]+/v(?:ideo)?|videos)/
        |
        player\.twitch\.tv/\?[^#]*\bvideo=v?
        |
        (?:(?:www|m)\.)?twitch\.tv/[^/?#]+/schedule\?[^#]*\bvodID=
    )
    (?P<id>\d+)
    """,
    re.I,
)
_CLOCK_RE = re.compile(r"(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)")
_HMS_RE = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?", re.I)


class TwitchError(Exception):
    pass


def parse_time(token):
    """Return seconds, or None for the literal end. Raises TwitchError."""
    text = (token or "").strip()
    if text.lower() == "end":
        return None
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        return float(text)
    match = _CLOCK_RE.fullmatch(text)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2))
        seconds = float(match.group(3))
        if minutes >= 60 or seconds >= 60:
            raise TwitchError(f"invalid Twitch time {token!r}")
        return hours * 3600 + minutes * 60 + seconds
    match = _HMS_RE.fullmatch(text)
    if match and any(match.groups()):
        return int(match.group(1) or 0) * 3600 + int(match.group(2) or 0) * 60 + float(match.group(3) or 0)
    raise TwitchError(f"invalid Twitch time {token!r}; use seconds, MM:SS, H:MM:SS, or 1h2m3s")


def parse_section(spec):
    """Return (start_sec, end_sec or None). end None means the media's own end."""
    text = (spec or "").strip()
    if text.startswith("*"):
        text = text[1:].strip()
    if "-" not in text:
        raise TwitchError("Twitch --section must be START-END (example: 0-20 or 1:00:00-1:00:20)")
    start_tok, end_tok = text.split("-", 1)
    start = parse_time(start_tok)
    end = parse_time(end_tok)
    if start is None:
        raise TwitchError("Twitch --section start cannot be 'end'")
    if start < 0 or (end is not None and end < 0):
        raise TwitchError("Twitch --section times must be >= 0")
    if end is not None and end <= start:
        raise TwitchError("Twitch --section end must be after start")
    return start, end


def _clock(seconds):
    whole = int(round(seconds))
    hours, rem = divmod(whole, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def classify_twitch(url):
    """Return kind, id, canonical https URL, and optional bookmark seconds.

    Channel, live, collection, and video-list URLs raise. They are not one media file.
    """
    raw = (url or "").strip()
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or parsed.username or parsed.password:
        raise TwitchError("expected a public http(s) Twitch clip or VOD URL")
    if host != "twitch.tv" and not host.endswith(".twitch.tv"):
        raise TwitchError("expected a public http(s) Twitch clip or VOD URL")
    clip = _CLIP_RE.search(raw)
    if clip:
        slug = clip.group("id")
        if not slug or slug.lower() == "embed":
            raise TwitchError("Twitch clip URL has no clip id")
        return {
            "kind": "clip",
            "id": slug,
            "ident": f"clip:{slug}",
            "canonical_url": f"https://clips.twitch.tv/{slug}",
            "bookmark_sec": None,
        }
    vod = _VOD_RE.search(raw)
    if vod:
        vod_id = vod.group("id")
        bookmark = None
        t_values = parse_qs(parsed.query).get("t")
        if t_values and t_values[0]:
            try:
                parsed_t = parse_time(t_values[0])
            except TwitchError:
                parsed_t = None
            if parsed_t is not None and parsed_t >= 0:
                bookmark = parsed_t
        return {
            "kind": "vod",
            "id": vod_id,
            "ident": f"vod:{vod_id}",
            "canonical_url": f"https://www.twitch.tv/videos/{vod_id}",
            "bookmark_sec": bookmark,
        }
    path = parsed.path or "/"
    if re.search(r"/collections(?:/|$)", path, re.I):
        raise TwitchError("Twitch collection URLs are not one clip or VOD; pass /videos/{id} or a clip URL")
    if re.search(r"/(?:videos|clips|profile)(?:/|$)", path, re.I) or "filter=" in (parsed.query or ""):
        raise TwitchError("Twitch video/clip list URLs are not one media file; pass /videos/{id} or a clip URL")
    raise TwitchError(
        "Twitch channel and live URLs are not a clip or VOD. "
        "Pass https://clips.twitch.tv/{slug} or https://www.twitch.tv/videos/{id}. "
        "Live streams are not recorded."
    )


def _video_format(fmt):
    """A real video rendition. Storyboards and audio-only are not video.

    Twitch clips often omit vcodec/acodec on a progressive MP4. Missing codecs
    are not the same as an explicit "none".
    """
    format_id = str(fmt.get("format_id") or "")
    if not format_id or format_id.startswith("sb") or fmt.get("protocol") == "mhtml":
        return False
    if fmt.get("vcodec") == "none":
        return False
    height = fmt.get("height")
    return isinstance(height, int) and height > 0


def choose_format(formats):
    """Prefer the highest video at or below 480p, else 720p, else the lowest.

    When a height has a rendition with a declared audio codec, use that.
    """
    videos = [fmt for fmt in formats or [] if _video_format(fmt)]
    if not videos:
        raise TwitchError("public Twitch metadata has no video format; not acquired")
    declared_audio = [fmt for fmt in videos if fmt.get("acodec") not in (None, "none")]
    pool = declared_audio or videos

    def best_at_or_below(limit):
        under = [fmt for fmt in pool if fmt["height"] <= limit]
        if not under:
            return None
        return max(under, key=lambda fmt: (fmt["height"], str(fmt["format_id"])))

    chosen = best_at_or_below(480) or best_at_or_below(720)
    if chosen is None:
        chosen = min(pool, key=lambda fmt: (fmt["height"], str(fmt["format_id"])))
    if re.search(r"[\s,/+\[\]()]", str(chosen["format_id"])):
        raise TwitchError("Twitch format id is not a single public format; not acquired")
    return chosen


def planning_bytes(height, seconds):
    rate = _RATE_ABOVE_1080
    for limit, bps in _RATE_BY_MAX_HEIGHT:
        if height <= limit:
            rate = bps
            break
    return int(math.ceil(seconds * rate))


def plan_window(kind, duration, formats, section, max_bytes, bookmark_sec=None):
    """Decide the exact window or raise before any media download."""
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise TwitchError("Twitch metadata has no positive duration; refusing an unbounded download")
    duration = float(duration)
    label = "VOD" if kind == "vod" else "clip"
    if section is None:
        if duration > TWITCH_MAX_WINDOW_SEC:
            bookmark = ""
            if bookmark_sec is not None:
                bookmark = (
                    f" The URL t={bookmark_sec:g}s bookmark was ignored; it is not a download range."
                )
            raise TwitchError(
                f"Twitch {label} is {duration:.0f}s ({_clock(duration)}). "
                f"Full public acquire is limited to {TWITCH_MAX_WINDOW_SEC}s. "
                f"Refusing to trim it silently. Pass --section START-END "
                f"(at most {TWITCH_MAX_WINDOW_SEC}s) or the file is not acquired."
                f"{bookmark} Chat/title is not the video."
            )
        start, end = 0.0, duration
    else:
        start, end = section
        if end is None:
            end = duration
        if start < 0 or end - duration > 0.05 or end <= start:
            raise TwitchError(
                f"Twitch --section {start:g}-{end:g} is outside the {duration:.0f}s media. "
                "Refusing to shorten it silently."
            )
        if end > duration:
            end = duration
        if end - start > TWITCH_MAX_WINDOW_SEC:
            raise TwitchError(
                f"Twitch --section is {end - start:.0f}s. The public limit is {TWITCH_MAX_WINDOW_SEC}s. "
                "Refusing a longer range. Nothing was downloaded."
            )
    window = end - start
    chosen = choose_format(formats)
    estimate = planning_bytes(chosen["height"], window)
    full = start <= 0.05 and abs(end - duration) <= 0.05
    if estimate > max_bytes:
        raise TwitchError(
            f"Twitch {label} window {window:.0f}s at {chosen['height']}p is estimated {estimate} bytes, "
            f"over the {max_bytes}-byte cap. Refusing before download. "
            "Pass a shorter --section or raise --max-mb. Nothing was truncated into a success."
        )
    return {
        "start": start,
        "end": end,
        "window": window,
        "full": full,
        "format_id": str(chosen["format_id"]),
        "height": chosen["height"],
        "estimated_bytes": estimate,
        "source_duration": duration,
        "bookmark_sec": bookmark_sec,
    }


def public_failure(stderr):
    """Map downloader stderr to a short error. Never echo URLs or tokens."""
    text = (stderr or "").lower()
    if "subscriber" in text or "sub only" in text or "subscribers only" in text:
        return "Twitch requires a login or subscription; no cookie/credential fallback"
    if "login" in text or "logged-in" in text or "authentication" in text:
        return "Twitch requires a login or subscription; no cookie/credential fallback"
    if "drm" in text:
        return "Twitch media is DRM; stopped"
    if "does not exist" in text or "unavailable" in text:
        return "Twitch media does not exist or is unavailable"
    return "yt-dlp failed; no verified file (no cookie/profile fallback)"


def _base_args():
    return [
        "yt-dlp", "--ignore-config", "--no-playlist", "--no-progress", "--no-overwrites",
        "--retries", "0", "--fragment-retries", "0", "--socket-timeout", "20",
        "--no-warnings",
    ]


def metadata_args(canonical_url):
    return _base_args() + ["-J", "--skip-download", canonical_url]


def download_args(canonical_url, work, plan, max_bytes):
    args = _base_args() + [
        "--max-filesize", str(max_bytes),
        "-f", plan["format_id"],
        "--merge-output-format", "mp4",
        "-o", str(Path(work) / "media.%(ext)s"),
    ]
    if not plan["full"]:
        args += ["--download-sections", f"*{plan['start']:.3f}-{plan['end']:.3f}"]
    args.append(canonical_url)
    return args


def _safe_metadata(data, kind):
    if not isinstance(data, dict):
        raise TwitchError("yt-dlp metadata was not an object; no file")
    if data.get("is_live") or data.get("live_status") in {"is_live", "is_upcoming"}:
        raise TwitchError("Twitch live streams are not acquired; pass a finished /videos/{id} or a clip")
    formats = []
    for fmt in data.get("formats") or []:
        if not isinstance(fmt, dict):
            continue
        height = fmt.get("height")
        formats.append({
            "format_id": fmt.get("format_id"),
            "height": height if isinstance(height, int) else None,
            "vcodec": fmt.get("vcodec"),
            "acodec": fmt.get("acodec"),
            "protocol": fmt.get("protocol"),
        })
    return {"kind": kind, "duration": data.get("duration"), "formats": formats}


def default_run(args, timeout):
    if not shutil.which("yt-dlp"):
        raise TwitchError("yt-dlp is not installed")
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise TwitchError("yt-dlp timed out; no verified file") from exc
    if "-J" in args and "--skip-download" in args:
        if result.returncode:
            raise TwitchError(public_failure(result.stderr))
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise TwitchError("yt-dlp metadata was not JSON; no file") from exc
    if result.returncode:
        raise TwitchError(public_failure(result.stderr))
    return None


def _saved_media(work):
    files = [path for path in Path(work).glob("media.*") if path.suffix in (".mp4", ".mkv", ".webm")]
    if len(files) != 1:
        raise TwitchError("yt-dlp did not save exactly one media file (size limit or unavailable)")
    return files[0]


def acquire_public(url, work, max_bytes, section_text=None, runner=None):
    """Download one public clip, short VOD, or explicit section into work.

    Returns path, method, expected_duration_sec, receipt fields.
    Does not ffprobe. Does not publish outside work.
    """
    classified = classify_twitch(url)
    section = parse_section(section_text) if section_text else None
    run = runner or default_run
    raw = run(metadata_args(classified["canonical_url"]), 45)
    info = _safe_metadata(raw, classified["kind"])
    plan = plan_window(
        classified["kind"], info["duration"], info["formats"], section, max_bytes,
        bookmark_sec=classified.get("bookmark_sec"),
    )
    run(download_args(classified["canonical_url"], work, plan, max_bytes), 300)
    path = _saved_media(work)
    if path.stat().st_size > max_bytes:
        path.unlink(missing_ok=True)
        raise TwitchError(
            "media exceeds --max-mb after download; discarded, not truncated into a success"
        )
    extra = {
        "twitch_kind": classified["kind"],
        "twitch_id": classified["id"],
        "twitch_source_duration_sec": plan["source_duration"],
        "twitch_full": plan["full"],
        "twitch_height": plan["height"],
    }
    if not plan["full"]:
        extra["section_start_sec"] = plan["start"]
        extra["section_end_sec"] = plan["end"]
    if plan.get("bookmark_sec") is not None:
        extra["twitch_bookmark_sec"] = plan["bookmark_sec"]
        extra["twitch_bookmark_applied"] = False
    expected = plan["source_duration"] if plan["full"] else plan["window"]
    return path, "twitch_ytdlp_public", expected, extra
