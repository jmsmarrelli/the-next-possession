# Current validation — October 22, 2026

## What changed

Original issue: The tournament miscounted finalists after byes, favored a strongest-team bye and differed structurally in R; schedule joins silently imputed missing teams.

Implemented: Fixed Python/R tournament accounting, neutral series probabilities and random byes; rejected invalid probabilities/missing opponents; added Python and R regressions; rebuilt seven projects and aligned scope wording.

## Evidence and limits

14 Python tests passed. R tests: 25 expectations passed. Four deterministic R/Python table comparisons and Monte Carlo tournament conservation/agreement checks passed; this does not mean every model agrees across languages. The built R source archive passed R CMD check (Status: OK); optional Arrow was unavailable. Python test coverage is 30%; separate build runs are not included in that coverage figure.

Heuristic stress/chemistry coefficients are not calibrated. The 80-game schedule is incomplete for full-season wins; 106-game availability mixes regular season and playoffs. No NBA title odds or causal player effects.

Test/runtime checks used an existing Python 3.14.7 environment (NumPy 2.5.2, pandas 3.0.5, SciPy 1.18.1, scikit-learn 1.9.0, matplotlib 3.11.1, pytest 9.1.1). The older studies specify Python 3.12 and different NumPy/pandas pins. A fresh installation of that pinned environment was not possible offline and is a release gate. R execution used R 4.6.1 with an existing package library. Earlier validation files and executed notebooks describe earlier runs and were preserved; notebooks were not re-executed in this review.

HTML now uses the pinned CommonMark renderer `markdown-it-py==4.2.0` with tables; local and CI use the same renderer. This replaces an unavailable local Python-Markdown package. Generated result CSVs retain full precision; readable article tables round for display only. The seven-project Quarto collection uses its separate Pandoc fallback.

## Review and publication

Changes are local to `audit/2026-10-22-portfolio`. No push, merge, repository visibility change or public release occurred. The local PR draft records the intended summary. Publication requires a reachable authenticated GitHub connection and the owner's approval. Read [PROVENANCE.md](PROVENANCE.md) before describing personal authorship or validation in an application.


Current delivery policy: feature branches and pull requests are authorized; merging into default branches requires separate owner approval. Repository visibility must remain unchanged.
