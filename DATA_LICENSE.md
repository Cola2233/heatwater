# Data and figure permissions

MIT applies to original source code and project-authored documentation.
Synthetic arrays and geometric features from scripts/synthetic_case.py are
also MIT-licensed. They do not represent observed places or people.

Third-party inputs are not relicensed by this repository. These Changchun
inputs are excluded from the public repository:

| Input | Known provenance | Redistribution status |
|---|---|---|
| Early/late summer LST | Existing Landsat-derived composites | Product terms and processing provenance require review |
| Transition | Existing GLC_FCS30D-derived codes | Upstream terms require review |
| Water-screening index | Existing teaching workflow | Component sources and terms require review |
| Building functions | Existing SinoBF-1 subset | Upstream terms require review |
| Context vectors | Existing project GeoPackage | Individual source terms require review |
| Road-derived blocks | Local road layer with OSM-style identifiers and tags | Source provenance and attribution require review; real block polygons remain local |

The Changchun research data and derived figures remain local pending source
review. The public quickstart uses synthetic data. The separate Beijing
temperature examples under `cases/` use USGS Landsat Collection 2 Level-2 Surface Temperature.
USGS states that Landsat products have no use restrictions and requests citation.
The scene identifiers and coverage are listed on each case page in the repository's `cases/` directory.
QA steps and source citation are in [the temperature sample notes](docs/beijing-temperature-demo.md).

The Beijing v0.2.0 built-up mask is derived from ESA WorldCover 2021 v200
(CC BY 4.0). © ESA WorldCover project 2021 / Contains modified Copernicus
Sentinel data (2021) processed by ESA WorldCover consortium.
[Source dataset and citation](https://doi.org/10.5281/zenodo.7254221).
