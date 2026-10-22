# Validation report

Verified on 2026-08-25 in a clean local R library.

## Environments

- R 4.6.1 (aarch64-apple-darwin)
- RStudio 2026.08.1+195
- Python 3.14.7
- Random seed 210 for both implementations

## Completed checks

- `R CMD check`: **Status: OK**, including package installation, examples, and tests.
- R regression suite: **5 test cases / 13 expectations passed**.
- RStudio project bootstrap and data-contract validation passed.
- Project execution: all **7 `analysis.R` entry points passed** independently.
- Full R build: **14 project result tables** generated in `data/processed_r/`.
- Cross-language parity: matching game/team identifiers and core numeric schedule,
  probability, Wembanyama-impact, and Finals columns passed at explicit tolerances.
- Python tests: **10 passed**.
- Python static checks: Ruff and mypy passed.
- Rendered site: 10 pages and their local links were previously audited successfully.

## Portability note

Arrow is optional in R. The default lightweight setup reads the committed CSV
snapshots; installing Arrow activates Parquet reads without changing the analysis API.

## Modeling boundary

The Python and R title paths intentionally differ: Python simulates best-of-seven
series, while R supplies a dependency-light Bradley-Terry sensitivity baseline.
That difference is documented and is not treated as a parity failure.
