# DataGuard

**Local CSV contracts, data profiling and dataset comparisons.**

An independent Python project for checking data before an analytics or machine-learning pipeline. No third-party runtime dependencies, account, API key or network connection required. Early-stage prototype, developed with AI assistance; not a production-certified monitoring platform.

## Quick start

Requires Python 3.10+. From this directory:

```bash
python dataguard.py examples/current.csv --contract examples/contract.json --baseline examples/baseline.csv --output-dir reports/demo
python -m unittest discover -s tests -v
```

Open `reports/demo/report.html` in a browser; `report.json` is machine-readable. The output directory must be new: use `reports/demo2` for a repeat run. Exit codes: 0 = contract passed, 1 = validation failures, 2 = configuration/input/output error.

## What it does

| Feature | Behavior |
| --- | --- |
| Contracts | Required values, uniqueness, number/integer types, inclusive bounds and exact allowed strings |
| Structural checks | Unique named headers, field counts, empty datasets and exact duplicate records |
| Profiling | Blank counts, distinct counts and finite numeric min/max/mean |
| Comparison | Added/removed columns, blank-rate changes, numeric mean changes and categorical total variation |
| Reports | Local JSON and self-contained HTML with escaped content |
| Automation | Nonzero exit codes and a GitHub Actions test workflow |

## Contracts

See `examples/contract.json`. Every named contract column must exist, even when `required` is false. `required` controls blank cells. Extra CSV columns are allowed and profiled. Unknown rule names are rejected to catch typos. Allowed values and uniqueness compare exact nonblank strings; whitespace is not normalized. Blank means empty or whitespace only. Numeric constraints skip optional blanks. Uniqueness excludes blanks; duplicate-record checks include all fields.

`type` supports `string` (default), `number`, or `integer`. Bounds apply only to numeric types. Missing values are not silently imputed. Strings such as `NaN` or `infinity` are invalid numeric values.

## Understand the example

Both files contain synthetic records created for this project. Current mean amount is 35; baseline mean is 25, so mean change is +10. Category A changes from 50% to 25%; category B changes from 50% to 75%. Total variation is 0.25 (0 means identical category frequencies; 1 means disjoint categories).

Comparisons are descriptive, not hypothesis tests or automatic drift alerts. They do not fail the contract or establish that model performance has degraded. Numeric comparisons use finite parseable values and report their counts. Categorical comparison includes blanks as exact values. With empty datasets, unavailable comparison metrics are null. Numeric means can miss important distribution changes. Do not interpret small samples as reliable evidence of population drift.

## Privacy and limitations

No source rows are included in reports and no data is transmitted. Reports still contain column names and aggregate values; review them before sharing. Input files are read only. Existing output directories are rejected. A disk failure may leave a partial new report directory.

The tool loads CSV records into memory; it is intended for modest datasets, not distributed processing. It expects comma-separated UTF-8 CSV (BOM accepted). Numeric parsing uses floating point, unsuitable for exact financial arithmetic or very large integer identity checks. Not implemented: SQL/cloud connectors, scheduled monitoring, statistical significance, automatic remediation or multi-user access.

## Development

Tests verify known comparison values, invalid contracts, bad CSV, HTML escaping and CLI output protection. GitHub Actions runs the suite on Python 3.10 and 3.12 when this project is uploaded at a repository root and Actions is enabled.

Contributions: include a minimal synthetic reproduction, expected/actual behavior and tests. Never upload private datasets or secrets. See `CONTRIBUTING.md` and `LICENSE`.
