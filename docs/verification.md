# Verification — 2026-10-25

Local release candidate: 0.1.0. These are local checks, not hosted CI results.

- QGIS Python: 21 tests passed, including GIS integration and reviewer regressions.
- Core tests can run without GDAL; GIS tests explicitly skip in that environment.
- Synthetic full pipeline completed on a 48×40 grid with 1,872 valid cells.
- Real local case completed on a 679×654 grid with 436,411 valid cells.
- Both complete runs validated 20 required output artifacts and their manifest.
- Real-data reproduction matched the existing ten raster arrays numerically;
  both summary CSV files were byte-identical to the local comparison baseline.
- The 0.55 heat-weight / 0.67 threshold sensitivity row matched all four
  baseline component-quadrant areas.
- A wheel was built with no dependency downloads and installed into a temporary
  project-local target. The installed heatwater namespace imported successfully.
- Synthetic preview images were visually inspected for labels and layout.
- The Git index excludes local configs, third-party rasters/vectors, competition
  packages and legacy competition narratives. Public files were scanned for
  personal absolute paths and credential-shaped strings.

Independent review identified runtime-discovery, resampling-dtype, source-range,
transition-coverage, metadata and overwrite-protection defects. Regression
tests were observed failing before fixes; the final suite passed.

The first public GitHub Actions run, upstream data-license verification,
independent flood observation evaluation and a citable archive are pending.
