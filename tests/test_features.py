from __future__ import annotations

import numpy as np
import pandas as pd

from spurslab.features import haversine_miles, schedule_stress


def test_haversine_is_symmetric_and_zero() -> None:
    assert haversine_miles(29.4241, -98.4936, 29.4241, -98.4936) == 0
    forward = haversine_miles(29.4241, -98.4936, 40.7128, -74.0060)
    reverse = haversine_miles(40.7128, -74.0060, 29.4241, -98.4936)
    assert np.isclose(forward, reverse)
    assert 1500 < forward < 2000


def test_schedule_stress_has_expected_density(tiny_schedule: pd.DataFrame) -> None:
    result = schedule_stress(tiny_schedule)
    assert result["game_id"].is_unique
    assert result["travel_miles"].ge(0).all()
    assert bool(result.loc[result["game_id"] == "2", "back_to_back"].iloc[0])
    assert int(result.iloc[-1]["games_in_4"]) == 3
    assert result["stress_score"].notna().all()

