"""Separate sensitivity of continuous scores from quadrant classification."""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
from .risk_logic import combine_risk, classify_compound_risk, classify_exposure_priority

WEIGHTS = (0.5, 0.55, 0.6, 0.7)
THRESHOLDS = (0.5, 0.6, 0.67, 0.7)

def sweep(heat, water, valid):
    return [dict(heat_weight=w, water_weight=1-w, threshold=t,
                 compound=combine_risk(heat,water,valid,heat_weight=w,water_weight=1-w),
                 zones=classify_compound_risk(heat,water,valid,threshold=t))
            for w in WEIGHTS for t in THRESHOLDS]

def run(config):
    from . import build_heat_water_resilience as geo
    def read(name):
        return geo.read_band(config.output_dir / name)[1]
    heat = read("heat_persistence_risk_30m.tif")
    water = read("water_risk_normalized_30m.tif")
    exposure = read("building_function_exposure_30m.tif")
    valid = (heat >= 0) & (water >= 0) & (exposure >= 0)
    dest = config.output_dir / "sensitivity"
    dest.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in sweep(heat, water, valid):
        human = classify_exposure_priority(r["compound"],exposure,valid,
            compound_threshold=r["threshold"],
            exposure_threshold=config.parameters["exposure_threshold"])
        row = {k: r[k] for k in ("heat_weight","water_weight","threshold")}
        row["mean_compound_score"] = float(np.nanmean(r["compound"]))
        row["high_score_area_km2"] = float(np.sum(valid & (r["compound"] >= r["threshold"])) * 0.0009)
        row["high_score_high_exposure_area_km2"] = float(np.sum(human == 1) * 0.0009)
        for code in range(1,5):
            row[f"zone_{code}_area_km2"] = float(np.sum(r["zones"] == code) * 0.0009)
        rows.append(row)
    with (dest / "parameter_sensitivity.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1,2,figsize=(12,4),constrained_layout=True)
    if config.synthetic:
        fig.suptitle("SYNTHETIC DEMO — NOT OBSERVATIONS")
    baseline = [r for r in rows if r["heat_weight"] == 0.55]
    x = [r["threshold"] for r in baseline]
    bottom = np.zeros(len(x))
    for code,color in enumerate(("#e8f5e9","#ef6c5b","#42a5f5","#6a1b9a"),1):
        y=np.array([r[f"zone_{code}_area_km2"] for r in baseline])
        axes[0].bar(range(len(x)),y,bottom=bottom,label=f"Zone {code}",color=color)
        bottom += y
    axes[0].set_xticks(range(len(x)),x)
    axes[0].set(xlabel="Component threshold",ylabel="Area (km²)",title="Quadrant areas (independent of weights)")
    axes[0].legend()
    for threshold in THRESHOLDS:
        selected = [r for r in rows if r["threshold"] == threshold]
        axes[1].plot(WEIGHTS,[r["high_score_area_km2"] for r in selected],
                     marker="o",label=str(threshold))
    axes[1].set(xlabel="Heat weight",ylabel="High-score area (km²)",title="Score sensitivity")
    axes[1].legend(title="Score threshold")
    fig.savefig(dest / "sensitivity.png",dpi=180)
    plt.close(fig)
    return rows

def main():
    import argparse
    from .project_config import load_project_config
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",required=True,type=Path)
    args=parser.parse_args()
    run(load_project_config(args.config))

if __name__ == "__main__":
    main()
