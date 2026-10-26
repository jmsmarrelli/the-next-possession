local({
  project_library <- file.path(getwd(), ".Rlib")
  if (dir.exists(project_library)) {
    .libPaths(c(project_library, .libPaths()))
  }
  options(
    repos = c(CRAN = "https://cloud.r-project.org"),
    stringsAsFactors = FALSE
  )
})
