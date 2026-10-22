"""Transparent Monte Carlo models for schedule wins and contender title odds."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.special import ndtr

from .data import require_columns


@dataclass(frozen=True)
class SimulationConfig:
    home_court_points: float = 2.2
    margin_sd: float = 12.0
    prior_rating_weight: float = 0.72
    seed: int = 210


TEAM_ABBREVIATIONS = {
    "Atlanta Hawks": "ATL",
    "Boston Celtics": "BOS",
    "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA",
    "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET",
    "Golden State Warriors": "GS",
    "Houston Rockets": "HOU",
    "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC",
    "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL",
    "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NO",
    "New York Knicks": "NY",
    "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SA",
    "Toronto Raptors": "TOR",
    "Utah Jazz": "UTAH",
    "Washington Wizards": "WSH",
}


def game_win_probability(expected_margin: np.ndarray | float, margin_sd: float = 12.0) -> np.ndarray:
    return np.asarray(ndtr(np.asarray(expected_margin, dtype=float) / margin_sd), dtype=float)


def prepare_ratings(ratings: pd.DataFrame, prior_weight: float = 0.72) -> pd.DataFrame:
    require_columns(ratings, ["team", "adjusted_net_rating", "conference"], "ratings")
    frame = ratings.copy()
    frame["abbreviation"] = frame["team"].map(TEAM_ABBREVIATIONS)
    frame["forecast_rating"] = frame["adjusted_net_rating"] * prior_weight
    return frame


def schedule_probabilities(
    schedule_features: pd.DataFrame,
    ratings: pd.DataFrame,
    config: SimulationConfig | None = None,
) -> pd.DataFrame:
    config = config or SimulationConfig()
    rating_frame = prepare_ratings(ratings, config.prior_rating_weight)
    lookup = rating_frame.set_index("abbreviation")["forecast_rating"]
    spurs_rating = float(lookup.loc["SA"])
    frame = schedule_features.copy()
    frame["opponent_rating"] = frame["opponent"].map(lookup)
    fallback = float(rating_frame["forecast_rating"].median())
    frame["opponent_rating"] = frame["opponent_rating"].fillna(fallback)
    home_adjustment = np.where(frame["is_neutral"], 0, np.where(frame["is_home"], config.home_court_points, -config.home_court_points))
    rest_adjustment = np.clip(frame["rest_days"] - 1, -1, 2) * 0.35
    travel_adjustment = -np.minimum(frame["travel_miles"] / 1000, 2.5) * 0.25
    stress_adjustment = -frame["stress_score"] / 100 * 1.25
    frame["expected_margin"] = (
        spurs_rating
        - frame["opponent_rating"]
        + home_adjustment
        + rest_adjustment
        + travel_adjustment
        + stress_adjustment
    )
    frame["win_probability"] = game_win_probability(frame["expected_margin"], config.margin_sd)
    return frame


def simulate_schedule(
    probabilities: pd.DataFrame, simulations: int = 25_000, seed: int = 210
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    p = probabilities["win_probability"].to_numpy()
    wins = (rng.random((simulations, len(p))) < p).sum(axis=1)
    summary = pd.DataFrame(
        {
            "metric": ["mean_wins", "median_wins", "p10_wins", "p90_wins", "prob_50_plus", "prob_55_plus", "prob_60_plus"],
            "value": [
                wins.mean(),
                np.median(wins),
                np.quantile(wins, 0.10),
                np.quantile(wins, 0.90),
                (wins >= 50).mean(),
                (wins >= 55).mean(),
                (wins >= 60).mean(),
            ],
        }
    )
    distribution = pd.Series(wins).value_counts().sort_index().rename_axis("wins").reset_index(name="simulations")
    distribution["probability"] = distribution["simulations"] / simulations
    return summary, distribution


def _series_win_probability(team_rating: float, opponent_rating: float, home_games: int = 4) -> float:
    home_p = float(game_win_probability(team_rating - opponent_rating + 2.2))
    away_p = float(game_win_probability(team_rating - opponent_rating - 2.2))
    game_probs = [home_p, home_p, away_p, away_p, home_p, away_p, home_p][: home_games + 3]
    states = np.zeros((8, 8))
    states[0, 0] = 1.0
    for probability in game_probs:
        next_states = states.copy() * 0
        for wins in range(4):
            for losses in range(4):
                mass = states[wins, losses]
                next_states[wins + 1, losses] += mass * probability
                next_states[wins, losses + 1] += mass * (1 - probability)
        next_states[4, :] += states[4, :]
        next_states[:, 4] += states[:, 4]
        states = next_states
    return float(states[4, :4].sum())


def contender_title_odds(
    ratings: pd.DataFrame, contender_count: int = 12, simulations: int = 50_000, seed: int = 210
) -> pd.DataFrame:
    """Neutral-field knockout model across the strongest prior-year teams.

    This is a deliberately compact preseason baseline. It is not presented as a
    sportsbook model: injuries, roster changes, and bracket-specific paths are
    intentionally left for scenario updates.
    """

    frame = prepare_ratings(ratings).nsmallest(contender_count, "rank").copy()
    names = frame["team"].to_numpy()
    strengths = frame["forecast_rating"].to_numpy()
    rng = np.random.default_rng(seed)
    championships = dict.fromkeys(names, 0)
    finals = dict.fromkeys(names, 0)

    for _ in range(simulations):
        active = list(rng.permutation(len(names)))
        while len(active) > 1:
            if len(active) % 2:
                # The highest-rated remaining team receives a bye.
                bye = max(active, key=lambda idx: strengths[idx])
                active.remove(bye)
                next_round = [bye]
            else:
                next_round = []
            if len(active) == 2:
                finals[names[active[0]]] += 1
                finals[names[active[1]]] += 1
            for left, right in zip(active[::2], active[1::2], strict=False):
                probability = _series_win_probability(strengths[left], strengths[right])
                next_round.append(left if rng.random() < probability else right)
            active = next_round
        championships[names[active[0]]] += 1

    frame["finals_probability"] = frame["team"].map(finals) / simulations
    frame["title_probability"] = frame["team"].map(championships) / simulations
    frame["title_odds_rank"] = frame["title_probability"].rank(method="min", ascending=False).astype(int)
    return frame.sort_values("title_probability", ascending=False).reset_index(drop=True)
