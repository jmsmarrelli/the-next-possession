# The Next Possession

### Seven reproducible NBA data projects for the 2026–27 San Antonio Spurs

This portfolio treats San Antonio's 2025–26 Finals run as the start of the question, not the end of the story. It combines a shared Python package, an R package, paired project entry points, cached public-data ingestion, analysis-ready snapshots, tests, model cards, generated charts, and a Quarto website.

## The portfolio

| # | Project | Basketball question | Methods | Main artifact |
|---:|---|---|---|---|
| 01 | Schedule Gauntlet | Where will travel and density apply the most pressure? | Haversine distance, rolling windows, transparent index | Per-game stress table |
| 02 | Contender Landscape | Which teams define the two-way title bar? | Adjusted ratings, contender quadrants | Offense-defense map |
| 03 | Rotation Co-appearance | Which pair/unit signals deserve deeper study? | Heuristic co-appearance scores | Pair and starter tables |
| 04 | Wemby Impact | How different were results when Wembanyama played? | Availability split, game margins | Game-level impact table |
| 05 | Finals Clutch Autopsy | When did Finals control change? | Play-by-play state, win probability, clutch flags | Enriched possession log |
| 06 | Player Archetypes | Where do Spurs roles overlap or complement? | Standardization, k-means | Leaguewide role map |
| 07 | Tournament Scenario | What do explicit simulation assumptions imply? | Normal-margin model, Monte Carlo | Schedule wins / illustrative tournament |

## Why 2026–27

The official record makes this a particularly coherent analytics season:

- San Antonio went 62–20, earned the West's No. 2 seed, beat Oklahoma City in a seven-game conference final, and lost the NBA Finals 4–1 to New York.
- Victor Wembanyama was First-Team All-NBA and Defensive Player of the Year; Keldon Johnson won Sixth Man of the Year.
- The upcoming schedule opens against Oklahoma City, sends the Spurs to Madison Square Garden on Christmas, and includes regular-season dates in Paris and Manchester.

Direct official and data-source links are documented in [SOURCES.md](SOURCES.md).

## Quick start

Python 3.12+ and Quarto 1.5+:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,notebooks]"
spurslab all
python -m pytest
quarto render
```

Open `docs/index.html` after rendering.

### R

R 4.2+:

```bash
mkdir -p .Rlib
Rscript -e '.libPaths(c(".Rlib", .libPaths())); install.packages(c("dplyr", "lubridate", "purrr", "readr", "rlang", "tibble", "yaml", "testthat"), lib = ".Rlib")'
```

Arrow is optional: when it is installed, R reads the fast Parquet snapshots;
otherwise it automatically uses the committed portable CSV snapshots.

Then run the complete R build from the repository root:

```bash
Rscript R/run_all.R
python scripts/verify_r_parity.py
```

Every project also exposes its own `analysis.py` and `analysis.R` entry point.

The included build was executed with R 4.6.1 and Python 3.14.7. The R package
tests, all seven R entry points, and numeric parity checks are part of the
validation workflow.

See [VALIDATION.md](VALIDATION.md) for the completed verification record.

### RStudio

Open `TheNextPossession.Rproj` in RStudio. The project disables automatic
workspace restoration, fixes the repository root, and activates `.Rlib` when
the local package library exists. In the Console, run:

```r
source("R/setup.R")             # first run only
source("R/rstudio_validate.R") # contracts + R regression tests
source("R/run_all.R")          # rebuild all seven R projects
```

You can also open any `projects/*/analysis.R` file and choose **Source** to run
that project independently.

## Common commands

```bash
spurslab data          # fetch/cache and normalize data
spurslab data --refresh
spurslab build         # rebuild seven project outputs
make test
make lint
make render
```

## Repository map

```text
config/                Season assumptions and venue coordinates
data/raw/               Cached provider responses (ignored)
data/processed/         Fast Parquet snapshots
data/snapshots/         Portable committed CSV snapshots + manifest
src/spurslab/           Shared Python ingestion, features, models, visuals
R/spurslabR/            Reusable R package implementation
TheNextPossession.Rproj RStudio project entry point
projects/01...07/       Paired entry points, output tables, project pages
reports/                Generated narrative fragments and metrics
assets/                 Generated portfolio visuals and CSS
tests/                  Data-contract and model tests
docs/                   Rendered Quarto site
```

## Reproducibility contract

- Random seed: **210**.
- Network responses are cached and requests are deliberately paced.
- Portable CSV snapshots allow offline review; Parquet files make rebuilds fast.
- `manifest.json` records build time, row counts, and every snapshot schema.
- Two 2026–27 NBA Cup flex games are not assigned at build time. The schedule model uses 80 games and labels all win totals accordingly.
- Python and R use the same input tables and settings. Where algorithms intentionally differ, the methodology page says so.

## Interpretation guardrails

The portfolio does not hide uncertainty behind polished charts. Rotation chemistry is a screening proxy, not true lineup impact. The Wembanyama split is descriptive, not causal. The neutral tournament is a demonstration without NBA brackets, injuries or transaction priors. Each project names the next validation step that would be required before operational basketball use.

## Attribution

Educational project; not affiliated with or endorsed by the NBA, ESPN, Basketball Reference, or the San Antonio Spurs. Team names and marks belong to their owners. Data access is subject to provider terms. Code is released under the MIT License.

## October 2026 review

The tournament is a neutral-site demonstration with random matchups and byes. It does not represent NBA playoff qualification or conference brackets, so its output must not be described as NBA championship odds. Schedule penalties are assumptions requiring historical calibration. See [VALIDATION_CURRENT.md](VALIDATION_CURRENT.md) for actual execution coverage and [PROVENANCE.md](PROVENANCE.md) for AI assistance.
