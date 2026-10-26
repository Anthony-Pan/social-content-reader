#!/usr/bin/env python3
"""Extract keyframes from a local video with ffmpeg. One JSON object on stdout.

Modes:
  fps    uniform samples (default 1 fps), capped by --max-frames
  scene  first frame plus scene-change frames

This helper does not download URLs. Acquire a local file first.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


INSTALL_HINT = (
    "Install ffmpeg and ffprobe and put them on PATH. "
    "macOS: brew install ffmpeg. "
    "Windows: winget install --id Gyan.FFmpeg --exact, then reopen the shell. "
    "Linux: install the distro ffmpeg package."
)

PTS_TIME_RE = re.compile(r"pts_time:([0-9]+(?:\.[0-9]+)?)")
DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


class FrameError(Exception):
    """An actionable error safe to include in the JSON response."""


def parse_showinfo_timestamps(stderr: str) -> list[float]:
    """Pull pts_time values from ffmpeg showinfo lines."""
    return [float(match) for match in PTS_TIME_RE.findall(stderr or "")]


def parse_duration_text(text: str) -> float | None:
    match = DURATION_RE.search(text or "")
    if not match:
        return None
    hours, minutes, seconds = int(match.group(1)), int(match.group(2)), float(match.group(3))
    return hours * 3600 + minutes * 60 + seconds


def format_number(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:.4g}"


def build_vf(mode: str, fps: float, scene_threshold: float) -> str:
    """ffmpeg -vf argument. Commas inside select() are escaped for the filtergraph."""
    if mode == "fps":
        return f"fps={format_number(fps)},showinfo"
    threshold = format_number(scene_threshold)
    return f"select='eq(n\\,0)+gt(scene\\,{threshold})',showinfo"


def build_ffmpeg_command(ffmpeg: str, media: Path, vf: str, out_pattern: Path,
                         max_frames: int, sync_flag: str = "-fps_mode") -> list[str]:
    return [
        ffmpeg, "-hide_banner", "-y",
        "-i", str(media),
        "-an",
        "-vf", vf,
        sync_flag, "vfr",
        "-q:v", "3",
        "-frames:v", str(max_frames),
        str(out_pattern),
    ]


def assert_local_media(media: Path, raw: str) -> None:
    lowered = raw.strip().lower()
    if lowered.startswith(("http://", "https://", "ftp://")):
        raise FrameError(
            "Refusing a URL. Acquire a local video file first; extract_frames.py does not download."
        )
    if not media.is_file():
        raise FrameError("Media file not found or not a regular file: " + str(media))
    if media.stat().st_size == 0:
        raise FrameError("Media file is empty: " + str(media))


def prepare_out_dir(requested: str | None) -> Path:
    if not requested:
        return Path(tempfile.mkdtemp(prefix="scr-frames-"))
    out = Path(requested).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    existing = [p for p in out.glob("frame_*.jpg") if p.is_file()]
    if existing:
        raise FrameError(
            "Output directory already contains frame_*.jpg. Pass an empty --out-dir. " + str(out)
        )
    return out


def probe_duration(media: Path) -> float | None:
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        proc = subprocess.run(
            [
                ffprobe, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(media),
            ],
            capture_output=True, text=True, timeout=60, errors="replace",
        )
        raw = (proc.stdout or "").strip()
        if proc.returncode == 0 and raw and raw.upper() != "N/A":
            try:
                return float(raw)
            except ValueError:
                pass
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(media)],
        capture_output=True, text=True, timeout=60, errors="replace",
    )
    return parse_duration_text((proc.stderr or "") + (proc.stdout or ""))


def list_frames(out_dir: Path) -> list[Path]:
    frames = [p for p in out_dir.glob("frame_*.jpg") if p.is_file() and p.stat().st_size > 0]
    return sorted(frames, key=lambda p: p.name)


def pair_frames(paths: list[Path], timestamps: list[float]) -> list[dict]:
    frames = []
    for index, path in enumerate(paths):
        timestamp = timestamps[index] if index < len(timestamps) else None
        frames.append({
            "index": index,
            "path": str(path),
            "timestamp_sec": timestamp,
        })
    return frames


def run_ffmpeg(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=300, errors="replace",
    )


def extract(media_raw: str, mode: str, fps: float, scene_threshold: float,
            max_frames: int, out_dir: str | None) -> dict:
    if mode not in {"fps", "scene"}:
        raise FrameError("mode must be fps or scene")
    if max_frames < 1 or max_frames > 300:
        raise FrameError("--max-frames must be between 1 and 300")
    if mode == "fps" and not (0 < fps <= 10):
        raise FrameError("--fps must be greater than 0 and at most 10")
    if mode == "scene" and not (0 < scene_threshold < 1):
        raise FrameError("--scene-threshold must be between 0 and 1")

    media = Path(media_raw).expanduser().resolve()
    assert_local_media(media, media_raw)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise FrameError("ffmpeg not on PATH. " + INSTALL_HINT)

    dest = prepare_out_dir(out_dir)
    vf = build_vf(mode, fps, scene_threshold)
    pattern = dest / "frame_%04d.jpg"
    proc = None
    for sync_flag in ("-fps_mode", "-vsync"):
        cmd = build_ffmpeg_command(ffmpeg, media, vf, pattern, max_frames, sync_flag)
        try:
            proc = run_ffmpeg(cmd)
        except subprocess.TimeoutExpired as exc:
            raise FrameError("ffmpeg timed out while extracting frames.") from exc
        frames = list_frames(dest)
        stderr = ((proc.stderr or "") + (proc.stdout or "")) if proc else ""
        if frames:
            break
        unrecognized = (
            sync_flag == "-fps_mode"
            and "fps_mode" in stderr
            and ("Unrecognized option" in stderr or "Option not found" in stderr)
        )
        if unrecognized:
            continue
        detail = " ".join(stderr.strip().split())
        if len(detail) > 400:
            detail = detail[-400:]
        raise FrameError(
            "ffmpeg produced no frames. If this file is audio-only, run asr_local.py for speech "
            "and report that there are no pictures. " + detail
        )

    timestamps = parse_showinfo_timestamps((proc.stderr or "") if proc else "")
    paired = pair_frames(list_frames(dest), timestamps)
    duration = probe_duration(media)
    return {
        "ok": True,
        "media_path": str(media),
        "mode": mode,
        "fps": fps if mode == "fps" else None,
        "scene_threshold": scene_threshold if mode == "scene" else None,
        "duration_sec": duration,
        "out_dir": str(dest),
        "truncated": len(paired) >= max_frames,
        "frames": paired,
        "error": None,
    }


def empty_record(media: str, mode: str, fps: float, scene_threshold: float) -> dict:
    return {
        "ok": False,
        "media_path": media,
        "mode": mode,
        "fps": fps if mode == "fps" else None,
        "scene_threshold": scene_threshold if mode == "scene" else None,
        "duration_sec": None,
        "out_dir": None,
        "truncated": False,
        "frames": [],
        "error": None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract local-video keyframes with ffmpeg (no URL downloader).",
        epilog=INSTALL_HINT,
    )
    parser.add_argument("--media", required=True, help="Path to a local video file")
    parser.add_argument("--mode", choices=["fps", "scene"], default="fps",
                        help="fps: uniform samples. scene: first frame plus scene changes. Default: fps")
    parser.add_argument("--fps", type=float, default=1.0,
                        help="Samples per second for --mode fps (0 < fps <= 10). Default: 1")
    parser.add_argument("--scene-threshold", type=float, default=0.3,
                        help="Scene-change sensitivity for --mode scene (0-1). Default: 0.3")
    parser.add_argument("--max-frames", type=int, default=24,
                        help="Cap emitted frames (1-300). Default: 24. truncated=true when the cap is hit")
    parser.add_argument("--out-dir", default=None,
                        help="Empty directory for frame_NNNN.jpg. Default: a new temp directory")
    args = parser.parse_args(argv)
    record = empty_record(args.media, args.mode, args.fps, args.scene_threshold)
    try:
        record = extract(
            args.media, args.mode, args.fps, args.scene_threshold, args.max_frames, args.out_dir,
        )
    except FrameError as exc:
        record["error"] = str(exc)
    except Exception as exc:
        record["error"] = f"Frame extraction failed ({type(exc).__name__}). " + INSTALL_HINT
    print(json.dumps(record, ensure_ascii=True))
    return 0 if record["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
