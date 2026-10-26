#!/usr/bin/env python3
"""OCR burned-in text from local frame images. One JSON object on stdout.

Engines:
  tesseract  CLI on PATH (preferred)
  vision     macOS Vision via swiftc + ocr_vision.swift, when tesseract is absent

If neither engine is available the command fails honestly (ok: false, engine: none).
It does not invent on-screen text and does not download URLs.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


INSTALL_HINT = (
    "Optional OCR. macOS: brew install tesseract tesseract-lang. "
    "Windows: winget install --id UB-Mannheim.TesseractOCR --exact, then reopen the shell. "
    "Linux: install tesseract-ocr and, for Chinese burned-in text, tesseract-ocr-chi-sim. "
    "macOS alternative: Xcode swiftc on PATH and --engine vision "
    "(scripts/ocr_vision.swift). "
    "If OCR is unavailable, use the host vision tool on the frame files and say OCR did not run. "
    "Do not invent burned-in text from the share caption."
)

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
SCRIPT_DIR = Path(__file__).resolve().parent
VISION_SOURCE = SCRIPT_DIR / "ocr_vision.swift"


class OCRError(Exception):
    """An actionable error safe to include in the JSON response."""


def choose_lang(available: set[str], requested: str) -> str:
    parts = [part for part in (requested or "").split("+") if part]
    if parts and all(part in available for part in parts):
        return "+".join(parts)
    if "chi_sim" in available and "eng" in available:
        return "chi_sim+eng"
    if "eng" in available:
        return "eng"
    if available:
        return sorted(available)[0]
    raise OCRError(
        "tesseract has no language data. Install eng and, for Chinese text, chi_sim. "
        + INSTALL_HINT
    )


def parse_tesseract_langs(output: str) -> set[str]:
    langs = set()
    for line in (output or "").splitlines():
        line = line.strip()
        if not line or line.lower().startswith("list of"):
            continue
        langs.add(line)
    return langs


def combine_ocr_text(frames: list[dict]) -> str:
    """Join frame text. Drop empty lines and consecutive duplicates (static titles)."""
    lines = []
    previous = None
    for frame in frames:
        text = " ".join((frame.get("text") or "").split())
        if not text or text == previous:
            continue
        previous = text
        timestamp = frame.get("timestamp_sec")
        if isinstance(timestamp, (int, float)):
            lines.append(f"[{float(timestamp):.2f}s] {text}")
        else:
            lines.append(text)
    return "\n".join(lines)


def assert_local_image(raw: str) -> Path:
    lowered = raw.strip().lower()
    if lowered.startswith(("http://", "https://", "ftp://")):
        raise OCRError("Refusing a URL. OCR reads local frame files only.")
    path = Path(raw).expanduser().resolve()
    if not path.is_file():
        raise OCRError("Frame not found or not a regular file: " + str(path))
    if path.stat().st_size == 0:
        raise OCRError("Frame is empty: " + str(path))
    if path.suffix.lower() not in IMAGE_SUFFIXES:
        raise OCRError("Unsupported frame type (want an image file): " + str(path))
    return path


def load_frame_specs(frames_json: str | None, frame_args: list[str] | None,
                     directory: str | None) -> list[dict]:
    specs: list[dict] = []
    if frames_json:
        payload = json.loads(Path(frames_json).expanduser().read_text(encoding="utf-8"))
        items = payload.get("frames", []) if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            raise OCRError("--frames-json must be a list or an object with a frames array")
        for item in items:
            if isinstance(item, str):
                specs.append({"path": item, "timestamp_sec": None})
            elif isinstance(item, dict) and item.get("path"):
                specs.append({
                    "path": item["path"],
                    "timestamp_sec": item.get("timestamp_sec"),
                })
    for raw in frame_args or []:
        specs.append({"path": raw, "timestamp_sec": None})
    if directory:
        folder = Path(directory).expanduser().resolve()
        if not folder.is_dir():
            raise OCRError("Frame directory not found: " + str(folder))
        for path in sorted(folder.iterdir()):
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
                specs.append({"path": str(path), "timestamp_sec": None})
    if not specs:
        raise OCRError("No frames. Pass --frames-json, --frame, or --dir.")
    return specs


def tesseract_langs(binary: str) -> set[str]:
    proc = subprocess.run(
        [binary, "--list-langs"],
        capture_output=True, text=True, timeout=30, errors="replace",
    )
    return parse_tesseract_langs((proc.stdout or "") + "\n" + (proc.stderr or ""))


def ocr_tesseract(binary: str, image: Path, lang: str, psm: int) -> str:
    proc = subprocess.run(
        [binary, str(image), "stdout", "-l", lang, "--psm", str(psm)],
        capture_output=True, text=True, timeout=60, errors="replace",
    )
    if proc.returncode != 0:
        detail = " ".join(((proc.stderr or "") + (proc.stdout or "")).split())
        if len(detail) > 300:
            detail = detail[-300:]
        raise OCRError(detail or f"tesseract exited {proc.returncode}")
    return (proc.stdout or "").strip()


def vision_available() -> bool:
    return sys.platform == "darwin" and shutil.which("swiftc") is not None and VISION_SOURCE.is_file()


def compile_vision(cache: dict) -> str:
    if "binary" in cache:
        return cache["binary"]
    if not VISION_SOURCE.is_file():
        raise OCRError("ocr_vision.swift is missing next to ocr_frames.py")
    swiftc = shutil.which("swiftc")
    if not swiftc:
        raise OCRError("swiftc not on PATH. " + INSTALL_HINT)
    dest = Path(tempfile.mkdtemp(prefix="scr-vision-")) / "ocr_vision"
    proc = subprocess.run(
        [swiftc, "-O", "-o", str(dest), str(VISION_SOURCE)],
        capture_output=True, text=True, timeout=180, errors="replace",
    )
    if proc.returncode != 0 or not dest.is_file():
        detail = " ".join(((proc.stderr or "") + (proc.stdout or "")).split())
        if len(detail) > 300:
            detail = detail[-300:]
        raise OCRError("swiftc failed to build ocr_vision.swift. " + detail)
    cache["binary"] = str(dest)
    return cache["binary"]


def ocr_vision(image: Path, cache: dict) -> str:
    binary = compile_vision(cache)
    proc = subprocess.run(
        [binary, str(image)],
        capture_output=True, text=True, timeout=60, errors="replace",
    )
    if proc.returncode != 0:
        detail = " ".join((proc.stderr or "").split())
        raise OCRError(detail or f"vision OCR exited {proc.returncode}")
    return (proc.stdout or "").strip()


def select_engine(requested: str) -> str:
    tesseract = shutil.which("tesseract")
    if requested == "tesseract":
        if not tesseract:
            raise OCRError("tesseract not on PATH. " + INSTALL_HINT)
        return "tesseract"
    if requested == "vision":
        if not vision_available():
            raise OCRError(
                "macOS Vision OCR needs darwin, swiftc on PATH, and ocr_vision.swift. "
                + INSTALL_HINT
            )
        return "vision"
    if tesseract:
        return "tesseract"
    if vision_available():
        return "vision"
    raise OCRError("No OCR engine on PATH. " + INSTALL_HINT)


def ocr(frames_json: str | None, frame_args: list[str] | None, directory: str | None,
        engine: str, lang: str, psm: int, max_frames: int) -> dict:
    if max_frames < 1 or max_frames > 300:
        raise OCRError("--max-frames must be between 1 and 300")
    if psm < 0 or psm > 13:
        raise OCRError("--psm must be a tesseract page-segmentation mode (0-13)")
    specs = load_frame_specs(frames_json, frame_args, directory)
    truncated = len(specs) > max_frames
    specs = specs[:max_frames]
    selected = select_engine(engine)
    language = None
    binary = shutil.which("tesseract")
    if selected == "tesseract":
        language = choose_lang(tesseract_langs(binary), lang)

    vision_cache: dict = {}
    results = []
    failures = 0
    for spec in specs:
        try:
            path = assert_local_image(spec["path"])
            if selected == "tesseract":
                text = ocr_tesseract(binary, path, language, psm)
            else:
                text = ocr_vision(path, vision_cache)
            results.append({
                "path": str(path),
                "timestamp_sec": spec.get("timestamp_sec"),
                "text": text,
                "error": None,
            })
        except OCRError as exc:
            failures += 1
            results.append({
                "path": spec.get("path"),
                "timestamp_sec": spec.get("timestamp_sec"),
                "text": "",
                "error": str(exc),
            })
    if results and failures == len(results):
        raise OCRError(results[0]["error"] or "OCR failed on every frame")
    note = None
    if failures:
        note = f"OCR failed on {failures} of {len(results)} frames"
    return {
        "ok": True,
        "engine": selected,
        "language": language,
        "text": combine_ocr_text(results),
        "truncated": truncated,
        "frames": results,
        "error": note,
    }


def empty_record() -> dict:
    return {
        "ok": False,
        "engine": "none",
        "language": None,
        "text": "",
        "truncated": False,
        "frames": [],
        "error": None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="OCR local frame images (tesseract, or macOS Vision). No URL downloader.",
        epilog=INSTALL_HINT,
    )
    parser.add_argument("--frames-json", default=None,
                        help="extract_frames.py JSON, or a JSON list of frame paths")
    parser.add_argument("--frame", action="append", default=None,
                        help="Local image path. Repeat for more frames")
    parser.add_argument("--dir", default=None, help="Directory of frame images")
    parser.add_argument("--engine", choices=["auto", "tesseract", "vision"], default="auto")
    parser.add_argument("--lang", default="chi_sim+eng",
                        help="Requested tesseract languages. Falls back when data is missing. Default: chi_sim+eng")
    parser.add_argument("--psm", type=int, default=6,
                        help="tesseract page segmentation mode. Default: 6")
    parser.add_argument("--max-frames", type=int, default=48,
                        help="Cap frames read (1-300). Default: 48")
    args = parser.parse_args(argv)
    record = empty_record()
    try:
        record = ocr(
            args.frames_json, args.frame, args.dir,
            args.engine, args.lang, args.psm, args.max_frames,
        )
    except OCRError as exc:
        record["error"] = str(exc)
    except Exception as exc:
        record["error"] = f"OCR failed ({type(exc).__name__}). " + INSTALL_HINT
    print(json.dumps(record, ensure_ascii=True))
    return 0 if record["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
