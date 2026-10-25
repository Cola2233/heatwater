# Interactive HTML interface

website/index.html is a buildless public demonstration. It loads only generated
synthetic arrays from website/data/demo.js. No online maps, fonts, analytics or
third-party JavaScript are required. The public default therefore works offline.

website/local.html is generated locally and ignored by Git. It additionally
loads the local Changchun raster arrays from ignored website/data/local.js.
Do not upload these local files until the underlying data permissions have
been reviewed. A manually uploaded directory can bypass Git ignore rules;
publish only tracked files.

The interface displays heat, water proxy, weighted score, functional exposure,
component quadrants and impervious expansion priority. It exposes weights and
thresholds and exports PNG/CSV/exploration JSON. Changing weights cannot change
component quadrants; the UI explains this distinction. It also distinguishes
the component double-high area from high-score/high-exposure candidates.

The exporter first validates the Python output manifest. Float32 arrays retain
their normalized source values and declared NoData is converted to NaN; the
transition input is exported as byte codes. Browser statistics use all valid
source pixels, not a downsampled display. Default Changchun values were checked
against the existing CSV: 392.77 km² valid, 52.87 km² component double-high,
119.70 km² high compound score, and 70.19 km² high-score/high-exposure.

Local browser checks covered desktop and 390 px mobile widths, layer switching,
weight/threshold updates, baseline reset, CSV/settings exports and public demo
fallback without loading the local data. Four dependency-free numerical tests
also cover invalid cells, classification, weights and aggregate counts.
Hosted deployment and hosted CI have not been run.
