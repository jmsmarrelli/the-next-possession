"""Compare R-generated result files to their Python equivalents when R is available."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if shutil.which("Rscript") is None:
        print("Rscript is not installed; Python artifacts verified, R parity check skipped.")
        return 0
    subprocess.run(["Rscript", "R/run_all.R"], cwd=ROOT, check=True)
    checks = [
        (
            "projects/01_schedule_gauntlet/schedule_stress.csv",
            "data/processed_r/schedule_stress.csv",
            "game_id",
            [
                "rest_days", "games_in_4", "games_in_7", "travel_miles",
                "time_zones_crossed", "stress_score",
            ],
        ),
        (
            "projects/07_title_odds/game_win_probabilities.csv",
            "data/processed_r/game_win_probabilities.csv",
            "game_id",
            ["opponent_rating", "expected_margin", "win_probability"],
        ),
        (
            "projects/04_wemby_impact/wemby_impact_summary.csv",
            "data/processed_r/wemby_impact_summary.csv",
            "availability",
            ["games", "win_pct", "avg_margin", "team_points", "opponent_points"],
        ),
        (
            "projects/05_finals_clutch_autopsy/finals_lead_summary.csv",
            "data/processed_r/finals_lead_summary.csv",
            "game_id",
            [
                "max_spurs_lead", "final_margin", "lead_surrendered",
                "peak_spurs_win_probability", "clutch_plays", "clutch_scoring_plays",
            ],
        ),
    ]
    for python_path, r_path, key, numeric_columns in checks:
        left = pd.read_csv(ROOT / python_path).sort_values(key).reset_index(drop=True)
        right = pd.read_csv(ROOT / r_path).sort_values(key).reset_index(drop=True)
        if left[key].astype(str).tolist() != right[key].astype(str).tolist():
            raise AssertionError(f"Identifier mismatch: {python_path} vs {r_path}")
        for column in numeric_columns:
            if not np.allclose(left[column], right[column], rtol=1e-9, atol=1e-7, equal_nan=True):
                difference = np.nanmax(np.abs(left[column].to_numpy() - right[column].to_numpy()))
                raise AssertionError(
                    f"Numeric mismatch in {column}: {python_path} vs {r_path}; max difference={difference}"
                )
    print("R/Python identifier and numeric parity checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
