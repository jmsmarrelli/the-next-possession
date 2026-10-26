\name{spurslabR}
\alias{spurslabR}
\alias{contender_title_odds}
\alias{finals_clutch_profile}
\alias{game_win_probability}
\alias{haversine_miles}
\alias{load_settings}
\alias{player_archetypes}
\alias{read_snapshot}
\alias{rotation_pair_proxies}
\alias{schedule_probabilities}
\alias{schedule_stress}
\alias{simulate_schedule}
\alias{starter_unit_proxies}
\alias{wemby_game_impact}
\title{Spurs-centered NBA analytics functions}
\description{
Reusable R implementations for the seven projects in The Next Possession,
including schedule engineering, boxscore proxies, player archetypes,
play-by-play summaries, and preseason simulations.
}
\usage{
haversine_miles(lat1, lon1, lat2, lon2)

load_settings(root = ".")

read_snapshot(name, root = ".")

schedule_stress(schedule, root = ".")

rotation_pair_proxies(boxscores, team = "SA", min_games = 8)

starter_unit_proxies(boxscores, schedule, team = "SA")

wemby_game_impact(boxscores, schedule, player = "Victor Wembanyama")

finals_clutch_profile(plays, finals_game_ids)

player_archetypes(players, season_end = 2026, clusters = 8, seed = 210)

game_win_probability(expected_margin, margin_sd = 12)

schedule_probabilities(schedule_features, ratings,
  home_court_points = 2.2, margin_sd = 12, prior_rating_weight = 0.72)

simulate_schedule(probabilities, simulations = 25000, seed = 210)

contender_title_odds(ratings, contender_count = 12,
  simulations = 50000, seed = 210, prior_weight = 0.72, margin_sd = 12)
}
\arguments{
  \item{lat1, lon1, lat2, lon2}{Numeric latitude and longitude vectors.}
  \item{root}{Portfolio repository root.}
  \item{name}{Snapshot base name.}
  \item{schedule, schedule_features}{Schedule data frames.}
  \item{boxscores}{Player-game boxscore data.}
  \item{team}{Team abbreviation.}
  \item{min_games}{Minimum shared-game threshold.}
  \item{player}{Player name.}
  \item{plays}{Play-by-play data frame.}
  \item{finals_game_ids}{Finals game identifiers.}
  \item{players}{League player-season data.}
  \item{season_end}{Season-ending year.}
  \item{clusters}{Number of k-means clusters.}
  \item{seed}{Random seed.}
  \item{expected_margin}{Expected scoring margin.}
  \item{margin_sd}{Standard deviation of scoring margin.}
  \item{ratings}{Team ratings data frame.}
  \item{home_court_points}{Home-court adjustment in points.}
  \item{prior_weight}{Rating shrinkage for the illustrative neutral tournament, not NBA title odds.}
  \item{prior_rating_weight}{Weight applied to the prior-season rating.}
  \item{probabilities}{Per-game win probability data.}
  \item{simulations}{Number of simulation draws.}
  \item{contender_count}{Number of leading teams to retain.}
}
\value{
A numeric vector, data frame, or named list of analysis tables, depending on
the function. See the paired project scripts for complete workflows.
}
\examples{
haversine_miles(29.4241, -98.4936, 40.7128, -74.0060)
game_win_probability(2.5)
}
