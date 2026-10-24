# Contributing

Describe the research question or reproducible failure in an issue.
Add a synthetic regression test for code changes and run:

```sh
python -m unittest discover -s tests -v
python -m compileall -q scripts
```

Geospatial changes also require GDAL integration tests and the synthetic
end-to-end workflow in docs/reproducibility.md. Keep formulas in
scripts/risk_logic.py and validation in scripts/project_config.py.
Explain parameter changes and update the methods and data dictionary.

Do not attach private data or local.json. Proposed datasets need a source
version, license and attribution. Do not commit generated outputs.
