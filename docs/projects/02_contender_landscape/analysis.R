source(file.path("R", "bootstrap.R"))
ratings <- read_snapshot("nba_team_ratings_2025_26", root)
contenders <- ratings |> dplyr::slice_min(.data$rank, n = 12)
readr::write_csv(contenders, file.path(root, "projects", "02_contender_landscape", "contender_ratings_r.csv"))
