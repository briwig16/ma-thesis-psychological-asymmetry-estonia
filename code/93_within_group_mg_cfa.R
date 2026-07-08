# =============================================================================
# Within-group multi-group CFA — 2020 vs 2023, separately for Estonians and
# Russians. For each composite × ethnic group, fits configural / metric /
# scalar invariance models with year as the grouping variable.
#
# SD: General Out-group is skipped (item set differs across waves: 3 items
# in 2020 vs. 6 items in 2023; longitudinal multi-group CFA on shared items
# is not defined).
#
# Estimator: MLR. Missing data: FIML.
# Output: code/_within_group_mg_cfa.tsv
# =============================================================================

suppressPackageStartupMessages({
  library(lavaan)
})

ROOT <- "/Users/brianwiggins/Desktop/Claude Code/EIM2"
d <- read.csv(file.path(ROOT, "data/EIM_stacked.csv"), stringsAsFactors = FALSE)

specs <- list(
  list(name = "Superordinate Identity",
       items = c("si1","si2","si3")),
  list(name = "SD: Primary Out-group",
       items = c("sdp1","sdp2","sdp3")),
  list(name = "Comparative Opportunity Assessment",
       items = paste0("co", 1:12)),
  list(name = "Belief in Inevitable Conflict",
       items = c("bic1","bic2","bic3","bic4")),
  list(name = "Minority Support Inclusion",
       items = c("ms1","ms2","ms3")),
  list(name = "Contact: Estonian Speakers",
       items = paste0("ce", 1:6)),
  list(name = "Contact: Russian Speakers",
       items = paste0("cr", 1:6))
)

fit_row <- function(fit, comp, group_label, level) {
  fm <- fitMeasures(fit, c("chisq.scaled","df.scaled","pvalue.scaled",
                           "cfi.scaled","tli.scaled",
                           "rmsea.scaled","srmr"))
  data.frame(
    composite = comp, group = group_label, level = level,
    chisq = unname(fm["chisq.scaled"]),
    df    = unname(fm["df.scaled"]),
    p     = unname(fm["pvalue.scaled"]),
    cfi   = unname(fm["cfi.scaled"]),
    tli   = unname(fm["tli.scaled"]),
    rmsea = unname(fm["rmsea.scaled"]),
    srmr  = unname(fm["srmr"]),
    d_chisq = NA_real_, d_df = NA_integer_, d_p = NA_real_,
    d_cfi = NA_real_,   d_rmsea = NA_real_,
    row.names = NULL
  )
}

out <- list()

for (s in specs) {
  model <- paste0("F =~ ", paste(s$items, collapse = " + "))

  for (grp in c("Estonian", "Russian")) {
    sub <- d[d$group == grp, c("year", s$items)]

    fit_c <- try(cfa(model, data = sub, group = "year",
                     missing = "fiml", estimator = "MLR"), silent = TRUE)
    fit_m <- try(cfa(model, data = sub, group = "year",
                     group.equal = "loadings",
                     missing = "fiml", estimator = "MLR"), silent = TRUE)
    fit_s <- try(cfa(model, data = sub, group = "year",
                     group.equal = c("loadings","intercepts"),
                     missing = "fiml", estimator = "MLR"), silent = TRUE)

    row_c <- if (!inherits(fit_c, "try-error")) fit_row(fit_c, s$name, grp, "configural") else NULL
    row_m <- if (!inherits(fit_m, "try-error")) fit_row(fit_m, s$name, grp, "metric")     else NULL
    row_s <- if (!inherits(fit_s, "try-error")) fit_row(fit_s, s$name, grp, "scalar")     else NULL

    # Δχ² via Satorra-Bentler scaled difference test (lavTestLRT)
    if (!is.null(row_c) && !is.null(row_m)) {
      lrt_cm <- try(lavTestLRT(fit_c, fit_m, method = "satorra.bentler.2001"),
                    silent = TRUE)
      if (!inherits(lrt_cm, "try-error")) {
        row_m$d_chisq <- lrt_cm[2, "Chisq diff"]
        row_m$d_df    <- lrt_cm[2, "Df diff"]
        row_m$d_p     <- lrt_cm[2, "Pr(>Chisq)"]
      }
      row_m$d_cfi   <- row_m$cfi   - row_c$cfi
      row_m$d_rmsea <- row_m$rmsea - row_c$rmsea
    }
    if (!is.null(row_m) && !is.null(row_s)) {
      lrt_ms <- try(lavTestLRT(fit_m, fit_s, method = "satorra.bentler.2001"),
                    silent = TRUE)
      if (!inherits(lrt_ms, "try-error")) {
        row_s$d_chisq <- lrt_ms[2, "Chisq diff"]
        row_s$d_df    <- lrt_ms[2, "Df diff"]
        row_s$d_p     <- lrt_ms[2, "Pr(>Chisq)"]
      }
      row_s$d_cfi   <- row_s$cfi   - row_m$cfi
      row_s$d_rmsea <- row_s$rmsea - row_m$rmsea
    }

    if (!is.null(row_c)) out[[length(out) + 1]] <- row_c
    if (!is.null(row_m)) out[[length(out) + 1]] <- row_m
    if (!is.null(row_s)) out[[length(out) + 1]] <- row_s
  }
}

result <- do.call(rbind, out)
write.table(result, file.path(ROOT, "code/_within_group_mg_cfa.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE)

cat("Wrote: code/_within_group_mg_cfa.tsv (", nrow(result), " rows)\n", sep = "")
print(result, row.names = FALSE)
