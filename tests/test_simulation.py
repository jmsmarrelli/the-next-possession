from __future__ import annotations

import numpy as np
import pandas as pd

from spurslab.simulation import game_win_probability, simulate_schedule


def test_game_probability_is_bounded_and_monotonic() -> None:
    margins = np.array([-20, -5, 0, 5, 20])
    probabilities = game_win_probability(margins)
    assert ((probabilities >= 0) & (probabilities <= 1)).all()
    assert np.all(np.diff(probabilities) > 0)
    assert probabilities[2] == 0.5


def test_schedule_simulation_is_seeded() -> None:
    games = pd.DataFrame({"win_probability": [0.25, 0.5, 0.75]})
    first_summary, first_distribution = simulate_schedule(games, simulations=2_000, seed=210)
    second_summary, second_distribution = simulate_schedule(games, simulations=2_000, seed=210)
    pd.testing.assert_frame_equal(first_summary, second_summary)
    pd.testing.assert_frame_equal(first_distribution, second_distribution)
    mean = first_summary.loc[first_summary["metric"] == "mean_wins", "value"].iloc[0]
    assert 1.4 < mean < 1.6

