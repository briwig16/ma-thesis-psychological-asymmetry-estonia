# =============================================================================
# MIMIC — Minority Inclusion Support with 4-category group_year predictor
# =============================================================================
# Replaces the ethnicity × year interaction with a single 4-level variable:
#   E20 = Estonian 2020   (reference)
#   R20 = Russian  2020
#   E23 = Estonian 2023
#   R23 = Russian  2023
#
# Three dummy regressors:
#   D_R20 = 1 if R20, else 0
#   D_E23 = 1 if E23, else 0
#   D_R23 = 1 if R23, else 0
#
# Each dummy's coefficient = latent-mean difference vs. E20.
#
# Indicators: ms1, ms2, ms3 (1-4 scale, lower = more supportive of inclusion)
#
# Procedure:
#   STEP 1: Measurement model — F =~ ms1 + ms2 + ms3 (CFA only, no covariates)
#   STEP 2: Baseline MIMIC — F ~ D_R20 + D_E23 + D_R23
#   STEP 3: DIF check — per-item LRT, one direct path at a time
#           (item ~ dummy), 9 tests total (3 items × 3 dummies)
#   STEP 4: Final MIMIC with DIF paths added safely. To preserve
#           identification with k=3 indicators, at most 2 items per
#           dummy can carry direct paths. Strategy:
#             For each dummy, sort items by Step-3 LRT chi-square and
#             add direct paths for items above a chi-square threshold
#             (p < .05), capped at 2 items per dummy (keep ≥1 anchor).
#             Then check the final fit converges and is identified.
# =============================================================================

suppressPackageStartupMessages({
  library(lavaan)
})

ROOT <- "/Users/brianwiggins/Desktop/Claude Code/EIM2"

d <- read.csv(file.path(ROOT, "data/EIM_stacked.csv"), stringsAsFactors = FALSE)

# -----------------------------------------------------------------------------
# Build 4-level group_year + dummies
# -----------------------------------------------------------------------------
d$group_year <- with(d, ifelse(group_num == 0 & year == 2020, "E20",
                        ifelse(group_num == 1 & year == 2020, "R20",
                        ifelse(group_num == 0 & year == 2023, "E23",
                        ifelse(group_num == 1 & year == 2023, "R23", NA)))))
d$D_R20 <- as.integer(d$group_year == "R20")
d$D_E23 <- as.integer(d$group_year == "E23")
d$D_R23 <- as.integer(d$group_year == "R23")

# Restrict to MIMIC variables and drop rows missing all 3 indicators
d <- d[, c("group_year","D_R20","D_E23","D_R23","ms1","ms2","ms3")]
d <- d[rowSums(!is.na(d[, c("ms1","ms2","ms3")])) > 0, ]

cat("group_year cell counts:\n")
print(table(d$group_year, useNA = "ifany"))

cat("\nDummy sums (sanity):\n")
cat(sprintf("  D_R20 = %d, D_E23 = %d, D_R23 = %d, E20 (reference) = %d\n",
            sum(d$D_R20), sum(d$D_E23), sum(d$D_R23),
            sum(d$D_R20 == 0 & d$D_E23 == 0 & d$D_R23 == 0)))


# =============================================================================
# STEP 1 — MEASUREMENT MODEL (CFA only)
# =============================================================================
cat("\n", strrep("=", 80), "\n", sep = "")
cat("STEP 1 — MEASUREMENT MODEL  F =~ ms1 + ms2 + ms3\n")
cat(strrep("=", 80), "\n", sep = "")

mod_meas <- 'F =~ ms1 + ms2 + ms3'
fit_meas <- cfa(mod_meas, data = d, missing = "fiml", estimator = "MLR")

cat("\nFit indices:\n")
print(round(fitMeasures(fit_meas,
  c("chisq","df","pvalue","cfi","tli","rmsea","srmr","aic","bic")), 3))

cat("\nMeasurement loadings (unstandardized + std.all):\n")
pe <- parameterEstimates(fit_meas, standardized = TRUE)
print(pe[pe$op == "=~", c("lhs","op","rhs","est","se","z","pvalue","std.all")])


# =============================================================================
# STEP 2 — BASELINE MIMIC (no DIF paths)
# =============================================================================
cat("\n", strrep("=", 80), "\n", sep = "")
cat("STEP 2 — BASELINE MIMIC  F ~ D_R20 + D_E23 + D_R23  (E20 = reference)\n")
cat(strrep("=", 80), "\n", sep = "")

mod_base <- '
  F =~ ms1 + ms2 + ms3
  F ~ D_R20 + D_E23 + D_R23
'
fit_base <- cfa(mod_base, data = d, missing = "fiml", estimator = "MLR")

cat("\nFit indices:\n")
print(round(fitMeasures(fit_base,
  c("chisq","df","pvalue","cfi","tli","rmsea","srmr","aic","bic")), 3))

cat("\nStructural paths (F ~):\n")
pe <- parameterEstimates(fit_base, standardized = TRUE)
struct <- pe[pe$op == "~" & pe$lhs == "F",
             c("lhs","op","rhs","est","se","z","pvalue","ci.lower","ci.upper","std.all")]
print(struct)


# =============================================================================
# STEP 3 — DIF CHECK  (per-item LRT, 9 tests)
# =============================================================================
cat("\n", strrep("=", 80), "\n", sep = "")
cat("STEP 3 — DIF CHECK  (item ~ dummy, one direct path at a time)\n")
cat(strrep("=", 80), "\n", sep = "")

