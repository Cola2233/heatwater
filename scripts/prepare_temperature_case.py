"""Rebuild an offline Landsat temperature case from its recorded public scenes."""

import argparse
import json
from pathlib import Path
import re
import ssl
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import urlopen

import numpy as np

from .build_temperature_demo import build as build_viewer
from .geo_runtime import configure

API = "https://planetarycomputer.microsoft.com/api"
COLLECTION = "landsat-c2-l2"
BANDS = ("lwir11", "qa_pixel", "qa_radsat")
NODATA = -9999
SCENE_PATTERN = re.compile(r"LC0[89]_L2SP_\d{6}_\d{8}_\d{2}_T1")


def temperature_celsius(dn, qa_pixel, qa_radsat):
    """Apply the Landsat 8/9 QA mask and convert product DN to Celsius."""
    if dn.shape != qa_pixel.shape or dn.shape != qa_radsat.shape:
        raise ValueError("Temperature and QA arrays must share the same shape")
    good = (dn > 0) & ((qa_pixel & 63) == 0) & (qa_radsat == 0)
    result = np.full(dn.shape, NODATA, dtype=np.float32)
    result[good] = dn[good].astype(np.float32) * .00341802 + 149 - 273.15
    return result


def validate_manifest(case):
    if not re.fullmatch(r"[a-z][a-z0-9-]*", case["slug"]):
        raise ValueError("Expected a lowercase city slug")
    west, south, east, north = case["bounds_lonlat"]
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("Expected bounds in west, south, east, north order")
    if not isinstance(case["epsg"], int) or case["resolution_grid_m"] <= 0:
        raise ValueError("Expected an integer EPSG code and positive grid resolution")
    ids = [record["scene"] for record in case["scenes"]]
    if not ids or len(ids) != len(set(ids)) or not all(map(SCENE_PATTERN.fullmatch, ids)):
        raise ValueError("Expected distinct Landsat 8/9 L2SP Tier 1 scene identifiers")


def read_json(endpoint):
    for attempt in range(3):
        try:
            with urlopen(endpoint, timeout=25) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code not in {429, 502, 503, 504} or attempt == 2:
                raise RuntimeError(f"Public Landsat API returned HTTP {error.code}") from None
            retry = error.headers.get("Retry-After", "")
            time.sleep(min(int(retry), 25) if retry.isdigit() else 4 * (attempt + 1))
        except (URLError, TimeoutError):
            if attempt == 2:
                raise RuntimeError("Public Landsat API could not be reached") from None
            time.sleep(4 * (attempt + 1))


def open_window(gdal, href, case):
    signed = read_json(f"{API}/sas/v1/sign?{urlencode({'href': href})}")["href"]
    if urlsplit(signed).scheme != "https":
        raise RuntimeError("Expected an HTTPS Landsat asset")
    resolution = case["resolution_grid_m"]
    # Suppress GDAL's raw URL in errors, which can contain a short-lived SAS token.
    gdal.PushErrorHandler("CPLQuietErrorHandler")
    try:
        ds = gdal.Warp(
            "", "/vsicurl/" + signed, format="MEM", dstSRS=f"EPSG:{case['epsg']}",
            outputBounds=case["bounds_lonlat"], outputBoundsSRS="EPSG:4326",
            xRes=resolution, yRes=resolution, targetAlignedPixels=True,
            resampleAlg="near",
        )
    except RuntimeError:
        raise RuntimeError("GDAL could not read the requested public raster window") from None
    finally:
        gdal.PopErrorHandler()
    return ds


