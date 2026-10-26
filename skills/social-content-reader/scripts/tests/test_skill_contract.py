"""Guard the media-first contract so caption-only does not creep back in as success."""

from pathlib import Path
import unittest


SKILL = Path(__file__).resolve().parents[2]
PLATFORMS = SKILL / "platforms"


class SkillContractTests(unittest.TestCase):
    def test_version_and_media_first_recipe(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('version: "0.4.0"', text)
        self.assertIn("extract_frames.py", text)
        self.assertIn("ocr_frames.py", text)
        self.assertIn("asr_local.py", text)
        self.assertIn("Do not write Understanding from the caption", text)
        lowered = text.lower()
        self.assertNotIn("caption-only if share page gives text", lowered)

    def test_shared_video_recipe_documents_douyin_wall(self):
        text = (PLATFORMS / "_video-body.md").read_text(encoding="utf-8")
        self.assertIn("extract_frames.py", text)
        self.assertIn("ocr_frames.py", text)
        self.assertIn("7696098282904259850", text)
        self.assertIn("v.douyin.com/2qulGbSTiRI", text)
        self.assertIn("请尝试在抖音内观看", text)
        self.assertIn("yt-dlp", text)
        self.assertIn("m.douyin.com/share/video", text)
        self.assertIn("playwm", text)

    def test_douyin_default_acquire_is_the_mobile_player(self):
        text = (PLATFORMS / "douyin.md").read_text(encoding="utf-8")
        self.assertIn("acquire_douyin.py", text)
        self.assertIn("https://www.douyin.com/", text)
        self.assertIn("https://m.douyin.com/share/video/{id}", text)
        self.assertIn("/aweme/v1/playwm", text)
        self.assertLess(text.index("acquire_douyin.py"), text.index("User export is the fallback"))
        self.assertIn("Do not write Understanding from the caption", text)

    def test_every_platform_points_at_the_media_pipeline(self):
        docs = sorted(path for path in PLATFORMS.glob("*.md") if not path.name.startswith("_"))
        self.assertGreaterEqual(len(docs), 16)
        for path in docs:
            text = path.read_text(encoding="utf-8")
            self.assertIn("_video-body.md", text, path.name)
            self.assertNotIn("answer from the caption", text, path.name)


if __name__ == "__main__":
    unittest.main()
