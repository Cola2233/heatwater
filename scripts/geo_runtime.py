"""Discover QGIS runtime from its interpreter or QGIS_ROOT, keeping DLL handles alive."""
import os
import sys
from pathlib import Path
_HANDLES = []

def configure():
    explicit = os.environ.get("QGIS_ROOT")
    if explicit:
        root = Path(explicit)
    else:
        root = next((p for p in Path(sys.executable).resolve().parents
                     if (p / "apps").is_dir()), None)
        if root is None:
            return
    if not (root / "apps").is_dir():
        return
    for relative in ("apps/Qt6/bin", "apps/qgis/bin", "apps/Python312/DLLs", "bin"):
        path = root / relative
        if hasattr(os, "add_dll_directory") and path.is_dir():
            _HANDLES.append(os.add_dll_directory(str(path)))
    for key, relative in (("GDAL_DATA", "apps/gdal/share/gdal"), ("PROJ_DATA", "share/proj")):
        if (root / relative).is_dir():
            os.environ.setdefault(key, str(root / relative))
