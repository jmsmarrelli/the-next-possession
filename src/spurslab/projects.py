"""End-to-end project runners and report generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .config import Paths, load_settings
from .data import load_snapshot
from .features import (
    finals_clutch_profile,
    player_archetypes,
    rotation_pair_proxies,
    schedule_stress,
    starter_unit_proxies,
    wemby_game_impact,
)
from .simulation import (
    SimulationConfig,
    contender_title_odds,
    schedule_probabilities,
    simulate_schedule,
)
from .visuals import (
    plot_archetypes,
    plot_contender_landscape,
    plot_finals_leads,
    plot_pair_chemistry,
    plot_schedule_stress,
    plot_title_odds,
    plot_wemby_impact,
    plot_win_distribution,
)


def _save(frame: pd.DataFrame, project: Path, name: str) -> None:
    project.mkdir(parents=True, exist_ok=True)
    frame.to_csv(project / f"{name}.csv", index=False)


def _fmt_pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def run_schedule(paths: Paths) -> dict[str, Any]:
    schedule = load_snapshot("spurs_schedule_2026_27", paths)
    stress = schedule_stress(schedule)
    _save(stress, paths.root / "projects" / "01_schedule_gauntlet", "schedule_stress")
    plot_schedule_stress(stress, paths.assets / "01_schedule_stress.png")
    hardest = stress.nlargest(1, "stress_score").iloc[0]
    metrics = {
        "scheduled_games": len(stress),
        "back_to_backs": int(stress["back_to_back"].sum()),
        "three_in_four": int(stress["three_in_four"].sum()),
        "travel_miles": int(stress["travel_miles"].sum()),
        "hardest_game": f"{hardest['date']:%b %d} {'vs' if hardest['is_home'] else '@'} {hardest['opponent']}",
        "hardest_score": float(hardest["stress_score"]),
    }
    report = f"""## What the model says

The published schedule currently contains **{metrics['scheduled_games']} assigned games**; two NBA Cup flex slots remain unresolved. Across those assigned dates, San Antonio has **{metrics['back_to_backs']} back-to-backs**, **{metrics['three_in_four']} three-games-in-four-nights spots**, and roughly **{metrics['travel_miles']:,} miles** of venue-to-venue travel. The highest-stress assigned date is **{metrics['hardest_game']}** (score {metrics['hardest_score']:.1f}).

The stress score is an auditable index—not an injury prediction. It combines rest, recent game density, travel distance, time-zone changes, and international travel. Every component is retained in the downloadable result table.

![Hardest schedule spots](../../assets/01_schedule_stress.png)
"""
    (paths.reports / "01_schedule_gauntlet.md").write_text(report, encoding="utf-8")
    return metrics


def run_contenders(paths: Paths) -> dict[str, Any]:
    ratings = load_snapshot("nba_team_ratings_2025_26", paths)
    contender = ratings.nsmallest(12, "rank").copy()
    _save(contender, paths.root / "projects" / "02_contender_landscape", "contender_ratings")
    plot_contender_landscape(ratings, paths.assets / "02_contender_landscape.png")
    spurs = ratings[ratings["team"] == "San Antonio Spurs"].iloc[0]
    best = ratings.iloc[0]
    report = f"""## What the model says

San Antonio finished 2025–26 **No. {int(spurs['rank'])} in adjusted margin** at **{spurs['adjusted_net_rating']:+.2f} points per 100 possessions**, behind {best['team']} ({best['adjusted_net_rating']:+.2f}). The Spurs' adjusted offense ({spurs['adjusted_off_rating']:.2f}) and defense ({spurs['adjusted_def_rating']:.2f}) put them in the true two-way contender quadrant.

That makes the 2026–27 question less about arriving early and more about closing the remaining gap against elite paths: Oklahoma City in the West and the New York/Boston/Cleveland group in the East.

![Contender map](../../assets/02_contender_landscape.png)
"""
    (paths.reports / "02_contender_landscape.md").write_text(report, encoding="utf-8")
    return {
        "spurs_rank": int(spurs["rank"]),
        "spurs_adjusted_net_rating": float(spurs["adjusted_net_rating"]),
        "best_team": best["team"],
        "gap_to_best": float(best["adjusted_net_rating"] - spurs["adjusted_net_rating"]),
    }


def run_rotation(paths: Paths) -> dict[str, Any]:
    box = load_snapshot("spurs_player_boxscores_2025_26", paths)
    schedule = load_snapshot("spurs_schedule_2025_26", paths)
    pairs = rotation_pair_proxies(box)
    units = starter_unit_proxies(box, schedule)
    project = paths.root / "projects" / "03_rotation_chemistry"
    _save(pairs, project, "pair_chemistry_proxies")
    _save(units, project, "starter_unit_proxies")
    plot_pair_chemistry(pairs, paths.assets / "03_rotation_chemistry.png")
    leader = pairs.iloc[0]
    common = units.iloc[0]
    report = f"""## What the model says

