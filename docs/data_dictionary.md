# Data dictionary

All final rasters have one band on the reference grid (EPSG:32651, 30 m).
Float outputs use Float32, NoData=-9999, and range [0,1].
Categorical outputs use Byte. The following names are under the output directory.

| Filename | Meaning | Unit / codes |
|---|---|---|
| heat_risk_2013_2015_30m.tif | Normalized early LST | Relative score |
| heat_risk_2021_2023_30m.tif | Normalized late LST | Relative score |
| heat_persistence_risk_30m.tif | Mean of two heat scores | Relative score |
| water_risk_normalized_30m.tif | Normalized aligned water proxy | Relative score |
| compound_heat_water_risk_30m.tif | Weighted heat/water combination | Relative score |
| compound_action_zones_30m.tif | Component quadrants | 0 invalid; 1 low/low; 2 heat; 3 water; 4 both |
| new_impervious_compound_priority_30m.tif | Expansion priority | 0 unselected or invalid; 1 both high; 2 one high; 3 neither |
| building_function_exposure_30m.tif | Weighted functional presence | Relative score, not persons |
| human_exposure_priority_score_30m.tif | Score adjusted for exposure | Relative score |
| human_exposure_priority_zones_30m.tif | Score/exposure quadrants | 0 invalid; 1 high/high; 2 high/low; 3 low/high; 4 low/low |

Component and exposure categorical rasters use NoData=0. Expansion uses
NoData=0, intentionally treating unselected land as outside the product.
Derived building-presence rasters use 0=absence, 1=presence, NoData=255;
absence must never be treated as invalid. Other derived rasters use -9999.

Summary CSV files contain zone_code, zone_label, pixel_count, area_km2,
share_percent and mean scores. Area is cell count×0.0009 km²; shares use
the joint valid analysis mask. Expansion area fields count transition==2.

data_manifest.csv lists input role, source filename, SHA-256 and byte size.
output_manifest.csv lists each required output relative to project_root,
its SHA-256 and byte size. run_metadata.json records UTC time, software
versions, Git revision when available, parameters, grid and source hashes.
Metadata also records the synthetic/observational designation, selected
building layer/field and NumPy version. No absolute input paths are included.

sensitivity/parameter_sensitivity.csv contains the two weights, threshold,
mean compound score, high-score area, high-score/high-exposure area and four
component-quadrant areas for each combination. Areas use km².
