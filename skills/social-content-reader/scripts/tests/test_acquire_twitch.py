"""Twitch public acquire: clip vs VOD, explicit sections, no silent trim."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import acquire_media as media
import acquire_twitch as tw


LONG = "https://www.twitch.tv/videos/2096474672"
SHORT = "https://www.twitch.tv/videos/2128758214"
CLIP = "https://clips.twitch.tv/FaintLightGullWholeWheat"
MAX = 128 * 1024 ** 2


def formats(*rows):
    return [{"format_id": fid, "height": height, "vcodec": "avc1", "acodec": "mp4a.40.2"} for fid, height in rows]


def long_meta():
    return {
        "duration": 15434,
        "is_live": False,
        "live_status": "was_live",
        "formats": formats(("160p30", 160), ("480p30", 480), ("Source", 1080))
        + [{"format_id": "sb0", "height": 124, "vcodec": "none", "acodec": "none", "protocol": "mhtml"},
           {"format_id": "Audio_Only", "height": None, "vcodec": "none", "acodec": "mp4a.40.2"}],
    }


def source_only(duration):
    return {"duration": duration, "formats": formats(("Source", 1080))}


class ClassifyTests(unittest.TestCase):
    def test_clip_and_vod_urls(self):
        cases = {
            CLIP: ("clip", "FaintLightGullWholeWheat", "https://clips.twitch.tv/FaintLightGullWholeWheat"),
            "https://www.twitch.tv/ea/clip/FaintLightGullWholeWheat": (
                "clip", "FaintLightGullWholeWheat", "https://clips.twitch.tv/FaintLightGullWholeWheat"),
            "https://clips.twitch.tv/embed?clip=FaintLightGullWholeWheat&parent=example.com": (
                "clip", "FaintLightGullWholeWheat", "https://clips.twitch.tv/FaintLightGullWholeWheat"),
            LONG: ("vod", "2096474672", "https://www.twitch.tv/videos/2096474672"),
            "https://m.twitch.tv/videos/2096474672": (
                "vod", "2096474672", "https://www.twitch.tv/videos/2096474672"),
            "https://player.twitch.tv/?parent=example.com&video=v2096474672": (
                "vod", "2096474672", "https://www.twitch.tv/videos/2096474672"),
            "https://www.twitch.tv/riotgames/v/6528877": (
                "vod", "6528877", "https://www.twitch.tv/videos/6528877"),
            "https://www.twitch.tv/foo/schedule?vodID=99": (
                "vod", "99", "https://www.twitch.tv/videos/99"),
        }
        for url, expected in cases.items():
            with self.subTest(url=url):
                info = tw.classify_twitch(url)
                self.assertEqual((info["kind"], info["id"], info["canonical_url"]), expected)
                routed = media.route(url)
                self.assertEqual(routed[0], "twitch")
                self.assertEqual(routed[1], expected[2])

    def test_bookmark_is_not_part_of_the_canonical_url(self):
        info = tw.classify_twitch("https://www.twitch.tv/videos/2096474672?t=1h2m3s")
        self.assertEqual(info["canonical_url"], "https://www.twitch.tv/videos/2096474672")
        self.assertEqual(info["bookmark_sec"], 3723)
        self.assertIsNone(tw.classify_twitch(CLIP)["bookmark_sec"])

    def test_channel_live_and_lists_are_not_media(self):
        for url in (
            "https://www.twitch.tv/twitch",
            "https://www.twitch.tv/twitch/videos",
            "https://www.twitch.tv/twitch/clips",
            "https://www.twitch.tv/collections/abc",
            "https://twitch.tv/",
            "file:///tmp/x",
            "https://user:pass@www.twitch.tv/videos/1",
        ):
            with self.subTest(url=url), self.assertRaises(tw.TwitchError):
                tw.classify_twitch(url)
            if url.startswith("https://www.twitch.tv") or url.startswith("https://twitch.tv"):
                with self.subTest(route=url), self.assertRaises(media.AcquireError):
                    media.route(url)

    def test_channel_failure_names_twitch_and_has_no_body(self):
        with tempfile.TemporaryDirectory() as temp:
            result = media.acquire("https://www.twitch.tv/twitch", Path(temp))
        self.assertFalse(result["ok"])
        self.assertEqual(result["platform"], "twitch")
        self.assertNotIn("body_text", result)
        self.assertNotIn("path", result)
        self.assertIn("not a clip or VOD", result["error"])


class SectionAndPlanTests(unittest.TestCase):
    def test_parse_section_forms(self):
        self.assertEqual(tw.parse_section("0-20"), (0, 20))
        self.assertEqual(tw.parse_section("*1:00:00-1:00:20"), (3600, 3620))
        self.assertEqual(tw.parse_section("5m10s-5m40s"), (310, 340))
        self.assertEqual(tw.parse_section("0-end"), (0, None))
        for bad in ("20", "20-10", "end-10", "-5-10", "1h-"):
            with self.subTest(bad=bad), self.assertRaises(tw.TwitchError):
                tw.parse_section(bad)

    def test_prefers_480p_over_source_and_ignores_storyboard(self):
        chosen = tw.choose_format(long_meta()["formats"])
        self.assertEqual(chosen["format_id"], "480p30")
        self.assertEqual(tw.choose_format(formats(("Source", 1080)))["format_id"], "Source")
        clip = tw.choose_format([{
            "format_id": "1080", "height": 1080, "vcodec": None, "acodec": None, "protocol": "https",
        }])
        self.assertEqual(clip["format_id"], "1080")
        with self.assertRaises(tw.TwitchError):
            tw.choose_format([{"format_id": "Audio_Only", "height": None, "vcodec": "none", "acodec": "mp4a.40.2"}])

    def test_long_vod_refuses_before_a_silent_prefix(self):
        with self.assertRaises(tw.TwitchError) as ctx:
            tw.plan_window("vod", 15434, long_meta()["formats"], None, MAX, bookmark_sec=3723)
        text = str(ctx.exception)
        self.assertIn("15434", text)
        self.assertIn("600", text)
        self.assertIn("--section", text)
        self.assertIn("bookmark", text)
        self.assertNotIn("http", text)

    def test_section_limits_fail_closed(self):
        with self.assertRaises(tw.TwitchError) as too_long:
            tw.plan_window("vod", 15434, long_meta()["formats"], (0, 601), MAX)
        self.assertIn("601", str(too_long.exception))
        with self.assertRaises(tw.TwitchError) as outside:
            tw.plan_window("vod", 15434, long_meta()["formats"], (16000, 16100), MAX)
        self.assertIn("outside", str(outside.exception))
        with self.assertRaises(tw.TwitchError):
            tw.plan_window("vod", 15434, long_meta()["formats"], (0, None), MAX)

    def test_source_only_vod_over_default_cap_is_refused_before_download(self):
        with self.assertRaises(tw.TwitchError) as ctx:
            tw.plan_window("vod", 402, formats(("Source", 1080)), None, MAX)
        self.assertIn("before download", str(ctx.exception))
        self.assertIn("1080", str(ctx.exception))

    def test_twenty_second_section_of_long_vod_is_allowed(self):
        plan = tw.plan_window("vod", 15434, long_meta()["formats"], (0, 20), MAX)
        self.assertFalse(plan["full"])
        self.assertEqual(plan["format_id"], "480p30")
        self.assertEqual(plan["window"], 20)
        self.assertLess(plan["estimated_bytes"], MAX)
        args = tw.download_args("https://www.twitch.tv/videos/2096474672", Path("/tmp/w"), plan, MAX)
        self.assertIn("--ignore-config", args)
        self.assertIn("--download-sections", args)
        self.assertIn("*0.000-20.000", args)
        self.assertIn("480p30", args)
        self.assertNotIn("--cookies", args)
        self.assertFalse(any("cookie" in part or "password" in part for part in args))

    def test_full_clip_has_no_section_flag(self):
        plan = tw.plan_window("clip", 32, formats(("1080", 1080)), None, MAX)
        self.assertTrue(plan["full"])
        args = tw.download_args("https://clips.twitch.tv/FaintLightGullWholeWheat", Path("/tmp/w"), plan, MAX)
        self.assertNotIn("--download-sections", args)
        self.assertIn("1080", args)


class RunnerTests(unittest.TestCase):
    def test_long_vod_metadata_does_not_start_a_download(self):
        calls = []

        def runner(args, timeout):
            calls.append(args)
            self.assertIn("--skip-download", args)
            self.assertIn("https://www.twitch.tv/videos/2096474672", args)
            self.assertNotIn("t=", " ".join(args))
            return long_meta()

        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(tw.TwitchError) as ctx:
                tw.acquire_public(LONG + "?t=1h2m3s", Path(temp), MAX, None, runner=runner)
            self.assertEqual(list(Path(temp).iterdir()), [])
        self.assertIn("bookmark", str(ctx.exception))
        self.assertEqual(len(calls), 1)

    def test_section_command_uses_canonical_url_and_one_file(self):
        calls = []

        def runner(args, timeout):
            calls.append(list(args))
            if "--skip-download" in args:
                return long_meta()
            template = args[args.index("-o") + 1]
            Path(template.replace("%(ext)s", "mp4")).write_bytes(b"abcd")
            return None

        with tempfile.TemporaryDirectory() as temp:
            path, method, expected, extra = tw.acquire_public(
                LONG + "?t=30s", Path(temp), MAX, "1:00:00-1:00:20", runner=runner)
            self.assertEqual(method, "twitch_ytdlp_public")
            self.assertEqual(expected, 20)
            self.assertFalse(extra["twitch_full"])
            self.assertEqual(extra["section_start_sec"], 3600)
            self.assertEqual(extra["section_end_sec"], 3620)
            self.assertEqual(extra["twitch_source_duration_sec"], 15434)
            self.assertEqual(extra["twitch_height"], 480)
            self.assertFalse(extra["twitch_bookmark_applied"])
            self.assertEqual(path.read_bytes(), b"abcd")
        download = calls[1]
        self.assertIn("*3600.000-3620.000", download)
        self.assertIn("https://www.twitch.tv/videos/2096474672", download)
        self.assertNotIn("t=30s", " ".join(download))

    def test_oversize_file_is_deleted(self):
        def runner(args, timeout):
            if "--skip-download" in args:
                return {"duration": 1, "formats": formats(("1080", 1080))}
            template = args[args.index("-o") + 1]
            Path(template.replace("%(ext)s", "mp4")).write_bytes(b"x" * 1_100_000)
            return None

        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(tw.TwitchError) as ctx:
                tw.acquire_public(CLIP, Path(temp), 1_000_000, None, runner=runner)
            self.assertEqual(list(Path(temp).iterdir()), [])
        self.assertIn("discarded", str(ctx.exception))

    def test_downloader_stderr_urls_are_not_returned(self):
        message = tw.public_failure(
            "ERROR: [twitch:vod] 1: Video 1 does not exist\n"
            "https://example.invalid/secret.m3u8?token=abc"
        )
        self.assertNotIn("http", message)
        self.assertNotIn("token", message)
        self.assertIn("does not exist", message)
        login = tw.public_failure(
            "You must be logged into an account that has access to this subscriber-only content "
            "https://gql.twitch.tv/gql?token=secret"
        )
        self.assertNotIn("http", login)
        self.assertIn("subscription", login)
        with patch.object(tw.shutil, "which", return_value="/bin/yt-dlp"), \
             patch.object(tw.subprocess, "run", return_value=Mock(
                 returncode=1, stdout="", stderr="https://cdn.example/a.m3u8?sig=1\nVideo 9 does not exist")):
            with self.assertRaises(tw.TwitchError) as ctx:
                tw.default_run(["yt-dlp", "-J", "--skip-download", "https://www.twitch.tv/videos/9"], 10)
        self.assertNotIn("http", str(ctx.exception))
        self.assertNotIn("sig", str(ctx.exception))

    def test_live_metadata_is_refused(self):
        def runner(args, timeout):
            return {"duration": 10, "is_live": True, "formats": formats(("480p30", 480))}

        with tempfile.TemporaryDirectory() as temp, self.assertRaises(tw.TwitchError) as ctx:
            tw.acquire_public(SHORT, Path(temp), MAX, None, runner=runner)
        self.assertIn("live", str(ctx.exception).lower())


class ReceiptTests(unittest.TestCase):
    def test_published_clip_receipt_has_no_body(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tiny = root / "tiny.mp4"
            subprocess.run([
                "ffmpeg", "-v", "error", "-y",
                "-f", "lavfi", "-i", "testsrc=size=160x120:rate=10:duration=2",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(tiny),
            ], check=True, timeout=30)
            probed = media.probe(tiny)

            def fake(url, work, max_bytes, section_text=None, runner=None):
                dest = Path(work) / "media.mp4"
                shutil.copy(tiny, dest)
                return dest, "twitch_ytdlp_public", probed["duration_sec"], {
                    "twitch_kind": "clip",
                    "twitch_id": "FaintLightGullWholeWheat",
                    "twitch_source_duration_sec": probed["duration_sec"],
                    "twitch_full": True,
                    "twitch_height": 1080,
                }

            with patch.object(media, "acquire_public", fake):
                result = media.acquire(CLIP, root / "out")
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["method"], "twitch_ytdlp_public")
            self.assertTrue(result["twitch_full"])
            self.assertNotIn("body_text", result)
            self.assertNotIn("title", result)
            self.assertTrue(result["has_video"])
            receipt = json.loads(Path(result["path"] + ".json").read_text())
            self.assertNotIn("body_text", receipt)
            self.assertEqual(receipt["twitch_id"], "FaintLightGullWholeWheat")


if __name__ == "__main__":
    unittest.main()