def prepare(manifest_path, output_dir, ca_bundle=None, rasters_only=False):
    case = json.loads(manifest_path.read_text(encoding="utf-8"))
    if "periods" in case:
        if not rasters_only:
            raise ValueError("Use --rasters-only for a seasonal manifest")
        case["scenes"] = [record for period in case["periods"] for record in period["scenes"]]
    validate_manifest(case)
    if output_dir.exists():
        raise FileExistsError(f"Choose a new output directory: {output_dir}")
    configure()
    from osgeo import gdal, osr

    gdal.UseExceptions()
    crs = osr.SpatialReference()
    if crs.ImportFromEPSG(case["epsg"]) or not crs.IsProjected() or crs.GetLinearUnits() != 1:
        raise ValueError("Expected a projected coordinate system with metre units")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".temperature-", dir=output_dir.parent) as work:
        work = Path(work)
        result_dir = work / "case"
        result_dir.mkdir()
        options = {"GDAL_HTTP_TIMEOUT": "25", "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR"}
        if ca_bundle is None and not gdal.GetConfigOption("CURL_CA_BUNDLE"):
            # Use the trust roots from Python's system TLS configuration.
            ca_bundle = work / "trust.pem"
            certs = ssl.create_default_context().get_ca_certs(binary_form=True)
            ca_bundle.write_text("".join(map(ssl.DER_cert_to_PEM_cert, certs)), encoding="ascii")
        if ca_bundle is not None:
            options["CURL_CA_BUNDLE"] = str(ca_bundle.resolve(strict=True))
        previous = {key: gdal.GetConfigOption(key) for key in options}
        try:
            for key, value in options.items():
                gdal.SetConfigOption(key, value)
            scenes = [prepare_scene(gdal, case, record, result_dir) for record in case["scenes"]]
        finally:
            for key, value in previous.items():
                gdal.SetConfigOption(key, value)
        report = {**case, "scenes": scenes, "source_collection": COLLECTION}
        report_path = result_dir / "verification.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not rasters_only:
            build_viewer(report_path, result_dir / f"heatwater-{case['slug']}-temperature.html")
        result_dir.rename(output_dir)
    return report


def prepare_scene(gdal, case, record, result_dir):
    scene_id = record["scene"]
    item = read_json(f"{API}/stac/v1/collections/{COLLECTION}/items/{scene_id}")
    if item.get("id") != scene_id or not all(key in item["assets"] for key in BANDS):
        raise ValueError(f"Required temperature and quality bands are missing for {scene_id}")
    thermal, qa_pixel, qa_radsat = [open_window(gdal, item["assets"][key]["href"], case) for key in BANDS]
    grid = (thermal.GetGeoTransform(), thermal.GetProjection())
    if any((band.GetGeoTransform(), band.GetProjection()) != grid for band in (qa_pixel, qa_radsat)):
        raise ValueError(f"Temperature and QA grids disagree for {scene_id}")
    values = temperature_celsius(*(band.ReadAsArray() for band in (thermal, qa_pixel, qa_radsat)))
    height, width = values.shape
    valid_count = int(np.count_nonzero(values != NODATA))
    expected = {"width": width, "height": height, "valid_count": valid_count}
    if not valid_count or any(key in record and record[key] != value for key, value in expected.items()):
        raise ValueError(f"{scene_id} differs from recorded dimensions or valid count: {expected}")
    filename = scene_id + ".tif"
    ds = gdal.GetDriverByName("GTiff").Create(
        str(result_dir / filename), width, height, 1, gdal.GDT_Float32, ["COMPRESS=DEFLATE"])
    ds.SetGeoTransform(grid[0])
    ds.SetProjection(grid[1])
    band = ds.GetRasterBand(1)
    band.SetNoDataValue(NODATA)
    band.SetUnitType("degC")
    band.WriteArray(values)
    ds.FlushCache()
    band = ds = None
    return {"scene": scene_id, "file": filename, **expected, "coverage": valid_count / values.size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, required=True, help="City scenes.json")
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    parser.add_argument("--ca-bundle", type=Path, help="Optional trusted CA bundle for GDAL")
    parser.add_argument("--rasters-only", action="store_true", help="Prepare QA-masked rasters without a single-scene viewer")
    args = parser.parse_args()
    try:
        report = prepare(args.case, args.output, args.ca_bundle, args.rasters_only)
    except (KeyError, ValueError, OSError, RuntimeError) as error:
        parser.exit(1, f"Could not build temperature case: {error}\n")
    print(f"Built {report['slug']} from {len(report['scenes'])} Landsat scene(s): {args.output}")


if __name__ == "__main__":
    main()
