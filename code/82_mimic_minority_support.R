# =============================================================================
# MIMIC Model — Minority Inclusion Support
# =============================================================================
# Multiple Indicators, Multiple Causes (MIMIC) model on the stacked dataset.
#
# Indicators (3 items, scale 1-4, lower = more supportive of inclusion):
#   ms1, ms2, ms3
#
# Causes (covariates):
#   ethnicity      0 = Estonian, 1 = Russian
#   year           0 = 2020,     1 = 2023
#   eth_year_int   ethnicity × year (= 1 only for Russians in 2023)
#
# Procedure:
#   STEP 1+2: Baseline MIMIC model (no direct paths)
#       F =~ ms1 + ms2 + ms3
#       F  ~ ethnicity + year + eth_year_int
#
#   STEP 3:   DIF check — modification indices for direct paths from
#             ethnicity to each item; also explicit per-item LRT by adding
#             one direct path at a time.
#
#   STEP 4:   Final MIMIC with DIF-correction paths included for any item
#             flagged in Step 3, plus full parameter estimates.
# =============================================================================

suppressPackageStartupMessages({
  library(lavaan)
})

ROOT <- "/Users/brianwiggins/Desktop/Claude Code/EIM2"

d <- read.csv(file.path(ROOT, "data/EIM_stacked.csv"), stringsAsFactors = FALSE)

# Build covariates
d$ethnicity    <- d$group_num                     # 0 Est, 1 Rus
d$year_bin     <- ifelse(d$year == 2023, 1L, 0L)  # 0 = 2020, 1 = 2023
d$eth_year_int <- d$ethnicity * d$year_bin

# Keep only the columns we need
d <- d[, c("ethnicity", "year_bin", "eth_year_int", "ms1", "ms2", "ms3")]

# Drop rows missing all three indicators (uninformative for the latent factor)
d <- d[rowSums(!is.na(d[, c("ms1","ms2","ms3")])) > 0, ]

cat("MIMIC data summary:\n")
cat(sprintf("  N rows = %d\n", nrow(d)))
cat(sprintf("  ethnicity:    0=Est %d, 1=Rus %d\n",
            sum(d$ethnicity == 0), sum(d$ethnicity == 1)))
cat(sprintf("  year_bin:     0=2020 %d, 1=2023 %d\n",
            sum(d$year_bin == 0), sum(d$year_bin == 1)))
cat(sprintf("  eth_year_int: 1 (Russian × 2023) = %d\n",
            sum(d$eth_year_int == 1)))


# =============================================================================
# STEP 1 + 2 — BASELINE MIMIC MODEL
# =============================================================================
cat("\n", strrep("=", 80), "\n", sep = "")
cat("STEP 1 + 2 — BASELINE MIMIC MODEL\n")
cat("  Measurement: F =~ ms1 + ms2 + ms3\n")
cat("  Structural : F  ~ ethnicity + year_bin + eth_year_int\n")
cat(strrep("=", 80), "\n", sep = "")

mod_baseline <- '
  # Measurement model
  F =~ ms1 + ms2 + ms3

  # Structural model
  F ~ ethnicity + year_bin + eth_year_int
'

fit_base <- cfa(mod_baseline, data = d, missing = "fiml", estimator = "MLR")

cat("\nFit indices:\n")
print(round(fitMeasures(fit_base,
  c("chisq","df","pvalue","cfi","tli","rmsea","srmr","aic","bic")), 3))

cat("\nParameter estimates (baseline):\n")
print(parameterEstimates(fit_base, standardized = TRUE)[
  , c("lhs","op","rhs","est","se","z","pvalue","ci.lower","ci.upper","std.all")])


# =============================================================================
# STEP 3 — DIF CHECK
# =============================================================================
cat("\n", strrep("=", 80), "\n", sep = "")
cat("STEP 3 — DIF CHECK\n")
cat("  3a) Modification indices (direct paths from covariates → items)\n")
cat("  3b) Per-item LRT: add one direct path ethnicity → item, compare to baseline\n")
cat(strrep("=", 80), "\n", sep = "")

