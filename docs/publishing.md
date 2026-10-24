# Publication procedure

The repository contains code, documentation, config templates and synthetic
preview figures. Real data, local configuration and competition packages
are excluded by .gitignore.

Before publication, inspect git status, git diff --cached --stat and
git ls-files. Check attribution and MIT authorship, then run the documented
tests and synthetic workflow.

Create an empty GitHub repository named changchun-heat-water-resilience under
the intended account. From the project repository:

```sh
git remote add origin https://github.com/Cola2233/changchun-heat-water-resilience.git
git push -u origin main
```

The remote command is an example for the connected account, not evidence of
publication. Verify account/name before running. CI is configured locally;
only a successful GitHub run establishes hosted CI success.
Create release v0.1.0 after CI passes and use CHANGELOG.md for release notes.
Then add the actual repository URL and release date to CITATION.cff.
A Zenodo DOI can be added after a real archive has been created.
