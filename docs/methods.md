# Methods

## Case study and inputs

The local Changchun case uses a 679×654, north-up 30 m EPSG:32651 grid.
Inputs are two summer LST composites (2013–2015 and 2021–2023), a 2013–2022
land-cover transition raster, an existing water-screening index, and building
functions. LST is in degrees Celsius; transition code 2 denotes newly
impervious land. The source acquisition and QA/cloud-masking pipeline must
be documented with the inputs; this repository starts from prepared composites.

## Common grid and validity

Late LST and transition must already share the early LST grid. Mismatches fail
preflight. The water proxy is aligned by bilinear resampling; values outside
[0,1] in its source are rejected before interpolation. All declared NoData
cells are excluded. Interpolation outputs Float32 even for integer sources.
Transition codes must be 1–4 throughout common LST coverage; unknown coverage
is rejected instead of being interpreted as no expansion. Both LST rasters must be
finite and within (-50,80) Celsius. Normalization uses the joint valid mask.
Optional hardening and low-elevation layers are support products only.

## Relative heat and water scores

For each LST composite and the aligned water proxy, compute P5 and P95 on the
joint valid mask, then clip (x-P5)/(P95-P5) to [0,1]. Constant-valued fields
receive zero; no valid sample raises an error. Heat persistence is the mean
of the two normalized LST fields. This measures spatially relative heat
across two windows, not an annual warming trend.

The continuous compound score is 0.55×heat + 0.45×water by default.
The four quadrants use separate component thresholds, both 0.67:
1 low/low; 2 heat-high only; 3 water-high only; 4 both high.
Weights affect the continuous score, not this quadrant classification.

## Expansion and exposure

Transition==2 is intersected with the quadrants:
1 both high, 2 one high, 3 neither high; zero outside the selected expansion.
Building polygons are rasterized with ALL_TOUCHED. For each cell:

```text
Exposure = clip(0.60*Residential + 0.90*Educational +
                1.00*Healthcare + 0.70*PublicService, 0, 1)
PriorityScore = Compound * (0.4 + 0.6*Exposure)
```

Overlapping functions add before clipping. Functional presence is not a
population count. The exposure quadrant uses Compound>=0.67 and Exposure>=0.60.

## Sensitivity

Run 16 combinations: heat weights 0.50, 0.55, 0.60, 0.70 and thresholds
0.50, 0.60, 0.67, 0.70. Report component quadrant areas separately from
continuous-score threshold areas and high-score/high-exposure areas.
For fixed component threshold, changing weights must leave quadrant areas
unchanged. The default configuration is included in the sweep.

These choices are research assumptions, not calibrated engineering standards.
See limitations.md for validation requirements.