# 3a) Modification indices, restricted to direct paths from covariates → items
mi <- modindices(fit_base, sort = TRUE)
mi_dif <- mi[mi$op == "~" &
             mi$lhs %in% c("ms1","ms2","ms3") &
             mi$rhs %in% c("ethnicity","year_bin","eth_year_int"), ]
cat("\nModification indices for direct covariate → item paths:\n")
if (nrow(mi_dif) == 0) {
  cat("  (no DIF candidate paths reported)\n")
} else {
  print(mi_dif[, c("lhs","op","rhs","mi","epc","sepc.all")])
}

# 3b) Per-item LRT
cat("\nPer-item LRT — add direct path ethnicity → item:\n")
lrt_results <- data.frame()
for (item in c("ms1","ms2","ms3")) {
  mod_dif <- paste0(mod_baseline, "\n  ", item, " ~ ethnicity\n")
  fit_dif <- tryCatch(
    cfa(mod_dif, data = d, missing = "fiml", estimator = "MLR"),
    error = function(e) NULL
  )
  if (is.null(fit_dif)) {
    lrt_results <- rbind(lrt_results, data.frame(
      item = item, chisq_diff = NA, df = NA, p = NA,
      direct_path_est = NA, direct_path_se = NA, direct_path_p = NA))
    next
  }
  a <- anova(fit_base, fit_dif)
  pe <- parameterEstimates(fit_dif)
  dp <- pe[pe$op == "~" & pe$lhs == item & pe$rhs == "ethnicity", ]
  lrt_results <- rbind(lrt_results, data.frame(
    item = item,
    chisq_diff = a$"Chisq diff"[2],
    df = a$"Df diff"[2],
    p = a$"Pr(>Chisq)"[2],
    direct_path_est = dp$est,
    direct_path_se = dp$se,
    direct_path_p = dp$pvalue
  ))
}
print(lrt_results)


# =============================================================================
# STEP 4 — FINAL MIMIC MODEL (with DIF paths if any)
# =============================================================================
cat("\n", strrep("=", 80), "\n", sep = "")
cat("STEP 4 — FINAL MIMIC MODEL\n")
cat(strrep("=", 80), "\n", sep = "")

# Decision rule: include direct path for any item with LRT p < .05
dif_items <- lrt_results$item[!is.na(lrt_results$p) & lrt_results$p < .05]
cat(sprintf("\nItems with significant DIF (LRT p < .05): %s\n",
            if (length(dif_items) == 0) "none" else paste(dif_items, collapse = ", ")))

if (length(dif_items) > 0) {
  dif_lines <- paste0("  ", dif_items, " ~ ethnicity", collapse = "\n")
  mod_final <- paste0(mod_baseline, "\n", dif_lines, "\n")
} else {
  mod_final <- mod_baseline
}
cat("\nFinal model syntax:\n")
cat(mod_final, "\n")

fit_final <- cfa(mod_final, data = d, missing = "fiml", estimator = "MLR")

cat("\nFit indices (final):\n")
print(round(fitMeasures(fit_final,
  c("chisq","df","pvalue","cfi","tli","rmsea","srmr","aic","bic")), 3))

cat("\nParameter estimates (final, with std.all):\n")
print(parameterEstimates(fit_final, standardized = TRUE)[
  , c("lhs","op","rhs","est","se","z","pvalue","ci.lower","ci.upper","std.all")])

cat("\nStructural-path estimates (F ~ covariates):\n")
pe <- parameterEstimates(fit_final, standardized = TRUE)
struct <- pe[pe$op == "~" & pe$lhs == "F", ]
print(struct[, c("lhs","op","rhs","est","se","z","pvalue","ci.lower","ci.upper","std.all")])


# =============================================================================
# Save output
# =============================================================================
out_path <- file.path(ROOT, "code", "_mimic_minority_support.tsv")
final_pe <- parameterEstimates(fit_final, standardized = TRUE)
write.table(final_pe, out_path, sep = "\t", row.names = FALSE, quote = FALSE)
cat(sprintf("\nSaved: %s\n", out_path))
