"""Layer 4 E2E & Contract Tests: Stage 4 Chrome/Edge Extension (`manifest.json`, `content.js`, `popup`)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXT_DIR = PROJECT_ROOT / "src" / "features" / "extension"


class TestBrowserExtensionStage4Contract(unittest.TestCase):
    """Verifies Stage 4 Browser Extension requirements and UI/UX contracts."""

    def test_manifest_v3_structure(self) -> None:
        manifest_path = EXT_DIR / "manifest.json"
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["manifest_version"], 3)
        self.assertIn("activeTab", manifest["permissions"])
        self.assertIn("storage", manifest["permissions"])
        self.assertEqual(manifest["background"]["service_worker"], "background.js")
        self.assertEqual(manifest["action"]["default_popup"], "popup/popup.html")
        cs = manifest["content_scripts"][0]
        self.assertIn("content.js", cs["js"])
        self.assertIn("content.css", cs["css"])

    def test_content_js_blur_and_warning_button_requirements(self) -> None:
        """BR-EXT-02: Verify exact `blur(10px)` CSS and warning button copy in `content.js`."""
        content_js = (EXT_DIR / "content.js").read_text(encoding="utf-8")
        self.assertIn('style.filter = "blur(10px)"', content_js)
        self.assertIn(
            "Quảng cáo này có thể chứa nội dung độc hại. Nhấp để xem",
            content_js,
        )
        self.assertIn("MutationObserver", content_js)
        self.assertIn("data-testid", content_js)

    def test_popup_ui_four_states_and_mobile_first_rules(self) -> None:
        """BR-EXT-03 & RULE 06: Verify all 4 UI states, 44px touch targets, and 16px input font."""
        popup_html = (EXT_DIR / "popup" / "popup.html").read_text(encoding="utf-8")
        popup_css = (EXT_DIR / "popup" / "popup.css").read_text(encoding="utf-8")

        for testid in (
            "extension__state--loading",
            "extension__state--error",
            "extension__state--empty",
            "extension__state--success",
            "extension__scan--btn",
            "extension__api-url--input",
        ):
            self.assertIn(testid, popup_html)

        self.assertIn("min-height: 44px", popup_css)
        self.assertIn("font-size: 16px", popup_css)


if __name__ == "__main__":
    unittest.main()
