source(file.path("R", "bootstrap.R"))

schedule <- read_snapshot("spurs_schedule_2026_27", root)
ratings <- read_snapshot("nba_team_ratings_2025_26", root)
stress <- schedule_stress(schedule, root)
probabilities <- schedule_probabilities(stress, ratings)

stopifnot(
  nrow(schedule) == 80,
  nrow(stress) == nrow(schedule),
  all(is.finite(stress$stress_score)),
  all(probabilities$win_probability >= 0 & probabilities$win_probability <= 1),
  dplyr::n_distinct(ratings$team) == 30
)

testthat::test_dir(
  file.path(root, "R", "spurslabR", "tests", "testthat"),
  env = globalenv(),
  reporter = "summary"
)

message(
  "RStudio validation passed: ", nrow(schedule), " assigned games, ",
  sum(stress$back_to_back), " back-to-backs, and ", nrow(ratings), " team ratings."
)