dif_results <- data.frame()
for (item in c("ms1","ms2","ms3")) {
  for (dummy in c("D_R20","D_E23","D_R23")) {
    mod_dif <- paste0(mod_base, "\n  ", item, " ~ ", dummy, "\n")
    fit_dif <- tryCatch(
      cfa(mod_dif, data = d, missing = "fiml", estimator = "MLR"),
      error = function(e) NULL
    )
    if (is.null(fit_dif) || !lavInspect(fit_dif, "converged")) {
      dif_results <- rbind(dif_results, data.frame(
        item = item, dummy = dummy,
        chisq_diff = NA, df = NA, p = NA,
        path_est = NA, path_se = NA, path_p = NA))
      next
    }
    a <- anova(fit_base, fit_dif)
    pe <- parameterEstimates(fit_dif)
    dp <- pe[pe$op == "~" & pe$lhs == item & pe$rhs == dummy, ]
    dif_results <- rbind(dif_results, data.frame(
      item = item, dummy = dummy,
      chisq_diff = a$"Chisq diff"[2],
      df = a$"Df diff"[2],
      p = a$"Pr(>Chisq)"[2],
      path_est = dp$est, path_se = dp$se, path_p = dp$pvalue
    ))
  }
}
cat("\nFull DIF table (9 single-path tests):\n")
print(dif_results)

# Sort by chi-square within each dummy
cat("\nDIF ranked by chi-square within each dummy:\n")
for (dum in c("D_R20","D_E23","D_R23")) {
  sub <- dif_results[dif_results$dummy == dum, ]
  sub <- sub[order(-sub$chisq_diff), ]
  cat(sprintf("\n  %s:\n", dum))
  print(sub[, c("item","chisq_diff","p","path_est","path_p")])
}


# =============================================================================
# STEP 4 — FINAL MIMIC WITH DIF PATHS
# =============================================================================
# Identification rule: with 3 indicators per latent factor, at most 2 items
# per dummy can carry a direct path (≥1 anchor). I add a path for an item
# only if its single-path LRT p < .05, AND I cap at 2 paths per dummy (the
# top 2 by chi-square).
cat("\n", strrep("=", 80), "\n", sep = "")
cat("STEP 4 — FINAL MIMIC WITH DIF PATHS\n")
cat("Rule: include path if LRT p < .05; cap at 2 paths per dummy (≥1 anchor)\n")
cat(strrep("=", 80), "\n", sep = "")

dif_paths <- character()
for (dum in c("D_R20","D_E23","D_R23")) {
  sub <- dif_results[dif_results$dummy == dum & !is.na(dif_results$p) & dif_results$p < .05, ]
  sub <- sub[order(-sub$chisq_diff), ]
  if (nrow(sub) > 2) sub <- sub[1:2, ]
  for (i in seq_len(nrow(sub))) {
    dif_paths <- c(dif_paths, sprintf("%s ~ %s", sub$item[i], sub$dummy[i]))
  }
}

cat("\nSelected DIF paths:\n")
if (length(dif_paths) == 0) cat("  (none)\n") else
  for (p in dif_paths) cat("  ", p, "\n", sep = "")

mod_final <- mod_base
if (length(dif_paths) > 0) {
  mod_final <- paste0(mod_base, "\n  ",
                      paste(dif_paths, collapse = "\n  "), "\n")
}
cat("\nFinal model:\n", mod_final, "\n")

fit_final <- cfa(mod_final, data = d, missing = "fiml", estimator = "MLR")

cat("\nConverged:", lavInspect(fit_final, "converged"), "\n")
cat("\nFit indices (final):\n")
print(round(fitMeasures(fit_final,
  c("chisq","df","pvalue","cfi","tli","rmsea","srmr","aic","bic")), 3))

cat("\nMeasurement loadings (final):\n")
pe_f <- parameterEstimates(fit_final, standardized = TRUE)
print(pe_f[pe_f$op == "=~", c("lhs","rhs","est","se","z","pvalue","std.all")])

cat("\nStructural paths F ~ dummies (final):\n")
print(pe_f[pe_f$op == "~" & pe_f$lhs == "F",
           c("lhs","rhs","est","se","z","pvalue","ci.lower","ci.upper","std.all")])

cat("\nDirect-path (DIF) coefficients:\n")
dif_rows <- pe_f[pe_f$op == "~" & pe_f$lhs %in% c("ms1","ms2","ms3"), ]
if (nrow(dif_rows) == 0) cat("  (none)\n") else
  print(dif_rows[, c("lhs","rhs","est","se","z","pvalue","std.all")])


# =============================================================================
# Save outputs
# =============================================================================
write.table(dif_results, file.path(ROOT, "code", "_mimic_minority_dif.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE, na = "")
write.table(parameterEstimates(fit_base, standardized = TRUE),
            file.path(ROOT, "code", "_mimic_minority_baseline_params.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE, na = "")
write.table(parameterEstimates(fit_final, standardized = TRUE),
            file.path(ROOT, "code", "_mimic_minority_final_params.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE, na = "")

cat("\nSaved:\n")
cat("  code/_mimic_minority_dif.tsv\n")
cat("  code/_mimic_minority_baseline_params.tsv\n")
cat("  code/_mimic_minority_final_params.tsv\n")
