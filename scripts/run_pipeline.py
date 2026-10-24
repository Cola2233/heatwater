"""Run validated GIS processing, figures, sensitivity and provenance."""
from __future__ import annotations
import argparse
import csv
import json
import subprocess
from pathlib import Path
from .project_config import load_project_config
from .provenance import file_record, run_metadata

def run(config):
    from . import build_heat_water_resilience as geo
    from . import make_figures, sensitivity_analysis
    from .validate_outputs import preflight, validate, RASTERS, FIGURES, TABLES
    from osgeo import gdal
    preflight(config)
    geo.main(config)
    make_figures.main(config)
    sensitivity_analysis.run(config)
    try:
        revision=subprocess.check_output(["git","rev-parse","HEAD"],
            cwd=config.project_root,stderr=subprocess.DEVNULL,text=True).strip()
    except (OSError,subprocess.CalledProcessError):
        revision=None
    metadata=run_metadata(config,gdal.VersionInfo("--version"),revision)
    (config.output_dir/"run_metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    paths=[config.output_dir/n for n in RASTERS+TABLES]
    paths += [config.figure_dir/n for n in FIGURES]
    paths += [config.output_dir/"run_metadata.json",
              config.output_dir/"sensitivity/parameter_sensitivity.csv",
              config.output_dir/"sensitivity/sensitivity.png"]
    rows=[file_record(p,config.project_root) for p in paths]
    manifest=config.output_dir/"output_manifest.csv"
    with manifest.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print("Validated output files:",validate(config))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",type=Path,required=True)
    args=parser.parse_args()
    run(load_project_config(args.config))

if __name__=="__main__":
    main()
