# =============================================================================
# Minority Inclusion Support — CFA fit indices
# =============================================================================
# Two models:
#   (1) Pooled single-group CFA on all 2,263 respondents.
#       3 items, 1 factor → df = 0 (saturated). Reported for the record;
#       fit indices are degenerate by construction.
#   (2) Multi-group CFA across 4 cells (Estonian-2020, Russian-2020,
#       Estonian-2023, Russian-2023) at three invariance levels:
#         configural → metric → scalar.
#       Loadings/intercepts accumulate constraints; df > 0 for metric
#       and scalar, so CFI/TLI/RMSEA/SRMR become informative.
#
# Estimator: MLR (robust to non-normality), FIML for missing data.
# =============================================================================

suppressPackageStartupMessages({
  library(lavaan)
})

ROOT <- "/Users/brianwiggins/Desktop/Claude Code/EIM2"
df   <- read.csv(file.path(ROOT, "data/EIM_stacked.csv"), stringsAsFactors = FALSE)

# Build a 4-cell grouping variable for the multi-group model
df$cell <- paste(df$group, df$year, sep = "_")
df$cell <- factor(df$cell, levels = c("Estonian_2020", "Estonian_2023",
                                      "Russian_2020",  "Russian_2023"))

mis_model <- 'MIS =~ ms1 + ms2 + ms3'

fit_row <- function(fit, label) {
  fm <- fitMeasures(fit, c("chisq.scaled","df.scaled","pvalue.scaled",
                           "cfi.scaled","tli.scaled",
                           "rmsea.scaled","rmsea.ci.lower.scaled",
                           "rmsea.ci.upper.scaled","srmr"))
  data.frame(
    model  = label,
    chisq  = round(fm["chisq.scaled"], 3),
    df     = fm["df.scaled"],
    p      = round(fm["pvalue.scaled"], 4),
    CFI    = round(fm["cfi.scaled"], 4),
    TLI    = round(fm["tli.scaled"], 4),
    RMSEA  = round(fm["rmsea.scaled"], 4),
    RMSEA_lo = round(fm["rmsea.ci.lower.scaled"], 4),
    RMSEA_hi = round(fm["rmsea.ci.upper.scaled"], 4),
    SRMR   = round(fm["srmr"], 4),
    row.names = NULL
  )
}

# -----------------------------------------------------------------------------
# (1) Pooled single-group CFA — saturated by construction
# -----------------------------------------------------------------------------
cat("\n", strrep("=", 78), "\n", sep = "")
cat("(1) POOLED SINGLE-GROUP CFA — 2,263 respondents (all cells stacked)\n")
cat(strrep("=", 78), "\n\n", sep = "")

fit_pooled <- cfa(mis_model, data = df,
                  estimator = "MLR", missing = "fiml")

cat("--- Standardized loadings ---\n")
pe <- parameterEstimates(fit_pooled, standardized = TRUE)
loadings <- pe[pe$op == "=~", c("lhs","rhs","est","se","z","pvalue","std.all")]
num_cols <- sapply(loadings, is.numeric)
loadings[num_cols] <- lapply(loadings[num_cols], round, 3)
print(loadings, row.names = FALSE)

cat("\n--- Fit indices ---\n")
pooled_row <- fit_row(fit_pooled, "Pooled (1 group, df=0)")
print(pooled_row, row.names = FALSE)

cat("\nNote: 3 items × 1 factor = just-identified (df = 0).\n")
cat("Fit is saturated; CFI/TLI/RMSEA/SRMR are degenerate by construction.\n")


# -----------------------------------------------------------------------------
# (2) Multi-group CFA — 4 cells, configural / metric / scalar
# -----------------------------------------------------------------------------
cat("\n", strrep("=", 78), "\n", sep = "")
cat("(2) MULTI-GROUP CFA — 4 cells (Estonian_2020, Estonian_2023,\n")
cat("                                 Russian_2020,  Russian_2023)\n")
cat(strrep("=", 78), "\n\n", sep = "")

# Configural — same factor structure, all params free across cells
fit_conf <- cfa(mis_model, data = df, group = "cell",
                estimator = "MLR", missing = "fiml")

# Metric — loadings constrained equal across cells
fit_metric <- cfa(mis_model, data = df, group = "cell",
                  group.equal = c("loadings"),
                  estimator = "MLR", missing = "fiml")

# Scalar — loadings AND intercepts constrained equal across cells
fit_scalar <- cfa(mis_model, data = df, group = "cell",
                  group.equal = c("loadings", "intercepts"),
                  estimator = "MLR", missing = "fiml")

mg_table <- rbind(
  fit_row(fit_conf,   "Configural (loadings/intercepts free)"),
  fit_row(fit_metric, "Metric     (loadings equal)"),
  fit_row(fit_scalar, "Scalar     (loadings + intercepts equal)")
)
print(mg_table, row.names = FALSE)

cat("\n--- Likelihood-ratio comparisons (Satorra-Bentler scaled Δχ²) ---\n")
print(lavTestLRT(fit_conf, fit_metric, fit_scalar, method = "satorra.bentler.2001"))

cat("\nN per cell:\n")
print(table(df$cell))


# -----------------------------------------------------------------------------
# Save combined fit table
# -----------------------------------------------------------------------------
out <- rbind(pooled_row, mg_table)
write.table(out, file.path(ROOT, "code/_mis_cfa_fit.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE)
cat("\nWrote: code/_mis_cfa_fit.tsv\n")
