"""Build an offline temperature viewer from QA-masked, aligned Celsius rasters."""

import argparse
import base64
import json
from pathlib import Path
import re

import numpy as np

from .geo_runtime import configure


def build(report, output):
    configure()
    from osgeo import gdal

    gdal.UseExceptions()
    manifest = json.loads(report.read_text(encoding="utf-8"))
    scenes = []
    reference = None
    for record in manifest["scenes"]:
        ds = gdal.Open(str(report.parent / record["file"]))
        band = ds.GetRasterBand(1)
        raster = band.ReadAsArray()
        grid = (ds.GetGeoTransform(), ds.GetProjection(), raster.shape)
        if reference is None:
            reference = grid
        elif reference != grid:
            raise ValueError("Temperature rasters must share the same grid")
        if band.GetUnitType() != "degC":
            raise ValueError("Expected temperature in degrees Celsius")
        valid = np.isfinite(raster) & (raster != band.GetNoDataValue())
        if int(valid.sum()) != record["valid_count"]:
            raise ValueError("Raster coverage disagrees with the manifest")
        values = np.full(raster.shape, -32768, dtype="<i2")
        values[valid] = np.rint(raster[valid] * 100).astype("<i2")
        scenes.append({"id": record["scene"], "coverage": float(valid.mean()),
                       "values": base64.b64encode(values.tobytes()).decode("ascii")})
    if not scenes:
        raise ValueError("At least one raster is required")

    height, width = reference[2]
    slug = manifest.get("slug", "beijing")
    if not re.fullmatch(r"[a-z][a-z0-9-]*", slug):
        raise ValueError("Expected a lowercase city slug")
    payload = {"width": width, "height": height, "cellSize": 4, "scenes": scenes,
               "slug": slug, "title": manifest.get("title", "北京"),
               "titleEn": manifest.get("title_en", "Beijing"),
               "epsg": manifest["epsg"], "resolution": manifest["resolution_grid_m"]}
    template = Path(__file__).resolve().parents[1] / "website/temperature-demo.html"
    html = template.read_text(encoding="utf-8").replace(
        "/* DATA */", json.dumps(payload, separators=(",", ":")).replace("<", "\\u003c"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.report, args.output)