The strongest high-sample box-score pair proxy is **{leader['player_a']} + {leader['player_b']}** across **{int(leader['games_together'])} co-appearances**. The most-used starting group logged **{int(common['games'])} games** with a **{common['win_pct']:.3f} win rate** and a **{common['avg_game_margin']:+.1f} average game margin**.

This section demonstrates an important analytical boundary: co-appearance and box plus/minus are not shared-possession lineup data. The project therefore exposes reliability and calls the result a *proxy*, making it a candidate generator for deeper play-by-play work rather than a causal conclusion.

![Rotation chemistry proxy](../../assets/03_rotation_chemistry.png)
"""
    (paths.reports / "03_rotation_chemistry.md").write_text(report, encoding="utf-8")
    return {
        "top_pair": f"{leader['player_a']} + {leader['player_b']}",
        "top_pair_games": int(leader["games_together"]),
        "most_used_starter_games": int(common["games"]),
    }


def run_wemby(paths: Paths) -> dict[str, Any]:
    box = load_snapshot("spurs_player_boxscores_2025_26", paths)
    schedule = load_snapshot("spurs_schedule_2025_26", paths)
    games, summary = wemby_game_impact(box, schedule)
    project = paths.root / "projects" / "04_wemby_impact"
    _save(games, project, "wemby_game_splits")
    _save(summary, project, "wemby_impact_summary")
    plot_wemby_impact(summary, paths.assets / "04_wemby_impact.png")
    played = summary[summary["availability"] == "Wemby played"].iloc[0]
    out = summary[summary["availability"] == "Wemby out"].iloc[0]
    report = f"""## What the model says

The Spurs went **{_fmt_pct(played['win_pct'])}** in games Wembanyama played with a **{played['avg_margin']:+.1f} average margin**, versus **{_fmt_pct(out['win_pct'])}** and **{out['avg_margin']:+.1f}** when he was out. The descriptive margin gap is **{played['avg_margin'] - out['avg_margin']:+.1f} points per game**.

Availability is entangled with schedule strength, teammate availability, and game state, so this is a decision-oriented descriptive split—not a causal on/off estimate. The companion data keeps opponent and season-type fields available for a controlled extension.

![Wembanyama availability split](../../assets/04_wemby_impact.png)
"""
    (paths.reports / "04_wemby_impact.md").write_text(report, encoding="utf-8")
    return {
        "played_games": int(played["games"]),
        "out_games": int(out["games"]),
        "played_win_pct": float(played["win_pct"]),
        "out_win_pct": float(out["win_pct"]),
        "margin_gap": float(played["avg_margin"] - out["avg_margin"]),
    }


def run_finals(paths: Paths) -> dict[str, Any]:
    plays = load_snapshot("spurs_postseason_plays_2026", paths)
    schedule = load_snapshot("spurs_schedule_2025_26", paths)
    finals = schedule[(schedule["season_type"] == "Postseason") & (schedule["opponent"] == "NY")]
    detail, summary = finals_clutch_profile(plays, finals["game_id"].astype(str).tolist())
    project = paths.root / "projects" / "05_finals_clutch_autopsy"
    _save(detail, project, "finals_play_by_play_enriched")
    _save(summary, project, "finals_lead_summary")
    plot_finals_leads(detail, paths.assets / "05_finals_leads.png")
    report = f"""## What the model says

San Antonio held a lead of at least **{summary['max_spurs_lead'].max():.0f} points** in the series, yet its average peak-to-final swing was **{summary['lead_surrendered'].mean():.1f} points**. Across the five games there were **{int(summary['clutch_plays'].sum())} clutch-state plays**—fourth quarter, five minutes or less, score within five—despite the 4–1 series result.

This is the most actionable offseason story in the portfolio: the gap was not simply “talent.” The play-by-play view isolates when control changed and creates a clean base for possession tagging, timeout sequencing, shot-quality review, and late-clock decision analysis.

![Finals lead progression](../../assets/05_finals_leads.png)
"""
    (paths.reports / "05_finals_clutch_autopsy.md").write_text(report, encoding="utf-8")
    return {
        "games": len(summary),
        "largest_spurs_lead": float(summary["max_spurs_lead"].max()),
        "average_lead_surrendered": float(summary["lead_surrendered"].mean()),
        "clutch_plays": int(summary["clutch_plays"].sum()),
    }


def run_archetypes(paths: Paths) -> dict[str, Any]:
    players = load_snapshot("nba_player_seasons_2022_26", paths)
    archetypes = player_archetypes(players)
    project = paths.root / "projects" / "06_player_archetypes"
    _save(archetypes, project, "player_archetypes")
    spurs = archetypes[archetypes["team"] == "SAS"].copy()
    _save(spurs, project, "spurs_archetypes")
    plot_archetypes(archetypes, paths.assets / "06_player_archetypes.png")
    core = spurs.sort_values("bpm", ascending=False).head(5)
    core_text = ", ".join(f"{row.player} ({row.archetype})" for row in core.itertuples())
    report = f"""## What the model says

