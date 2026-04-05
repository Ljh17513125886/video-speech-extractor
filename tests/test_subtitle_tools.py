import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from extract_subtitles import build_auth_guidance, build_transcript_markdown, is_auth_error, select_best_language
from subtitle_to_text import convert_subtitle_to_text


class SubtitleToolTests(unittest.TestCase):
    def fixture(self, name: str) -> str:
        return str(ROOT / "tests" / "fixtures" / name)

    def test_convert_vtt_to_text(self) -> None:
        text = convert_subtitle_to_text(self.fixture("sample.vtt"))
        self.assertEqual(text, "Hello world\nSecond line")

    def test_convert_srt_to_text(self) -> None:
        text = convert_subtitle_to_text(self.fixture("sample.srt"))
        self.assertEqual(text, "Hello world\nSecond line")

    def test_convert_ass_to_text(self) -> None:
        text = convert_subtitle_to_text(self.fixture("sample.ass"))
        self.assertEqual(text, "Hello world\nSecond\nline")

    def test_language_selection_prefers_manual_over_auto(self) -> None:
        selected, source = select_best_language(["en"], ["zh-Hans"], None)
        self.assertEqual(selected, "en")
        self.assertEqual(source, "manual")

    def test_auth_error_detection(self) -> None:
        self.assertTrue(is_auth_error("ERROR: Sign in to confirm you're not a bot"))
        self.assertFalse(is_auth_error("ERROR: This site returned a 404"))

    def test_auth_guidance_mentions_cookies_options(self) -> None:
        guidance = build_auth_guidance("https://youtu.be/example", list_mode=True, preferred_language="en")
        self.assertIn("--cookies-from-browser chrome", guidance)
        self.assertIn("--cookies /path/to/cookies.txt", guidance)
        self.assertIn("--list", guidance)
        self.assertIn("--language en", guidance)

    def test_markdown_render_includes_metadata(self) -> None:
        markdown = build_transcript_markdown(
            title="Sample Video",
            url="https://example.com/video",
            duration=65,
            transcript_text="Hello world",
            subtitle_language="en",
            subtitle_source="manual",
        )
        self.assertIn("# Sample Video", markdown)
        self.assertIn("> Duration: 00:01:05", markdown)
        self.assertIn("> Subtitle language: en", markdown)
        self.assertIn("## Transcript", markdown)
        self.assertIn("Hello world", markdown)


if __name__ == "__main__":
    unittest.main()
