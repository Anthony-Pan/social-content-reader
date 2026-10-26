"""Douyin acquire checks. No browser, no network, no caption-as-body."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import Mock


spec = importlib.util.spec_from_file_location(
    "acquire_douyin", Path(__file__).resolve().parents[1] / "acquire_douyin.py"
)
acquire = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acquire)


PLAYWM = (
    "https://m.douyin.com/aweme/v1/playwm/?video_id=v0abc123&line=0&token=secret"
)


class ParseTests(unittest.TestCase):
    def test_aweme_id_from_mobile_share_and_desktop_urls(self):
        samples = [
            "https://m.douyin.com/share/video/7696098282904259850",
            "https://www.douyin.com/video/7696098282904259850?previous_page=app_code_link",
            "https://www.iesdouyin.com/share/video/7696098282904259850/?from_ssr=1",
        ]
        for sample in samples:
            self.assertEqual(acquire.aweme_id_from_text(sample), "7696098282904259850")

    def test_short_link_follows_public_redirect_then_stops(self):
        def fetch(url):
            if "v.douyin.com" in url:
                return 302, "https://www.iesdouyin.com/share/video/7696098282904259850/", ""
            raise AssertionError("should not fetch past the id: " + url)
        found = acquire.resolve_aweme_id("https://v.douyin.com/2qulGbSTiRI/", fetch=fetch)
        self.assertEqual(found, "7696098282904259850")

    def test_out_dir_file_is_video_mp4(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            dest = acquire.media_dest(temp)
            self.assertEqual(dest.name, "video.mp4")
            self.assertEqual(dest.parent, Path(temp).resolve())
            self.assertTrue(dest.parent.is_dir())

    def test_share_page_is_mobile_not_iesdouyin(self):
        self.assertEqual(
            acquire.share_page_url("7696098282904259850"),
            "https://m.douyin.com/share/video/7696098282904259850",
        )

    def test_pick_playwm_over_other_srcs_and_ignore_blob(self):
        chosen = acquire.pick_video_src([
            {"src": "blob:https://m.douyin.com/1234", "currentSrc": ""},
            {"src": "https://m.douyin.com/aweme/v1/playwm/?video_id=v0abc", "currentSrc": ""},
        ])
        self.assertIn("/aweme/v1/playwm", chosen)
        self.assertTrue(chosen.startswith("https://"))

    def test_prefers_current_src_playwm(self):
        chosen = acquire.pick_video_src([{
            "src": "",
            "currentSrc": PLAYWM,
        }])
        self.assertEqual(chosen, PLAYWM)

    def test_redact_drops_token_and_keeps_video_id(self):
        redacted = acquire.redact_play_url(PLAYWM)
        self.assertIn("video_id=v0abc123", redacted)
        self.assertNotIn("token", redacted)
        self.assertNotIn("secret", redacted)
        self.assertTrue(redacted.startswith("https://m.douyin.com/aweme/v1/playwm"))

    def test_rejects_private_and_non_https_srcs(self):
        self.assertIsNone(acquire.pick_video_src([
            {"src": "http://m.douyin.com/aweme/v1/playwm/?video_id=v0", "currentSrc": ""},
            {"src": "https://127.0.0.1/aweme/v1/playwm/?video_id=v0", "currentSrc": ""},
            {"src": "https://192.168.1.5/video.mp4", "currentSrc": ""},
        ]))

    def test_wall_without_src_is_failure_and_mentions_caption_is_not_the_body(self):
        message = acquire.failure_reason("7696098282904259850", wall=True, captcha=False)
        self.assertIn(acquire.WALL_TEXT, message)
        self.assertIn("m.douyin.com/share/video/7696098282904259850", message)
        self.assertIn("caption", message.lower())
        self.assertIn("not", message.lower())

    def test_validate_media_accepts_ftyp_and_rejects_html(self):
        mp4 = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 5000
        self.assertIsNone(acquire.validate_media(mp4, "application/octet-stream"))
        self.assertIsNone(acquire.validate_media(b"\x00" * 8000, "video/mp4"))
        html = b"<html>" + b"x" * 8000
        self.assertIsNotNone(acquire.validate_media(html, "text/html"))
        self.assertIsNotNone(acquire.validate_media(b"{}", "application/json"))
        self.assertIsNotNone(acquire.validate_media(b"tiny", "video/mp4"))

    def test_success_record_does_not_carry_a_caption_body(self):
        record = acquire.success_record(
            "7696098282904259850",
            "https://m.douyin.com/share/video/7696098282904259850",
            Path("/tmp/video.mp4"),
            8_000_000,
            "video/mp4",
            PLAYWM,
        )
        self.assertTrue(record["ok"])
        self.assertEqual(record["path"], "/tmp/video.mp4")
        self.assertEqual(record["bytes"], 8_000_000)
        self.assertEqual(record["content_type"], "video/mp4")
        self.assertEqual(record["aweme_id"], "7696098282904259850")
        self.assertEqual(record["play_url"], PLAYWM)
        self.assertTrue(record["acquired"])
        self.assertEqual(record["fetch_method"], "playwright_playwm")
        self.assertFalse(record["caption_used_as_body"])
        self.assertNotIn("caption", record)

    def test_missing_playwright_is_honest(self):
        def boom():
            raise acquire.AcquireError("playwright is not installed. " + acquire.INSTALL_HINT)

        original = acquire.load_playwright
        acquire.load_playwright = boom
        try:
            output = io.StringIO()
            with redirect_stdout(output), redirect_stderr(io.StringIO()):
                code = acquire.main([
                    "--url", "https://v.douyin.com/2qulGbSTiRI/",
                    "--aweme-id", "7696098282904259850",
                ])
        finally:
            acquire.load_playwright = original
        record = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertFalse(record["ok"])
        self.assertFalse(record["acquired"])
        self.assertFalse(record["caption_used_as_body"])
        self.assertIn("playwright", record["error"])
        self.assertIn("caption", record["error"].lower())
        self.assertIsNone(record["path"])
        self.assertIsNone(record["play_url"])
        for key in ("ok", "path", "bytes", "content_type", "aweme_id", "play_url"):
            self.assertIn(key, record)


class BrowserFlowTests(unittest.TestCase):
    def test_download_uses_referer_and_same_context(self):
        body = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 5000
        response = Mock()
        response.status = 200
        response.body.return_value = body
        response.headers = {"content-type": "video/mp4"}
        context = Mock()
        context.request.get.return_value = response
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "7696098282904259850.mp4"
            saved = acquire.download_play_url(
                context, PLAYWM,
                "https://m.douyin.com/share/video/7696098282904259850",
                dest,
            )
            context.request.get.assert_called_once()
            args, kwargs = context.request.get.call_args
            self.assertEqual(args[0], PLAYWM)
            self.assertEqual(
                kwargs["headers"]["Referer"],
                "https://m.douyin.com/share/video/7696098282904259850",
            )
            self.assertEqual(saved["content_type"], "video/mp4")
            self.assertTrue(dest.is_file())
            self.assertGreater(dest.stat().st_size, 4096)

    def test_browser_flow_visits_homepage_then_mobile_share(self):
        body = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 5000
        response = Mock(status=200, headers={"content-type": "video/mp4"})
        response.body.return_value = body
        page = Mock()
        page.evaluate.return_value = {
            "videos": [{"src": "", "currentSrc": PLAYWM}],
            "wall": False,
            "captcha": False,
        }
        context = Mock()
        context.request.get.return_value = response
        context.new_page.return_value = page
        browser = Mock()
        browser.new_context.return_value = context
        chromium = Mock()
        chromium.launch.return_value = browser
        playwright = Mock()
        playwright.chromium = chromium
        module = Mock()
        module.sync_playwright.return_value.__enter__ = Mock(return_value=playwright)
        module.sync_playwright.return_value.__exit__ = Mock(return_value=False)

        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "7696098282904259850.mp4"
            record = acquire.acquire_with_browser("7696098282904259850", dest, module)
            self.assertTrue(dest.is_file())
        urls = [call.args[0] for call in page.goto.call_args_list]
        self.assertEqual(urls[0], "https://www.douyin.com/")
        self.assertEqual(urls[1], "https://m.douyin.com/share/video/7696098282904259850")
        self.assertTrue(record["ok"])
        self.assertTrue(record["acquired"])
        self.assertFalse(record["caption_used_as_body"])
        self.assertEqual(record["path"], str(dest))
        self.assertEqual(record["play_url"], PLAYWM)
        self.assertEqual(record["bytes"], len(body))
        self.assertEqual(record["content_type"], "video/mp4")

    def test_wall_without_video_src_does_not_download(self):
        page = Mock()
        page.evaluate.return_value = {"videos": [], "wall": True, "captcha": False}
        context = Mock()
        context.new_page.return_value = page
        browser = Mock()
        browser.new_context.return_value = context
        playwright = Mock()
        playwright.chromium.launch.return_value = browser
        module = Mock()
        module.sync_playwright.return_value.__enter__ = Mock(return_value=playwright)
        module.sync_playwright.return_value.__exit__ = Mock(return_value=False)
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "7696098282904259850.mp4"
            with self.assertRaises(acquire.AcquireError) as caught:
                acquire.acquire_with_browser("7696098282904259850", dest, module)
            self.assertFalse(dest.exists())
        self.assertIn(acquire.WALL_TEXT, str(caught.exception))
        self.assertIn("caption", str(caught.exception).lower())
        context.request.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