An eight-cluster model places every qualifying rotation player into a role using scoring, playmaking, rebounding, shooting volume/efficiency, usage, defensive events, and box impact. San Antonio's leading qualifying profiles are **{core_text}**.

The useful output is not the label itself; it is the leaguewide neighborhood around each Spur. That makes role overlap, succession planning, and complementary-player searches reproducible without pretending that positions capture how players actually produce value.

![Player archetypes](../../assets/06_player_archetypes.png)
"""
    (paths.reports / "06_player_archetypes.md").write_text(report, encoding="utf-8")
    return {"qualified_players": len(archetypes), "spurs_players": len(spurs), "archetypes": int(archetypes["archetype"].nunique())}


def run_title_odds(paths: Paths) -> dict[str, Any]:
    settings = load_settings()
    ratings = load_snapshot("nba_team_ratings_2025_26", paths)
    schedule = load_snapshot("spurs_schedule_2026_27", paths)
    stress = schedule_stress(schedule)
    model = settings["model"]
    config = SimulationConfig(
        home_court_points=model["home_court_points"],
        margin_sd=model["margin_sd"],
        prior_rating_weight=model["prior_rating_weight"],
        seed=settings["portfolio"]["random_seed"],
    )
    games = schedule_probabilities(stress, ratings, config)
    win_summary, distribution = simulate_schedule(
        games, model["schedule_simulations"], settings["portfolio"]["random_seed"]
    )
    odds = contender_title_odds(
        ratings,
        model["contender_count"],
        model["playoff_simulations"],
        settings["portfolio"]["random_seed"],
    )
    project = paths.root / "projects" / "07_title_odds"
    _save(games, project, "game_win_probabilities")
    _save(win_summary, project, "schedule_simulation_summary")
    _save(distribution, project, "win_distribution")
    _save(odds, project, "contender_title_odds")
    plot_title_odds(odds, paths.assets / "07_title_odds.png")
    plot_win_distribution(distribution, paths.assets / "07_win_distribution.png")
    spurs = odds[odds["team"] == "San Antonio Spurs"].iloc[0]
    mean_wins = float(win_summary.loc[win_summary["metric"] == "mean_wins", "value"].iloc[0])
    report = f"""## What the model says

The schedule model projects **{mean_wins:.1f} wins across the {len(games)} currently assigned games**. In the separate contender knockout baseline, San Antonio ranks **No. {int(spurs['title_odds_rank'])}** with a **{_fmt_pct(spurs['title_probability'])} title probability**.

The estimates are baselines, not forecasts carved in stone. Prior adjusted net rating is regressed toward average, game probabilities include home court/rest/travel, and the title model excludes injury and transaction assumptions. The CSV outputs make every scenario parameter replaceable as 2026–27 evidence arrives.

![Title odds](../../assets/07_title_odds.png)

![Win distribution](../../assets/07_win_distribution.png)
"""
    (paths.reports / "07_title_odds.md").write_text(report, encoding="utf-8")
    return {
        "assigned_games": len(games),
        "mean_wins": mean_wins,
        "spurs_title_probability": float(spurs["title_probability"]),
        "spurs_title_rank": int(spurs["title_odds_rank"]),
    }


def run_all() -> dict[str, dict[str, Any]]:
    paths = Paths()
    paths.ensure()
    results = {
        "schedule": run_schedule(paths),
        "contenders": run_contenders(paths),
        "rotation": run_rotation(paths),
        "wemby": run_wemby(paths),
        "finals": run_finals(paths),
        "archetypes": run_archetypes(paths),
        "title_odds": run_title_odds(paths),
    }
    (paths.reports / "metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    schedule = results["schedule"]
    title = results["title_odds"]
    finals = results["finals"]
    executive = f"""## Portfolio thesis

San Antonio enters 2026–27 as a defending Western Conference champion with a real two-way title profile. These seven projects turn that context into a coherent decision system: **where the schedule applies pressure, which contenders define the bar, which rotation combinations deserve deeper study, how much outcomes move with Wembanyama's availability, why the Finals slipped, where roster archetypes overlap, and what a transparent preseason simulation implies.**

### Headline outputs

- **Schedule:** {schedule['scheduled_games']} assigned games, {schedule['back_to_backs']} back-to-backs, about {schedule['travel_miles']:,} travel miles.
- **Prior-year level:** No. {results['contenders']['spurs_rank']} adjusted margin, {results['contenders']['spurs_adjusted_net_rating']:+.2f} per 100.
- **Finals pressure point:** {finals['average_lead_surrendered']:.1f}-point average peak-to-final swing.
- **Simulation baseline:** {title['mean_wins']:.1f} wins in assigned games; No. {title['spurs_title_rank']} among modeled title contenders.

Each project has paired Python and R entry points, an analysis-ready CSV, methods and limitations, and a rendered visual. The build is deterministic at seed 210.
"""
    (paths.reports / "executive_summary.md").write_text(executive, encoding="utf-8")
    return results

