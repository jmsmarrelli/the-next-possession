root <- normalizePath(".")
local_library <- file.path(root, ".Rlib")
if (dir.exists(local_library)) {
  .libPaths(c(local_library, .libPaths()))
}

required_packages <- c("dplyr", "lubridate", "purrr", "readr", "rlang", "tibble", "yaml")
missing_packages <- required_packages[
  !vapply(required_packages, requireNamespace, logical(1), quietly = TRUE)
]
if (length(missing_packages) > 0) {
  stop(
    "Missing R packages: ", paste(missing_packages, collapse = ", "),
    ". Follow the local-library setup in README.md."
  )
}

suppressPackageStartupMessages(library(dplyr))
r_files <- list.files(file.path(root, "R", "spurslabR", "R"), pattern = "[.]R$", full.names = TRUE)
invisible(lapply(r_files, source))
