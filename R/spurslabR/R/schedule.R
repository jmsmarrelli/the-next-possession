#' Great-circle distance in miles
#' @export
haversine_miles <- function(lat1, lon1, lat2, lon2) {
  radius <- 3958.7613
  to_rad <- pi / 180
  phi1 <- lat1 * to_rad
  phi2 <- lat2 * to_rad
  dphi <- (lat2 - lat1) * to_rad
  dlambda <- (lon2 - lon1) * to_rad
  a <- sin(dphi / 2)^2 + cos(phi1) * cos(phi2) * sin(dlambda / 2)^2
  radius * 2 * atan2(sqrt(a), sqrt(1 - a))
}

games_in_window <- function(dates, days) {
  purrr::map_int(seq_along(dates), function(i) {
    delta <- as.numeric(difftime(dates[i], dates[seq_len(i)], units = "days"))
    sum(delta >= 0 & delta < days, na.rm = TRUE)
  })
}

#' Engineer travel and rest schedule stress
#' @export
schedule_stress <- function(schedule, root = ".") {
  venues <- readr::read_csv(file.path(root, "config", "venues.csv"), show_col_types = FALSE)
  parsed_date_utc <- if (inherits(schedule$date_utc, "POSIXt")) {
    as.POSIXct(schedule$date_utc, tz = "UTC")
  } else {
    lubridate::ymd_hms(schedule$date_utc, quiet = TRUE, tz = "UTC")
  }
  if (anyNA(parsed_date_utc)) {
    stop("One or more schedule timestamps could not be parsed")
  }
  x <- schedule %>%
    dplyr::mutate(
      date_utc = parsed_date_utc,
      date = as.Date(
        lubridate::with_tz(.data$date_utc, "America/Chicago"),
        tz = "America/Chicago"
      )
    ) %>%
    dplyr::arrange(.data$date_utc) %>%
    dplyr::left_join(venues, by = "city")
  if (any(is.na(x$latitude) | is.na(x$longitude))) {
    stop("One or more schedule cities are missing from config/venues.csv")
  }
  x <- x %>%
    dplyr::mutate(
      rest_days = pmax(as.numeric(.data$date - dplyr::lag(.data$date)) - 1, 0),
      rest_days = dplyr::if_else(is.na(.data$rest_days), 3, .data$rest_days),
      back_to_back = .data$rest_days == 0,
      games_in_4 = games_in_window(.data$date, 4),
      games_in_7 = games_in_window(.data$date, 7),
      three_in_four = .data$games_in_4 >= 3,
      five_in_seven = .data$games_in_7 >= 5,
      previous_latitude = dplyr::lag(.data$latitude),
      previous_longitude = dplyr::lag(.data$longitude),
      travel_miles = haversine_miles(
        .data$previous_latitude, .data$previous_longitude, .data$latitude, .data$longitude
      ),
      travel_miles = dplyr::if_else(is.na(.data$travel_miles), 0, .data$travel_miles),
      time_zones_crossed = abs(.data$utc_offset_hours - dplyr::lag(.data$utc_offset_hours)),
      time_zones_crossed = dplyr::if_else(is.na(.data$time_zones_crossed), 0, .data$time_zones_crossed),
      international = .data$country != "USA",
      stress_score = round(
        28 * .data$back_to_back +
          14 * .data$three_in_four +
          11 * .data$five_in_seven +
          22 * pmin(.data$travel_miles / 2200, 1.5) +
          8 * pmin(.data$time_zones_crossed, 3) / 3 +
          12 * pmax(0, 2 - .data$rest_days) / 2 +
          5 * .data$international,
        1
      ),
      stress_percentile = round(dplyr::percent_rank(.data$stress_score) * 100),
      stress_tier = cut(
        .data$stress_percentile,
        breaks = c(-Inf, 50, 75, 90, Inf),
        labels = c("Routine", "Elevated", "Hard", "Red alert")
      )
    ) %>%
    dplyr::select(-dplyr::starts_with("previous_"))
  x
}
