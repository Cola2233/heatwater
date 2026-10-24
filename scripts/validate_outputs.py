"""Validate input contracts and checksum/grid integrity of pipeline outputs."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
import numpy as np
from .provenance import validate_records
from .geo_runtime import configure
configure()

RASTERS = (
"heat_risk_2013_2015_30m.tif","heat_risk_2021_2023_30m.tif",
"heat_persistence_risk_30m.tif","water_risk_normalized_30m.tif",
"compound_heat_water_risk_30m.tif","compound_action_zones_30m.tif",
"new_impervious_compound_priority_30m.tif","building_function_exposure_30m.tif",
"human_exposure_priority_score_30m.tif","human_exposure_priority_zones_30m.tif")
FIGURES=("01_heat_water_compound_dashboard.png","02_human_exposure_priority.png",
         "heat_persistence_risk_map.png","water_risk_map.png")
TABLES=("compound_action_zone_summary.csv","human_exposure_priority_summary.csv","data_manifest.csv")

def grid_signature(ds):
    from osgeo import osr
    srs=osr.SpatialReference(wkt=ds.GetProjection())
    return ds.RasterXSize,ds.RasterYSize,ds.GetGeoTransform(),srs

def same_grid(a,b):
    sa,sb=grid_signature(a),grid_signature(b)
    return sa[:2]==sb[:2] and np.allclose(sa[2],sb[2],rtol=0,atol=1e-7) and bool(sa[3].IsSame(sb[3]))

def preflight(config):
    from osgeo import gdal,ogr,osr
    gdal.UseExceptions()
    for role,path in config.inputs.items():
        if not path.is_file():
            raise FileNotFoundError(f"Missing {role}: {path}")
    ref=gdal.Open(str(config.input_path("heat_early")))
    signature=grid_signature(ref)
    expected=osr.SpatialReference()
    expected.ImportFromEPSG(config.grid["epsg"])
    gt=signature[2]
    if not signature[3].IsSame(expected) or not np.allclose((gt[1],gt[2],gt[4],gt[5]),(30,0,0,-30)):
        raise ValueError("Reference grid must be north-up 30 m EPSG:32651")
    for role in ("heat_late","transition"):
        ds=gdal.Open(str(config.input_path(role)))
        if not same_grid(ref,ds):
            raise ValueError(role+" grid differs from heat_early")
    for role in ("heat_early","heat_late"):
        ds=gdal.Open(str(config.input_path(role)))
        band=ds.GetRasterBand(1)
        array=band.ReadAsArray()
        valid=np.isfinite(array)
        if band.GetNoDataValue() is not None:
            valid &= array != band.GetNoDataValue()
        if not valid.any() or not np.all((array[valid]>-50)&(array[valid]<80)):
            raise ValueError(role+" must contain Celsius LST in (-50,80)")
    def values(role):
        ds=gdal.Open(str(config.input_path(role)))
        band=ds.GetRasterBand(1)
        a=band.ReadAsArray().astype(np.float32)
        if band.GetNoDataValue() is not None:
            a[a==band.GetNoDataValue()]=np.nan
        return a
    needed=np.isfinite(values("heat_early")) & np.isfinite(values("heat_late"))
    transition=values("transition")
    if not np.all(np.isin(transition[needed], (1,2,3,4))):
        raise ValueError("transition requires codes 1–4 across the common LST coverage")
    water=values("water_risk")
    finite=np.isfinite(water)
    if not finite.any() or not np.all((water[finite]>=0)&(water[finite]<=1)):
        raise ValueError("water_risk requires finite source values within [0,1] before interpolation")
    ds=gdal.Open(str(config.input_path("water_risk")))
    if not ds.GetProjection():
        raise ValueError("water_risk requires a coordinate reference system")
    vector=ogr.Open(str(config.input_path("building_functions")))
    layer=vector.GetLayerByName(config.building_layer)
    if layer is None or layer.GetSpatialRef() is None:
        raise ValueError("Missing building layer or coordinate reference system")
    if layer.GetLayerDefn().GetFieldIndex(config.building_field)<0:
        raise ValueError("Missing building field: "+config.building_field)
    values={f.GetField(config.building_field) for f in layer}
    expected_values={"Residential","Educational","Healthcare","Public service"}
    if not values.intersection(expected_values):
        raise ValueError("No supported building function categories")
    return ref

def validate(config, manifest: Path | None=None):
    from osgeo import gdal
    manifest=manifest or config.output_dir/"output_manifest.csv"
    with manifest.open(encoding="utf-8-sig") as f:
        rows=list(csv.DictReader(f))
    validate_records(rows,config.project_root)
    expected=[config.output_dir/name for name in RASTERS+TABLES]
    expected += [config.figure_dir/name for name in FIGURES]
    expected += [config.output_dir/"run_metadata.json",
                 config.output_dir/"sensitivity/parameter_sensitivity.csv",
                 config.output_dir/"sensitivity/sensitivity.png"]
    declared={(config.project_root/r["relative_path"]).resolve() for r in rows}
    if not all(p.resolve() in declared for p in expected):
        raise ValueError("Output manifest does not declare every required product")
    ref=gdal.Open(str(config.output_dir/RASTERS[0]))
    for name in RASTERS:
        ds=gdal.Open(str(config.output_dir/name))
        if not same_grid(ref,ds) or ds.GetRasterBand(1).GetNoDataValue() is None:
            raise ValueError("Output grid or NoData mismatch: "+name)
    return len(rows)

def main():
    from .project_config import load_project_config
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",required=True,type=Path)
    parser.add_argument("--manifest",type=Path)
    args=parser.parse_args()
    print("Validated output files:",validate(load_project_config(args.config),args.manifest))

if __name__=="__main__":
    main()
