from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = ROOT / "data" / "snapshots"


pytestmark = pytest.mark.skipif(not SNAPSHOTS.exists(), reason="portfolio snapshots not built")


def test_schedule_snapshots_are_complete_and_unique() -> None:
    upcoming = pd.read_csv(SNAPSHOTS / "spurs_schedule_2026_27.csv")
    prior = pd.read_csv(SNAPSHOTS / "spurs_schedule_2025_26.csv")
    assert len(upcoming) == 80
    assert upcoming["game_id"].is_unique
    assert prior["game_id"].is_unique
    assert prior[["team_score", "opponent_score"]].notna().all(axis=None)
    assert set(prior["result"]) == {"W", "L"}


def test_simulation_outputs_obey_probability_contracts() -> None:
    project = ROOT / "projects" / "07_title_odds"
    games = pd.read_csv(project / "game_win_probabilities.csv")
    odds = pd.read_csv(project / "contender_title_odds.csv")
    distribution = pd.read_csv(project / "win_distribution.csv")
    assert games["win_probability"].between(0, 1).all()
    assert odds["title_probability"].between(0, 1).all()
    assert odds["title_probability"].sum() == pytest.approx(1, abs=1e-9)
    assert distribution["probability"].sum() == pytest.approx(1, abs=1e-9)


def test_finals_output_has_five_games_and_valid_margins() -> None:
    finals = pd.read_csv(
        ROOT / "projects" / "05_finals_clutch_autopsy" / "finals_lead_summary.csv"
    )
    assert len(finals) == 5
    assert finals["max_spurs_lead"].ge(0).all()
    assert finals["lead_surrendered"].ge(0).all()


def test_roster_snapshot_contains_current_core() -> None:
    roster = pd.read_csv(SNAPSHOTS / "spurs_roster_2026_27.csv")
    core = {"Victor Wembanyama", "De'Aaron Fox", "Stephon Castle", "Dylan Harper"}
    assert core.issubset(set(roster["player"]))

