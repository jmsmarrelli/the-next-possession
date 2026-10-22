# Sources and access notes

Context was verified on 2026-08-25.

## Official season context

- [Spurs announce the 2026–27 schedule](https://www.nba.com/spurs/news/san-antonio-spurs-announce-2026-27-season-schedule) — opener, Christmas game, national-TV count, Austin/Paris/Manchester dates.
- [2026 NBA Playoffs schedule and series results](https://www.nba.com/news/2026-nba-playoffs-schedule) — Spurs' road through the West and Knicks' Finals result.
- [How the Knicks won the 2026 championship](https://www.nba.com/news/how-the-knicks-won-the-2026-nba-championship) — Finals framing and close-game context.
- [2025–26 NBA awards](https://www.nba.com/news/2025-2026-regular-season-awards) — Wembanyama DPOY, Keldon Johnson Sixth Man, and other award winners.
- [2025–26 All-NBA teams](https://www.nba.com/news/2025-26-all-nba-teams-announced) — Wembanyama First Team and contender star context.

## Analysis feeds

- [ESPN Spurs team page](https://www.espn.com/nba/team/_/name/sa/san-antonio-spurs) — public team identifiers and presentation layer for schedule, roster, boxscore, and play-by-play JSON used by the ingestion code.
- [Basketball Reference 2025–26 ratings](https://www.basketball-reference.com/leagues/NBA_2026_ratings.html) — adjusted team ratings.
- [Basketball Reference 2025–26 player per-game table](https://www.basketball-reference.com/leagues/NBA_2026_per_game.html) — rotation volume and production.
- [Basketball Reference 2025–26 advanced table](https://www.basketball-reference.com/leagues/NBA_2026_advanced.html) — player rate and impact features.
- [nba_api endpoint documentation](https://github.com/swar/nba_api/tree/master/docs/nba_api/stats/endpoints) — optional extension path for NBA Stats endpoints; the showcase uses cached ESPN/Basketball Reference snapshots because `stats.nba.com` can throttle automated requests.

## Notes

- ESPN abbreviates San Antonio as `SA`; Basketball Reference uses `SAS`. The ingestion layer normalizes identifiers at model boundaries.
- The published 2026–27 team schedule contains 80 assigned regular-season games at build time. Two NBA Cup flex dates remain TBD and are not silently imputed.
- Data should be refreshed politely and used subject to each source's terms.

