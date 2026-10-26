source(file.path("R", "bootstrap.R"))
players <- read_snapshot("nba_player_seasons_2022_26", root)
result <- player_archetypes(players)
readr::write_csv(result, file.path(root, "projects", "06_player_archetypes", "player_archetypes_r.csv"))
readr::write_csv(
  result |> dplyr::filter(.data$team == "SAS"),
  file.path(root, "projects", "06_player_archetypes", "spurs_archetypes_r.csv")
)
