"""Integration checks run only with GDAL installed."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np

try:
    from scripts.geo_runtime import configure
    configure()
    from osgeo import gdal
    HAS_GDAL=True
except ImportError:
    HAS_GDAL=False

@unittest.skipUnless(HAS_GDAL, "GDAL integration requires the geospatial runtime")
class GeoPipelineTests(unittest.TestCase):
    def test_water_range_and_unknown_transition_are_rejected(self):
        from scripts.synthetic_case import create_case
        from scripts.project_config import load_project_config
        from scripts.validate_outputs import preflight
        for role,value,expected in (("water_risk",2,"water"),("transition",-9999,"transition")):
            with tempfile.TemporaryDirectory() as d:
                c=load_project_config(create_case(Path(d)))
                ds=gdal.Open(str(c.input_path(role)),gdal.GA_Update)
                ds.GetRasterBand(1).Fill(value)
                ds=None
                with self.assertRaisesRegex(ValueError,expected):
                    preflight(c)

    def test_demo_does_not_overwrite_config(self):
        from scripts.synthetic_case import create_case
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"config.json"
            p.write_text("keep")
            with self.assertRaises(FileExistsError):
                create_case(Path(d))
            self.assertEqual(p.read_text(),"keep")

    def test_alignment_uses_float_output_for_integer_inputs(self):
        from scripts.build_heat_water_resilience import align_to_reference
        from scripts.synthetic_case import create_case
        from scripts.project_config import load_project_config
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            c=load_project_config(create_case(root))
            ref=gdal.Open(str(c.input_path("heat_early")))
            path=root/"byte.tif"
            ds=gdal.GetDriverByName("GTiff").Create(str(path),48,40,1,gdal.GDT_Byte)
            ds.SetGeoTransform((680015,30,0,4870000,0,-30))
            ds.SetProjection(ref.GetProjection())
            ds.GetRasterBand(1).WriteArray(np.tile(np.arange(48)%2,(40,1)).astype(np.uint8))
            ds=None
            dest=root/"aligned.tif"
            align_to_reference(path,ref,dest)
            aligned=gdal.Open(str(dest))
            dtype=aligned.GetRasterBand(1).DataType
            a=aligned.ReadAsArray()
            aligned=ref=None
            self.assertEqual(dtype,gdal.GDT_Float32)
            self.assertTrue(((a>0)&(a<1)).any())

    def test_synthetic_inputs_preflight_and_grid_mismatch(self):
        from scripts.synthetic_case import create_case
        from scripts.project_config import load_project_config
        from scripts.validate_outputs import preflight
        with tempfile.TemporaryDirectory() as d:
            c=load_project_config(create_case(Path(d)))
            preflight(c)
            ds=gdal.Open(str(c.input_path("heat_late")),gdal.GA_Update)
            ds.SetGeoTransform((0,30,0,1000,0,-30))
            ds=None
            with self.assertRaisesRegex(ValueError, "grid"):
                preflight(c)

    def test_nodata_and_missing_building_field(self):
        from scripts.synthetic_case import create_case
        from scripts.project_config import load_project_config
        from scripts.validate_outputs import preflight
        from scripts.build_heat_water_resilience import read_band
        with tempfile.TemporaryDirectory() as d:
            path=create_case(Path(d))
            c=load_project_config(path)
            _,a,_=read_band(c.input_path("heat_early"))
            self.assertTrue(np.isnan(a[0,0]))
            raw=json.loads(path.read_text())
            raw["building_field"]="absent"
            path.write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError, "field"):
                preflight(load_project_config(path))
