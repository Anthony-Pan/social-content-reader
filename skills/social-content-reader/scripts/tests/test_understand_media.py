"""Understanding glue. Stubs prove the join; the ffmpeg test uses a generated file.

No platform download, model weight, or caption-as-body.
"""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "understand_media", Path(__file__).resolve().parents[1] / "understand_media.py"
)
understand = importlib.util.module_from_spec(spec)
spec.loader.exec_module(understand)


CAPTION = "CAPTION_SENTINEL_share_text"
TITLE = "TITLE_SENTINEL_upload_name"
SPEECH = "spoken words from the file"
OCR_TEXT = "[0.00s] ON SCREEN HELLO"
VISION = "A person holds a red card toward the camera."


def probe_av():
    return {
        "ok": True, "validated": True, "duration_sec": 2.5,
        "has_video": True, "has_audio": True, "codecs": ["h264", "aac"], "error": None,
    }


def probe_video_only():
    data = probe_av()
    data["has_audio"] = False
    data["codecs"] = ["h264"]
    return data


def probe_audio_only():
    data = probe_av()
    data["has_video"] = False
    data["codecs"] = ["aac"]
    return data


class UnderstandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.media = Path(self.temp.name) / "clip.mp4"
        self.media.write_bytes(b"stub-media-bytes")
        self.frame = Path(self.temp.name) / "frame_0001.jpg"
        self.frame.write_bytes(b"\xff\xd8\xff\xd9")

    def run_cli(self, *args):
        output, diagnostics = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(diagnostics):
            code = understand.main(list(args))
        return code, json.loads(output.getvalue()), diagnostics.getvalue()

    def frames_record(self):
        return {
            "ok": True,
            "media_path": str(self.media),
            "frames": [{"index": 0, "path": str(self.frame), "timestamp_sec": 0.0}],
            "truncated": False,
            "out_dir": self.temp.name,
            "error": None,
            "duration_sec": 2.5,
        }

    def test_url_is_refused_and_does_not_read(self):
        with patch.object(understand, "probe_media") as probe, \
             patch.object(understand.extract_frames, "extract") as extract, \
             patch.object(understand.asr_local, "transcribe") as transcribe:
            code, result, _ = self.run_cli(
                "--media", "https://example.com/video.mp4", "--caption", CAPTION, "--title", TITLE,
            )
        self.assertEqual(code, 1)
        self.assertFalse(result["ok"])
        self.assertTrue(result["blocked"])
        self.assertFalse(result["evidence"]["validated"])
        self.assertIn("Refusing a URL", result["error"])
        self.assertEqual(result["record"]["body_kind"], "unavailable")
        self.assertEqual(result["record"]["fetch_method"], "blocked")
        self.assertEqual(result["record"]["body_text"], "The video was not read.")
        self.assertEqual(result["record"]["caption"], CAPTION)
        self.assertNotIn(CAPTION, result["understanding"])
        self.assertNotIn(TITLE, result["understanding"])
        self.assertNotIn(CAPTION, result["record"]["body_text"])
        probe.assert_not_called()
        extract.assert_not_called()
        transcribe.assert_not_called()

    def test_unvalidated_file_does_not_call_helpers(self):
        if not shutil.which("ffprobe"):
            self.skipTest("ffprobe not installed")
        with patch.object(understand.extract_frames, "extract") as extract, \
             patch.object(understand.ocr_frames, "ocr") as ocr, \
             patch.object(understand.asr_local, "select_backend") as select_backend:
            code, result, _ = self.run_cli("--media", str(self.media), "--caption", CAPTION)
        self.assertEqual(code, 1)
        self.assertFalse(result["evidence"]["validated"])
        self.assertIn("not read", result["error"].lower())
        self.assertNotIn(CAPTION, result["understanding"])
        self.assertEqual(result["record"]["speech_text"], "")
        self.assertEqual(result["record"]["visual_text"], "")
        extract.assert_not_called()
        ocr.assert_not_called()
        select_backend.assert_not_called()

    def test_missing_engines_are_none_and_caption_is_not_the_body(self):
        def explode_ocr(requested):
            raise understand.ocr_frames.OCRError("No OCR engine on PATH. install tesseract")

        def explode_asr(requested):
            raise understand.asr_local.ASRError(f"{requested}: import unavailable")

        with patch.object(understand, "probe_media", return_value=probe_av()), \
             patch.object(understand.extract_frames, "extract", return_value=self.frames_record()), \
             patch.object(understand.ocr_frames, "select_engine", side_effect=explode_ocr), \
             patch.object(understand.asr_local, "select_backend", side_effect=explode_asr), \
             patch.object(understand.asr_local, "transcribe") as transcribe:
            code, result, _ = self.run_cli(
                "--media", str(self.media), "--caption", CAPTION, "--title", TITLE,
                "--platform", "youtube", "--url", "https://www.youtube.com/watch?v=abc",
            )
        self.assertEqual(code, 1)
        self.assertFalse(result["ok"])
        self.assertFalse(result["complete"])
        self.assertTrue(result["blocked"])
        self.assertEqual(result["ocr_engine"], "none")
        self.assertEqual(result["asr_engine"], "none")
        self.assertEqual(result["evidence"]["ocr"]["reason"], "engine_missing")
        self.assertEqual(result["evidence"]["asr"]["reason"], "engine_missing")
        self.assertIn("OCR engine: none", result["error"])
        self.assertIn("ASR engine: none", result["error"])
        self.assertIn("OCR engine: none", result["understanding"])
        self.assertIn("ASR engine: none", result["understanding"])
        self.assertNotIn(CAPTION, result["understanding"])
        self.assertNotIn(TITLE, result["understanding"])
        record = result["record"]
        self.assertEqual(record["body_kind"], "unavailable")
        self.assertEqual(record["fetch_method"], "blocked")
        self.assertEqual(record["body_text"], "The video was not read.")
        self.assertEqual(record["speech_text"], "")
        self.assertEqual(record["visual_text"], "")
        self.assertEqual(record["visual_description"], "")
        self.assertEqual(record["caption"], CAPTION)
        self.assertEqual(record["title"], TITLE)
        self.assertEqual(record["platform"], "youtube")
        self.assertNotIn(CAPTION, record["body_text"])
        self.assertIn("OCR engine: none.", record["limits"])
        self.assertIn("ASR engine: none.", record["limits"])
        transcribe.assert_not_called()

    def test_frames_ocr_and_asr_become_media_understanding(self):
        seen = []

        def select(requested):
            seen.append(requested)
            if requested == "openai-api":
                raise AssertionError("local mode must not select the API")
            if requested == "faster-whisper":
                raise understand.asr_local.ASRError("faster-whisper missing")
            return "openai-whisper", object()

        with patch.object(understand, "probe_media", return_value=probe_av()), \
             patch.object(understand.extract_frames, "extract", return_value=self.frames_record()), \
             patch.object(understand.ocr_frames, "ocr", return_value={
                 "ok": True, "engine": "tesseract", "language": "eng", "text": OCR_TEXT,
                 "truncated": False, "frames": [], "error": None,
             }), \
             patch.object(understand.asr_local, "select_backend", side_effect=select), \
             patch.object(understand.asr_local, "transcribe", return_value=(SPEECH, "en")):
            code, result, _ = self.run_cli(
                "--media", str(self.media), "--caption", CAPTION, "--title", TITLE,
                "--visual-description", VISION, "--author", "Ada",
            )
        self.assertEqual(seen, ["faster-whisper", "openai-whisper"])
        self.assertEqual(code, 0)
        self.assertTrue(result["ok"])
        self.assertTrue(result["complete"])
        self.assertFalse(result["blocked"])
        self.assertIsNone(result["error"])
        self.assertEqual(result["ocr_engine"], "tesseract")
        self.assertEqual(result["asr_engine"], "openai-whisper")
        record = result["record"]
        self.assertEqual(record["body_kind"], "media_understanding")
        self.assertEqual(record["fetch_method"], "media_pipeline")
        self.assertEqual(record["confidence"], "high")
        self.assertEqual(record["speech_text"], SPEECH)
        self.assertEqual(record["visual_text"], OCR_TEXT)
        self.assertEqual(record["visual_description"], VISION)
        self.assertEqual(record["language"], "en")
        self.assertEqual(record["author"], "Ada")
        self.assertIn("Pictures: " + VISION, record["body_text"])
        self.assertIn("On-screen text: " + OCR_TEXT, record["body_text"])
        self.assertIn("Speech: " + SPEECH, record["body_text"])
        self.assertNotIn(CAPTION, record["body_text"])
        self.assertNotIn(TITLE, record["body_text"])
        self.assertIn("Pictures and speech", result["understanding"])
        self.assertIn(SPEECH, result["understanding"])
        self.assertIn(OCR_TEXT, result["understanding"])
        self.assertIn(VISION, result["understanding"])
        self.assertIn("metadata, not the video body", result["understanding"])
        self.assertIn(CAPTION, result["understanding"])
        self.assertLess(result["understanding"].index("Pictures and speech"), result["understanding"].index(CAPTION))
        self.assertEqual(result["evidence"]["sha256"], hashlib.sha256(b"stub-media-bytes").hexdigest())
        self.assertTrue(result["evidence"]["vision"]["accepted"])

    def test_vision_and_speech_with_ocr_engine_none_stays_honest(self):
        def explode_ocr(requested):
            raise understand.ocr_frames.OCRError("tesseract not on PATH.")

        with patch.object(understand, "probe_media", return_value=probe_av()), \
             patch.object(understand.extract_frames, "extract", return_value=self.frames_record()), \
             patch.object(understand.ocr_frames, "select_engine", side_effect=explode_ocr), \
             patch.object(understand.asr_local, "select_backend", return_value=("faster-whisper", object())), \
             patch.object(understand.asr_local, "transcribe", return_value=("你好", "zh")):
            code, result, _ = self.run_cli(
                "--media", str(self.media), "--visual-description", VISION, "--caption", CAPTION,
            )
        self.assertEqual(code, 0)
        self.assertTrue(result["ok"])
        self.assertTrue(result["complete"])
        self.assertEqual(result["ocr_engine"], "none")
        self.assertEqual(result["asr_engine"], "faster-whisper")
        self.assertEqual(result["record"]["visual_text"], "")
        self.assertEqual(result["record"]["visual_description"], VISION)
        self.assertEqual(result["record"]["speech_text"], "你好")
        self.assertEqual(result["record"]["confidence"], "medium")
        self.assertIn("OCR engine: none.", result["record"]["limits"])
        self.assertNotIn(CAPTION, result["record"]["body_text"])

    def test_caption_is_not_accepted_as_vision_or_speech(self):
        with patch.object(understand, "probe_media", return_value=probe_av()), \
             patch.object(understand.extract_frames, "extract", return_value=self.frames_record()), \
             patch.object(understand.ocr_frames, "ocr", return_value={
                 "ok": True, "engine": "tesseract", "language": "eng", "text": "",
                 "truncated": False, "frames": [], "error": None,
             }), \
             patch.object(understand.asr_local, "select_backend", return_value=("faster-whisper", object())), \
             patch.object(understand.asr_local, "transcribe", return_value=(SPEECH, "en")):
            code, result, _ = self.run_cli(
                "--media", str(self.media), "--caption", CAPTION, "--title", TITLE,
                "--visual-description", "  " + CAPTION + "  ",
                "--speech-text", TITLE,
            )
        self.assertEqual(code, 0)
        record = result["record"]
        self.assertEqual(record["visual_description"], "")
        self.assertEqual(record["speech_text"], SPEECH)
        self.assertEqual(record["body_kind"], "transcript")
        self.assertFalse(result["complete"])
        self.assertIn("matched the share caption", " ".join(record["limits"]))
        self.assertIn("matched the title", " ".join(record["limits"]))
        self.assertIn("Graphics were not read.", record["limits"])
        self.assertNotIn(CAPTION, record["body_text"])
        self.assertNotIn(TITLE, record["speech_text"])

    def test_video_without_audio_skips_asr(self):
        with patch.object(understand, "probe_media", return_value=probe_video_only()), \
             patch.object(understand.extract_frames, "extract", return_value=self.frames_record()), \
             patch.object(understand.ocr_frames, "ocr", return_value={
                 "ok": True, "engine": "tesseract", "language": "eng", "text": OCR_TEXT,
                 "truncated": False, "frames": [], "error": None,
             }), \
             patch.object(understand.asr_local, "select_backend") as select_backend:
            code, result, _ = self.run_cli("--media", str(self.media), "--caption", CAPTION)
        self.assertEqual(code, 0)
        self.assertEqual(result["record"]["body_kind"], "visual")
        self.assertEqual(result["record"]["fetch_method"], "media_pipeline")
        self.assertEqual(result["asr_engine"], "none")
        self.assertEqual(result["evidence"]["asr"]["reason"], "no_audio")
        self.assertEqual(result["record"]["speech_text"], "")
        self.assertIn("no audio stream", " ".join(result["record"]["limits"]).lower())
        self.assertIn("Pictures only", result["understanding"])
        self.assertNotIn(CAPTION, result["record"]["body_text"])
        select_backend.assert_not_called()

    def test_audio_only_is_transcript_and_does_not_extract_frames(self):
        with patch.object(understand, "probe_media", return_value=probe_audio_only()), \
             patch.object(understand.extract_frames, "extract") as extract, \
             patch.object(understand.ocr_frames, "ocr") as ocr, \
             patch.object(understand.asr_local, "select_backend", return_value=("faster-whisper", object())), \
             patch.object(understand.asr_local, "transcribe", return_value=(SPEECH, "en")):
            code, result, _ = self.run_cli(
                "--media", str(self.media),
                "--visual-description", VISION,
            )
        self.assertEqual(code, 0)
        self.assertEqual(result["record"]["body_kind"], "transcript")
        self.assertEqual(result["record"]["fetch_method"], "user_media_asr")
        self.assertEqual(result["record"]["visual_description"], "")
        self.assertEqual(result["evidence"]["vision"]["reason"], "ignored_without_frames")
        self.assertIn("no frames were read", " ".join(result["record"]["limits"]))
        self.assertIn("Graphics were not read.", result["record"]["limits"])
        self.assertIn(SPEECH, result["record"]["body_text"])
        self.assertNotIn(VISION, result["record"]["body_text"])
        extract.assert_not_called()
        ocr.assert_not_called()

    def test_official_track_plus_frames_skips_asr(self):
        speech_file = Path(self.temp.name) / "cc.txt"
        speech_file.write_text("official closed caption line\n", encoding="utf-8")
        with patch.object(understand, "probe_media", return_value=probe_av()), \
             patch.object(understand.extract_frames, "extract", return_value=self.frames_record()), \
             patch.object(understand.ocr_frames, "ocr", return_value={
                 "ok": True, "engine": "tesseract", "language": "eng", "text": OCR_TEXT,
                 "truncated": False, "frames": [], "error": None,
             }), \
             patch.object(understand.asr_local, "select_backend") as select_backend:
            code, result, _ = self.run_cli(
                "--media", str(self.media), "--speech-file", str(speech_file),
                "--visual-description", VISION,
            )
        self.assertEqual(code, 0)
        self.assertTrue(result["complete"])
        self.assertEqual(result["asr_engine"], "official_track")
        self.assertEqual(result["record"]["speech_text"], "official closed caption line")
        self.assertEqual(result["record"]["fetch_method"], "media_pipeline")
        self.assertEqual(result["record"]["confidence"], "medium")
        self.assertIn("official track", " ".join(result["record"]["limits"]))
        select_backend.assert_not_called()

    def test_reused_frames_must_match_the_media_file(self):
        other = Path(self.temp.name) / "other.mp4"
        other.write_bytes(b"other")
        payload = self.frames_record()
        payload["media_path"] = str(other)
        spec_path = Path(self.temp.name) / "frames.json"
        spec_path.write_text(json.dumps(payload), encoding="utf-8")
        with patch.object(understand, "probe_media", return_value=probe_av()), \
             patch.object(understand.extract_frames, "extract") as extract, \
             patch.object(understand.asr_local, "transcribe") as transcribe:
            code, result, _ = self.run_cli(
                "--media", str(self.media), "--frames-json", str(spec_path), "--caption", CAPTION,
            )
        self.assertEqual(code, 1)
        self.assertIn("does not match", result["error"])
        self.assertNotIn(CAPTION, result["understanding"])
        extract.assert_not_called()
        transcribe.assert_not_called()

    def test_reused_frames_skip_extraction(self):
        payload = self.frames_record()
        spec_path = Path(self.temp.name) / "frames.json"
        spec_path.write_text(json.dumps(payload), encoding="utf-8")
        with patch.object(understand, "probe_media", return_value=probe_av()), \
             patch.object(understand.extract_frames, "extract") as extract, \
             patch.object(understand.ocr_frames, "ocr", return_value={
                 "ok": True, "engine": "tesseract", "language": "eng", "text": OCR_TEXT,
                 "truncated": False, "frames": [], "error": None,
             }), \
             patch.object(understand.asr_local, "select_backend", return_value=("faster-whisper", object())), \
             patch.object(understand.asr_local, "transcribe", return_value=(SPEECH, "en")):
            code, result, _ = self.run_cli(
                "--media", str(self.media), "--frames-json", str(spec_path),
                "--visual-description-file", self.write_text("vision.txt", VISION),
            )
        self.assertEqual(code, 0)
        self.assertTrue(result["complete"])
        self.assertEqual(result["evidence"]["frames"]["reason"], "reused")
        self.assertEqual(result["record"]["visual_description"], VISION)
        extract.assert_not_called()

    def write_text(self, name, text):
        path = Path(self.temp.name) / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_generated_sample_does_not_invent_speech_or_caption(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("ffmpeg not installed")
        sample = Path(self.temp.name) / "sample.mp4"
        out = Path(self.temp.name) / "out"
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "testsrc=duration=1:size=160x120:rate=10",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
                "-map", "0:v", "-map", "1:a", "-shortest",
                "-pix_fmt", "yuv420p", str(sample),
            ],
            check=True, timeout=60,
        )
        code, result, _ = self.run_cli(
            "--media", str(sample), "--out-dir", str(out),
            "--max-frames", "4", "--fps", "1",
            "--caption", CAPTION, "--title", TITLE,
        )
        self.assertTrue(result["evidence"]["validated"], result.get("error"))
        self.assertGreater(result["evidence"]["probe"]["duration_sec"], 0)
        self.assertTrue(result["evidence"]["probe"]["has_video"])
        self.assertTrue(result["evidence"]["probe"]["has_audio"])
        frames = result["evidence"]["frames"]["frames"]
        self.assertGreaterEqual(len(frames), 1)
        self.assertTrue(Path(frames[0]["path"]).is_file())
        record = result["record"]
        for field in ("body_text", "speech_text", "visual_text", "visual_description"):
            self.assertNotIn(CAPTION, record[field])
            self.assertNotIn(TITLE, record[field])
        self.assertEqual(record["caption"], CAPTION)
        self.assertNotEqual(record["body_kind"], "caption")
        self.assertEqual(len(result["evidence"]["sha256"]), 64)
        if result["ocr_engine"] == "none":
            self.assertEqual(record["visual_text"], "")
        if result["asr_engine"] == "none":
            self.assertEqual(record["speech_text"], "")
        if result["ocr_engine"] == "none" and result["asr_engine"] == "none":
            self.assertEqual(code, 1)
            self.assertFalse(result["ok"])
            self.assertTrue(result["blocked"])
            self.assertFalse(result["complete"])
            self.assertEqual(record["fetch_method"], "blocked")
            self.assertEqual(record["body_kind"], "unavailable")
            self.assertEqual(record["body_text"], "The video was not read.")
            self.assertNotIn(CAPTION, result["understanding"])
            self.assertNotIn(TITLE, result["understanding"])
            self.assertIn("OCR engine: none", result["understanding"])
            self.assertIn("ASR engine: none", result["understanding"])
        elif result["ok"]:
            self.assertIn("metadata, not the video body", result["understanding"])


if __name__ == "__main__":
    unittest.main()
