# Architecture

```mermaid
flowchart LR
  A[JSON config and input files] --> B[Preflight: paths, grid, units, vector fields]
  B --> C[Align water proxy to LST reference]
  C --> D[Percentile normalization]
  D --> E[Heat-water score and component quadrants]
  E --> F[Expansion and building-function exposure]
  F --> G[GeoTIFF, CSV, figures and sensitivity]
  G --> H[Checksums and output validation]
```

- scripts/project_config.py: portable path and parameter contract.
- scripts/risk_logic.py: NumPy formulas independent of GIS software.
- scripts/build_heat_water_resilience.py: GDAL/OGR processing.
- scripts/make_figures.py: map rendering; optional context vectors.
- scripts/provenance.py and validate_outputs.py: integrity and grid checks.
- scripts/run_pipeline.py: single orchestration entry.
- scripts/synthetic_case.py: generated demonstration inputs, never observations.
- scripts/sensitivity_analysis.py: score and classification parameter sweeps.

Source execution uses the scripts package. Installation exposes the same files
as the heatwater package and the heatwater CLI; formulas are not duplicated.
