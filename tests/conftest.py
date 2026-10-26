from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def tiny_schedule() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "game_id": ["1", "2", "3"],
            "date_utc": pd.to_datetime(
                ["2026-10-21T01:30:00Z", "2026-10-22T01:30:00Z", "2026-10-24T00:00:00Z"],
                utc=True,
            ),
            "city": ["San Antonio", "Dallas", "San Antonio"],
            "opponent": ["OKC", "DAL", "HOU"],
            "is_home": [True, False, True],
            "is_neutral": [False, False, False],
        }
    )

