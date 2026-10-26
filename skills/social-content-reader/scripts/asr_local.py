#!/usr/bin/env python3
"""Transcribe a user-supplied local media file; emit one JSON record on stdout."""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import importlib
import json
import os
from pathlib import Path
import shutil
import sys


INSTALL_HINTS = (
    "Windows: python -m pip install faster-whisper (preferred), or "
    "python -m pip install openai-whisper; install ffmpeg with "
    "winget install --id Gyan.FFmpeg --exact, then reopen PowerShell. "
    "API alternative: python -m pip install openai and set OPENAI_API_KEY "
    "via your environment/secret store."
)
MODULES = {
    "faster-whisper": "faster_whisper",
    "openai-whisper": "whisper",
    "openai-api": "openai",
}


class ASRError(Exception):
    """An actionable error safe to include in the JSON response."""


def select_backend(requested: str) -> tuple[str, object]:
    """Fall back on unavailable imports only, never after inference/upload fails."""
    candidates = list(MODULES) if requested == "auto" else [requested]
    unavailable = []
    for backend in candidates:
        if backend == "openai-api" and not os.environ.get("OPENAI_API_KEY"):
            unavailable.append("openai-api: OPENAI_API_KEY is not set")
            continue
        try:
            return backend, importlib.import_module(MODULES[backend])
        except (ImportError, OSError) as exc:
            unavailable.append(f"{backend}: import unavailable ({type(exc).__name__})")
    raise ASRError("; ".join(unavailable) + ". " + INSTALL_HINTS)


def transcribe(media: Path, language: str | None, backend: str,
               model: str, module: object) -> tuple[str, str | None]:
    if backend == "faster-whisper":
        engine = module.WhisperModel(model, device="cpu", compute_type="int8")
        segments, info = engine.transcribe(str(media), language=language, task="transcribe")
        # Iteration is required: faster-whisper performs inference lazily.
        text = "".join(segment.text for segment in segments)
        return text.strip(), info.language

    if backend == "openai-whisper":
        if not shutil.which("ffmpeg"):
            raise ASRError("openai-whisper requires ffmpeg on PATH. " + INSTALL_HINTS)
        engine = module.load_model(model, device="cpu")
        result = engine.transcribe(str(media), language=language, task="transcribe",
                                   fp16=False, verbose=False)
        return result["text"].strip(), result.get("language")

    # whisper-1 accepts a limited set of upload formats and files up to 25 MB.
    if media.suffix.lower() not in {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"}:
        raise ASRError("API upload format unsupported by this helper; convert to MP3/WAV "
                       "with ffmpeg or use a local backend. " + INSTALL_HINTS)
    if media.stat().st_size > 25_000_000:
        raise ASRError("API upload exceeds the helper's 25 MB limit; compress/split with "
                       "ffmpeg or use a local backend. " + INSTALL_HINTS)
    options = {"model": model, "response_format": "verbose_json"}
    if language:
        options["language"] = language
    # Use the official endpoint; do not forward uploads to an implicit custom base URL.
    with module.OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                       base_url="https://api.openai.com/v1",
                       timeout=120.0, max_retries=0) as client:
        with media.open("rb") as audio:
            result = client.audio.transcriptions.create(file=audio, **options)
    detected = getattr(result, "language", None) or language
    detected = {"english": "en", "chinese": "zh"}.get(
        str(detected).lower(), detected
    )
    return result.text.strip(), detected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Transcribe a local audio/video file to JSON (no URL downloader).",
        epilog=INSTALL_HINTS,
    )
    parser.add_argument("--media", required=True, help="Path to user-provided audio/video")
    parser.add_argument("--language", choices=["zh", "en", "auto"], default="auto")
    parser.add_argument("--model", default="base",
                        help="Local Whisper model, e.g. tiny/base/small/medium/large-v3; "
                             "API always uses whisper-1. Default: base")
    parser.add_argument("--backend", choices=["auto", *MODULES], default="auto",
                        help="auto: faster-whisper, then openai-whisper, then OpenAI API "
                             "(uploads media when OPENAI_API_KEY is set)")
    args = parser.parse_args(argv)
    record = {"ok": False, "text": "", "language": None,
              "backend": args.backend, "model": args.model, "media_path": args.media}
    try:
        # Keep library chatter/progress off the machine-readable stdout stream.
        with redirect_stdout(sys.stderr):
            media = Path(args.media).expanduser().resolve()
            record["media_path"] = str(media)
            if not media.is_file():
                raise ASRError("Media file not found or not a regular file: " + str(media))
            if media.stat().st_size == 0:
                raise ASRError("Media file is empty: " + str(media))
            backend, module = select_backend(args.backend)
            model = "whisper-1" if backend == "openai-api" else args.model
            record.update(backend=backend, model=model)
            language = None if args.language == "auto" else args.language
            text, detected = transcribe(media, language, backend, model, module)
            record.update(text=text, language=detected)
            if not text:
                raise ASRError("No speech text returned; check audio and language. "
                               "Do not substitute the caption for a transcript.")
            record["ok"] = True
    except ASRError as exc:
        record["error"] = str(exc)
    except Exception as exc:
        # SDK exceptions can contain credentials/request bodies; never print them.
        status = getattr(exc, "status_code", None)
        detail = f"; HTTP {status}" if isinstance(status, int) else ""
        record["error"] = (
            f"Transcription failed ({type(exc).__name__}{detail}). "
            "Check media/audio, model availability, disk/memory and, for API, key/network/quota. "
            "No runtime fallback or automatic retry was attempted. " + INSTALL_HINTS
        )
    print(json.dumps(record, ensure_ascii=True))
    return 0 if record["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
