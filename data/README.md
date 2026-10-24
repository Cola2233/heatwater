# Input data contract

Public quick-start: generate the synthetic case described in
../docs/reproducibility.md. No third-party data download is necessary.

For the real case, acquire your own permitted copies and set config/local.json:

| Role | Required | Expected content |
|---|---|---|
| heat_early | yes | Early Celsius LST composite, north-up 30 m EPSG:32651 |
| heat_late | yes | Late Celsius LST, identical grid to heat_early |
| transition | yes | Identical grid; complete common LST coverage, codes 1–4; 2=new impervious |
| water_risk | yes | Water proxy in [0,1], CRS and NoData declared |
| building_functions | yes | GPKG with declared CRS and supported function field |
| hardening | no | Support raster with valid CRS |
| low_elevation | no | Support raster with valid CRS |
| context_vectors | no | city_boundary, waterways, major_roads layers, reference CRS |

Building defaults: layer changchun_4ring_building_function, field Function,
values Residential, Educational, Healthcare, Public service.
Set building_layer/building_field in JSON to override layer and field names.
At least one supported category is required; absence of another category means
zero presence for that category.

Input paths resolve relative to project_root, itself relative to the config file.
Place third-party data in ignored data/external/. Store licensing evidence and
source acquisition/QA records alongside your local data. Review DATA_LICENSE.md
before distributing any real or derived data.
