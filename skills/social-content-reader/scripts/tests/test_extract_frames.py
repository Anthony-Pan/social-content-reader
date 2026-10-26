"""Keyframe extraction checks. The sample-video test runs only when ffmpeg is on PATH."""

from contextlib import redirect_stderr, redirect_stdout
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
    "extract_frames", Path(__file__).resolve().parents[1] / "extract_frames.py"
)
frames = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frames)


SHOWINFO = """
[Parsed_showinfo_1] n:   0 pts:      0 pts_time:0       duration:      1 duration_time:1
[Parsed_showinfo_1] n:   1 pts:      1 pts_time:1.5     duration:      1 duration_time:1
"""


class ParseTests(unittest.TestCase):
    def test_parse_showinfo_timestamps(self):
        self.assertEqual(frames.parse_showinfo_timestamps(SHOWINFO), [0.0, 1.5])

    def test_parse_duration_text(self):
        self.assertEqual(frames.parse_duration_text("Duration: 00:01:02.50, start: 0.000000"), 62.5)
        self.assertIsNone(frames.parse_duration_text("no duration here"))

    def test_build_vf_fps_and_scene(self):
        self.assertEqual(frames.build_vf("fps", 1, 0.3), "fps=1,showinfo")
        scene = frames.build_vf("scene", 1, 0.3)
        self.assertIn(r"eq(n\,0)", scene)
        self.assertIn(r"gt(scene\,0.3)", scene)
        self.assertTrue(scene.endswith(",showinfo"))

    def test_command_is_local_file_only(self):
        cmd = frames.build_ffmpeg_command(
            "ffmpeg", Path("/tmp/clip.mp4"), "fps=1,showinfo",
            Path("/tmp/out/frame_%04d.jpg"), 4,
        )
        self.assertNotIn("http://", " ".join(cmd))
        self.assertIn("-frames:v", cmd)
        self.assertIn("4", cmd)

    def test_refuses_url(self):
        with self.assertRaises(frames.FrameError):
            frames.assert_local_media(Path("clip.mp4"), "https://example.com/clip.mp4")


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        output, diagnostics = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(diagnostics):
            code = frames.main(list(args))
        return code, json.loads(output.getvalue()), diagnostics.getvalue()

    def test_missing_file(self):
        code, record, _ = self.run_cli("--media", "/no/such/video.mp4")
        self.assertEqual(code, 1)
        self.assertFalse(record["ok"])
        self.assertEqual(record["frames"], [])
        self.assertIn("not found", record["error"])

    def test_missing_ffmpeg_is_honest(self):
        with tempfile.TemporaryDirectory() as temp:
            media = Path(temp) / "clip.mp4"
            media.write_bytes(b"not a real video")
            with patch.object(frames.shutil, "which", return_value=None):
                code, record, _ = self.run_cli("--media", str(media))
        self.assertEqual(code, 1)
        self.assertFalse(record["ok"])
        self.assertIn("ffmpeg", record["error"])
        self.assertIn("brew install ffmpeg", record["error"])

    def test_generated_sample_video_fps_and_scene(self):
        if not shutil.which("ffmpeg"):
            self.skipTest("ffmpeg not installed")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sample = root / "sample.mp4"
            scene_video = root / "scene.mp4"
            fps_dir = root / "fps"
            scene_dir = root / "scene"
            subprocess.run(
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "testsrc=duration=2:size=160x120:rate=10",
                    "-pix_fmt", "yuv420p", str(sample),
                ],
                check=True, timeout=60,
            )
            subprocess.run(
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "color=c=red:s=160x120:d=1:r=10",
                    "-f", "lavfi", "-i", "color=c=blue:s=160x120:d=1:r=10",
                    "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0",
                    "-pix_fmt", "yuv420p", str(scene_video),
                ],
                check=True, timeout=60,
            )

            code, record, _ = self.run_cli(
                "--media", str(sample), "--mode", "fps", "--fps", "1",
                "--max-frames", "8", "--out-dir", str(fps_dir),
            )
            self.assertEqual(code, 0, record.get("error"))
            self.assertTrue(record["ok"])
            self.assertGreaterEqual(len(record["frames"]), 2)
            self.assertFalse(record["truncated"])
            timestamps = [frame["timestamp_sec"] for frame in record["frames"]]
            self.assertEqual(timestamps, sorted(timestamps))
            self.assertEqual(record["frames"][0]["timestamp_sec"], 0.0)
            for frame in record["frames"]:
                self.assertTrue(Path(frame["path"]).is_file())
                self.assertGreater(Path(frame["path"]).stat().st_size, 0)

            code, record, _ = self.run_cli(
                "--media", str(scene_video), "--mode", "scene",
                "--scene-threshold", "0.3", "--max-frames", "8",
                "--out-dir", str(scene_dir),
            )
            self.assertEqual(code, 0, record.get("error"))
            self.assertGreaterEqual(len(record["frames"]), 2)
            self.assertGreaterEqual(record["frames"][1]["timestamp_sec"], 0.5)


if __name__ == "__main__":
    unittest.main()
