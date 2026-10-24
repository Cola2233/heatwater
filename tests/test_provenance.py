import tempfile
import unittest
from pathlib import Path

from scripts.provenance import file_record, validate_records, run_metadata

class ProvenanceTests(unittest.TestCase):
    def test_metadata_records_method_selection_and_synthetic_status(self):
        import json
        from scripts.project_config import load_project_config
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            source=root/"source"
            source.write_text("source")
            payload={"project_root":".","synthetic":True,"building_layer":"custom",
                     "building_field":"Type","inputs":{k:"source" for k in
                     ("heat_early","heat_late","transition","water_risk","building_functions")}}
            p=root/"config.json"
            p.write_text(json.dumps(payload))
            m=run_metadata(load_project_config(p),"test-gdal",None)
            self.assertTrue(m["synthetic"])
            self.assertEqual(m["building_layer"],"custom")
            self.assertEqual(m["building_field"],"Type")
            self.assertIn("numpy",m)
            self.assertNotIn(str(root),json.dumps(m))
    def test_checksum_relative_path_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = root / "out.txt"
            p.write_text("result", encoding="utf-8")
            record = file_record(p, root)
            self.assertEqual(record["relative_path"], "out.txt")
            self.assertEqual(len(record["sha256"]), 64)
            validate_records([record], root)
            p.write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum"):
                validate_records([record], root)
            p.unlink()
            with self.assertRaises(FileNotFoundError):
                validate_records([record], root)

    def test_manifest_path_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                validate_records([{"relative_path": "../outside"}], Path(d))
