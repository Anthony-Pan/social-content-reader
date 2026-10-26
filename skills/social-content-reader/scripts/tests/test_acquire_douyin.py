"""Checks for the Mac-verified Douyin helper. No browser and no network."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "acquire_douyin", Path(__file__).resolve().parents[1] / "acquire_douyin.py"
)
acquire = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acquire)


class ParseTests(unittest.TestCase):
    def test_numeric_aweme_id(self):
        self.assertEqual(acquire.parse_aweme_id("7696098282904259850"), "7696098282904259850")

    def test_video_url_id(self):
        self.assertEqual(
            acquire.parse_aweme_id("https://www.douyin.com/video/7696098282904259850"),
            "7696098282904259850",
        )
        self.assertEqual(
            acquire.parse_aweme_id("https://m.douyin.com/share/video/7696098282904259850"),
            "7696098282904259850",
        )

    def test_short_link_is_resolved_in_the_browser_not_by_regex(self):
        self.assertEqual(acquire.parse_aweme_id("https://v.douyin.com/2qulGbSTiRI/"), "")


class CliTests(unittest.TestCase):
    def test_missing_playwright_is_honest_and_has_no_caption_body(self):
        real_import = __import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "playwright.sync_api" or name == "playwright":
                raise ImportError("playwright not installed")
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=fake_import):
            result = acquire.acquire("https://v.douyin.com/2qulGbSTiRI/", Path("/tmp"))
        self.assertFalse(result["ok"])
        self.assertIn("playwright", result["error"])
        self.assertNotIn("path", result)
        self.assertNotIn("body_text", result)

    def test_cli_takes_positional_url_and_out_dir(self):
        captured = {}

        def fake_acquire(url_or_id, out_dir):
            captured["url"] = url_or_id
            captured["out"] = out_dir
            return {
                "ok": True,
                "path": str(Path(out_dir) / "douyin_7696098282904259850.mp4"),
                "bytes": 8_000_000,
                "content_type": "video/mp4",
                "aweme_id": "7696098282904259850",
                "play_url": "https://m.douyin.com/aweme/v1/playwm/?video_id=v0abc",
            }

        output = io.StringIO()
        argv = [
            "acquire_douyin.py",
            "https://v.douyin.com/2qulGbSTiRI/",
            "--out-dir",
            "/tmp/douyin-out",
        ]
        with patch.object(acquire, "acquire", fake_acquire), \
             patch.object(acquire.sys, "argv", argv), \
             redirect_stdout(output), redirect_stderr(io.StringIO()):
            code = acquire.main()
        record = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(captured["url"], "https://v.douyin.com/2qulGbSTiRI/")
        self.assertEqual(captured["out"], Path("/tmp/douyin-out"))
        for key in ("ok", "path", "bytes", "content_type", "aweme_id", "play_url"):
            self.assertIn(key, record)
        self.assertTrue(record["ok"])
        self.assertTrue(record["path"].endswith("douyin_7696098282904259850.mp4"))
        self.assertEqual(record["bytes"], 8_000_000)
        self.assertIn("/aweme/v1/playwm", record["play_url"])


if __name__ == "__main__":
    unittest.main()
