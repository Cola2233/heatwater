import tempfile
import unittest
from pathlib import Path
from scripts.build_single_html import build_single_html

class SingleHtmlTests(unittest.TestCase):
    def test_assets_inlined_after_body_and_keep_execution_order(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"style.css").write_text("body {color: green}")
            (root/"data.js").write_text("window.DATA=123;")
            (root/"app.js").write_text("document.getElementById('map').textContent=DATA;")
            entry=root/"index.html"
            entry.write_text('<html><head><link rel="stylesheet" href="style.css">'
                '<script defer src="data.js"></script><script defer src="app.js"></script>'
                '</head><body><div id="map"></div></body></html>')
            out=root/"standalone.html"
            build_single_html(entry,out)
            text=out.read_text(encoding="utf-8")
            self.assertIn("body {color: green}",text)
            self.assertNotIn('src="',text)
            self.assertNotIn('href="style.css"',text)
            self.assertLess(text.index('id="map"'),text.index("window.DATA"))
            self.assertLess(text.index("window.DATA"),text.index("document.getElementById"))

    def test_asset_outside_entry_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"web").mkdir()
            (root/"private.js").write_text("private")
            entry=root/"web/index.html"
            entry.write_text('<html><body><script src="../private.js"></script></body></html>')
            with self.assertRaises(ValueError):
                build_single_html(entry,root/"out.html")

    def test_output_cannot_overwrite_entry(self):
        with tempfile.TemporaryDirectory() as d:
            entry=Path(d)/"index.html"
            entry.write_text("<html><body></body></html>")
            with self.assertRaises(ValueError):
                build_single_html(entry,entry)
