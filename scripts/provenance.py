"""Checksums and output manifests without user-specific source paths."""
from __future__ import annotations
import hashlib
import platform
from datetime import datetime, timezone
import numpy as np
from pathlib import Path

def run_metadata(config, gdal_version: str, revision: str | None) -> dict:
    from . import __version__
    return dict(
        software_version=__version__, git_revision=revision,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        python=platform.python_version(), numpy=np.__version__, gdal=gdal_version,
        synthetic=config.synthetic, building_layer=config.building_layer,
        building_field=config.building_field,
        parameters=config.parameters, grid=config.grid,
        source_files={k:dict(name=p.name,sha256=sha256(p),size_bytes=p.stat().st_size)
                      for k,p in config.inputs.items()},
        scientific_scope="Research screening proxy; no flood forecasting or population estimates.")

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def file_record(path: Path, root: Path) -> dict:
    path, root = path.resolve(), root.resolve()
    return dict(relative_path=path.relative_to(root).as_posix(),
                sha256=sha256(path), size_bytes=path.stat().st_size)

def validate_records(records: list[dict], root: Path) -> None:
    root = root.resolve()
    if not records:
        raise ValueError("Manifest contains no outputs")
    for row in records:
        path = (root / row["relative_path"]).resolve()
        if root not in path.parents:
            raise ValueError("Manifest path escapes output root")
        if not path.is_file():
            raise FileNotFoundError(path.name)
        if path.stat().st_size != int(row["size_bytes"]) or sha256(path) != row["sha256"]:
            raise ValueError("Output checksum mismatch: " + row["relative_path"])
