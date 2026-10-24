"""Generate a deterministic, redistributable GIS demo (not observations)."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from .geo_runtime import configure
configure()
from osgeo import gdal, ogr, osr

def create_case(root: Path) -> Path:
    root=root.resolve()
    if (root / "config.json").exists():
        raise FileExistsError("Synthetic configuration already exists")
    raw=root / "data"
    raw.mkdir(parents=True,exist_ok=True)
    if any(raw.iterdir()):
        raise FileExistsError("Synthetic data directory must be empty")
    osr.UseExceptions()
    srs=osr.SpatialReference()
    srs.ImportFromEPSG(32651)
    gt=(680000,30,0,4870000,0,-30)
    y,x=np.mgrid[0:40,0:48].astype(np.float32)
    sources=dict(heat_early=22+x/5+y/20,heat_late=24+x/6+y/15,
                 water_risk=np.clip(0.2+y/50-x/200,0,1),
                 transition=np.where((x%7)<3,2,1).astype(np.float32))
    inputs={}
    for role,array in sources.items():
        path=raw / (role+".tif")
        ds=gdal.GetDriverByName("GTiff").Create(str(path),48,40,1,gdal.GDT_Float32)
        ds.SetGeoTransform(gt)
        ds.SetProjection(srs.ExportToWkt())
        array[0,:]=-9999
        ds.GetRasterBand(1).SetNoDataValue(-9999)
        ds.GetRasterBand(1).WriteArray(array)
        ds=None
        inputs[role]="data/"+path.name
    vector=raw / "buildings.gpkg"
    ds=ogr.GetDriverByName("GPKG").CreateDataSource(str(vector))
    layer=ds.CreateLayer("buildings",srs,ogr.wkbPolygon)
    layer.CreateField(ogr.FieldDefn("Function",ogr.OFTString))
    for i,name in enumerate(("Residential","Educational","Healthcare","Public service")):
        x0=gt[0]+i*300
        y0=gt[3]-100
        geom=ogr.CreateGeometryFromWkt(
            f"POLYGON (({x0} {y0},{x0+250} {y0},{x0+250} {y0-900},{x0} {y0-900},{x0} {y0}))")
        feature=ogr.Feature(layer.GetLayerDefn())
        feature.SetField("Function",name)
        feature.SetGeometry(geom)
        layer.CreateFeature(feature)
    ds=None
    inputs["building_functions"]="data/buildings.gpkg"
    config=dict(project_root=".",inputs=inputs,building_layer="buildings",synthetic=True,
                outputs=dict(output_dir="results",derived_dir="derived",figure_dir="figures"))
    path=root / "config.json"
    path.write_text(json.dumps(config,indent=2),encoding="utf-8")
    return path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory",type=Path,default=Path("demo"))
    print(create_case(parser.parse_args().directory))

if __name__=="__main__":
    main()
