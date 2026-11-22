import tempfile
import unittest
from pathlib import Path

import numpy as np

from scripts.build_built_up_mask import build

try:
    from osgeo import gdal, osr
except ImportError:
    gdal = osr = None


@unittest.skipIf(gdal is None, "GDAL is required to test raster alignment")
class BuiltUpMaskTests(unittest.TestCase):
    def test_keeps_class_50_on_reference_grid(self):
        spatial = osr.SpatialReference()
        spatial.ImportFromEPSG(32650)
        transform = (400000, 30, 0, 4420000, 0, -30)
        classes = np.array([[50, 10], [40, 50]], dtype=np.uint8)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "cover.tif"
            output = root / "mask.tif"
            raster = gdal.GetDriverByName("GTiff").Create(str(source), 2, 2, 1, gdal.GDT_Byte)
            raster.SetGeoTransform(transform)
            raster.SetProjection(spatial.ExportToWkt())
            raster.GetRasterBand(1).WriteArray(classes)
            raster = None
            self.assertEqual(build(source, output, str(source)), (2, 4))
            with gdal.Open(str(output)) as result:
                self.assertEqual(result.GetGeoTransform(), transform)
                np.testing.assert_array_equal(result.ReadAsArray(), [[1, 0], [0, 1]])
                self.assertIsNone(result.GetRasterBand(1).GetNoDataValue())
                self.assertEqual(result.GetMetadataItem("SOURCE_CLASS"), "50")
