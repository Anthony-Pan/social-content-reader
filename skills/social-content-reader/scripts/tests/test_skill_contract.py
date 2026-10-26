"""Guard the media-first contract so caption-only does not creep back in as success."""

from pathlib import Path
import unittest


SKILL = Path(__file__).resolve().parents[2]
PLATFORMS = SKILL / "platforms"


class SkillContractTests(unittest.TestCase):
    def test_version_and_media_first_recipe(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('version: "0.5.1"', text)
        self.assertIn("extract_frames.py", text)
        self.assertIn("ocr_frames.py", text)
        self.assertIn("asr_local.py", text)
        self.assertIn("Do not write Understanding from the caption", text)
        lowered = text.lower()
        self.assertNotIn("caption-only if share page gives text", lowered)

    def test_shared_video_recipe_documents_validated_acquire(self):
        text = (PLATFORMS / "_video-body.md").read_text(encoding="utf-8")
        self.assertIn("extract_frames.py", text)
        self.assertIn("ocr_frames.py", text)
        self.assertIn("acquire_media.py", text)
        self.assertIn("Content-Range", text)
        self.assertIn("error.mp4", text)
        self.assertIn("User export is last resort", text)
        self.assertIn("No browser profile/cookie extraction", text)

    def test_douyin_default_acquire_is_the_mobile_player(self):
        text = (PLATFORMS / "douyin.md").read_text(encoding="utf-8")
        self.assertIn("acquire_douyin.py", text)
        self.assertIn("https://www.douyin.com/", text)
        self.assertIn("https://m.douyin.com/share/video/{id}", text)
        self.assertIn("/aweme/v1/playwm", text)
        self.assertLess(text.index("acquire_douyin.py"), text.index("User Save/export"))
        self.assertIn("Do not write Understanding from the caption", text)

    def test_all_platforms_relisted_with_honest_walls(self):
        for path in [SKILL / 'SKILL.md', SKILL.parents[1] / 'README.md']:
            text = path.read_text(encoding='utf-8')
            for name in ['LinkedIn', '小红书', 'Telegram', 'Twitch']:
                self.assertIn(name, text)
            self.assertNotIn('not listed as supported', text)
            self.assertIn('risk wall', text)
            self.assertIn('QR / app-only', text)

    def test_every_platform_points_at_the_media_pipeline(self):
        docs = sorted(path for path in PLATFORMS.glob("*.md") if not path.name.startswith("_"))
        self.assertGreaterEqual(len(docs), 16)
        for path in docs:
            text = path.read_text(encoding="utf-8")
            self.assertIn("_video-body.md", text, path.name)
            self.assertNotIn("answer from the caption", text, path.name)


if __name__ == "__main__":
    unittest.main()
