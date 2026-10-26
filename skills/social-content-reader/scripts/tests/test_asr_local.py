"""Behavior checks with stubs: no models, media downloads, or API calls."""

from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location(
    "asr_local", Path(__file__).resolve().parents[1] / "asr_local.py"
)
asr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asr)


class ASRTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.media = Path(self.temp.name) / "speech.wav"
        self.media.write_bytes(b"stub media; never decoded")

    def run_cli(self, *args):
        output, diagnostics = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(diagnostics):
            code = asr.main(["--media", str(self.media), *args])
        return code, json.loads(output.getvalue()), diagnostics.getvalue()

    def test_auto_selects_first_importable_backend(self):
        for available, expected in [
            ({"faster_whisper", "whisper", "openai"}, "faster-whisper"),
            ({"whisper", "openai"}, "openai-whisper"),
            ({"openai"}, "openai-api"),
        ]:
            with self.subTest(backend=expected):
                def load(name):
                    if name in available:
                        return name
                    raise ImportError("unavailable")
                with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True), \
                     patch.object(asr.importlib, "import_module", side_effect=load):
                    backend, _ = asr.select_backend("auto")
                self.assertEqual(backend, expected)

    def test_api_requires_key_without_import_or_upload(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(asr.importlib, "import_module") as importer:
            code, record, _ = self.run_cli("--backend", "openai-api")
        self.assertEqual(code, 1)
        self.assertIn("OPENAI_API_KEY", record["error"])
        importer.assert_not_called()

    def test_missing_dependencies_include_windows_install_hints(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(asr.importlib, "import_module", side_effect=ImportError):
            code, record, _ = self.run_cli()
        self.assertEqual(code, 1)
        self.assertFalse(record["ok"])
        for text in ["pip install faster-whisper", "pip install openai-whisper", "winget", "ffmpeg"]:
            self.assertIn(text, record["error"])

    def test_faster_whisper_consumes_generator_and_preserves_unicode(self):
        def segments():
            print("backend progress")
            yield SimpleNamespace(text=" \u4f60\u597d")
            yield SimpleNamespace(text=" world")
        engine = Mock()
        engine.transcribe.return_value = (segments(), SimpleNamespace(language="zh"))
        module = SimpleNamespace(WhisperModel=Mock(return_value=engine))
        with patch.object(asr, "select_backend", return_value=("faster-whisper", module)):
            code, record, diagnostics = self.run_cli("--language", "auto", "--model", "tiny")
        self.assertEqual(code, 0)
        self.assertEqual(record["text"], "\u4f60\u597d world")
        self.assertEqual(record["language"], "zh")
        self.assertIn("backend progress", diagnostics)
        module.WhisperModel.assert_called_once_with("tiny", device="cpu", compute_type="int8")
        self.assertIsNone(engine.transcribe.call_args.kwargs["language"])

    def test_openai_whisper_cpu_and_explicit_language(self):
        engine = Mock()
        engine.transcribe.return_value = {"text": " Hello ", "language": "en"}
        module = SimpleNamespace(load_model=Mock(return_value=engine))
        with patch.object(asr, "select_backend", return_value=("openai-whisper", module)), \
             patch.object(asr.shutil, "which", return_value="ffmpeg.exe"):
            code, record, _ = self.run_cli("--language", "en")
        self.assertEqual(code, 0)
        self.assertEqual(record["text"], "Hello")
        self.assertEqual(engine.transcribe.call_args.kwargs["language"], "en")
        self.assertFalse(engine.transcribe.call_args.kwargs["fp16"])

    def test_missing_ffmpeg_does_not_load_model(self):
        module = SimpleNamespace(load_model=Mock())
        with patch.object(asr, "select_backend", return_value=("openai-whisper", module)), \
             patch.object(asr.shutil, "which", return_value=None):
            code, record, _ = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("ffmpeg", record["error"])
        module.load_model.assert_not_called()

    def test_api_upload_model_language_and_closed_file(self):
        client = Mock()
        client.audio.transcriptions.create.return_value = SimpleNamespace(text=" Speech ", language="english")
        context = Mock()
        context.__enter__ = Mock(return_value=client)
        context.__exit__ = Mock(return_value=False)
        module = SimpleNamespace(OpenAI=Mock(return_value=context))
        with patch.object(asr, "select_backend", return_value=("openai-api", module)), \
             patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            code, record, _ = self.run_cli("--language", "en", "--model", "tiny")
        self.assertEqual(code, 0)
        self.assertEqual(record["model"], "whisper-1")
        self.assertEqual(record["language"], "en")
        options = client.audio.transcriptions.create.call_args.kwargs
        self.assertEqual(options["language"], "en")
        self.assertEqual(options["response_format"], "verbose_json")
        self.assertTrue(options["file"].closed)
        self.assertEqual(module.OpenAI.call_args.kwargs["base_url"], "https://api.openai.com/v1")

    def test_api_rejects_oversized_or_unsupported_files_before_upload(self):
        module = SimpleNamespace(OpenAI=Mock())
        with self.media.open("r+b") as audio:
            audio.truncate(25_000_001)
        with patch.object(asr, "select_backend", return_value=("openai-api", module)):
            code, record, _ = self.run_cli()
            self.assertEqual(code, 1)
            self.assertIn("25 MB", record["error"])
            self.media = self.media.with_suffix(".avi")
            self.media.write_bytes(b"stub")
            code, record, _ = self.run_cli()
            self.assertEqual(code, 1)
            self.assertIn("format", record["error"])
        module.OpenAI.assert_not_called()

    def test_runtime_error_is_redacted_and_never_falls_back(self):
        module = SimpleNamespace(WhisperModel=Mock(side_effect=RuntimeError("secret-body")))
        with patch.object(asr, "select_backend", return_value=("faster-whisper", module)) as select:
            code, record, _ = self.run_cli()
        self.assertEqual(code, 1)
        self.assertNotIn("secret-body", record["error"])
        self.assertEqual(record["backend"], "faster-whisper")
        select.assert_called_once()

    def test_empty_transcript_fails(self):
        with patch.object(asr, "select_backend", return_value=("faster-whisper", Mock())), \
             patch.object(asr, "transcribe", return_value=("", "en")):
            code, record, _ = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("No speech", record["error"])

    def test_missing_or_empty_media_never_selects_backend(self):
        for remove in [False, True]:
            with self.subTest(missing=remove):
                self.media.write_bytes(b"")
                if remove:
                    self.media.unlink()
                with patch.object(asr, "select_backend") as select:
                    code, record, _ = self.run_cli()
                self.assertEqual(code, 1)
                self.assertFalse(record["ok"])
                select.assert_not_called()


if __name__ == "__main__":
    unittest.main()
