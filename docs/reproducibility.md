# Reproduce the workflow

## Minimal tests, no GIS installation

From the repository root:

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
```

GDAL integration checks are skipped when the GIS runtime is unavailable.

## Full environment

The preferred portable setup uses conda-forge:

```sh
conda env create -f environment.yml
conda activate heatwater
```

Alternatively run source commands with the Python interpreter supplied by your
QGIS installation. Set QGIS_ROOT only if runtime discovery cannot find its
apps directory. GDAL and its Python bindings must match; pip installation of
the base package intentionally does not install GDAL.

## Synthetic end-to-end case

Use an empty demo directory:

```sh
python -m scripts.synthetic_case --directory demo
python -m scripts.run_pipeline --config demo/config.json
python -m scripts.validate_outputs --config demo/config.json
```

Installed equivalents: heatwater-demo --directory demo, heatwater --config
demo/config.json, heatwater-validate --config demo/config.json.
The generated rasters and polygons are deterministic simulated values.
Titles explicitly say SYNTHETIC DEMO. Reuse a different empty directory
when regenerating inputs; the generator refuses to overwrite existing data.

Expected: 20 required artifacts validated, plus output_manifest.csv.
The demo analysis grid is 48×40; the first row is deliberately invalid.
Synthetic output includes ten rasters, two summary tables, input manifest,
four maps, run metadata and two sensitivity artifacts.

## Changchun case

Copy config/example.json to ignored config/local.json, acquire the permitted
inputs listed in data/README.md, and adjust paths. JSON backslashes must be
escaped; forward slashes work on Windows. Inputs resolve from project_root.
The default parameters reproduce the legacy implementation.

```sh
python -m scripts.run_pipeline --config config/local.json
python -m scripts.validate_outputs --config config/local.json
```

PowerShell wrapper: ./run_pipeline.ps1 -Python python -ConfigPath config/local.json.
For comparison with existing outputs, choose new, disjoint output, derived and
figure directories. The pipeline replaces its named generated products on rerun;
it checks inputs before writing. Archive results you need to retain.

Core outputs must have identical grid/NoData and match their recorded checksums.
Floating arrays can vary slightly across GDAL/NumPy versions; compare class
counts and numeric differences rather than expecting GeoTIFF byte equality
between separate software environments.
