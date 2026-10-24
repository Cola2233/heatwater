"""Validated portable project configuration; imports no GIS runtime."""
from __future__ import annotations
import json
import math
from dataclasses import dataclass
from pathlib import Path

DEFAULTS = dict(heat_weight=0.55, water_weight=0.45, zone_threshold=0.67,
                compound_threshold=0.67, exposure_threshold=0.6)
REQUIRED = ("heat_early", "heat_late", "transition", "water_risk", "building_functions")

@dataclass(frozen=True)
class ProjectConfig:
    project_root: Path
    inputs: dict
    parameters: dict
    output_dir: Path
    derived_dir: Path
    figure_dir: Path
    grid: dict
    building_layer: str
    building_field: str
    synthetic: bool

    def input_path(self, role: str) -> Path:
        return self.inputs[role]

def load_project_config(path: Path) -> ProjectConfig:
    path = Path(path).resolve()
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    root = (path.parent / raw.get("project_root", "..")).resolve()
    def resolve(value):
        return (root / value).resolve()
    inputs = raw.get("inputs", {})
    for key in REQUIRED:
        if not inputs.get(key):
            raise ValueError("Missing required input: " + key)
    inputs = {k: resolve(v) for k,v in inputs.items() if v}
    params = {**DEFAULTS, **raw.get("parameters", {})}
    for key, value in params.items():
        if not isinstance(value, (int,float)) or isinstance(value,bool) or not math.isfinite(value):
            raise ValueError("Invalid numeric parameter: " + key)
    if min(params["heat_weight"], params["water_weight"]) < 0 or not math.isclose(
            params["heat_weight"] + params["water_weight"], 1.0, abs_tol=1e-8):
        raise ValueError("heat_weight and water_weight must sum to 1")
    for key in ("zone_threshold","compound_threshold","exposure_threshold"):
        if not 0 < params[key] < 1:
            raise ValueError(key + " must be between 0 and 1")
    grid = {**dict(resolution_m=30, epsg=32651), **raw.get("grid", {})}
    if grid["resolution_m"] != 30 or grid["epsg"] != 32651:
        raise ValueError("This case study requires 30 m EPSG:32651")
    outputs = raw.get("outputs", {})
    dirs = [resolve(outputs.get(k, default)) for k, default in (
        ("output_dir","outputs"),("derived_dir","data/derived"),("figure_dir","figures"))]
    for dest in dirs:
        if dest == path or dest in path.parents:
            raise ValueError("output directory contains the configuration file")
        if root not in dest.parents:
            raise ValueError("output directories must be inside project_root")
        if dest == root or dest == root.parent:
            raise ValueError("output directory cannot be project root")
        if any(p == dest or dest in p.parents for p in inputs.values()):
            raise ValueError("output directory contains an input")
    for a in dirs:
        for b in dirs:
            if a != b and (a in b.parents or b in a.parents):
                raise ValueError("output directories must not overlap")
    if len(set(dirs)) != len(dirs):
        raise ValueError("output directories must be distinct")
    return ProjectConfig(root, inputs, params, *dirs, grid,
        raw.get("building_layer","changchun_4ring_building_function"),
        raw.get("building_field","Function"), bool(raw.get("synthetic", False)))
