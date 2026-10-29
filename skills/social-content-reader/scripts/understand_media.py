#!/usr/bin/env python3
"""Understand a validated local media file. One JSON object on stdout.

Pipeline: ffprobe → extract_frames → ocr_frames → local asr_local (or a
caller-supplied official speech track) → ContentRecord + a short summary.

The summary quotes only evidence those steps returned. A share caption or
title is stored as metadata and is never copied into body_text, speech_text,
visual_text, or visual_description. This helper does not download URLs, does
not run a vision model, and does not upload audio unless --asr-backend
openai-api is explicit. Missing OCR/ASR engines are engine: none, not guessed
text. ok is true only when at least one real channel produced evidence.
complete is true only for pictures and speech together (body_kind
media_understanding).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import asr_local
import extract_frames
import ocr_frames


PROBE_HINT = (
    "Install ffmpeg so ffprobe is on PATH. "
    "macOS: brew install ffmpeg. "
    "Windows: winget install --id Gyan.FFmpeg --exact. "
    "Linux: install the distro ffmpeg package."
)
TEXT_LIMIT = 1_000_000
SUMMARY_LIMIT = 400


class UnderstandError(Exception):
    """An actionable error safe to include in the JSON response."""


def norm(text: str) -> str:
    return " ".join((text or "").casefold().split())


def clip_text(text: str, limit: int = SUMMARY_LIMIT) -> str:
    flat = " ".join((text or "").split())
    if len(flat) <= limit:
        return flat
    return flat[:limit].rstrip() + "… [truncated in summary; full text is in the record]"


def matches_metadata(text: str, caption: str, title: str) -> str | None:
    folded = norm(text)
    if not folded:
        return None
    if caption and folded == norm(caption):
        return "caption"
    if title and folded == norm(title):
        return "title"
    return None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe_media(path: Path) -> dict:
    base = {
        "ok": False,
        "validated": False,
        "duration_sec": None,
        "has_video": False,
        "has_audio": False,
        "codecs": [],
        "error": None,
    }
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        base["error"] = "ffprobe not on PATH. The file was not validated. " + PROBE_HINT
        return base
    try:
        proc = subprocess.run(
            [ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
            capture_output=True, text=True, timeout=30, errors="replace",
        )
    except subprocess.TimeoutExpired:
        base["error"] = "ffprobe timed out. The file was not validated."
        return base
    if proc.returncode != 0:
        base["error"] = "ffprobe could not decode this file. It was not read."
        return base
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        base["error"] = "ffprobe returned no JSON. The file was not validated."
        return base
    streams = [item for item in (data.get("streams") or []) if isinstance(item, dict)]
    types = {item.get("codec_type") for item in streams}
    try:
        duration = float((data.get("format") or {}).get("duration"))
    except (TypeError, ValueError):
        duration = 0.0
    if not math.isfinite(duration) or duration <= 0 or not ({"video", "audio"} & types):
        base["error"] = (
            "File has no positive duration and no audio or video stream. It was not read."
        )
        return base
    return {
        "ok": True,
        "validated": True,
        "duration_sec": duration,
        "has_video": "video" in types,
        "has_audio": "audio" in types,
        "codecs": [item.get("codec_name") for item in streams],
        "error": None,
    }


def validate_local_media(raw: str) -> tuple[Path, dict]:
    text = (raw or "").strip()
    if text.lower().startswith(("http://", "https://", "ftp://")):
        raise UnderstandError(
            "Refusing a URL. understand_media.py reads a validated local file and does not download."
        )
    path = Path(text).expanduser().resolve()
    if not path.is_file():
        raise UnderstandError("Media file not found or not a regular file: " + str(path))
    if path.stat().st_size == 0:
        raise UnderstandError("Media file is empty: " + str(path))
    probe = probe_media(path)
    if not probe["validated"]:
        raise UnderstandError(probe["error"] or "Media file was not validated.")
    return path, probe


def read_local_text(raw: str, label: str) -> str:
    text = (raw or "").strip()
    if text.lower().startswith(("http://", "https://", "ftp://")):
        raise UnderstandError(f"Refusing a URL for {label}. Pass a local text file.")
    path = Path(text).expanduser().resolve()
    if not path.is_file():
        raise UnderstandError(f"{label} file not found: " + str(path))
    if path.stat().st_size > TEXT_LIMIT:
        raise UnderstandError(f"{label} file is larger than 1 MB.")
    if path.stat().st_size == 0:
        raise UnderstandError(f"{label} file is empty: " + str(path))
    return path.read_text(encoding="utf-8")


def resolve_optional_text(inline: str | None, file_arg: str | None, label: str) -> str:
    if inline and file_arg:
        raise UnderstandError(f"Pass only one {label} value.")
    if file_arg:
        return read_local_text(file_arg, label)
    return inline or ""


def load_reused_frames(raw: str, media: Path) -> dict:
    path = Path(raw).expanduser().resolve()
    if not path.is_file():
        raise UnderstandError("frames JSON not found: " + str(path))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise UnderstandError("frames JSON is not valid JSON.") from exc
    if not isinstance(payload, dict) or not payload.get("ok"):
        raise UnderstandError("frames JSON is not an ok extract_frames result.")
    recorded = payload.get("media_path")
    if not recorded:
        raise UnderstandError("frames JSON has no media_path.")
    if Path(str(recorded)).expanduser().resolve() != media:
        raise UnderstandError("frames JSON media_path does not match --media.")
    frames = payload.get("frames") or []
    if not isinstance(frames, list) or not frames:
        raise UnderstandError("frames JSON has no frames.")
    for item in frames:
        if not isinstance(item, dict) or not item.get("path"):
            raise UnderstandError("frames JSON entry is missing a path.")
        frame = Path(str(item["path"])).expanduser().resolve()
        if not frame.is_file() or frame.stat().st_size == 0:
            raise UnderstandError("frame file missing: " + str(frame))
        item["path"] = str(frame)
    payload["reason"] = "reused"
    payload["frames_json"] = str(path)
    return payload


def run_frames(media: Path, probe: dict, mode: str, fps: float, scene_threshold: float,
               max_frames: int, out_dir: str | None, frames_json: str | None) -> dict:
    if frames_json:
        return load_reused_frames(frames_json, media)
    if not probe.get("has_video"):
        return {
            "ok": False, "frames": [], "truncated": False, "out_dir": None,
            "error": "No video stream. Frames were not extracted.", "reason": "no_video",
        }
    dest = None
    if out_dir:
        dest = str(Path(out_dir).expanduser().resolve() / "frames")
    try:
        record = extract_frames.extract(
            str(media), mode, fps, scene_threshold, max_frames, dest,
        )
    except extract_frames.FrameError as exc:
        return {
            "ok": False, "frames": [], "truncated": False, "out_dir": dest,
            "error": str(exc), "reason": "error",
        }
    record["reason"] = "ok" if record.get("ok") and record.get("frames") else "error"
    if record.get("ok") and record.get("out_dir"):
        spec = Path(record["out_dir"]) / "frames.json"
        spec.write_text(json.dumps(record), encoding="utf-8")
        record["frames_json"] = str(spec)
    return record


def ocr_engine_missing(message: str) -> bool:
    lowered = (message or "").lower()
    return "no ocr engine" in lowered or "not on path" in lowered


def run_ocr(frames_record: dict, engine: str, lang: str, max_frames: int) -> dict:
    empty = {
        "ok": False, "engine": "none", "language": None, "text": "",
        "truncated": False, "frames": [], "error": None, "reason": "no_frames",
    }
    frames = frames_record.get("frames") or []
    if not frames_record.get("ok") or not frames:
        empty["error"] = "OCR did not run because no frames were read."
        return empty
    spec = {
        "frames": [
            {"path": item.get("path"), "timestamp_sec": item.get("timestamp_sec")}
            for item in frames if isinstance(item, dict) and item.get("path")
        ]
    }
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    spec_path = Path(handle.name)
    try:
        json.dump(spec, handle)
        handle.close()
        try:
            result = ocr_frames.ocr(str(spec_path), None, None, engine, lang, 6, max_frames)
        except ocr_frames.OCRError as exc:
            message = str(exc)
            empty["error"] = message
            if ocr_engine_missing(message):
                empty["reason"] = "engine_missing"
                empty["engine"] = "none"
            else:
                empty["reason"] = "error"
                empty["engine"] = "none"
            return empty
    finally:
        spec_path.unlink(missing_ok=True)
    result["reason"] = "ok"
    if result.get("engine") in (None, "", "none"):
        result["engine"] = "none"
        result["reason"] = "engine_missing"
        result["ok"] = False
    return result


def select_asr(requested: str):
    if requested == "local":
        errors = []
        for name in ("faster-whisper", "openai-whisper"):
            try:
                return asr_local.select_backend(name)
            except asr_local.ASRError as exc:
                errors.append(str(exc))
        raise asr_local.ASRError("No local ASR engine. " + " ".join(errors))
    return asr_local.select_backend(requested)


def run_asr(media: Path, language: str, backend: str, model: str, has_audio: bool) -> dict:
    record = {
        "ok": False, "text": "", "language": None, "backend": None, "model": None,
        "engine": "none", "media_path": str(media), "error": None, "reason": None,
    }
    if not has_audio:
        record["reason"] = "no_audio"
        record["error"] = "No audio stream in the validated file. Speech was not transcribed."
        return record
    try:
        selected, module = select_asr(backend)
    except asr_local.ASRError as exc:
        record["reason"] = "engine_missing"
        record["error"] = str(exc)
        record["engine"] = "none"
        return record
    model_name = "whisper-1" if selected == "openai-api" else model
    record.update(backend=selected, model=model_name, engine=selected)
    lang = None if language == "auto" else language
    try:
        with redirect_stdout(sys.stderr):
            text, detected = asr_local.transcribe(media, lang, selected, model_name, module)
    except asr_local.ASRError as exc:
        record["reason"] = "error"
        record["error"] = str(exc)
        return record
    except Exception:
        record["reason"] = "error"
        record["error"] = (
            "Transcription failed. No speech text was produced. "
            "No runtime fallback or automatic retry was attempted."
        )
        return record
    text = (text or "").strip()
    if not text:
        record["reason"] = "empty"
        record["error"] = "No speech text returned. The caption was not substituted."
        return record
    record.update(ok=True, text=text, language=detected, reason="asr", error=None)
    return record


def base_record(platform: str, url: str, title: str, author: str, caption: str) -> dict:
    return {
        "platform": platform or "",
        "url": url or "",
        "canonical_id": None,
        "title": title or "",
        "author": author or "",
        "published_at": None,
        "language": None,
        "body_text": "The video was not read.",
        "body_kind": "unavailable",
        "speech_text": "",
        "visual_text": "",
        "visual_description": "",
        "caption": caption or "",
        "media_notes": "",
        "fetch_method": "blocked",
        "confidence": "low",
        "limits": [],
    }


def blocked_result(error: str, *, platform: str, url: str, title: str, author: str,
                   caption: str, media_raw: str, probe: dict | None = None,
                   sha256: str | None = None) -> dict:
    record = base_record(platform, url, title, author, caption)
    record["limits"] = [error]
    record["media_notes"] = "validated=false" if not (probe or {}).get("validated") else "validated=true; read stopped"
    understanding = "The video was not watched. " + error
    return {
        "ok": False,
        "complete": False,
        "blocked": True,
        "error": error,
        "understanding": understanding,
        "ocr_engine": "none",
        "asr_engine": "none",
        "record": record,
        "evidence": {
            "media_path": media_raw,
            "sha256": sha256,
            "validated": bool((probe or {}).get("validated")),
            "probe": probe or {"ok": False, "validated": False, "error": error},
            "frames": None,
            "frames_json": None,
            "ocr": {"ok": False, "engine": "none", "text": "", "reason": "not_run"},
            "asr": {"ok": False, "engine": "none", "text": "", "reason": "not_run"},
            "vision": {"accepted": False, "reason": "not_run"},
        },
    }


def add_limit(limits: list[str], text: str) -> None:
    if text and text not in limits:
        limits.append(text)


def build_body(visual_description: str, visual_text: str, speech_text: str) -> str:
    sections = []
    if visual_description:
        sections.append("Pictures: " + visual_description)
    if visual_text:
        sections.append("On-screen text: " + visual_text)
    if speech_text:
        sections.append("Speech: " + speech_text)
    if not sections:
        return "The video was not read."
    return "\n".join(sections)


def build_understanding(record: dict, *, ok: bool, ocr_reason: str, asr_reason: str) -> str:
    if not ok:
        lines = ["The video was not watched. Understanding was not produced from the local file."]
        if ocr_reason == "engine_missing":
            lines.append("OCR engine: none.")
        if asr_reason == "engine_missing":
            lines.append("ASR engine: none.")
        if record.get("limits"):
            lines.append("Limits: " + "; ".join(record["limits"]))
        return "\n".join(lines)
    kind = record.get("body_kind")
    if kind == "media_understanding":
        lines = ["Pictures and speech were read from the local file."]
    elif kind == "transcript":
        lines = ["Speech only. Graphics were not read from the file."]
    elif kind == "visual":
        lines = ["Pictures only. Speech was not established from the file."]
    else:
        lines = ["The video was not watched."]
    if record.get("visual_description"):
        lines.append("Pictures: " + clip_text(record["visual_description"]))
    if record.get("visual_text"):
        lines.append("On-screen text: " + clip_text(record["visual_text"]))
    if record.get("speech_text"):
        lines.append("Speech: " + clip_text(record["speech_text"]))
    if record.get("limits"):
        lines.append("Limits: " + "; ".join(record["limits"]))
    if record.get("caption"):
        lines.append(
            "Share caption (metadata, not the video body): " + clip_text(record["caption"], 240)
        )
    return "\n".join(lines)


def confidence_for(kind: str, *, truncated: bool, ocr_engine: str, speech_source: str) -> str:
    if kind == "unavailable":
        return "low"
    if kind != "media_understanding":
        return "medium"
    if truncated or ocr_engine == "none" or speech_source != "asr":
        return "medium"
    return "high"


def understand(media_raw: str, *, caption: str = "", title: str = "", author: str = "",
               platform: str = "", url: str = "", visual_description: str | None = None,
               visual_description_file: str | None = None, speech_text: str | None = None,
               speech_file: str | None = None, mode: str = "fps", fps: float = 1.0,
               scene_threshold: float = 0.3, max_frames: int = 24, out_dir: str | None = None,
               ocr_engine: str = "auto", ocr_lang: str = "chi_sim+eng",
               asr_backend: str = "local", asr_model: str = "base", language: str = "auto",
               frames_json: str | None = None) -> dict:
    try:
        media, probe = validate_local_media(media_raw)
    except UnderstandError as exc:
        return blocked_result(
            str(exc), platform=platform, url=url, title=title, author=author,
            caption=caption, media_raw=media_raw,
        )
    digest = file_sha256(media)
    try:
        supplied_vision = resolve_optional_text(
            visual_description, visual_description_file, "visual description",
        )
        supplied_speech = resolve_optional_text(speech_text, speech_file, "speech")
        frames = run_frames(
            media, probe, mode, fps, scene_threshold, max_frames, out_dir, frames_json,
        )
    except UnderstandError as exc:
        return blocked_result(
            str(exc), platform=platform, url=url, title=title, author=author,
            caption=caption, media_raw=str(media), probe=probe, sha256=digest,
        )

    frames_ok = bool(frames.get("ok") and frames.get("frames"))
    ocr = run_ocr(frames, ocr_engine, ocr_lang, max_frames)
    vision_text, vision_reason = accept_vision(supplied_vision, caption, title, frames_ok)
    speech, speech_source, asr = accept_speech(
        supplied_speech, caption, title, media, language, asr_backend, asr_model,
        bool(probe.get("has_audio")),
    )

    visual_text = ""
    if ocr.get("ok") and ocr.get("engine") not in (None, "", "none"):
        visual_text = (ocr.get("text") or "").strip()
    picture = bool(vision_text or visual_text)
    heard = bool(speech)
    limits: list[str] = []
    note_limits(limits, probe, frames, frames_ok, ocr, vision_reason, asr, speech_source, picture, heard)

    if picture and heard:
        kind = "media_understanding"
        method = "media_pipeline"
        ok = True
    elif heard:
        kind = "transcript"
        method = "public_api" if speech_source == "official_track" else "user_media_asr"
        ok = True
        add_limit(limits, "Graphics were not read.")
    elif picture:
        kind = "visual"
        method = "media_pipeline"
        ok = True
        add_limit(limits, "Speech was not read.")
    else:
        kind = "unavailable"
        method = "blocked"
        ok = False

    record = base_record(platform, url, title, author, caption)
    record.update(
        language=asr.get("language") if heard else None,
        body_text=build_body(vision_text, visual_text, speech),
        body_kind=kind,
        speech_text=speech,
        visual_text=visual_text,
        visual_description=vision_text,
        fetch_method=method,
        confidence=confidence_for(
            kind, truncated=bool(frames.get("truncated")),
            ocr_engine=ocr.get("engine") or "none", speech_source=speech_source,
        ),
        limits=limits,
        media_notes=media_notes(probe, digest, frames, ocr, asr),
    )
    ocr_name = ocr.get("engine") or "none"
    asr_name = asr.get("engine") or "none"
    understanding = build_understanding(
        record, ok=ok, ocr_reason=ocr.get("reason") or "", asr_reason=asr.get("reason") or "",
    )
    error = None
    if not ok:
        parts = ["Understanding blocked."]
        if ocr.get("reason") == "engine_missing":
            parts.append("OCR engine: none.")
        if asr.get("reason") == "engine_missing":
            parts.append("ASR engine: none.")
        if len(parts) == 1:
            parts.append("No speech, on-screen text, or visual description was produced.")
        error = " ".join(parts)
    return {
        "ok": ok,
        "complete": kind == "media_understanding",
        "blocked": not ok,
        "error": error,
        "understanding": understanding,
        "ocr_engine": ocr_name,
        "asr_engine": asr_name,
        "record": record,
        "evidence": {
            "media_path": str(media),
            "sha256": digest,
            "validated": True,
            "probe": probe,
            "frames": frames,
            "frames_json": frames.get("frames_json"),
            "ocr": ocr,
            "asr": asr,
            "vision": {"accepted": bool(vision_text), "reason": vision_reason},
        },
    }


def accept_vision(text: str, caption: str, title: str, frames_ok: bool) -> tuple[str, str]:
    cleaned = (text or "").strip()
    if not cleaned:
        return "", "not_provided"
    if not frames_ok:
        return "", "ignored_without_frames"
    why = matches_metadata(cleaned, caption, title)
    if why == "caption":
        return "", "ignored_matches_caption"
    if why == "title":
        return "", "ignored_matches_title"
    return cleaned, "accepted"


def accept_speech(supplied: str, caption: str, title: str, media: Path, language: str,
                  backend: str, model: str, has_audio: bool) -> tuple[str, str, dict]:
    cleaned = (supplied or "").strip()
    if cleaned:
        why = matches_metadata(cleaned, caption, title)
        if why:
            asr = run_asr(media, language, backend, model, has_audio)
            asr["supplied_speech_rejected"] = why
            if asr.get("ok"):
                return asr["text"], "asr", asr
            return "", "rejected_" + why, asr
        detected = None if language == "auto" else language
        asr = {
            "ok": True, "text": cleaned, "language": detected, "backend": "official_track",
            "model": None, "engine": "official_track", "media_path": str(media),
            "error": None, "reason": "official_track",
        }
        return cleaned, "official_track", asr
    asr = run_asr(media, language, backend, model, has_audio)
    if asr.get("ok"):
        return asr["text"], "asr", asr
    return "", asr.get("reason") or "none", asr


def note_limits(limits: list[str], probe: dict, frames: dict, frames_ok: bool, ocr: dict,
                vision_reason: str, asr: dict, speech_source: str, picture: bool, heard: bool) -> None:
    if frames.get("truncated"):
        add_limit(limits, "Frame extraction hit --max-frames; later frames were not read.")
    if probe.get("has_video") and not frames_ok:
        detail = " ".join((frames.get("error") or "Frames were not extracted.").split())
        add_limit(limits, clip_text(detail, 240))
    if not probe.get("has_video"):
        add_limit(limits, "The file has no video stream. Pictures were not read.")
    if ocr.get("reason") == "engine_missing":
        add_limit(limits, "OCR engine: none.")
    elif ocr.get("ok") and frames_ok and not (ocr.get("text") or "").strip():
        add_limit(limits, "OCR ran and found no burned-in text.")
    elif ocr.get("reason") == "error" and ocr.get("error"):
        add_limit(limits, "OCR failed: " + clip_text(ocr["error"], 200))
    if vision_reason == "ignored_without_frames":
        add_limit(limits, "A visual description was ignored because no frames were read from this file.")
    elif vision_reason == "ignored_matches_caption":
        add_limit(limits, "A visual description matched the share caption and was not used as pictures.")
    elif vision_reason == "ignored_matches_title":
        add_limit(limits, "A visual description matched the title and was not used as pictures.")
    elif vision_reason == "not_provided" and frames_ok and picture:
        add_limit(limits, "Visual description was not produced. Pictures in the summary are OCR text.")
    elif vision_reason == "not_provided" and frames_ok and not picture:
        add_limit(limits, "Visual description was not produced.")
    if speech_source == "official_track":
        add_limit(limits, "Speech text was supplied by the caller as an official track. This helper did not download that track.")
    if asr.get("supplied_speech_rejected") == "caption":
        add_limit(limits, "Supplied speech matched the share caption and was not used. Local ASR was tried instead.")
    elif asr.get("supplied_speech_rejected") == "title":
        add_limit(limits, "Supplied speech matched the title and was not used. Local ASR was tried instead.")
    if asr.get("reason") == "no_audio":
        add_limit(limits, "The file has no audio stream. Speech was not transcribed.")
    elif asr.get("reason") == "engine_missing":
        add_limit(limits, "ASR engine: none.")
    elif asr.get("reason") in {"empty", "error"} and not heard:
        add_limit(limits, "Speech was not transcribed.")
    if asr.get("backend") == "openai-api" and asr.get("ok"):
        add_limit(limits, "Speech was sent to the OpenAI Whisper API (whisper-1).")


def media_notes(probe: dict, digest: str, frames: dict, ocr: dict, asr: dict) -> str:
    count = len(frames.get("frames") or [])
    return (
        f"sha256={digest}; duration_sec={probe.get('duration_sec')}; "
        f"has_video={probe.get('has_video')}; has_audio={probe.get('has_audio')}; "
        f"frames={count}; truncated={bool(frames.get('truncated'))}; "
        f"frames_dir={frames.get('out_dir')}; ocr_engine={ocr.get('engine') or 'none'}; "
        f"asr_engine={asr.get('engine') or 'none'}; asr_model={asr.get('model')}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Understand a validated local media file (frames, OCR, speech). No URL downloader.",
        epilog="Missing OCR or ASR is engine: none. The share caption is metadata, never the body.",
    )
    parser.add_argument("--media", required=True, help="Path to a local audio/video file")
    parser.add_argument("--out-dir", default=None, help="Directory for extracted frames")
    parser.add_argument("--mode", choices=["fps", "scene"], default="fps")
    parser.add_argument("--fps", type=float, default=1.0)
    parser.add_argument("--scene-threshold", type=float, default=0.3)
    parser.add_argument("--max-frames", type=int, default=24)
    parser.add_argument("--frames-json", default=None, help="Reuse an extract_frames JSON for this same file")
    parser.add_argument("--ocr-engine", choices=["auto", "tesseract", "vision"], default="auto")
    parser.add_argument("--ocr-lang", default="chi_sim+eng")
    parser.add_argument("--asr-backend", choices=["local", "faster-whisper", "openai-whisper", "openai-api"],
                        default="local", help="local tries faster-whisper then openai-whisper and does not upload")
    parser.add_argument("--asr-model", default="base")
    parser.add_argument("--language", choices=["zh", "en", "auto"], default="auto")
    parser.add_argument("--speech-text", default=None, help="Official transcript text. Not a caption")
    parser.add_argument("--speech-file", default=None, help="Local file containing an official transcript")
    parser.add_argument("--visual-description", default=None, help="Host vision notes of the extracted frames")
    parser.add_argument("--visual-description-file", default=None, help="Local file of host vision notes")
    parser.add_argument("--caption", default="", help="Share caption. Stored as metadata only")
    parser.add_argument("--title", default="", help="Title. Stored as metadata only")
    parser.add_argument("--author", default="")
    parser.add_argument("--platform", default="")
    parser.add_argument("--url", default="")
    args = parser.parse_args(argv)
    try:
        result = understand(
            args.media, caption=args.caption, title=args.title, author=args.author,
            platform=args.platform, url=args.url, visual_description=args.visual_description,
            visual_description_file=args.visual_description_file, speech_text=args.speech_text,
            speech_file=args.speech_file, mode=args.mode, fps=args.fps,
            scene_threshold=args.scene_threshold, max_frames=args.max_frames, out_dir=args.out_dir,
            ocr_engine=args.ocr_engine, ocr_lang=args.ocr_lang, asr_backend=args.asr_backend,
            asr_model=args.asr_model, language=args.language, frames_json=args.frames_json,
        )
    except Exception as exc:
        result = blocked_result(
            f"Understanding failed ({type(exc).__name__}). The caption was not used as the body.",
            platform=args.platform, url=args.url, title=args.title, author=args.author,
            caption=args.caption, media_raw=args.media,
        )
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
