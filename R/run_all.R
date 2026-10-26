source(file.path("R", "bootstrap.R"))
dir.create(file.path(root, "data", "processed_r"), recursive = TRUE, showWarnings = FALSE)

schedule <- read_snapshot("spurs_schedule_2026_27", root)
ratings <- read_snapshot("nba_team_ratings_2025_26", root)
stress <- schedule_stress(schedule, root)
readr::write_csv(stress, file.path(root, "data", "processed_r", "schedule_stress.csv"))

probabilities <- schedule_probabilities(stress, ratings)
readr::write_csv(probabilities, file.path(root, "data", "processed_r", "game_win_probabilities.csv"))

contenders <- ratings |> dplyr::slice_min(.data$rank, n = 12)
readr::write_csv(contenders, file.path(root, "data", "processed_r", "contender_ratings.csv"))

boxscores <- read_snapshot("spurs_player_boxscores_2025_26", root)
prior_schedule <- read_snapshot("spurs_schedule_2025_26", root)
readr::write_csv(rotation_pair_proxies(boxscores), file.path(root, "data", "processed_r", "pair_chemistry_proxies.csv"))
readr::write_csv(starter_unit_proxies(boxscores, prior_schedule), file.path(root, "data", "processed_r", "starter_unit_proxies.csv"))

impact <- wemby_game_impact(boxscores, prior_schedule)
readr::write_csv(impact$games, file.path(root, "data", "processed_r", "wemby_game_splits.csv"))
readr::write_csv(impact$summary, file.path(root, "data", "processed_r", "wemby_impact_summary.csv"))

plays <- read_snapshot("spurs_postseason_plays_2026", root)
finals_ids <- prior_schedule |>
  dplyr::filter(.data$season_type == "Postseason", .data$opponent == "NY") |>
  dplyr::pull(.data$game_id)
finals <- finals_clutch_profile(plays, finals_ids)
readr::write_csv(finals$detail, file.path(root, "data", "processed_r", "finals_play_by_play_enriched.csv"))
readr::write_csv(finals$summary, file.path(root, "data", "processed_r", "finals_lead_summary.csv"))

players <- read_snapshot("nba_player_seasons_2022_26", root)
archetypes <- player_archetypes(players)
readr::write_csv(archetypes, file.path(root, "data", "processed_r", "player_archetypes.csv"))
readr::write_csv(
  archetypes |> dplyr::filter(.data$team == "SAS"),
  file.path(root, "data", "processed_r", "spurs_archetypes.csv")
)

simulations <- simulate_schedule(probabilities)
odds <- contender_title_odds(ratings)
readr::write_csv(simulations$summary, file.path(root, "data", "processed_r", "schedule_simulation_summary.csv"))
readr::write_csv(simulations$distribution, file.path(root, "data", "processed_r", "schedule_win_distribution.csv"))
readr::write_csv(odds, file.path(root, "data", "processed_r", "contender_title_odds.csv"))

message("All seven R portfolio projects built in data/processed_r")
