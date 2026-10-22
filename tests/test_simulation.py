from __future__ import annotations

import numpy as np
import pandas as pd

from spurslab.simulation import game_win_probability, simulate_schedule


def test_neutral_series_matches_binomial_reference_and_swap_symmetry() -> None:
    from scipy.stats import binom, norm

    from spurslab.simulation import _series_win_probability
    for margin in [-10, -3, 0, 3, 10]:
        actual = _series_win_probability(margin, 0)
        assert np.isclose(actual, binom.sf(3, 7, norm.cdf(margin / 12)))
        assert np.isclose(actual + _series_win_probability(0, margin), 1)
    assert _series_win_probability(0, 0) == 0.5


def test_tournament_conserves_one_champion_and_two_finalists_with_byes() -> None:
    from spurslab.simulation import contender_title_odds
    ratings = pd.DataFrame({
        'team': [f'Team {i}' for i in range(12)], 'rank': range(1, 13),
        'adjusted_net_rating': [0.] * 12, 'conference': ['West'] * 12,
    })
    result = contender_title_odds(ratings, simulations=5000)
    assert np.isclose(result.title_probability.sum(), 1)
    assert np.isclose(result.finals_probability.sum(), 2)
    assert (result.finals_probability <= 1).all()
    assert (result.title_probability - 1/12).abs().max() < .025


def test_invalid_schedule_probabilities_are_rejected() -> None:
    import pytest
    for probabilities in [[np.nan], [1.1], [-.1], []]:
        with pytest.raises(ValueError):
            simulate_schedule(pd.DataFrame({'win_probability': probabilities}))
    with pytest.raises(ValueError):
        simulate_schedule(pd.DataFrame({'win_probability': [.5]}), simulations=0)


def test_invalid_margin_scale_is_rejected() -> None:
    import pytest
    for scale in [0, -1, np.nan]:
        with pytest.raises(ValueError):
            game_win_probability(0, scale)


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

