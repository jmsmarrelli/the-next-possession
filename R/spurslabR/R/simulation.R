#' Game win probability under a normal margin model
#' @export
game_win_probability <- function(expected_margin, margin_sd = 12) {
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
  schedule_features %>%
    dplyr::left_join(
      rating_frame %>% dplyr::select(opponent = "abbreviation", opponent_rating = "forecast_rating"),
      by = "opponent"
    ) %>%
    dplyr::mutate(
      opponent_rating = dplyr::coalesce(.data$opponent_rating, stats::median(rating_frame$forecast_rating)),
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
  if (any(!is.finite(p))) {
    stop("All schedule win probabilities must be finite before simulation")
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

#' Compact contender title-odds baseline
#' @export
contender_title_odds <- function(ratings, contender_count = 12, simulations = 50000, seed = 210) {
  contenders <- ratings %>%
    dplyr::slice_min(.data$rank, n = contender_count) %>%
    dplyr::mutate(forecast_rating = .data$adjusted_net_rating * .72)
  # Bradley-Terry approximation for a four-series title path. This mirrors the
  # Python model's purpose while keeping the R implementation dependency-light.
  strength <- exp(contenders$forecast_rating / 12)
  path_probability <- purrr::map_dbl(seq_along(strength), function(i) {
    opponents <- strength[-i]
    single_series <- strength[i] / (strength[i] + opponents)
    mean(single_series)^4
  })
  contenders %>%
    dplyr::mutate(
      path_probability = path_probability,
      title_probability = .data$path_probability / sum(.data$path_probability),
      title_odds_rank = dplyr::min_rank(dplyr::desc(.data$title_probability))
    ) %>%
    dplyr::arrange(.data$title_odds_rank)
}
