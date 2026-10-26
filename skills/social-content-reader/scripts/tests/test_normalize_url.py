"""URL detect checks: no network.

``https://weixin.qq.com/sph/AAZ3p39sQm`` normalizes to a 视频号 share id.
A 2026-10-26 WebFetch of that page returned a caption (Codex token waste;
brainstorm in ChatGPT first). That caption is metadata, not Understanding.
"""

import importlib.util
import unittest
from pathlib import Path


spec = importlib.util.spec_from_file_location(
    "normalize_url", Path(__file__).resolve().parents[1] / "normalize_url.py"
)
normalize_url = importlib.util.module_from_spec(spec)
spec.loader.exec_module(normalize_url)


class NormalizeUrlTests(unittest.TestCase):
    def test_sph_aaz3_caption_is_not_understanding(self):
        got = normalize_url.detect("https://weixin.qq.com/sph/AAZ3p39sQm")
        self.assertEqual(got["platform"], "wechat-channels")
        self.assertEqual(got["canonical_id"], "AAZ3p39sQm")
        self.assertEqual(got["link_form"], "sph_share")
        limits = " ".join(got["limits"])
        self.assertIn("caption", limits)
        self.assertNotIn("enough to understand", limits)

    def test_weixin_sph_share_link(self):
        got = normalize_url.detect("https://weixin.qq.com/sph/AAZ3p39sQm")
        self.assertEqual(got["platform"], "wechat-channels")
        self.assertEqual(got["canonical_id"], "AAZ3p39sQm")
        self.assertEqual(got["canonical_url"], "https://weixin.qq.com/sph/AAZ3p39sQm")
        self.assertEqual(got["link_form"], "sph_share")
        self.assertTrue(any("caption" in item for item in got["limits"]))

    def test_www_sph_share_strips_host_and_query(self):
        got = normalize_url.detect(
            "https://www.weixin.qq.com/sph/AAZ3p39sQm?from=share#t"
        )
        self.assertEqual(got["platform"], "wechat-channels")
        self.assertEqual(got["canonical_id"], "AAZ3p39sQm")
        self.assertEqual(got["canonical_url"], "https://weixin.qq.com/sph/AAZ3p39sQm")
        self.assertEqual(got["link_form"], "sph_share")

    def test_sph_share_without_scheme_preserves_id_case(self):
        got = normalize_url.detect("weixin.qq.com/sph/AbC_d-12/")
        self.assertEqual(got["canonical_id"], "AbC_d-12")
        self.assertEqual(got["canonical_url"], "https://weixin.qq.com/sph/AbC_d-12")

    def test_channels_web_host_stays_wechat_channels_without_sph_id(self):
        raw = "https://channels.weixin.qq.com/web/pages/live?finderUsername=test"
        got = normalize_url.detect(raw)
        self.assertEqual(got["platform"], "wechat-channels")
        self.assertNotIn("canonical_id", got)
        self.assertNotEqual(got.get("link_form"), "sph_share")
        self.assertTrue(any("consumer fetch" in item for item in got["limits"]))

    def test_channels_host_does_not_steal_sph_substring(self):
        got = normalize_url.detect("https://channels.weixin.qq.com/sph/AAZ3p39sQm")
        self.assertEqual(got["platform"], "wechat-channels")
        self.assertNotEqual(got.get("link_form"), "sph_share")
        self.assertNotIn("canonical_id", got)

    def test_other_weixin_host_stays_unknown(self):
        got = normalize_url.detect("https://weixin.qq.com/")
        self.assertEqual(got["platform"], "unknown")


if __name__ == "__main__":
    unittest.main()
