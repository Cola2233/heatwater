"""Build paired summer temperature medians and per-pixel observation counts."""

import argparse
import base64
from datetime import datetime
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import warnings

import numpy as np

from .geo_runtime import configure
from .prepare_temperature_case import NODATA, SCENE_PATTERN

OUTSIDE_COUNT = np.iinfo(np.uint16).max


def date_from_scene(scene):
    if not SCENE_PATTERN.fullmatch(scene):
        raise ValueError(f"Invalid Landsat scene ID: {scene}")
    return datetime.strptime(scene.split("_")[3], "%Y%m%d").date()


def composite_by_day(observations, minimum=3):
    """Mosaic overlapping scenes by day, then give each day equal weight."""
    if not observations or not isinstance(minimum, int) or not 1 <= minimum <= 65535:
        raise ValueError("Expected scenes and a minimum observation count from 1 to 65535")
    daily = {}
    dimensions = observations[0][1].shape
    for scene, values in sorted(observations, key=lambda item: item[0]):
        if values.shape != dimensions or values.ndim != 2:
            raise ValueError("All temperature observations must share a two-dimensional grid")
        day = date_from_scene(scene)
        if day not in daily:
            daily[day] = np.full(dimensions, np.nan, dtype=np.float32)
        mosaic = daily[day]
        valid = np.isfinite(values) & (values != NODATA)
        fill = valid & np.isnan(mosaic)
        mosaic[fill] = values[fill]
    if len(daily) > np.iinfo(np.uint16).max:
        raise ValueError("Observation count exceeds UInt16 capacity")
    days = sorted(day for day, mosaic in daily.items() if np.isfinite(mosaic).any())
    if not days:
        return (np.full(dimensions, NODATA, dtype=np.float32),
                np.zeros(dimensions, dtype=np.uint16), [])
    stack = np.stack([daily[day] for day in days])
    count = np.count_nonzero(np.isfinite(stack), axis=0).astype(np.uint16)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="All-NaN slice encountered", category=RuntimeWarning)
        median = np.nanmedian(stack, axis=0)
    median[count < minimum] = NODATA
    return median, count, [day.isoformat() for day in days]


def write_raster(gdal, path, values, grid, dtype, unit, nodata=None):
    height, width = values.shape
    ds = gdal.GetDriverByName("GTiff").Create(str(path), width, height, 1, dtype, ["COMPRESS=DEFLATE"])
    ds.SetGeoTransform(grid[0])
    ds.SetProjection(grid[1])
    band = ds.GetRasterBand(1)
    if nodata is not None:
        band.SetNoDataValue(nodata)
    band.SetUnitType(unit)
    band.WriteArray(values)
    ds.FlushCache()


def read_domain(gdal, path, grid):
    if path is None:
        return np.ones(grid[2], dtype=bool), "中心城区矩形样区"
    ds = gdal.Open(str(path))
    values = ds.ReadAsArray()
    if (ds.GetGeoTransform(), ds.GetProjection(), values.shape) != grid:
        raise ValueError("Built-up mask must match the temperature grid")
    if not np.isin(values, [0, 1]).all() or not np.any(values == 1):
        raise ValueError("Expected a nonempty built-up mask encoded as 0/1")
    return values == 1, "中心城区样区内的 2021 年建成地表"


