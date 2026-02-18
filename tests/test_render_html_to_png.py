import tempfile
import unittest
from pathlib import Path

from render_html_to_png import (
    _build_md_block,
    _to_md_relative_path,
    _upsert_markdown_reference,
)


class TestRenderHtmlToPngMarkdownHelpers(unittest.TestCase):
    def test_relative_path_for_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            md = root / "docs" / "guide.rewritten_v2.md"
            img = root / "docs" / "images" / "flow.png"
            md.parent.mkdir(parents=True, exist_ok=True)
            img.parent.mkdir(parents=True, exist_ok=True)
            md.write_text("# Guide\n", encoding="utf-8")
            img.write_bytes(b"png")

            rel = _to_md_relative_path(md, img)
            self.assertEqual(rel, "images/flow.png")

    def test_build_md_block_with_comment(self):
        block = _build_md_block(
            image_rel_path="images/flow.png",
            alt_text="flow",
            source_description="ascii flow",
        )
        self.assertIn("<!-- Converted from ASCII art: ascii flow -->", block)
        self.assertIn("![flow](images/flow.png)", block)

    def test_append_markdown_reference_once(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            md = Path(tmpdir) / "guide.rewritten_v2.md"
            md.write_text("# Guide\n", encoding="utf-8")
            block = "![flow](images/flow.png)"

            _upsert_markdown_reference(md, block, "images/flow.png", marker="")
            first = md.read_text(encoding="utf-8")
            self.assertIn(block, first)

            _upsert_markdown_reference(md, block, "images/flow.png", marker="")
            second = md.read_text(encoding="utf-8")
            self.assertEqual(first, second)

    def test_replace_marker(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            md = Path(tmpdir) / "guide.rewritten_v2.md"
            md.write_text("# Guide\n\n{{DIAGRAM_BLOCK}}\n", encoding="utf-8")
            block = "![flow](images/flow.png)"

            _upsert_markdown_reference(md, block, "images/flow.png", marker="{{DIAGRAM_BLOCK}}")
            text = md.read_text(encoding="utf-8")
            self.assertIn(block, text)
            self.assertNotIn("{{DIAGRAM_BLOCK}}", text)


if __name__ == "__main__":
    unittest.main()
