project_root <- normalizePath(".")
project_library <- file.path(project_root, ".Rlib")
dir.create(project_library, recursive = TRUE, showWarnings = FALSE)
.libPaths(c(project_library, .libPaths()))
options(repos = c(CRAN = "https://cloud.r-project.org"))

required_packages <- c(
  "dplyr", "lubridate", "purrr", "readr", "rlang", "tibble", "yaml", "testthat"
)
missing_packages <- required_packages[
  !vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing_packages) > 0) {
  install.packages(missing_packages, lib = project_library)
}

message(
  "R setup complete. Local library: ", project_library,
  "\nNext: source(\"R/rstudio_validate.R\")"
)
