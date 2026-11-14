# Publication checklist

The source and sample explorer are maintained in this repository. Publication is a separate step.

## GitHub repository About settings

Description: Local CSV contracts, data profiling and dataset comparisons. Python CLI with no third-party runtime dependencies.

Suggested topics: `python`, `csv`, `data-quality`, `data-validation`, `data-contracts`, `data-profiling`, `cli`, `open-source`.

## GitHub Pages

1. Open repository Settings → Pages.
2. Select Deploy from a branch, branch `main`, folder `/docs`, and save.
3. Wait for the Pages deployment to succeed, then open the exact URL GitHub provides.
4. Add that verified URL to the repository About website field and README.

The explorer serves precomputed results for synthetic examples. It does not run Python in the browser or accept visitor uploads. Regenerate it after behavioral changes with `python scripts/build_demo.py`.

## First GitHub Release

After the tests and installation smoke check pass on the intended commit, create tag `v0.1.0` and a GitHub pre-release titled `DataGuard 0.1.0 — Initial preview` using the notes in `CHANGELOG.md`. Keep the preview designation until broader use and testing justify changing it.

The distribution name in `pyproject.toml` is local project metadata; no PyPI registration or publication is implied. GitHub automatically supplies source archives with a published release.
