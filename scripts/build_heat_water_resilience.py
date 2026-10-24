"""Build the Changchun 30 m heat-water compound-risk products.

The source analysis folders are intentionally read-only. All aligned rasters,
summary tables, and derived products are written to this project folder.
Run with a GDAL-enabled Python interpreter:

    python -m scripts.build_heat_water_resilience --config config/local.json
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

from .geo_runtime import configure
configure()

from osgeo import gdal, ogr

from .risk_logic import (
    classify_compound_risk,
    classify_exposure_priority,
    combine_risk,
    robust_minmax,
)

gdal.UseExceptions()

def configure_project(config):
    global CONFIG, DERIVED, OUTPUTS, HEAT_EARLY, HEAT_LATE, TRANSITION
    global WATER_RISK, HARDENING, LOW_ELEVATION, BUILDING_FUNCTIONS
    CONFIG = config
    DERIVED, OUTPUTS = config.derived_dir, config.output_dir
    HEAT_EARLY, HEAT_LATE, TRANSITION, WATER_RISK, BUILDING_FUNCTIONS = (
        config.input_path(k) for k in
        ("heat_early","heat_late","transition","water_risk","building_functions"))
    HARDENING = config.inputs.get("hardening")
    LOW_ELEVATION = config.inputs.get("low_elevation")

ZONE_LABELS = {
    1: "低热低涝—生态协同区",
    2: "高温治理优先区",
    3: "水涝治理优先区",
    4: "热涝双高—综合治理区",
}


def require_inputs() -> None:
    missing = [str(path) for path in CONFIG.inputs.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required inputs:\n" + "\n".join(missing))


def read_band(path: Path) -> tuple[gdal.Dataset, np.ndarray, float | None]:
    dataset = gdal.Open(str(path), gdal.GA_ReadOnly)
    if dataset is None:
        raise RuntimeError(f"Cannot open raster: {path}")
    band = dataset.GetRasterBand(1)
    array = band.ReadAsArray().astype(np.float32)
    nodata = band.GetNoDataValue()
    if nodata is not None:
        array[array == nodata] = np.nan
    return dataset, array, band.GetNoDataValue()


def reference_bounds(dataset: gdal.Dataset) -> tuple[float, float, float, float]:
    gt = dataset.GetGeoTransform()
    x_min = gt[0]
    y_max = gt[3]
    x_max = x_min + dataset.RasterXSize * gt[1]
    y_min = y_max + dataset.RasterYSize * gt[5]
    return x_min, y_min, x_max, y_max


def align_to_reference(
    source: Path,
    reference: gdal.Dataset,
    destination: Path,
    *,
    resample: str = "bilinear",
    nodata: float = -9999.0,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    options = gdal.WarpOptions(
        format="GTiff",
        outputType=gdal.GDT_Float32,
        outputBounds=reference_bounds(reference),
        width=reference.RasterXSize,
        height=reference.RasterYSize,
        dstSRS=reference.GetProjection(),
        resampleAlg=resample,
        dstNodata=nodata,
        multithread=True,
        creationOptions=["TILED=YES", "COMPRESS=LZW", "BIGTIFF=IF_SAFER"],
    )
    result = gdal.Warp(str(destination), str(source), options=options)
    if result is None:
        raise RuntimeError(f"Failed to align {source}")
    result = None


def write_like(
    reference: gdal.Dataset,
    destination: Path,
    array: np.ndarray,
    *,
    nodata: float,
    dtype: int = gdal.GDT_Float32,
    description: str = "",
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    driver = gdal.GetDriverByName("GTiff")
    output = driver.Create(
        str(destination),
        reference.RasterXSize,
        reference.RasterYSize,
        1,
        dtype,
        options=["TILED=YES", "COMPRESS=LZW", "BIGTIFF=IF_SAFER"],
    )
    if output is None:
        raise RuntimeError(f"Cannot create raster: {destination}")
    output.SetGeoTransform(reference.GetGeoTransform())
    output.SetProjection(reference.GetProjection())
    band = output.GetRasterBand(1)
    band.SetNoDataValue(nodata)
    if description:
        band.SetDescription(description)
    array_to_write = np.asarray(array).copy()
    if np.issubdtype(array_to_write.dtype, np.floating):
        array_to_write[~np.isfinite(array_to_write)] = nodata
    band.WriteArray(array_to_write)
    band.FlushCache()
    output.FlushCache()
    output = None


def valid_lst(array: np.ndarray) -> np.ndarray:
    return np.isfinite(array) & (array > -50.0) & (array < 80.0)


def valid_unit_risk(array: np.ndarray) -> np.ndarray:
    return np.isfinite(array) & (array >= 0.0) & (array <= 1.0)


def write_summary(
    path: Path,
    zones: np.ndarray,
    heat: np.ndarray,
    water: np.ndarray,
    compound: np.ndarray,
    transition: np.ndarray,
    pixel_area_km2: float,
) -> None:
    rows = []
    for code, label in ZONE_LABELS.items():
        mask = zones == code
        new_impervious = mask & (transition == 2)
        rows.append(
            {
                "zone_code": code,
                "zone_label": label,
                "pixel_count": int(mask.sum()),
                "area_km2": round(float(mask.sum() * pixel_area_km2), 4),
                "share_percent": round(float(mask.sum() / max((zones > 0).sum(), 1) * 100), 2),
                "mean_heat_risk": round(float(np.nanmean(heat[mask])) if mask.any() else math.nan, 4),
                "mean_water_risk": round(float(np.nanmean(water[mask])) if mask.any() else math.nan, 4),
                "mean_compound_risk": round(float(np.nanmean(compound[mask])) if mask.any() else math.nan, 4),
                "new_impervious_area_km2": round(float(new_impervious.sum() * pixel_area_km2), 4),
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(path: Path) -> None:
    from .provenance import sha256
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["role", "source_name", "sha256", "size_bytes"])
        for role, source in CONFIG.inputs.items():
            writer.writerow([role, source.name, sha256(source), source.stat().st_size])


def rasterize_building_function(reference: gdal.Dataset, function_name: str, destination: Path) -> bool:
    """Rasterize one SinoBF-1 building-function category on the heat grid."""
    if not BUILDING_FUNCTIONS.exists():
        return False
    if destination.exists():
        destination.unlink()
    driver = gdal.GetDriverByName("GTiff")
    raster = driver.Create(
        str(destination),
        reference.RasterXSize,
        reference.RasterYSize,
        1,
        gdal.GDT_Byte,
        options=["TILED=YES", "COMPRESS=LZW", "BIGTIFF=IF_SAFER"],
    )
    if raster is None:
        raise RuntimeError(f"Cannot create rasterized building layer: {destination}")
    raster.SetGeoTransform(reference.GetGeoTransform())
    raster.SetProjection(reference.GetProjection())
    band = raster.GetRasterBand(1)
    band.SetNoDataValue(255)
    band.Fill(0)

    vector = ogr.Open(str(BUILDING_FUNCTIONS), 0)
    if vector is None:
        raise RuntimeError(f"Cannot open building function data: {BUILDING_FUNCTIONS}")
    layer = vector.GetLayerByName(CONFIG.building_layer)
    if layer is None:
        raise RuntimeError("Building function layer not found")
    escaped = function_name.replace("'", "''")
    layer.SetAttributeFilter(f'"{CONFIG.building_field}" = \'{escaped}\'')
    if gdal.RasterizeLayer(raster, [1], layer, burn_values=[1], options=["ALL_TOUCHED=TRUE"]) != 0:
        raise RuntimeError("Building rasterization failed")
    layer.SetAttributeFilter(None)
    raster.FlushCache()
    raster = None
    vector = None
    return True


def build_exposure_products(
    reference: gdal.Dataset,
    compound: np.ndarray,
    valid: np.ndarray,
    pixel_area_km2: float,
) -> None:
    """Build functional-exposure and human-priority products from building polygons."""
    categories = {
        "Residential": 0.60,
        "Educational": 0.90,
        "Healthcare": 1.00,
        "Public service": 0.70,
    }
    masks = {}
    for category in categories:
        path = DERIVED / (category.lower().replace(" ", "_") + "_presence_30m.tif")
        if not rasterize_building_function(reference, category, path):
            print(f"Building function source unavailable; skipped {category}")
            return
        _, mask, _ = read_band(path)
        masks[category] = mask > 0

    exposure = np.zeros(compound.shape, dtype=np.float32)
    for category, weight in categories.items():
        exposure += weight * masks[category].astype(np.float32)
    exposure = np.clip(exposure, 0.0, 1.0)
    exposure[~valid] = np.nan
    exposure_priority = classify_exposure_priority(compound, exposure, valid,
        compound_threshold=CONFIG.parameters["compound_threshold"],
        exposure_threshold=CONFIG.parameters["exposure_threshold"])
    human_priority = np.full(compound.shape, np.nan, dtype=np.float32)
    human_priority[valid] = compound[valid] * (0.4 + 0.6 * exposure[valid])

    write_like(
        reference,
        OUTPUTS / "building_function_exposure_30m.tif",
        exposure,
        nodata=-9999,
        description="居住与公共服务建筑功能暴露代理",
    )
    write_like(
        reference,
        OUTPUTS / "human_exposure_priority_score_30m.tif",
        human_priority,
        nodata=-9999,
        description="复合风险与建筑功能暴露优先级",
    )
    write_like(
        reference,
        OUTPUTS / "human_exposure_priority_zones_30m.tif",
        exposure_priority,
        nodata=0,
        dtype=gdal.GDT_Byte,
        description="重点人群与公共服务暴露分区编码",
    )

    rows = []
    for code, label in {
        1: "重点人群与公共服务保护区",
        2: "环境治理优先区",
        3: "公共服务暴露监测区",
        4: "一般关注区",
    }.items():
        mask = exposure_priority == code
        rows.append(
            {
                "zone_code": code,
                "zone_label": label,
                "pixel_count": int(mask.sum()),
                "area_km2": round(float(mask.sum() * pixel_area_km2), 4),
                "share_percent": round(float(mask.sum() / max((exposure_priority > 0).sum(), 1) * 100), 2),
                "mean_compound_risk": round(float(np.nanmean(compound[mask])) if mask.any() else math.nan, 4),
                "mean_exposure": round(float(np.nanmean(exposure[mask])) if mask.any() else math.nan, 4),
            }
        )
    with (OUTPUTS / "human_exposure_priority_summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(config) -> None:
    configure_project(config)
    require_inputs()
    DERIVED.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    reference, early_lst, _ = read_band(HEAT_EARLY)
    _, late_lst, _ = read_band(HEAT_LATE)
    _, transition, _ = read_band(TRANSITION)

    aligned_water = DERIVED / "water_risk_on_heat_grid_30m.tif"
    align_to_reference(WATER_RISK, reference, aligned_water)
    _, water_raw, _ = read_band(aligned_water)

    if HARDENING is not None and HARDENING.exists():
        align_to_reference(HARDENING, reference, DERIVED / "surface_hardening_on_heat_grid_30m.tif")
    if LOW_ELEVATION is not None and LOW_ELEVATION.exists():
        align_to_reference(LOW_ELEVATION, reference, DERIVED / "low_elevation_on_heat_grid_30m.tif")

    heat_valid = valid_lst(early_lst) & valid_lst(late_lst)
    water_valid = valid_unit_risk(water_raw)
    valid = heat_valid & water_valid

    early_risk = robust_minmax(early_lst, valid)
    late_risk = robust_minmax(late_lst, valid)
    heat_persistence = np.full(early_lst.shape, np.nan, dtype=np.float32)
    heat_persistence[valid] = 0.5 * (early_risk[valid] + late_risk[valid])

    water_risk = robust_minmax(water_raw, valid)
    compound = combine_risk(heat_persistence, water_risk, valid,
        heat_weight=CONFIG.parameters["heat_weight"], water_weight=CONFIG.parameters["water_weight"])
    zones = classify_compound_risk(heat_persistence, water_risk, valid,
        threshold=CONFIG.parameters["zone_threshold"])

    for array in [early_risk, late_risk, heat_persistence, water_risk, compound]:
        array[~valid] = np.nan

    write_like(reference, OUTPUTS / "heat_risk_2013_2015_30m.tif", early_risk, nodata=-9999, description="2013—2015标准化热风险")
    write_like(reference, OUTPUTS / "heat_risk_2021_2023_30m.tif", late_risk, nodata=-9999, description="2021—2023标准化热风险")
    write_like(reference, OUTPUTS / "heat_persistence_risk_30m.tif", heat_persistence, nodata=-9999, description="多年夏季持续热风险")
    write_like(reference, OUTPUTS / "water_risk_normalized_30m.tif", water_risk, nodata=-9999, description="标准化水涝风险")
    write_like(reference, OUTPUTS / "compound_heat_water_risk_30m.tif", compound, nodata=-9999, description="热—涝复合风险")
    write_like(reference, OUTPUTS / "compound_action_zones_30m.tif", zones, nodata=0, dtype=gdal.GDT_Byte, description="热—涝治理分区编码")

    new_impervious = transition == 2
    expansion_priority = np.zeros(zones.shape, dtype=np.uint8)
    expansion_priority[new_impervious & (zones == 4)] = 1
    expansion_priority[new_impervious & np.isin(zones, [2, 3])] = 2
    expansion_priority[new_impervious & (zones == 1)] = 3
    write_like(
        reference,
        OUTPUTS / "new_impervious_compound_priority_30m.tif",
        expansion_priority,
        nodata=0,
        dtype=gdal.GDT_Byte,
        description="新增不透水面热—涝治理优先级",
    )

    pixel_area_km2 = abs(reference.GetGeoTransform()[1] * reference.GetGeoTransform()[5]) / 1_000_000.0
    write_summary(OUTPUTS / "compound_action_zone_summary.csv", zones, heat_persistence, water_risk, compound, transition, pixel_area_km2)
    build_exposure_products(reference, compound, valid, pixel_area_km2)
    write_manifest(OUTPUTS / "data_manifest.csv")

    print(f"Reference grid: {reference.RasterXSize} x {reference.RasterYSize} at 30 m")
    print(f"Valid cells: {int(valid.sum())}")
    print(f"Heat-water compound products written to: {OUTPUTS}")


if __name__ == "__main__":
    import argparse
    from .project_config import load_project_config
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    main(load_project_config(parser.parse_args().config))
