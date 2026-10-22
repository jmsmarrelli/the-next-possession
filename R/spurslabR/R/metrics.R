#' Boxscore co-appearance chemistry proxies
#' @export
rotation_pair_proxies <- function(boxscores, team = "SA", min_games = 8) {
  played <- boxscores %>%
    dplyr::filter(.data$team == .env$team, .data$minutes > 0)
  pair_games <- played %>%
    dplyr::select(dplyr::all_of(c(
      "game_id", "player", "minutes", "plus_minus", "points", "assists", "turnovers"
    ))) %>%
    dplyr::inner_join(
      played,
      by = "game_id",
      suffix = c("_a", "_b"),
      relationship = "many-to-many"
    ) %>%
    dplyr::filter(.data$player_a < .data$player_b) %>%
    dplyr::transmute(
      .data$game_id,
      player_a = .data$player_a,
      player_b = .data$player_b,
      shared_minutes_proxy = pmin(.data$minutes_a, .data$minutes_b),
      pair_plus_minus_proxy = rowMeans(cbind(.data$plus_minus_a, .data$plus_minus_b), na.rm = TRUE),
      pair_points = .data$points_a + .data$points_b,
      pair_assists = .data$assists_a + .data$assists_b,
      pair_turnovers = .data$turnovers_a + .data$turnovers_b
    )
  pair_games %>%
    dplyr::group_by(.data$player_a, .data$player_b) %>%
    dplyr::summarise(
      games_together = dplyr::n_distinct(.data$game_id),
      shared_minutes_proxy = sum(.data$shared_minutes_proxy, na.rm = TRUE),
      avg_pair_plus_minus = mean(.data$pair_plus_minus_proxy, na.rm = TRUE),
      avg_combined_points = mean(.data$pair_points, na.rm = TRUE),
      avg_combined_assists = mean(.data$pair_assists, na.rm = TRUE),
      avg_combined_turnovers = mean(.data$pair_turnovers, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    dplyr::filter(.data$games_together >= min_games) %>%
    dplyr::mutate(
      assist_turnover_ratio = .data$avg_combined_assists / dplyr::na_if(.data$avg_combined_turnovers, 0),
      reliability = pmin(.data$games_together / 40, 1),
      chemistry_index = round(
        .data$reliability * (0.65 * .data$avg_pair_plus_minus + 2 * (.data$assist_turnover_ratio - 1.5)),
        2
      )
    ) %>%
    dplyr::arrange(dplyr::desc(.data$chemistry_index)) %>%
    dplyr::select(-dplyr::all_of("reliability"))
}

#' Starting-unit boxscore proxies
#' @export
starter_unit_proxies <- function(boxscores, schedule, team = "SA") {
  units <- boxscores %>%
    dplyr::filter(.data$team == .env$team, .data$starter, .data$minutes > 0) %>%
    dplyr::arrange(.data$game_id, .data$player) %>%
    dplyr::group_by(.data$game_id) %>%
    dplyr::summarise(
      starter_unit = paste(sort(.data$player), collapse = " \u00b7 "),
      starter_count = dplyr::n(),
      .groups = "drop"
    )
  schedule %>%
    dplyr::mutate(margin = .data$team_score - .data$opponent_score) %>%
    dplyr::right_join(units, by = "game_id") %>%
    dplyr::filter(.data$starter_count == 5) %>%
    dplyr::group_by(.data$starter_unit) %>%
    dplyr::summarise(
      games = dplyr::n_distinct(.data$game_id),
      wins = sum(.data$result == "W", na.rm = TRUE),
      avg_game_margin = mean(.data$margin, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    dplyr::mutate(win_pct = .data$wins / .data$games) %>%
    dplyr::arrange(dplyr::desc(.data$games), dplyr::desc(.data$avg_game_margin))
}

#' Wembanyama game-level availability split
#' @export
wemby_game_impact <- function(boxscores, schedule, player = "Victor Wembanyama") {
  player_games <- boxscores %>%
    dplyr::filter(.data$team == "SA", .data$player == .env$player) %>%
    dplyr::mutate(available = dplyr::coalesce(.data$minutes, 0) > 0) %>%
    dplyr::select(dplyr::all_of(c(
      "game_id", "available", "minutes", "points", "rebounds", "assists", "blocks", "plus_minus"
    )))
  games <- schedule %>%
    dplyr::mutate(margin = .data$team_score - .data$opponent_score) %>%
    dplyr::left_join(player_games, by = "game_id") %>%
    dplyr::mutate(available = dplyr::coalesce(.data$available, FALSE))
  summary <- games %>%
    dplyr::group_by(.data$available) %>%
    dplyr::summarise(
      games = dplyr::n_distinct(.data$game_id),
      win_pct = mean(.data$result == "W", na.rm = TRUE),
      avg_margin = mean(.data$margin, na.rm = TRUE),
      team_points = mean(.data$team_score, na.rm = TRUE),
      opponent_points = mean(.data$opponent_score, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    dplyr::mutate(availability = ifelse(.data$available, "Wemby played", "Wemby out")) %>%
    dplyr::select(-dplyr::all_of("available"))
  list(games = games, summary = summary)
}

#' Finals clutch-state profile
#' @export
finals_clutch_profile <- function(plays, finals_game_ids) {
  detail <- plays %>%
    dplyr::filter(as.character(.data$game_id) %in% as.character(finals_game_ids)) %>%
    dplyr::mutate(
      spurs_margin = ifelse(
        .data$home_team == "SA",
        .data$home_score - .data$away_score,
        .data$away_score - .data$home_score
      ),
      spurs_win_probability = ifelse(
        .data$home_team == "SA", .data$home_win_probability, 1 - .data$home_win_probability
      ),
      clutch = .data$period == 4 & .data$clock_seconds <= 300 & abs(.data$spurs_margin) <= 5
    )
  summary <- detail %>%
    dplyr::arrange(.data$game_id, .data$sequence) %>%
    dplyr::group_by(.data$game_id) %>%
    dplyr::summarise(
      max_spurs_lead = max(.data$spurs_margin, na.rm = TRUE),
      final_margin = dplyr::last(stats::na.omit(.data$spurs_margin)),
      lead_surrendered = .data$max_spurs_lead - .data$final_margin,
      peak_spurs_win_probability = max(.data$spurs_win_probability, na.rm = TRUE),
      clutch_plays = sum(.data$clutch, na.rm = TRUE),
      clutch_scoring_plays = sum(.data$clutch & .data$scoring_play, na.rm = TRUE),
      .groups = "drop"
    )
  list(detail = detail, summary = summary)
}

#' Rotation-player archetypes
#' @export
player_archetypes <- function(players, season_end = 2026, clusters = 8, seed = 210) {
  features <- c(
    "pts", "ast", "trb", "three_pa", "three_p_pct", "ts_pct",
    "usg_pct", "ast_pct", "blk_pct", "stl_pct", "obpm", "dbpm"
  )
  frame <- players %>%
    dplyr::filter(
      .data$season_end == .env$season_end,
      .data$team != "TOT",
      .data$g >= 30,
      .data$mp >= 15
    )
  values <- frame[, features]
  values[] <- lapply(values, function(column) {
    column[is.na(column)] <- stats::median(column, na.rm = TRUE)
    column
  })
  set.seed(seed)
  fit <- stats::kmeans(scale(values), centers = clusters, nstart = 30)
  frame$cluster <- fit$cluster - 1L
  centroids <- stats::aggregate(frame[, features], list(cluster = frame$cluster), mean)
  remaining <- centroids$cluster
  labels <- stats::setNames(rep(NA_character_, nrow(centroids)), centroids$cluster)
  ranking_rules <- c(
    "Primary engines" = "ast_pct",
    "Volume creators" = "pts",
    "Rim protectors" = "blk_pct",
    "Two-way stars" = "dbpm",
    "Movement shooters" = "three_pa",
    "Connective wings" = "ast",
    "Interior finishers" = "trb",
    "Low-usage defenders" = "stl_pct"
  )
  for (label in names(ranking_rules)) {
    if (length(remaining) == 0) break
    candidates <- centroids[centroids$cluster %in% remaining, , drop = FALSE]
    cluster <- candidates$cluster[which.max(candidates[[ranking_rules[[label]]]])]
    labels[[as.character(cluster)]] <- label
    remaining <- setdiff(remaining, cluster)
  }
  frame$archetype <- unname(labels[as.character(frame$cluster)])
  frame %>% dplyr::arrange(.data$archetype, dplyr::desc(.data$bpm))
}
