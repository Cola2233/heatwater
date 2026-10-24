import json
import tempfile
import unittest
from pathlib import Path

from scripts.project_config import load_project_config

class ConfigTests(unittest.TestCase):
    def payload(self):
        return {"project_root": ".", "inputs": {k: "input/" + k for k in
            ("heat_early", "heat_late", "transition", "water_risk", "building_functions")},
            "outputs": {"output_dir": "results", "derived_dir": "derived", "figure_dir": "figures"}}

    def load(self, payload):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        path = Path(self.tmp.name) / "project.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return load_project_config(path)

    def test_resolves_paths_and_preserves_legacy_defaults(self):
        c = self.load(self.payload())
        self.assertEqual(c.input_path("heat_early"), c.project_root / "input/heat_early")
        self.assertEqual(c.parameters["heat_weight"], 0.55)
        self.assertEqual(c.parameters["zone_threshold"], 0.67)

    def test_missing_input_rejected(self):
        p = self.payload()
        del p["inputs"]["heat_early"]
        with self.assertRaisesRegex(ValueError, "heat_early"):
            self.load(p)

    def test_invalid_weights_and_threshold_rejected(self):
        for params in ({"heat_weight": 0.8}, {"zone_threshold": 1}, {"heat_weight": float("nan")}):
            p = self.payload()
            p["parameters"] = params
            with self.assertRaises(ValueError):
                self.load(p)

    def test_output_cannot_overwrite_input(self):
        p = self.payload()
        p["outputs"]["output_dir"] = "input"
        with self.assertRaisesRegex(ValueError, "input"):
            self.load(p)

    def test_output_directories_must_be_separate(self):
        p = self.payload()
        p["outputs"]["derived_dir"] = "results/derived"
        with self.assertRaises(ValueError):
            self.load(p)

    def test_outputs_cannot_escape_project_root(self):
        p = self.payload()
        p["outputs"]["output_dir"] = "../outside"
        with self.assertRaises(ValueError):
            self.load(p)

    def test_config_inside_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"results").mkdir()
            path=root/"results/run_metadata.json"
            p=self.payload()
            p["project_root"]=".."
            path.write_text(json.dumps(p))
            with self.assertRaises(ValueError):
                load_project_config(path)
