#' Game win probability under a normal margin model
#' @export
game_win_probability <- function(expected_margin, margin_sd = 12) {
  stopifnot(length(margin_sd) == 1, is.finite(margin_sd), margin_sd > 0,
            all(is.finite(expected_margin)))
  stats::pnorm(expected_margin / margin_sd)
}

team_abbreviations <- c(
  "Atlanta Hawks" = "ATL", "Boston Celtics" = "BOS", "Brooklyn Nets" = "BKN",
  "Charlotte Hornets" = "CHA", "Chicago Bulls" = "CHI", "Cleveland Cavaliers" = "CLE",
  "Dallas Mavericks" = "DAL", "Denver Nuggets" = "DEN", "Detroit Pistons" = "DET",
  "Golden State Warriors" = "GS", "Houston Rockets" = "HOU", "Indiana Pacers" = "IND",
  "Los Angeles Clippers" = "LAC", "Los Angeles Lakers" = "LAL", "Memphis Grizzlies" = "MEM",
  "Miami Heat" = "MIA", "Milwaukee Bucks" = "MIL", "Minnesota Timberwolves" = "MIN",
  "New Orleans Pelicans" = "NO", "New York Knicks" = "NY", "Oklahoma City Thunder" = "OKC",
  "Orlando Magic" = "ORL", "Philadelphia 76ers" = "PHI", "Phoenix Suns" = "PHX",
  "Portland Trail Blazers" = "POR", "Sacramento Kings" = "SAC", "San Antonio Spurs" = "SA",
  "Toronto Raptors" = "TOR", "Utah Jazz" = "UTAH", "Washington Wizards" = "WSH"
)

#' Per-game schedule probabilities
#' @export
schedule_probabilities <- function(
  schedule_features,
  ratings,
  home_court_points = 2.2,
  margin_sd = 12,
  prior_rating_weight = 0.72
) {
  rating_frame <- ratings %>%
    dplyr::mutate(
      abbreviation = unname(team_abbreviations[.data$team]),
      forecast_rating = .data$adjusted_net_rating * prior_rating_weight
    )
  spurs_rating <- rating_frame$forecast_rating[rating_frame$abbreviation == "SA"][[1]]
  joined <- schedule_features %>%
    dplyr::left_join(
      rating_frame %>% dplyr::select(opponent = "abbreviation", opponent_rating = "forecast_rating"),
      by = "opponent"
    )
  if (any(!is.finite(joined$opponent_rating))) stop("Missing or invalid opponent ratings")
  joined %>%
    dplyr::mutate(
      home_adjustment = dplyr::case_when(
        .data$is_neutral ~ 0,
        .data$is_home ~ home_court_points,
        TRUE ~ -home_court_points
      ),
      rest_adjustment = pmin(pmax(.data$rest_days - 1, -1), 2) * 0.35,
      travel_adjustment = -pmin(.data$travel_miles / 1000, 2.5) * 0.25,
      stress_adjustment = -.data$stress_score / 100 * 1.25,
      expected_margin = spurs_rating - .data$opponent_rating + .data$home_adjustment +
        .data$rest_adjustment + .data$travel_adjustment + .data$stress_adjustment,
      win_probability = game_win_probability(.data$expected_margin, margin_sd)
    )
}

#' Monte Carlo schedule simulation
#' @export
simulate_schedule <- function(probabilities, simulations = 25000, seed = 210) {
  set.seed(seed)
  p <- probabilities$win_probability
  if (!length(p) || any(!is.finite(p)) || any(p < 0 | p > 1) || simulations <= 0 || simulations != as.integer(simulations)) {
    stop("Supply finite probabilities in [0, 1] and a positive simulation count")
  }
  draws <- matrix(stats::runif(simulations * length(p)), nrow = simulations)
  wins <- rowSums(sweep(draws, 2, p, `<`))
  list(
    summary = tibble::tibble(
      metric = c("mean_wins", "median_wins", "p10_wins", "p90_wins", "prob_50_plus", "prob_55_plus", "prob_60_plus"),
      value = c(
        mean(wins), stats::median(wins), stats::quantile(wins, .1), stats::quantile(wins, .9),
        mean(wins >= 50), mean(wins >= 55), mean(wins >= 60)
      )
    ),
    distribution = tibble::as_tibble(table(wins)) %>%
      dplyr::transmute(wins = as.integer(as.character(.data$wins)), simulations = .data$n, probability = .data$n / simulations)
  )
}

#' Illustrative neutral-site tournament, not NBA championship odds
#' @export
contender_title_odds <- function(ratings, contender_count = 12, simulations = 50000, seed = 210,
                                 prior_weight = .72, margin_sd = 12) {
  stopifnot(contender_count >= 2, contender_count <= nrow(ratings), simulations > 0,
            simulations == as.integer(simulations), is.finite(margin_sd), margin_sd > 0)
  contenders <- ratings %>%
    dplyr::slice_min(.data$rank, n = contender_count, with_ties = FALSE) %>%
    dplyr::mutate(forecast_rating = .data$adjusted_net_rating * prior_weight)
  stopifnot(!anyDuplicated(contenders$team), all(is.finite(contenders$forecast_rating)))
  n <- nrow(contenders)
  game_p <- stats::pnorm(outer(contenders$forecast_rating, contenders$forecast_rating, `-`) / margin_sd)
  series_p <- matrix(stats::pbinom(3, 7, as.vector(game_p), lower.tail = FALSE), n, n)
  champion_counts <- finalist_counts <- numeric(n)
  set.seed(seed)
  for (iteration in seq_len(simulations)) {
    active <- sample.int(n)
    while (length(active) > 1) {
      if (length(active) == 2) finalist_counts[active] <- finalist_counts[active] + 1
      next_round <- integer()
      if (length(active) %% 2) {
        bye_position <- sample.int(length(active), 1)
        next_round <- active[bye_position]
        active <- active[-bye_position]
      }
      for (i in seq(1, length(active), by = 2)) {
        a <- active[i]; b <- active[i + 1]
        next_round <- c(next_round, if (stats::runif(1) < series_p[a, b]) a else b)
      }
      active <- next_round
    }
    champion_counts[active] <- champion_counts[active] + 1
  }
  contenders %>%
    dplyr::mutate(finals_probability = .env$finalist_counts / .env$simulations,
                  title_probability = .env$champion_counts / .env$simulations,
                  title_odds_rank = dplyr::min_rank(dplyr::desc(.data$title_probability))) %>%
    dplyr::arrange(dplyr::desc(.data$title_probability))
}
