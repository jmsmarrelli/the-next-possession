"""Feature engineering for schedule, player, lineup-proxy, and clutch projects."""

from __future__ import annotations

import math
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .config import Paths
from .data import require_columns


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles."""

    radius = 3958.7613
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _games_in_window(dates: pd.Series, days: int) -> list[int]:
    values = pd.to_datetime(dates).dt.normalize().tolist()
    return [sum(0 <= (date - prior).days < days for prior in values[: i + 1]) for i, date in enumerate(values)]


def schedule_stress(schedule: pd.DataFrame, venue_path: Path | None = None) -> pd.DataFrame:
    """Add travel, rest, density, and transparent schedule-stress features."""

    require_columns(schedule, ["date_utc", "city", "opponent", "is_home"], "schedule")
    venue_path = venue_path or Paths().config / "venues.csv"
    venues = pd.read_csv(venue_path)
    frame = schedule.sort_values("date_utc").copy()
    frame["date_utc"] = pd.to_datetime(frame["date_utc"], utc=True)
    frame["date"] = frame["date_utc"].dt.tz_convert("America/Chicago").dt.tz_localize(None).dt.normalize()
    frame = frame.merge(venues, on="city", how="left", validate="many_to_one")
    if frame[["latitude", "longitude"]].isna().any(axis=None):
        missing = sorted(frame.loc[frame["latitude"].isna(), "city"].dropna().unique())
        raise ValueError(f"Missing venue coordinates for: {missing}")

    frame["rest_days"] = frame["date"].diff().dt.days.sub(1).clip(lower=0).fillna(3)
    frame["back_to_back"] = frame["rest_days"].eq(0)
    frame["games_in_4"] = _games_in_window(frame["date"], 4)
    frame["games_in_7"] = _games_in_window(frame["date"], 7)
    frame["three_in_four"] = frame["games_in_4"].ge(3)
    frame["five_in_seven"] = frame["games_in_7"].ge(5)

    distances = [0.0]
    timezone_crossings = [0.0]
    for previous, current in zip(frame.iloc[:-1].itertuples(), frame.iloc[1:].itertuples(), strict=False):
        distances.append(
            haversine_miles(previous.latitude, previous.longitude, current.latitude, current.longitude)
        )
        timezone_crossings.append(abs(current.utc_offset_hours - previous.utc_offset_hours))
    frame["travel_miles"] = distances
    frame["time_zones_crossed"] = timezone_crossings
    frame["international"] = frame["country"].ne("USA")

    travel_component = np.minimum(frame["travel_miles"] / 2200, 1.5)
    low_rest_component = np.maximum(0, 2 - frame["rest_days"]) / 2
    raw = (
        28 * frame["back_to_back"].astype(float)
        + 14 * frame["three_in_four"].astype(float)
        + 11 * frame["five_in_seven"].astype(float)
        + 22 * travel_component
        + 8 * np.minimum(frame["time_zones_crossed"], 3) / 3
        + 12 * low_rest_component
        + 5 * frame["international"].astype(float)
    )
    frame["stress_score"] = raw.round(1)
    frame["stress_percentile"] = (frame["stress_score"].rank(pct=True) * 100).round(0)
    frame["stress_tier"] = pd.cut(
        frame["stress_percentile"],
        bins=[0, 50, 75, 90, 100],
        labels=["Routine", "Elevated", "Hard", "Red alert"],
        include_lowest=True,
    ).astype(str)
    return frame


def rotation_pair_proxies(boxscores: pd.DataFrame, team: str = "SA", min_games: int = 8) -> pd.DataFrame:
    """Estimate pair chemistry from co-appearance boxscore signals.

    This is deliberately named a proxy: a boxscore cannot recover true shared
    possessions. The output is useful for portfolio exploration, not coaching
    lineup decisions without possession-level validation.
    """

    require_columns(
        boxscores,
        ["game_id", "team", "player", "minutes", "plus_minus", "points", "assists", "turnovers"],
        "boxscores",
    )
    played = boxscores[(boxscores["team"] == team) & (boxscores["minutes"] > 0)].copy()
    rows: list[dict[str, Any]] = []
    for game_id, group in played.groupby("game_id"):
        records = group.to_dict("records")
        for left, right in combinations(records, 2):
            player_a, player_b = sorted([left["player"], right["player"]])
            first = left if left["player"] == player_a else right
            second = right if right["player"] == player_b else left
            rows.append(
                {
                    "game_id": game_id,
                    "player_a": player_a,
                    "player_b": player_b,
                    "shared_minutes_proxy": min(first["minutes"], second["minutes"]),
                    "pair_plus_minus_proxy": np.nanmean([first["plus_minus"], second["plus_minus"]]),
                    "pair_points": np.nansum([first["points"], second["points"]]),
                    "pair_assists": np.nansum([first["assists"], second["assists"]]),
                    "pair_turnovers": np.nansum([first["turnovers"], second["turnovers"]]),
                }
            )
    pairs = pd.DataFrame(rows)
    summary = (
        pairs.groupby(["player_a", "player_b"], as_index=False)
        .agg(
            games_together=("game_id", "nunique"),
            shared_minutes_proxy=("shared_minutes_proxy", "sum"),
            avg_pair_plus_minus=("pair_plus_minus_proxy", "mean"),
            avg_combined_points=("pair_points", "mean"),
            avg_combined_assists=("pair_assists", "mean"),
            avg_combined_turnovers=("pair_turnovers", "mean"),
        )
    )
    summary = summary[summary["games_together"] >= min_games].copy()
    summary["assist_turnover_ratio"] = summary["avg_combined_assists"] / summary[
        "avg_combined_turnovers"
    ].replace(0, np.nan)
    reliability = np.minimum(summary["games_together"] / 40, 1)
    summary["chemistry_index"] = (
        reliability
        * (
            0.65 * summary["avg_pair_plus_minus"].fillna(0)
            + 2.0 * (summary["assist_turnover_ratio"].fillna(0) - 1.5)
        )
    ).round(2)
    return summary.sort_values("chemistry_index", ascending=False).reset_index(drop=True)


def starter_unit_proxies(
    boxscores: pd.DataFrame, schedule: pd.DataFrame, team: str = "SA"
) -> pd.DataFrame:
    starters = boxscores[
        (boxscores["team"] == team) & boxscores["starter"] & (boxscores["minutes"] > 0)
    ].copy()
    units = (
        starters.groupby("game_id")["player"]
        .agg(lambda players: " · ".join(sorted(players)))
        .rename("starter_unit")
        .reset_index()
    )
    units["starter_count"] = units["starter_unit"].str.count(" · ") + 1
    schedule_copy = schedule.copy()
    schedule_copy["margin"] = schedule_copy["team_score"] - schedule_copy["opponent_score"]
    units = units.merge(
        schedule_copy[["game_id", "margin", "result", "season_type"]], on="game_id", how="left"
    )
    summary = (
        units[units["starter_count"] == 5]
        .groupby("starter_unit", as_index=False)
        .agg(
            games=("game_id", "nunique"),
            wins=("result", lambda values: int((values == "W").sum())),
            avg_game_margin=("margin", "mean"),
        )
    )
    summary["win_pct"] = summary["wins"] / summary["games"]
    return summary.sort_values(["games", "avg_game_margin"], ascending=False).reset_index(drop=True)


def wemby_game_impact(
    boxscores: pd.DataFrame, schedule: pd.DataFrame, player: str = "Victor Wembanyama"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    schedule_copy = schedule.copy()
    schedule_copy["margin"] = schedule_copy["team_score"] - schedule_copy["opponent_score"]
    player_games = boxscores[(boxscores["team"] == "SA") & (boxscores["player"] == player)].copy()
    player_games["available"] = player_games["minutes"].fillna(0) > 0
    columns = [
        "game_id",
        "available",
        "minutes",
        "points",
        "rebounds",
        "assists",
        "blocks",
        "plus_minus",
    ]
    games = schedule_copy.merge(player_games[columns], on="game_id", how="left")
    games["available"] = games["available"].fillna(False)
    summary = (
        games.groupby("available", as_index=False)
        .agg(
            games=("game_id", "nunique"),
            win_pct=("result", lambda values: (values == "W").mean()),
            avg_margin=("margin", "mean"),
            team_points=("team_score", "mean"),
            opponent_points=("opponent_score", "mean"),
        )
        .replace({"available": {True: "Wemby played", False: "Wemby out"}})
        .rename(columns={"available": "availability"})
    )
    return games, summary


def finals_clutch_profile(plays: pd.DataFrame, finals_game_ids: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = plays[plays["game_id"].astype(str).isin([str(x) for x in finals_game_ids])].copy()
    if frame.empty:
        raise ValueError("No Finals plays found for the supplied game IDs")
    frame["spurs_margin"] = np.where(
        frame["home_team"] == "SA",
        frame["home_score"] - frame["away_score"],
        frame["away_score"] - frame["home_score"],
    )
    frame["spurs_win_probability"] = np.where(
        frame["home_team"] == "SA",
        frame["home_win_probability"],
        1 - frame["home_win_probability"],
    )
    frame["clutch"] = (
        frame["period"].eq(4) & frame["clock_seconds"].le(300) & frame["spurs_margin"].abs().le(5)
    )
    metrics: list[dict[str, Any]] = []
    for game_id, group in frame.sort_values(["game_id", "sequence"]).groupby("game_id"):
        scoring = group.dropna(subset=["spurs_margin"])
        if scoring.empty:
            continue
        max_lead = scoring["spurs_margin"].max()
        final_margin = scoring.iloc[-1]["spurs_margin"]
        win_prob = scoring["spurs_win_probability"].dropna()
        metrics.append(
            {
                "game_id": str(game_id),
                "max_spurs_lead": max_lead,
                "final_margin": final_margin,
                "lead_surrendered": max_lead - final_margin,
                "peak_spurs_win_probability": win_prob.max() if not win_prob.empty else np.nan,
                "clutch_plays": int(group["clutch"].sum()),
                "clutch_scoring_plays": int((group["clutch"] & group["scoring_play"]).sum()),
            }
        )
    return frame, pd.DataFrame(metrics)


def player_archetypes(players: pd.DataFrame, season_end: int = 2026, clusters: int = 8) -> pd.DataFrame:
    """Cluster rotation players using interpretable rate and impact features."""

    frame = players[
        (players["season_end"] == season_end)
        & (players["team"] != "TOT")
        & (players["g"] >= 30)
        & (players["mp"] >= 15)
    ].copy()
    features = [
        "pts",
        "ast",
        "trb",
        "three_pa",
        "three_p_pct",
        "ts_pct",
        "usg_pct",
        "ast_pct",
        "blk_pct",
        "stl_pct",
        "obpm",
        "dbpm",
    ]
    values = frame[features].copy()
    values = values.fillna(values.median(numeric_only=True))
    scaled = StandardScaler().fit_transform(values)
    model = KMeans(n_clusters=clusters, random_state=210, n_init=30)
    frame["cluster"] = model.fit_predict(scaled)

    centroids = frame.groupby("cluster")[features].mean()
    labels: dict[int, str] = {}
    remaining = set(centroids.index)
    ranking_rules = [
        ("Primary engines", "ast_pct"),
        ("Volume creators", "pts"),
        ("Rim protectors", "blk_pct"),
        ("Two-way stars", "dbpm"),
        ("Movement shooters", "three_pa"),
        ("Connective wings", "ast"),
        ("Interior finishers", "trb"),
        ("Low-usage defenders", "stl_pct"),
    ]
    for label, metric in ranking_rules:
        if not remaining:
            break
        cluster = centroids.loc[list(remaining), metric].idxmax()
        labels[int(cluster)] = label
        remaining.remove(cluster)
    frame["archetype"] = frame["cluster"].map(labels)
    return frame.sort_values(["archetype", "bpm"], ascending=[True, False]).reset_index(drop=True)

