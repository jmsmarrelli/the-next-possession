from __future__ import annotations

from spurslab.data import normalize_roster, normalize_schedule


def test_normalize_schedule_minimal_payload() -> None:
    payload = {
        "events": [
            {
                "id": "abc",
                "date": "2026-10-21T01:30Z",
                "season": {"displayName": "2026-27"},
                "seasonType": {"name": "Regular Season"},
                "competitions": [
                    {
                        "neutralSite": False,
                        "venue": {"fullName": "Frost Bank Center", "address": {"city": "San Antonio", "state": "TX"}},
                        "competitors": [
                            {"homeAway": "home", "team": {"abbreviation": "SA", "displayName": "San Antonio Spurs"}},
                            {"homeAway": "away", "team": {"abbreviation": "OKC", "displayName": "Oklahoma City Thunder"}},
                        ],
                    }
                ],
            }
        ]
    }
    result = normalize_schedule(payload)
    assert result.loc[0, "opponent"] == "OKC"
    assert bool(result.loc[0, "is_home"])


def test_normalize_roster_minimal_payload() -> None:
    payload = {
        "athletes": [
            {
                "id": "1",
                "fullName": "Victor Wembanyama",
                "position": {"abbreviation": "F"},
                "age": 22,
            }
        ]
    }
    result = normalize_roster(payload)
    assert result.loc[0, "player"] == "Victor Wembanyama"
    assert result.loc[0, "age"] == 22

