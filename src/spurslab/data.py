"""Download, cache, normalize, and validate the portfolio's public NBA data."""

from __future__ import annotations

import json
import time
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

import numpy as np
import pandas as pd
import requests

from .config import Paths, load_settings


class DataContractError(ValueError):
    """Raised when an upstream payload no longer matches the expected contract."""


@dataclass
class ApiClient:
    """Small HTTP client with transparent raw-response caching."""

    paths: Paths
    timeout: int = 45
    pause: float = 0.15
    refresh: bool = False

    def get_json(self, url: str, params: dict[str, Any], cache_name: str) -> dict[str, Any]:
        cache_path = self.paths.raw / cache_name
        if cache_path.exists() and not self.refresh:
            return cast(dict[str, Any], json.loads(cache_path.read_text(encoding="utf-8")))

        response = requests.get(
            url,
            params=params,
            timeout=self.timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            },
        )
        response.raise_for_status()
        payload = cast(dict[str, Any], response.json())
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload), encoding="utf-8")
        time.sleep(self.pause)
        return payload


def _competitors(event: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    competitors = event["competitions"][0]["competitors"]
    home = next(team for team in competitors if team["homeAway"] == "home")
    away = next(team for team in competitors if team["homeAway"] == "away")
    return home, away


def normalize_schedule(payload: dict[str, Any], team_abbr: str = "SA") -> pd.DataFrame:
    """Convert an ESPN team schedule response to one row per game."""

    rows: list[dict[str, Any]] = []
    for event in payload.get("events", []):
        competition = event["competitions"][0]
        home, away = _competitors(event)
        team = home if home["team"]["abbreviation"] == team_abbr else away
        opponent = away if team is home else home
        is_home = team is home
        venue = competition.get("venue", {})
        address = venue.get("address", {})
        status = event.get("status", {}).get("type", {})
        team_score = _numeric_stat(team.get("score"))
        opponent_score = _numeric_stat(opponent.get("score"))
        if pd.notna(team_score) and pd.notna(opponent_score):
            result = "W" if team_score > opponent_score else "L"
        else:
            result = None
        rows.append(
            {
                "game_id": str(event["id"]),
                "date_utc": event["date"],
                "season": event.get("season", {}).get("displayName"),
                "season_type": event.get("seasonType", {}).get("name"),
                "is_home": is_home,
                "is_neutral": bool(competition.get("neutralSite", False)),
                "opponent": opponent["team"]["abbreviation"],
                "opponent_name": opponent["team"]["displayName"],
                "team_score": team_score,
                "opponent_score": opponent_score,
                "result": result,
                "venue": venue.get("fullName"),
                "city": address.get("city"),
                "state": address.get("state"),
                "status": status.get("name"),
                "status_detail": status.get("detail"),
                "event_name": event.get("name"),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise DataContractError("Schedule response contained no events")
    frame["date_utc"] = pd.to_datetime(frame["date_utc"], utc=True)
    return frame.sort_values("date_utc").reset_index(drop=True)


def normalize_roster(payload: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for athlete in payload.get("athletes", []):
        rows.append(
            {
                "player_id": str(athlete.get("id")),
                "player": athlete.get("fullName"),
                "display_name": athlete.get("displayName"),
                "jersey": athlete.get("jersey"),
                "position": athlete.get("position", {}).get("abbreviation"),
                "age": athlete.get("age"),
                "height": athlete.get("displayHeight"),
                "weight_lbs": athlete.get("weight"),
                "experience_years": athlete.get("experience", {}).get("years"),
                "college": athlete.get("college", {}).get("name"),
                "status": athlete.get("status", {}).get("name"),
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise DataContractError("Roster response contained no athletes")
    return frame.sort_values("player").reset_index(drop=True)


def _numeric_stat(value: Any) -> float:
    if isinstance(value, dict):
        value = value.get("value", value.get("displayValue"))
    if value in (None, "", "--"):
        return np.nan
    try:
        return float(str(value).replace("+", ""))
    except ValueError:
        return np.nan


def _split_made_attempted(value: Any) -> tuple[float, float]:
    try:
        made, attempted = str(value).split("-")
        return float(made), float(attempted)
    except (TypeError, ValueError):
        return np.nan, np.nan


def normalize_player_boxscore(
    summary: dict[str, Any], game_id: str, game_date: pd.Timestamp
) -> pd.DataFrame:
    """Normalize the ESPN player boxscore while retaining starters and DNPs."""

    rows: list[dict[str, Any]] = []
    for team_block in summary.get("boxscore", {}).get("players", []):
        team_abbr = team_block.get("team", {}).get("abbreviation")
        for stat_group in team_block.get("statistics", []):
            labels = stat_group.get("labels", [])
            for item in stat_group.get("athletes", []):
                athlete = item.get("athlete", {})
                stats = dict(zip(labels, item.get("stats", []), strict=False))
                fgm, fga = _split_made_attempted(stats.get("FG"))
                fg3m, fg3a = _split_made_attempted(stats.get("3PT"))
                ftm, fta = _split_made_attempted(stats.get("FT"))
                rows.append(
                    {
                        "game_id": str(game_id),
                        "game_date": game_date,
                        "team": team_abbr,
                        "player_id": str(athlete.get("id")),
                        "player": athlete.get("displayName"),
                        "position": athlete.get("position", {}).get("abbreviation"),
                        "starter": bool(item.get("starter", False)),
                        "did_not_play": bool(item.get("didNotPlay", False)),
                        "dnp_reason": item.get("reason"),
                        "minutes": _numeric_stat(stats.get("MIN")),
                        "points": _numeric_stat(stats.get("PTS")),
                        "fgm": fgm,
                        "fga": fga,
                        "fg3m": fg3m,
                        "fg3a": fg3a,
                        "ftm": ftm,
                        "fta": fta,
                        "rebounds": _numeric_stat(stats.get("REB")),
                        "assists": _numeric_stat(stats.get("AST")),
                        "turnovers": _numeric_stat(stats.get("TO")),
                        "steals": _numeric_stat(stats.get("STL")),
                        "blocks": _numeric_stat(stats.get("BLK")),
                        "offensive_rebounds": _numeric_stat(stats.get("OREB")),
                        "defensive_rebounds": _numeric_stat(stats.get("DREB")),
                        "fouls": _numeric_stat(stats.get("PF")),
                        "plus_minus": _numeric_stat(stats.get("+/-")),
                    }
                )
    return pd.DataFrame(rows)


def _clock_seconds(display_value: str | None) -> float:
    if not display_value:
        return np.nan
    parts = display_value.split(":")
    try:
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        return float(parts[0])
    except ValueError:
        return np.nan


def normalize_plays(summary: dict[str, Any], game_id: str) -> pd.DataFrame:
    """Normalize play-by-play and attach ESPN's home win probability."""

    header = summary.get("header", {}).get("competitions", [{}])[0]
    competitors = header.get("competitors", [])
    home: dict[str, Any] = next(
        (x for x in competitors if x.get("homeAway") == "home"), {}
    )
    away: dict[str, Any] = next(
        (x for x in competitors if x.get("homeAway") == "away"), {}
    )
    home_abbr = home.get("team", {}).get("abbreviation")
    away_abbr = away.get("team", {}).get("abbreviation")
    probability = {
        str(item.get("playId")): item.get("homeWinPercentage")
        for item in summary.get("winprobability", [])
    }
    rows: list[dict[str, Any]] = []
    for play in summary.get("plays", []):
        period = play.get("period", {}).get("number")
        clock_seconds = _clock_seconds(play.get("clock", {}).get("displayValue"))
        regulation_elapsed = ((period - 1) * 720 + (720 - clock_seconds)) if period and period <= 4 else np.nan
        rows.append(
            {
                "game_id": str(game_id),
                "play_id": str(play.get("id")),
                "sequence": pd.to_numeric(play.get("sequenceNumber"), errors="coerce"),
                "period": period,
                "clock": play.get("clock", {}).get("displayValue"),
                "clock_seconds": clock_seconds,
                "regulation_elapsed_seconds": regulation_elapsed,
                "play_type": play.get("type", {}).get("text"),
                "text": play.get("text"),
                "team_id": str(play.get("team", {}).get("id", "")),
                "away_score": play.get("awayScore"),
                "home_score": play.get("homeScore"),
                "score_value": play.get("scoreValue", 0),
                "scoring_play": bool(play.get("scoringPlay", False)),
                "shooting_play": bool(play.get("shootingPlay", False)),
                "home_win_probability": probability.get(str(play.get("id"))),
                "home_team": home_abbr,
                "away_team": away_abbr,
            }
        )
    return pd.DataFrame(rows)


def _flatten_columns(frame: pd.DataFrame) -> pd.DataFrame:
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = [
            str(second) if str(first).startswith("Unnamed") else f"{first}_{second}"
            for first, second in frame.columns
        ]
    return frame


def fetch_bref_ratings(season: int) -> pd.DataFrame:
    url = f"https://www.basketball-reference.com/leagues/NBA_{season}_ratings.html"
    frame = _flatten_columns(pd.read_html(url)[0])
    rename = {
        "Rk": "rank",
        "Team": "team",
        "Conf": "conference",
        "Div": "division",
        "W": "wins",
        "L": "losses",
        "W/L%": "win_pct",
        "Unadjusted_MOV": "margin",
        "Unadjusted_ORtg": "off_rating",
        "Unadjusted_DRtg": "def_rating",
        "Unadjusted_NRtg": "net_rating",
        "Adjusted_MOV/A": "adjusted_margin",
        "Adjusted_ORtg/A": "adjusted_off_rating",
        "Adjusted_DRtg/A": "adjusted_def_rating",
        "Adjusted_NRtg/A": "adjusted_net_rating",
    }
    frame = frame.rename(columns=rename)
    frame["team"] = frame["team"].astype(str).str.replace("*", "", regex=False)
    numeric = [column for column in rename.values() if column not in {"team", "conference", "division"}]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
    return frame[list(rename.values())].sort_values("rank").reset_index(drop=True)


def fetch_bref_players(season: int) -> pd.DataFrame:
    base = f"https://www.basketball-reference.com/leagues/NBA_{season}_{{table}}.html"
    per_game = pd.read_html(base.format(table="per_game"))[0]
    advanced = pd.read_html(base.format(table="advanced"))[0]
    per_game = per_game[per_game["Player"] != "Player"].copy()
    advanced = advanced[advanced["Player"] != "Player"].copy()
    keys = ["Player", "Age", "Team", "Pos", "G", "GS"]
    advanced_keep = keys + [
        "PER",
        "TS%",
        "3PAr",
        "FTr",
        "AST%",
        "STL%",
        "BLK%",
        "TOV%",
        "USG%",
        "WS",
        "WS/48",
        "OBPM",
        "DBPM",
        "BPM",
        "VORP",
    ]
    merged = per_game.merge(advanced[advanced_keep], on=keys, how="left", validate="one_to_one")
    merged["season_end"] = season
    merged["season"] = f"{season - 1}-{str(season)[-2:]}"
    merged.columns = [
        column.lower()
        .replace("%", "_pct")
        .replace("/", "_per_")
        .replace("3", "three_")
        .replace(" ", "_")
        for column in merged.columns
    ]
    for column in merged.columns:
        if column not in {"player", "team", "pos", "awards", "season"}:
            merged[column] = pd.to_numeric(merged[column], errors="coerce")
    return merged.reset_index(drop=True)


def fetch_bref_games(season: int) -> pd.DataFrame:
    months = ["october", "november", "december", "january", "february", "march", "april", "may", "june"]
    frames: list[pd.DataFrame] = []
    for month in months:
        url = f"https://www.basketball-reference.com/leagues/NBA_{season}_games-{month}.html"
        try:
            frame = pd.read_html(url)[0]
        except ValueError:
            continue
        frame["month_page"] = month
        frames.append(frame)
    games = pd.concat(frames, ignore_index=True)
    games = games[games["Date"] != "Date"].copy()
    games["Date"] = pd.to_datetime(games["Date"], errors="coerce")
    games["PTS"] = pd.to_numeric(games["PTS"], errors="coerce")
    games["PTS.1"] = pd.to_numeric(games["PTS.1"], errors="coerce")
    games = games.rename(
        columns={
            "Date": "date",
            "Visitor/Neutral": "away_team",
            "Home/Neutral": "home_team",
            "PTS": "away_score",
            "PTS.1": "home_score",
            "Attend.": "attendance",
            "Arena": "arena",
            "Notes": "notes",
        }
    )
    games["season_end"] = season
    games["is_playoffs"] = games["date"] >= pd.Timestamp(f"{season}-04-18")
    return games.reset_index(drop=True)


def _write_snapshot(frame: pd.DataFrame, paths: Paths, name: str) -> None:
    frame.to_csv(paths.snapshots / f"{name}.csv", index=False)
    frame.to_parquet(paths.processed / f"{name}.parquet", index=False)


def bootstrap_data(refresh: bool = False) -> dict[str, pd.DataFrame]:
    """Build all network-backed snapshots used by the seven projects."""

    settings = load_settings()
    paths = Paths()
    paths.ensure()
    data_cfg = settings["data"]
    portfolio = settings["portfolio"]
    client = ApiClient(
        paths,
        timeout=data_cfg["request_timeout_seconds"],
        pause=data_cfg["request_pause_seconds"],
        refresh=refresh,
    )

    schedule_payloads: list[dict[str, Any]] = []
    for season, season_type in [
        (portfolio["prior_season"], 2),
        (portfolio["prior_season"], 3),
        (portfolio["forecast_season"], 2),
    ]:
        payload = client.get_json(
            data_cfg["espn_schedule_url"].format(team=portfolio["team_espn"]),
            {"season": season, "seasontype": season_type},
            f"espn_schedule_{season}_{season_type}.json",
        )
        schedule_payloads.append(payload)

    prior_regular = normalize_schedule(schedule_payloads[0])
    prior_post = normalize_schedule(schedule_payloads[1])
    upcoming = normalize_schedule(schedule_payloads[2])
    prior_schedule = pd.concat([prior_regular, prior_post], ignore_index=True).sort_values("date_utc")

    roster_payload = client.get_json(
        data_cfg["espn_roster_url"].format(team=portfolio["team_espn"]),
        {"season": portfolio["forecast_season"]},
        f"espn_roster_{portfolio['forecast_season']}.json",
    )
    roster = normalize_roster(roster_payload)

    boxscore_frames: list[pd.DataFrame] = []
    play_frames: list[pd.DataFrame] = []
    for row in prior_schedule.itertuples(index=False):
        summary = client.get_json(
            data_cfg["espn_summary_url"],
            {"event": row.game_id},
            f"espn_summary_{row.game_id}.json",
        )
        boxscore_frames.append(normalize_player_boxscore(summary, row.game_id, row.date_utc))
        if row.season_type == "Postseason":
            play_frames.append(normalize_plays(summary, row.game_id))

    player_boxscores = pd.concat(boxscore_frames, ignore_index=True)
    postseason_plays = pd.concat(play_frames, ignore_index=True)
    ratings = fetch_bref_ratings(portfolio["prior_season"])
    games = fetch_bref_games(portfolio["prior_season"])
    player_seasons = pd.concat(
        [fetch_bref_players(season) for season in range(2023, portfolio["prior_season"] + 1)],
        ignore_index=True,
    )

    frames = {
        "spurs_schedule_2025_26": prior_schedule,
        "spurs_schedule_2026_27": upcoming,
        "spurs_roster_2026_27": roster,
        "spurs_player_boxscores_2025_26": player_boxscores,
        "spurs_postseason_plays_2026": postseason_plays,
        "nba_team_ratings_2025_26": ratings,
        "nba_games_2025_26": games,
        "nba_player_seasons_2022_26": player_seasons,
    }
    for name, frame in frames.items():
        _write_snapshot(frame, paths, name)

    manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "refresh": refresh,
        "datasets": {
            name: {"rows": len(frame), "columns": list(frame.columns)}
            for name, frame in frames.items()
        },
    }
    (paths.snapshots / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return frames


def load_snapshot(name: str, paths: Paths | None = None) -> pd.DataFrame:
    paths = paths or Paths()
    parquet = paths.processed / f"{name}.parquet"
    csv = paths.snapshots / f"{name}.csv"
    if parquet.exists():
        return pd.read_parquet(parquet)
    if csv.exists():
        return pd.read_csv(csv)
    raise FileNotFoundError(f"Missing snapshot {name!r}; run `spurslab data` first")


def require_columns(frame: pd.DataFrame, columns: Iterable[str], name: str) -> None:
    missing = set(columns).difference(frame.columns)
    if missing:
        raise DataContractError(f"{name} is missing required columns: {sorted(missing)}")
