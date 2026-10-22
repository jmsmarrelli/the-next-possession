#' Load portfolio settings
#' @export
load_settings <- function(root = ".") {
  yaml::read_yaml(file.path(root, "config", "settings.yml"))
}

#' Read an analysis-ready snapshot
#' @export
read_snapshot <- function(name, root = ".") {
  parquet <- file.path(root, "data", "processed", paste0(name, ".parquet"))
  csv <- file.path(root, "data", "snapshots", paste0(name, ".csv"))
  if (file.exists(parquet) && requireNamespace("arrow", quietly = TRUE)) {
    return(arrow::read_parquet(parquet))
  }
  if (file.exists(csv)) {
    return(readr::read_csv(csv, show_col_types = FALSE))
  }
  stop("Missing snapshot ", name, "; run the Python data bootstrap first.")
}
