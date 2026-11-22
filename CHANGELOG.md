# Changelog

## v0.2.0

- Added reproducible extraction of the seven public Landsat temperature samples from fixed scene manifests.
- Added paired Beijing summer composites with same-day mosaicking, median temperature, and per-pixel observation support.
- Applied a common WorldCover 2021 built-up mask within the Beijing central sample and documented its grid, attribution and interpretation.
- Packaged the offline map, GeoTIFFs, mask and scene manifest together for review and reuse.

## v0.1.0

- Published the Heatwater core and city case catalogue.
- Documented the complete Changchun Fourth Ring analysis, including 51 road-based units, 72 parameter combinations and screening outcomes.
- Added independent Landsat surface-temperature previews for cities with quality-checked scenes.
- Packaged the offline synthetic quickstart, Chinese walkthrough, source distribution and installation wheel.

## District explanation and parameter stability — 2026-11-06

- Extended the independent offline MapLibre preview with district evidence cards and indicator ranks.
- Reused the existing raster and block cores in a local Worker to evaluate 72 parameter combinations.
- Added selection-frequency maps, synchronized shortlist filters, per-case evidence and CSV with screening rules.
- Kept unsupported units out of selection-frequency and rank calculations; frequency is not event probability.
- Built real and synthetic standalone previews; retained the existing Canvas entry.

## Map parameter feedback — 2026-11-04

- Linked weight and threshold changes to explicit spatial difference maps.
- Added previous-step comparison, optional layer following and hover values.
- Kept raw scores intact; exported difference maps identify their comparison baseline.
- Verified real and synthetic offline interactions, exports and mobile layout.

## Unreleased — open-source onboarding, 2026-11-02

- Added a coarser overview scale, multi-scale switching and current-group-aware merging.
- Added optional road-derived blocks, raster-center summaries and diagnostics.
- Added block/raster map modes, selection, ranking, filters, pagination and CSV.
- Added nine generated public demo blocks; private Changchun blocks stay local.
- Adopted the selected atlas UI with linked charts and focused controls.
- Made standalone bundling default to the public synthetic entry.
- Added installed CLI entry points for web data export and HTML bundling.
- Added private-data-independent browser checks for source and standalone HTML.
- Added pinned browser-test dependencies, package/browser CI and artifact uploads.
- Reframed the README, contribution guide and roadmap around an open-source tool.

## Carbon-inspired UI refresh — 2026-10-25

- Applied awesome-design-md's IBM reference via a project-specific DESIGN.md.
- Reworked layout, typography, neutral surfaces, square controls and focus states.
- Added consistent vector icons and accessible mobile navigation.
- Preserved analytical colors, numerical baselines and standalone offline sharing.

## HTML explorer — 2026-10-25

- Added offline responsive map explorer, six layers and parameter controls.
- Added PNG/CSV/settings exports and accessible keyboard map navigation.
- Added portable browser data exporter, public synthetic and ignored local cases.
- Added numerical parity tests and optional desktop/mobile browser checks.

## 0.1.0 — local release candidate, 2026-10-25

- Portable JSON configuration and parameter validation.
- Preserved legacy weights 0.55/0.45 and component threshold 0.67.
- Input preflight, NoData masking, checksum manifests and metadata.
- Synthetic GIS case, sensitivity analysis, independent tests and CI.
- Separate code/data permissions, citation and reproducibility documentation.

Publication, upstream license review and observed-flood calibration remain pending.
