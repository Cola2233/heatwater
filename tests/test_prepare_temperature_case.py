import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import numpy as np

from scripts.prepare_temperature_case import prepare, temperature_celsius, validate_manifest


class TemperatureCaseTests(unittest.TestCase):
    def test_qa_removes_cloud_shadow_snow_saturation_and_fill_but_keeps_water(self):
        dn = np.array([[45000, 45000, 45000, 45000, 45000, 0, 45000]], dtype=np.uint16)
        flags = np.array([[0, 8, 16, 32, 0, 0, 128]], dtype=np.uint16)
        saturated = np.array([[0, 0, 0, 0, 1, 0, 0]], dtype=np.uint16)
        result = temperature_celsius(dn, flags, saturated)
        np.testing.assert_array_equal(result[0, 1:6], np.full(5, -9999))
        np.testing.assert_allclose(result[0, [0, 6]], 45000 * .00341802 + 149 - 273.15, atol=2e-5)

    def test_all_seven_public_manifests_are_buildable_inputs(self):
        root = Path(__file__).resolve().parents[1] / "cases"
        expected = {"beijing", "tianjin", "shanghai", "guangzhou", "shenzhen", "hong-kong", "taipei"}
        for slug in expected:
            case = json.loads((root / slug / "scenes.json").read_text(encoding="utf-8"))
            with self.subTest(city=slug):
                validate_manifest(case)
                self.assertEqual(case["slug"], slug)
                self.assertTrue(all(s["valid_count"] > 0 for s in case["scenes"]))

    @unittest.skipUnless(importlib.util.find_spec("osgeo"), "GDAL required")
    def test_prepare_outputs_viewer_and_preserves_existing_directory_on_failure(self):
        from scripts.geo_runtime import configure
        configure()
        from osgeo import gdal, osr

        case = {
            "slug": "sample", "title": "样区", "title_en": "Sample",
            "bounds_lonlat": [116, 39, 117, 40], "epsg": 32650, "resolution_grid_m": 30,
            "scenes": [{"scene": "LC08_L2SP_123032_20140819_02_T1", "valid_count": 16}],
        }
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(32650)
        bands = []
        for value in (45000, 0, 0):
            ds = gdal.GetDriverByName("MEM").Create("", 4, 4, 1, gdal.GDT_UInt16)
            ds.SetGeoTransform((400000, 30, 0, 4400000, 0, -30))
            ds.SetProjection(srs.ExportToWkt())
            ds.GetRasterBand(1).Fill(value)
            bands.append(ds)
        item = {"id": case["scenes"][0]["scene"],
                "assets": {name: {"href": "unused"} for name in ("lwir11", "qa_pixel", "qa_radsat")}}
        with TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "scenes.json"
            path.write_text(json.dumps(case), encoding="utf-8")
            with patch("scripts.prepare_temperature_case.read_json", return_value=item), \
                 patch("scripts.prepare_temperature_case.open_window", side_effect=bands * 2):
                output = root / "output"
                prepare(path, output)
                self.assertTrue((output / "heatwater-sample-temperature.html").is_file())
                self.assertEqual(len(list(output.glob("*.tif"))), 1)
                with self.assertRaises(FileExistsError):
                    prepare(path, output)
                case["scenes"][0]["valid_count"] = 15
                path.write_text(json.dumps(case), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "differs from recorded"):
                    prepare(path, root / "failed")
                self.assertFalse((root / "failed").exists())
                self.assertTrue((output / "verification.json").is_file())
