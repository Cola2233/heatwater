# Publication procedure

The repository contains code, documentation, config templates and synthetic
preview figures. Real data, local configuration and generated private packages
are excluded by .gitignore.

Before publication, inspect git status, git diff --cached --stat and
git ls-files. Check attribution and MIT authorship, then run the documented
tests and synthetic workflow.

## Build reviewable public artifacts locally

From the repository root:

```sh
python -m pip install build
python -m build
python -m scripts.build_single_html --output artifacts/releases/heatwater-demo.html
npm ci --ignore-scripts
npx playwright install chromium
npm test
npm run check
npm run test:browser
```

Set HEATWATER_PUBLIC_BUNDLE to artifacts/releases/heatwater-demo.html when
running the browser check to include the standalone artifact. Shell-specific
examples are in CONTRIBUTING.md. No real-data entry is needed for public CI.
Confirm the public HTML has only the demo dataset and that no local.js,
local.html, private configuration or real input appears in source distributions.

The default HTML entry is public synthetic data. Existing private Changchun
single-file exports remain local and are not Release assets. The Python wheel
contains backend code/CLI; the source distribution includes the public website.

CI builds both Python distributions and the public HTML, checks the installed
CLI outside the checkout, and uploads artifacts for inspection. Artifact upload
does not create a GitHub Release or deploy a website.

## Publish after reviewing the actual repository

Create an empty GitHub repository named heatwater under
the intended account. From the project repository:

```sh
git remote add origin https://github.com/OWNER/heatwater.git
git push -u origin main
```

Replace OWNER with the intended account before running. CI is configured locally;
only a successful GitHub run establishes hosted CI success.
Create release v0.1.0 after CI passes and use CHANGELOG.md for release notes.
Then add the actual repository URL and release date to CITATION.cff.
A Zenodo DOI can be added after a real archive has been created.

Use the validated Python distributions and heatwater-demo.html as public Release
assets. Add SHA-256 values for those exact files to the Release description.
Keep citation version/date aligned with the actual tagged release. Do not add
successful-build badges, Pages URLs or DOI links before those resources exist.

## Tutorial assets for the first release

Publish the [Chinese quickstart](quickstart-zh.md) and its preview image with
the repository. Attach both files below from the locally reviewed release folder:

- `artifacts/releases/heatwater-research-demo.html` is the offline MapLibre
  synthetic preview used by the tutorial.
- `artifacts/releases/heatwater-walkthrough-zh.mp4` is the 70-second walkthrough
  with Chinese captions, captured from that preview.
- `heatwater-quickstart-zh.zip` packages the research demo, video, and quickstart
  document for a single download. Keep the documentation paths intact and
  include the MapLibre license alongside the demo.

The research demo has a separate filename because its controls differ from the
standard `heatwater-demo.html` explorer. Include checksums for both tutorial
attachments with the other Release assets.

Include each validated `heatwater-<city>-temperature.html` as a separate
observational sample. Publish the case pages with the original Landsat scene
identifiers and quality-mask coverage. Review the checksum list for every
attachment before publishing.

Keep the public project entry in the root README and link each downloadable
city artifact from its [case page](../cases/README.md) once the artifact is live.
