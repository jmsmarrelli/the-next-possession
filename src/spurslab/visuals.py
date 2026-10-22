"""Consistent Spurs-inspired charts for reports and the portfolio site."""

from __future__ import annotations

import os
from pathlib import Path

MPL_CONFIG_DIR = Path(__file__).resolve().parents[2] / ".cache" / "matplotlib"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CONFIG_DIR))

import matplotlib.pyplot as plt  # noqa: E402 - cache must be configured before import
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

SILVER = "#c4ced4"
BLACK = "#0d1117"
CHARCOAL = "#263238"
CREAM = "#f5f1e8"
TEAL = "#00b2a9"
ORANGE = "#f36f45"
MAGENTA = "#e83e8c"


def set_theme() -> None:
    sns.set_theme(
        style="whitegrid",
        context="talk",
        rc={
            "figure.facecolor": CREAM,
            "axes.facecolor": CREAM,
            "axes.edgecolor": CHARCOAL,
            "axes.labelcolor": CHARCOAL,
            "text.color": BLACK,
            "xtick.color": CHARCOAL,
            "ytick.color": CHARCOAL,
            "grid.color": "#d8d2c4",
            "font.family": "DejaVu Sans",
        },
    )


def _finish(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def plot_schedule_stress(frame: pd.DataFrame, path: Path, top_n: int = 15) -> None:
    set_theme()
    top = frame.nlargest(top_n, "stress_score").sort_values("stress_score")
    labels = top["date"].dt.strftime("%b %d") + " · " + np.where(top["is_home"], "vs ", "@ ") + top["opponent"]
    colors = [ORANGE if tier == "Red alert" else TEAL for tier in top["stress_tier"]]
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.barh(labels, top["stress_score"], color=colors)
    ax.set_title("The 15 hardest schedule spots", loc="left", weight="bold", fontsize=22)
    ax.set_xlabel("Transparent stress score (higher is harder)")
    ax.set_ylabel("")
    ax.spines[["top", "right", "left"]].set_visible(False)
    _finish(fig, path)


def plot_contender_landscape(ratings: pd.DataFrame, path: Path) -> None:
    set_theme()
    fig, ax = plt.subplots(figsize=(11, 8))
    is_spurs = ratings["team"].eq("San Antonio Spurs")
    is_contender = ratings["rank"].le(12)
    ax.scatter(
        ratings.loc[~is_contender, "adjusted_off_rating"],
        ratings.loc[~is_contender, "adjusted_def_rating"],
        s=50,
        color=SILVER,
        alpha=0.75,
        label="League",
    )
    ax.scatter(
        ratings.loc[is_contender & ~is_spurs, "adjusted_off_rating"],
        ratings.loc[is_contender & ~is_spurs, "adjusted_def_rating"],
        s=105,
        color=TEAL,
        label="Contenders",
    )
    ax.scatter(
        ratings.loc[is_spurs, "adjusted_off_rating"],
        ratings.loc[is_spurs, "adjusted_def_rating"],
        s=190,
        color=ORANGE,
        edgecolor=BLACK,
        linewidth=1,
        label="Spurs",
        zorder=5,
    )
    for row in ratings[is_contender].itertuples():
        label = row.team.replace("San Antonio ", "").replace("Oklahoma City ", "OKC ")
        offsets = {
            "Toronto Raptors": (-25, 8),
            "Atlanta Hawks": (5, -10),
            "Minnesota Timberwolves": (5, 8),
            "Houston Rockets": (5, 8),
            "New York Knicks": (5, -10),
        }
        ax.annotate(
            label,
            (row.adjusted_off_rating, row.adjusted_def_rating),
            xytext=offsets.get(label, (5, 5)),
            textcoords="offset points",
            fontsize=9,
        )
    ax.invert_yaxis()
    ax.axvline(ratings["adjusted_off_rating"].mean(), color="#777", lw=1, ls="--")
    ax.axhline(ratings["adjusted_def_rating"].mean(), color="#777", lw=1, ls="--")
    ax.set_title("The contender map", loc="left", weight="bold", fontsize=22)
    ax.set_xlabel("Adjusted offensive rating → better")
    ax.set_ylabel("Adjusted defensive rating → better upward")
    ax.legend(frameon=False, loc="lower right")
    _finish(fig, path)


def plot_pair_chemistry(pairs: pd.DataFrame, path: Path, players: int = 10) -> None:
    set_theme()
    leaders = pd.concat([pairs["player_a"], pairs["player_b"]]).value_counts().head(players).index
    subset = pairs[pairs["player_a"].isin(leaders) & pairs["player_b"].isin(leaders)]
    matrix = pd.DataFrame(np.nan, index=leaders, columns=leaders)
    for row in subset.itertuples():
        matrix.loc[row.player_a, row.player_b] = row.chemistry_index
        matrix.loc[row.player_b, row.player_a] = row.chemistry_index
    for player in leaders:
        matrix.loc[player, player] = 0
    fig, ax = plt.subplots(figsize=(11, 9))
    sns.heatmap(matrix, cmap="vlag", center=0, linewidths=0.5, annot=True, fmt=".1f", ax=ax, cbar_kws={"label": "Chemistry proxy"})
    ax.set_title("Rotation chemistry map", loc="left", weight="bold", fontsize=22)
    ax.set_xlabel("")
    ax.set_ylabel("")
    _finish(fig, path)


def plot_wemby_impact(summary: pd.DataFrame, path: Path) -> None:
    set_theme()
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    for ax, metric, title in zip(axes, ["win_pct", "avg_margin"], ["Win rate", "Average margin"], strict=False):
        data = summary.copy()
        values = data[metric] * 100 if metric == "win_pct" else data[metric]
        ax.bar(data["availability"], values, color=[ORANGE, TEAL][: len(data)])
        ax.set_title(title, loc="left", weight="bold")
        ax.set_ylabel("Percent" if metric == "win_pct" else "Points")
        ax.spines[["top", "right", "left"]].set_visible(False)
    fig.subplots_adjust(top=0.76, wspace=0.20)
    fig.suptitle(
        "The Wembanyama availability split",
        x=0.05,
        y=0.98,
        ha="left",
        fontsize=22,
        weight="bold",
    )
    _finish(fig, path)


def plot_finals_leads(plays: pd.DataFrame, path: Path) -> None:
    set_theme()
    fig, ax = plt.subplots(figsize=(12, 7))
    for number, (_game_id, group) in enumerate(plays.groupby("game_id"), start=1):
        data = group.dropna(subset=["regulation_elapsed_seconds", "spurs_margin"])
        ax.plot(data["regulation_elapsed_seconds"] / 60, data["spurs_margin"], label=f"Game {number}", lw=2)
    ax.axhline(0, color=BLACK, lw=1.2)
    for minute in [12, 24, 36]:
        ax.axvline(minute, color="#888", ls=":", lw=1)
    ax.fill_between([0, 48], 0, 35, color=TEAL, alpha=0.04)
    ax.fill_between([0, 48], -35, 0, color=ORANGE, alpha=0.04)
    ax.set_xlim(0, 48)
    ax.set_xlabel("Game minute")
    ax.set_ylabel("Spurs scoring margin")
    ax.set_title("The Finals lead story", loc="left", weight="bold", fontsize=22)
    ax.legend(ncol=5, frameon=False, fontsize=10, loc="lower left")
    ax.spines[["top", "right"]].set_visible(False)
    _finish(fig, path)


def plot_archetypes(players: pd.DataFrame, path: Path) -> None:
    set_theme()
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.scatterplot(
        data=players,
        x="usg_pct",
        y="bpm",
        hue="archetype",
        size="mp",
        sizes=(30, 220),
        alpha=0.72,
        ax=ax,
        palette="tab10",
    )
    spurs = players[
        (players["team"] == "SAS")
        & players["player"].isin(
            ["Victor Wembanyama", "De'Aaron Fox", "Stephon Castle", "Dylan Harper"]
        )
    ]
    offsets = {
        "Victor Wembanyama": (8, 5),
        "De'Aaron Fox": (8, 8),
        "Stephon Castle": (8, -12),
        "Dylan Harper": (8, 5),
    }
    for row in spurs.itertuples():
        ax.annotate(
            row.player,
            (row.usg_pct, row.bpm),
            xytext=offsets[row.player],
            textcoords="offset points",
            fontsize=9,
            weight="bold",
        )
    ax.axhline(0, color="#777", ls="--", lw=1)
    ax.set_title("Player archetypes and the Spurs roster", loc="left", weight="bold", fontsize=22)
    ax.set_xlabel("Usage rate")
    ax.set_ylabel("Box Plus/Minus")
    ax.legend(frameon=False, bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=9)
    _finish(fig, path)


def plot_title_odds(odds: pd.DataFrame, path: Path) -> None:
    set_theme()
    data = odds.sort_values("title_probability")
    colors = [ORANGE if team == "San Antonio Spurs" else TEAL for team in data["team"]]
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.barh(data["team"], data["title_probability"] * 100, color=colors)
    ax.set_title("Preseason baseline title odds", loc="left", weight="bold", fontsize=22)
    ax.set_xlabel("Simulation probability (%)")
    ax.set_ylabel("")
    ax.spines[["top", "right", "left"]].set_visible(False)
    _finish(fig, path)


def plot_win_distribution(distribution: pd.DataFrame, path: Path) -> None:
    set_theme()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(distribution["wins"], distribution["probability"] * 100, color=ORANGE, width=0.9)
    ax.set_title("Spurs wins across schedule simulations", loc="left", weight="bold", fontsize=20)
    ax.set_xlabel("Wins in currently scheduled games")
    ax.set_ylabel("Probability (%)")
    ax.spines[["top", "right"]].set_visible(False)
    _finish(fig, path)