def build(manifest_path, rasters, output, domain_mask=None):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    periods = manifest["periods"]
    if len(periods) != 2 or len({p["id"] for p in periods}) != 2:
        raise ValueError("Expected two distinct periods")
    if output.exists():
        raise FileExistsError(f"Choose a new output directory: {output}")
    minimum = manifest["min_observations"]
    configure()
    from osgeo import gdal, osr

    gdal.UseExceptions()
    ref_srs = osr.SpatialReference()
    ref_srs.ImportFromEPSG(manifest["epsg"])
    output.parent.mkdir(parents=True, exist_ok=True)
    grid = None
    domain = None
    seen = set()
    summaries = []
    layers = []
    support = []
    with TemporaryDirectory(prefix=".seasonal-", dir=output.parent) as work:
        result_dir = Path(work) / "case"
        result_dir.mkdir()
        for period in periods:
            period_id = period["id"]
            if period_id not in ("early", "late"):
                raise ValueError("Period identifiers must be early and late")
            observations = []
            for record in period["scenes"]:
                scene = record["scene"]
                date = date_from_scene(scene)
                if scene in seen or not (period["years"][0] <= date.year <= period["years"][1]) or date.month not in (6, 7, 8):
                    raise ValueError(f"Duplicate or out-of-season scene: {scene}")
                seen.add(scene)
                ds = gdal.Open(str(rasters / (scene + ".tif")))
                band = ds.GetRasterBand(1)
                if band.GetUnitType() != "degC" or not ds.GetSpatialRef().IsSame(ref_srs):
                    raise ValueError(f"Unexpected temperature unit or CRS for {scene}")
                values = band.ReadAsArray().astype(np.float32, copy=False)
                if band.GetNoDataValue() is not None:
                    values[values == band.GetNoDataValue()] = NODATA
                source_grid = (ds.GetGeoTransform(), ds.GetProjection(), values.shape)
                resolution = manifest["resolution_grid_m"]
                if source_grid[0][1:3] != (resolution, 0) or source_grid[0][4:] != (0, -resolution):
                    raise ValueError(f"Unexpected sampling grid for {scene}")
                if grid is None:
                    grid = source_grid
                    domain, domain_label = read_domain(gdal, domain_mask, grid)
                elif grid != source_grid:
                    raise ValueError(f"Scene grids disagree for {scene}")
                if "valid_count" in record and int(np.count_nonzero(np.isfinite(values) & (values != NODATA))) != record["valid_count"]:
                    raise ValueError(f"Scene valid count differs from the manifest for {scene}")
                observations.append((scene, np.where(domain, values, NODATA)))
                band = ds = None
            temperature, count, days = composite_by_day(observations, minimum)
            if count.max() == OUTSIDE_COUNT:
                raise ValueError("Observation count collides with the outside-domain marker")
            supported = temperature != NODATA
            support.append(supported)
            if not supported.any():
                raise ValueError(f"{period_id} has no pixels with sufficient observation support")
            write_raster(gdal, result_dir / f"{period_id}-median-c.tif", temperature, grid,
                         gdal.GDT_Float32, "degC", NODATA)
            count[~domain] = OUTSIDE_COUNT
            write_raster(gdal, result_dir / f"{period_id}-observation-count.tif", count, grid,
                         gdal.GDT_UInt16, "days", int(OUTSIDE_COUNT) if domain_mask else None)
            summaries.append({"id": period_id, "label": period["label"], "days": days,
                              "scene_count": len(observations),
                              "support_fraction": float(supported.sum() / domain.sum()),
                              "support_pixels": int(supported.sum()),
                              "median_count": float(np.median(count[domain])),
                              "area_median_c": float(np.median(temperature[supported]))})
            encoded_temp = np.full(temperature.shape, -32768, dtype="<i2")
            encoded_temp[supported] = np.rint(temperature[supported] * 100).astype("<i2")
            layers.append({"label": period["label"],
                           "temperature": base64.b64encode(encoded_temp.tobytes()).decode("ascii"),
                           "counts": base64.b64encode(count.astype("<u2").tobytes()).decode("ascii"),
                           "summary": summaries[-1]})

        width, height = grid[2][1], grid[2][0]
        shared = int(np.count_nonzero(support[0] & support[1]))
        domain_pixels = int(domain.sum())
        report = {"city": manifest["title"], "grid": {"epsg": manifest["epsg"], "width": width, "height": height,
                                                      "resolution_m": manifest["resolution_grid_m"]},
                  "minimum_observation_days": minimum, "shared_support_pixels": shared,
                  "domain": domain_label, "domain_pixels": domain_pixels,
                  "domain_fraction": domain_pixels / (width * height),
                  "shared_support_fraction": shared / domain_pixels, "periods": summaries,
                  "aggregation": "median across distinct valid observation days"}
        (result_dir / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payload = {"width": width, "height": height, "layers": layers, "minimum": minimum,
                   "city": manifest["title"], "shared": report["shared_support_fraction"],
                   "resolution": manifest["resolution_grid_m"], "domain": domain_label,
                   "built_up_mask": domain_mask is not None}
        template = Path(__file__).resolve().parents[1] / "website/seasonal-temperature.html"
        html = template.read_text(encoding="utf-8").replace(
            "/* DATA */", json.dumps(payload, separators=(",", ":")).replace("<", "\\u003c"))
        (result_dir / "summer-temperature.html").write_text(html, encoding="utf-8")
        result_dir.rename(output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--rasters", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--domain-mask", type=Path, help="Optional aligned 0/1 built-up mask")
    args = parser.parse_args()
    print(json.dumps(build(args.case, args.rasters, args.output, args.domain_mask), ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
