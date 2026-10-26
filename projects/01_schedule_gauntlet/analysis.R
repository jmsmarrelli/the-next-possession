source(file.path("R", "bootstrap.R"))
schedule <- read_snapshot("spurs_schedule_2026_27", root)
result <- schedule_stress(schedule, root)
readr::write_csv(result, file.path(root, "projects", "01_schedule_gauntlet", "schedule_stress_r.csv"))
