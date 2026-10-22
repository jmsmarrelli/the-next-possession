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
    if not np.isfinite(margin_sd) or margin_sd <= 0:
        raise ValueError("margin_sd must be finite and positive")
    if not np.isfinite(np.asarray(expected_margin, dtype=float)).all():
        raise ValueError("Expected margins must be finite")
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
    if frame["opponent_rating"].isna().any():
        missing = sorted(frame.loc[frame["opponent_rating"].isna(), "opponent"].unique())
        raise ValueError(f"No prior rating for opponents: {missing}")
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
    if not isinstance(simulations, (int, np.integer)) or simulations <= 0:
        raise ValueError("simulations must be a positive integer")
    if not len(p) or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Win probabilities must be nonempty, finite and in [0, 1]")
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


def _series_win_probability(team_rating: float, opponent_rating: float, margin_sd: float = 12.0) -> float:
    """Best-of-seven win chance for independent, identically distributed neutral games.

    Winning a series is equivalent to winning at least four of seven games.
    This intentionally excludes home court and is not an NBA playoff forecast.
    """
    from math import comb
    p = float(game_win_probability(team_rating - opponent_rating, margin_sd))
    return float(sum(comb(7, k) * p**k * (1-p)**(7-k) for k in range(4, 8)))


def contender_title_odds(
    ratings: pd.DataFrame, contender_count: int = 12, simulations: int = 50_000, seed: int = 210,
    prior_weight: float = 0.72, margin_sd: float = 12.0,
) -> pd.DataFrame:
    """Neutral-field knockout model across the strongest prior-year teams.

    This illustrates a neutral tournament, not NBA championship odds. It has
    random matchups and byes, no conference brackets, no qualification model,
    and no injury or roster-change inputs.
    """

    if not isinstance(contender_count, int) or not 2 <= contender_count <= len(ratings):
        raise ValueError("contender_count must be between two and the number of teams")
    if not isinstance(simulations, (int, np.integer)) or simulations <= 0:
        raise ValueError("simulations must be a positive integer")
    frame = prepare_ratings(ratings, prior_weight).nsmallest(contender_count, "rank").copy()
    if frame.team.duplicated().any() or not np.isfinite(frame.forecast_rating).all():
        raise ValueError("Teams must be unique and ratings finite")
    names = frame["team"].to_numpy()
    strengths = frame["forecast_rating"].to_numpy()
    rng = np.random.default_rng(seed)
    championships = dict.fromkeys(names, 0)
    finals = dict.fromkeys(names, 0)
    pair_probability = np.array([
        [_series_win_probability(a, b, margin_sd) for b in strengths] for a in strengths
    ])

    for _ in range(simulations):
        active = list(rng.permutation(len(names)))
        while len(active) > 1:
            # Count finalists before removing a bye from a three-team round.
            if len(active) == 2:
                finals[names[active[0]]] += 1
                finals[names[active[1]]] += 1
            if len(active) % 2:
                # Random byes preserve symmetry among equally strong teams.
                bye = active[int(rng.integers(len(active)))]
                active.remove(bye)
                next_round = [bye]
            else:
                next_round = []
            for left, right in zip(active[::2], active[1::2], strict=False):
                probability = pair_probability[left, right]
                next_round.append(left if rng.random() < probability else right)
            active = next_round
        championships[names[active[0]]] += 1

    frame["finals_probability"] = frame["team"].map(finals) / simulations
    frame["title_probability"] = frame["team"].map(championships) / simulations
    frame["title_odds_rank"] = frame["title_probability"].rank(method="min", ascending=False).astype(int)
    return frame.sort_values("title_probability", ascending=False).reset_index(drop=True)
