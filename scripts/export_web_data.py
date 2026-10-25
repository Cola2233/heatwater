"""Export self-contained browser rasters. Real-data exports stay Git-ignored."""
from __future__ import annotations
import argparse
import base64
import json
from pathlib import Path
import numpy as np
from .project_config import load_project_config

def export(config, website: Path):
    from .validate_outputs import validate
    from .build_heat_water_resilience import read_band
    from .provenance import sha256
    validate(config)
    website=website.resolve()
    dest=website/"data"
    dest.mkdir(parents=True,exist_ok=True)
    source_names=dict(heat="heat_persistence_risk_30m.tif",
                      water="water_risk_normalized_30m.tif",
                      exposure="building_function_exposure_30m.tif")
    arrays={}
    reference=None
    for role,name in source_names.items():
        reference,array,_=read_band(config.output_dir/name)
        arrays[role]=base64.b64encode(array.astype("<f4").tobytes()).decode("ascii")
    # Expansion membership is obtained from the original same-grid transition input.
    _,transition,_=read_band(config.input_path("transition"))
    transition=np.nan_to_num(transition,nan=0).astype("u1")
    arrays["transition"]=base64.b64encode(transition.tobytes()).decode("ascii")
    meta=dict(id="demo" if config.synthetic else "changchun",
              title="模拟案例" if config.synthetic else "长春四环",
              synthetic=config.synthetic,width=reference.RasterXSize,height=reference.RasterYSize,
              resolution=config.grid["resolution_m"],epsg=config.grid["epsg"],
              geotransform=reference.GetGeoTransform(),
              periods=["2013–2015","2021–2023"] if not config.synthetic else ["模拟早期","模拟近期"],
              source_hashes={role:sha256(config.output_dir/name) for role,name in source_names.items()})
    payload=dict(meta=meta,arrays=arrays)
    filename="demo.js" if config.synthetic else "local.js"
    key="demo" if config.synthetic else "changchun"
    content="window.HEATWATER_DATASETS=window.HEATWATER_DATASETS||{};\n"
    content+="window.HEATWATER_DATASETS["+json.dumps(key)+"]="+json.dumps(payload,separators=(",",":"))+";\n"
    (dest/filename).write_text(content,encoding="utf-8")
    if not config.synthetic:
        template=(website/"index.html").read_text(encoding="utf-8")
        marker="<!-- LOCAL_DATA_SLOT -->"
        if marker not in template:
            raise ValueError("Website template has no local data slot")
        template=template.replace(marker,'<script src="data/local.js"></script>')
        (website/"local.html").write_text(template,encoding="utf-8")
    print("Browser data exported:",filename)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",type=Path,required=True)
    parser.add_argument("--website",type=Path,default=Path("website"))
    args=parser.parse_args()
    export(load_project_config(args.config),args.website)

if __name__=="__main__":
    main()
