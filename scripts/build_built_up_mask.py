"""Sample ESA WorldCover 2021 built-up class on an existing temperature grid."""

import argparse
from pathlib import Path

import numpy as np

from .geo_runtime import configure


BEIJING_WORLDCOVER = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
    "ESA_WorldCover_10m_2021_v200_N39E114_Map.tif"
)


def build(reference, output, worldcover=BEIJING_WORLDCOVER):
    configure()
    from osgeo import gdal
    from .seasonal_temperature import write_raster

    gdal.UseExceptions()
    if output.exists():
        raise FileExistsError(output)
    ref = gdal.Open(str(reference))
    gt = ref.GetGeoTransform()
    if gt[2] or gt[4] or gt[1] <= 0 or gt[5] >= 0 or not ref.GetProjection():
        raise ValueError("Expected a north-up georeferenced temperature raster")
    width, height = ref.RasterXSize, ref.RasterYSize
    source = "/vsicurl/" + worldcover if worldcover.startswith("https://") else worldcover
    aligned = gdal.Warp(
        "", source, format="MEM", dstSRS=ref.GetProjection(),
        outputBounds=(gt[0], gt[3] + height * gt[5], gt[0] + width * gt[1], gt[3]),
        width=width, height=height, dstNodata=0, resampleAlg="near",
    )
    if aligned.GetGeoTransform() != gt:
        raise ValueError("WorldCover output is not aligned to the temperature grid")
    classes = aligned.ReadAsArray()
    if np.any(classes == 0):
        raise ValueError("The WorldCover tile does not fully cover the requested grid")
    mask = (classes == 50).astype(np.uint8)
    if not mask.any():
        raise ValueError("No WorldCover built-up samples at this site")
    output.parent.mkdir(parents=True, exist_ok=True)
    write_raster(gdal, output, mask, (gt, ref.GetProjection()), gdal.GDT_Byte, "class")
    with gdal.Open(str(output), gdal.GA_Update) as result:
        result.SetMetadata({
            "SOURCE": "ESA WorldCover 2021 v200",
            "SOURCE_TILE": Path(worldcover).name,
            "SOURCE_CLASS": "50",
            "SAMPLING": "nearest source class at target pixel center",
            "MASK_VALUES": "1=built-up, 0=outside built-up mask",
        })
    return int(mask.sum()), int(mask.size)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--worldcover", default=BEIJING_WORLDCOVER, help="WorldCover GeoTIFF or HTTPS URL")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count, total = build(args.reference, args.output, args.worldcover)
    print(f"Built-up mask: {count}/{total} cells ({count / total:.2%})")


if __name__ == "__main__":
    main()
