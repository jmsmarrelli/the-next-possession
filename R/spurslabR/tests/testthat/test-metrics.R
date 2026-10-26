test_that("Wemby availability excludes other Spurs players", {
  boxscores <- data.frame(
    game_id = c(1, 2, 2),
    team = "SA",
    player = c("Victor Wembanyama", "Victor Wembanyama", "Other Spur"),
    minutes = c(30, 0, 28),
    points = c(25, 0, 12), rebounds = c(10, 0, 4), assists = c(4, 0, 2),
    blocks = c(3, 0, 0), plus_minus = c(8, 0, 2)
  )
  schedule <- data.frame(
    game_id = 1:2,
    team_score = c(120, 105), opponent_score = c(110, 108),
    result = c("W", "L")
  )

  summary <- wemby_game_impact(boxscores, schedule)$summary

  expect_equal(summary$games, c(1, 1))
  expect_equal(sort(summary$availability), c("Wemby out", "Wemby played"))
})

test_that("rotation pairs honor the requested team", {
  boxscores <- data.frame(
    game_id = c(1, 1, 1, 1),
    team = c("SA", "SA", "NY", "NY"),
    player = c("Spur A", "Spur B", "Knick A", "Knick B"),
    minutes = c(30, 28, 32, 29), plus_minus = c(5, 3, -5, -3),
    points = c(20, 15, 18, 16), assists = c(5, 4, 3, 2), turnovers = c(2, 1, 2, 2)
  )

  result <- rotation_pair_proxies(boxscores, team = "SA", min_games = 1)

  expect_equal(nrow(result), 1)
  expect_equal(result$player_a, "Spur A")
  expect_equal(result$player_b, "Spur B")
})

test_that("player archetypes honor the requested season", {
  players <- data.frame(
    season_end = c(rep(2026, 4), rep(2025, 3)),
    team = "SA", g = 40, mp = 20,
    pts = 1:7, ast = 2:8, trb = 3:9, three_pa = 4:10,
    three_p_pct = seq(.30, .36, length.out = 7), ts_pct = seq(.50, .62, length.out = 7),
    usg_pct = 15:21, ast_pct = 10:16, blk_pct = 1:7, stl_pct = 2:8,
    obpm = -3:3, dbpm = 3:-3, bpm = 0:6
  )

  result <- player_archetypes(players, season_end = 2026, clusters = 2)

  expect_equal(nrow(result), 4)
  expect_equal(unique(result$season_end), 2026)
})
