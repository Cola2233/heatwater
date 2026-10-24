import os
import unittest
from unittest.mock import patch
from scripts import geo_runtime

class RuntimeTests(unittest.TestCase):
    def test_short_python_path_does_not_crash(self):
        with patch.object(geo_runtime.sys, "executable", "C:/Python312/python.exe"):
            with patch.dict(os.environ, {"QGIS_ROOT": "C:/nonexistent-qgis"}):
                geo_runtime.configure()
