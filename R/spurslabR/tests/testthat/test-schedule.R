test_that("haversine is symmetric and zero at origin", {
  expect_equal(haversine_miles(29.4241, -98.4936, 29.4241, -98.4936), 0)
  forward <- haversine_miles(29.4241, -98.4936, 40.7128, -74.0060)
  reverse <- haversine_miles(40.7128, -74.0060, 29.4241, -98.4936)
  expect_equal(forward, reverse)
  expect_gt(forward, 1500)
})

test_that("midnight UTC games preserve their Central calendar dates", {
  temp_root <- tempfile("spurslabR-")
  dir.create(file.path(temp_root, "config"), recursive = TRUE)
  utils::write.csv(
    data.frame(
      city = "San Antonio", state = "TX", country = "USA",
      latitude = 29.4241, longitude = -98.4936, utc_offset_hours = -6
    ),
    file.path(temp_root, "config", "venues.csv"),
    row.names = FALSE
  )
  schedule <- data.frame(
    game_id = 1:3,
    date_utc = as.POSIXct(
      c("2026-10-21 01:30:00", "2026-10-25 00:00:00", "2026-10-28 00:00:00"),
      tz = "UTC"
    ),
    city = "San Antonio"
  )

  result <- schedule_stress(schedule, temp_root)

  expect_equal(as.character(result$date), c("2026-10-20", "2026-10-24", "2026-10-27"))
  expect_equal(result$rest_days, c(3, 3, 2))
  expect_true(all(is.finite(result$stress_score)))
})
