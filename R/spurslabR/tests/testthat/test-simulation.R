testthat::test_that("neutral series and tournament conserve probability", {
  ratings <- tibble::tibble(team = paste("Team", 1:12), rank = 1:12,
                           adjusted_net_rating = rep(0, 12))
  result <- contender_title_odds(ratings, simulations = 4000)
  testthat::expect_equal(sum(result$title_probability), 1)
  testthat::expect_equal(sum(result$finals_probability), 2)
  testthat::expect_lt(max(abs(result$title_probability - 1/12)), .03)
  testthat::expect_true(all(result$finals_probability <= 1))
  two <- contender_title_odds(ratings[1:2, ], contender_count = 2, simulations = 4000)
  testthat::expect_equal(two$finals_probability, c(1, 1))
  testthat::expect_lt(max(abs(two$title_probability - .5)), .03)
  # Real ratings contain a season 'wins' column. It must not mask local counts.
  with_wins <- dplyr::mutate(ratings, wins = 40:51)
  masked <- contender_title_odds(with_wins, simulations = 4000)
  testthat::expect_equal(masked$title_probability, result$title_probability)
  testthat::expect_equal(sum(masked$title_probability), 1)
})

testthat::test_that("invalid margin scale and probabilities fail explicitly", {
  testthat::expect_error(game_win_probability(0, 0))
  testthat::expect_error(game_win_probability(NA_real_))
  testthat::expect_error(simulate_schedule(tibble::tibble(win_probability = c(.5, NA))))
  testthat::expect_error(simulate_schedule(tibble::tibble(win_probability = .5), simulations = 1.5))
})
