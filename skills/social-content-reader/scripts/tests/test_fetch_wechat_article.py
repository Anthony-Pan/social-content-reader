"""Offline unit tests for WeChat 公众号 article fetch/parse."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"

spec = importlib.util.spec_from_file_location(
    "fetch_wechat_article", ROOT / "fetch_wechat_article.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class ParseBodyTests(unittest.TestCase):
    def test_rsa_snippet_accepts_ssr_visibility_hidden(self):
        html = load("wechat_rsa_snippet.html")
        result = mod.parse_article_html(
            html, "https://mp.weixin.qq.com/s/Rsa54LdbyhXIHheJYO6gkw"
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "ok")
        self.assertGreaterEqual(result["body_chars"], 40)
        self.assertIn("招商", result["body_text"])
        self.assertTrue(result["ssr_visibility_hidden"])
        self.assertEqual(result["title"], "一个错误，让我客户痛苦失去200万")
        self.assertEqual(result["body_kind"], "article")
        self.assertEqual(result["embed_count"], 0)

    def test_captcha_shell_is_captcha_required(self):
        with self.assertRaises(mod.FetchError) as ctx:
            mod.parse_article_html(load("wechat_captcha_shell.html"), "https://mp.weixin.qq.com/s/x")
        self.assertEqual(ctx.exception.status, "captcha_required")

    def test_display_none_rejected_even_with_long_text(self):
        with self.assertRaises(mod.FetchError) as ctx:
            mod.parse_article_html(load("wechat_display_none.html"), "https://mp.weixin.qq.com/s/x")
        self.assertEqual(ctx.exception.status, "unavailable")
        self.assertIn("display:none", ctx.exception.message)


class EmbedExtractionTests(unittest.TestCase):
    def test_extracts_three_mpvideo_vids(self):
        html = load("wechat_anm_embeds.html")
        embeds = mod.extract_mpvideo_embeds(html)
        vids = [e["vid"] for e in embeds]
        self.assertEqual(
            vids,
            [
                "wxv_4683490097843765252",
                "wxv_4683473112590647297",
                "wxv_4683357298663309319",
            ],
        )
        for e in embeds:
            self.assertIn("action=mpvideo", e["player_url"])
            self.assertIn(e["vid"], e["player_url"])

    def test_parse_includes_embeds(self):
        result = mod.parse_article_html(
            load("wechat_anm_embeds.html"),
            "https://mp.weixin.qq.com/s/aNmLs3qJVhFGcgtGxAVlig",
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["embed_count"], 3)
        self.assertGreaterEqual(result["body_chars"], 40)


class FetchHtmlGuardTests(unittest.TestCase):
    def test_rejects_non_https_and_wrong_host(self):
        for url in [
            "http://mp.weixin.qq.com/s/x",
            "https://evil.example/s/x",
            "https://user:pass@mp.weixin.qq.com/s/x",
            "file:///tmp/x",
        ]:
            with self.subTest(url=url), self.assertRaises(mod.FetchError):
                mod.fetch_html(url, timeout=1)


class OptionalMediaTests(unittest.TestCase):
    def test_try_embed_media_reports_missing_playwright(self):
        embeds = [{"vid": "wxv_1", "player_url": "https://mp.weixin.qq.com/mp/readtemplate?t=pages/video_player_tmpl&action=mpvideo&auto=0&vid=wxv_1"}]
        real_import = __import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "playwright.sync_api" or name == "playwright":
                raise ImportError("no playwright")
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=fake_import):
            result = mod.try_acquire_first_embed(embeds, Path("/tmp"), referer="https://mp.weixin.qq.com/s/x")
        self.assertIsNotNone(result)
        self.assertFalse(result["ok"])
        self.assertIn("playwright", result["error"])

    def test_article_ok_without_out_dir_skips_media(self):
        result = mod.fetch_article(
            "https://mp.weixin.qq.com/s/Rsa54LdbyhXIHheJYO6gkw",
            out_dir=None,
            try_embed_media=True,
            html=load("wechat_rsa_snippet.html"),
        )
        self.assertTrue(result["ok"])
        self.assertNotIn("embed_media", result)



class CliTests(unittest.TestCase):
    def test_html_file_cli(self):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(io.StringIO()):
            code = mod.main([
                "https://mp.weixin.qq.com/s/Rsa54LdbyhXIHheJYO6gkw",
                "--html-file",
                str(FIXTURES / "wechat_rsa_snippet.html"),
                "--no-embed-media",
            ])
        record = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertTrue(record["ok"])
        self.assertGreaterEqual(record["body_chars"], 40)


class AcquireMediaWireTests(unittest.TestCase):
    def test_acquire_media_routes_wechat_without_ffmpeg(self):
        import sys
        sys.path.insert(0, str(ROOT))
        import acquire_media as am

        html = load("wechat_rsa_snippet.html")

        def fake_fetch(url, out_dir=None, try_embed_media=True, **kwargs):
            return mod.fetch_article(
                url, out_dir=out_dir, try_embed_media=False, html=html
            )

        with patch.dict("sys.modules", {}), \
             patch("fetch_wechat_article.fetch_article", fake_fetch):
            # Import path used inside acquire: from fetch_wechat_article import fetch_article
            import fetch_wechat_article as fwa
            with patch.object(fwa, "fetch_article", fake_fetch), \
                 patch.object(am.shutil, "which", return_value=None):
                # Ensure we don't require ffmpeg for wechat path even if which is None
                result = am.acquire(
                    "https://mp.weixin.qq.com/s/Rsa54LdbyhXIHheJYO6gkw",
                    out_dir=Path("/tmp/scr-wechat-test-out"),
                )
        self.assertTrue(result["ok"])
        self.assertEqual(result["platform"], "wechat-article")
        self.assertEqual(result["body_kind"], "article")
        self.assertIn("body_text", result)
        self.assertNotIn("error", result)


if __name__ == "__main__":
    unittest.main()
