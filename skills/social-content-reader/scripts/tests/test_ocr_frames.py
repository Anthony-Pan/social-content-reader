"""OCR helper checks. No tesseract binary and no network required."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "ocr_frames", Path(__file__).resolve().parents[1] / "ocr_frames.py"
)
ocr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocr)


class OCRUnitTests(unittest.TestCase):
    def test_choose_lang_falls_back_when_chinese_data_is_missing(self):
        self.assertEqual(ocr.choose_lang({"eng"}, "chi_sim+eng"), "eng")
        self.assertEqual(ocr.choose_lang({"chi_sim", "eng"}, "chi_sim+eng"), "chi_sim+eng")
        self.assertEqual(ocr.choose_lang({"eng", "osd"}, "eng"), "eng")

    def test_parse_tesseract_lang_list(self):
        text = "List of available languages (2):\neng\nchi_sim\n"
        self.assertEqual(ocr.parse_tesseract_langs(text), {"eng", "chi_sim"})

    def test_combine_drops_empty_and_consecutive_duplicates(self):
        frames = [
            {"timestamp_sec": 0, "text": "Hello  world"},
            {"timestamp_sec": 1, "text": "Hello world"},
            {"timestamp_sec": 2, "text": ""},
            {"timestamp_sec": 3.5, "text": "Next line"},
        ]
        self.assertEqual(
            ocr.combine_ocr_text(frames),
            "[0.00s] Hello world\n[3.50s] Next line",
        )

    def test_refuses_url(self):
        with self.assertRaises(ocr.OCRError):
            ocr.assert_local_image("https://example.com/frame.jpg")

    def test_missing_engine_degrades(self):
        with tempfile.TemporaryDirectory() as temp:
            image = Path(temp) / "frame.jpg"
            image.write_bytes(b"\xff\xd8\xff not really jpeg but a non-empty file")
            output, diagnostics = io.StringIO(), io.StringIO()
            with patch.object(ocr.shutil, "which", return_value=None), \
                 patch.object(ocr, "vision_available", return_value=False), \
                 redirect_stdout(output), redirect_stderr(diagnostics):
                code = ocr.main(["--frame", str(image), "--engine", "auto"])
        record = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertFalse(record["ok"])
        self.assertEqual(record["engine"], "none")
        self.assertEqual(record["text"], "")
        self.assertIn("tesseract", record["error"])
        self.assertIn("brew install tesseract", record["error"])

    def test_tesseract_maps_text_without_calling_a_real_binary(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "a.jpg"
            second = root / "b.jpg"
            first.write_bytes(b"jpeg-a")
            second.write_bytes(b"jpeg-b")
            payload = {
                "frames": [
                    {"path": str(first), "timestamp_sec": 0},
                    {"path": str(second), "timestamp_sec": 1},
                ]
            }
            spec_path = root / "frames.json"
            spec_path.write_text(json.dumps(payload), encoding="utf-8")

            def fake_run(cmd, **kwargs):
                class Proc:
                    returncode = 0
                    stdout = ""
                    stderr = ""
                proc = Proc()
                if "--list-langs" in cmd:
                    proc.stdout = "List of available languages (1):\neng\n"
                elif "stdout" in cmd:
                    proc.stdout = "ON SCREEN" if cmd[1].endswith("a.jpg") else "SPOKEN CUE"
                else:
                    proc.returncode = 1
                    proc.stderr = "unexpected"
                return proc

            output = io.StringIO()
            with patch.object(ocr.shutil, "which", return_value="/usr/bin/tesseract"), \
                 patch.object(ocr.subprocess, "run", side_effect=fake_run), \
                 redirect_stdout(output):
                code = ocr.main(["--frames-json", str(spec_path), "--lang", "chi_sim+eng"])
        record = json.loads(output.getvalue())
        self.assertEqual(code, 0, record.get("error"))
        self.assertTrue(record["ok"])
        self.assertEqual(record["engine"], "tesseract")
        self.assertEqual(record["language"], "eng")
        self.assertIn("[0.00s] ON SCREEN", record["text"])
        self.assertIn("[1.00s] SPOKEN CUE", record["text"])
        self.assertEqual(len(record["frames"]), 2)


if __name__ == "__main__":
    unittest.main()
