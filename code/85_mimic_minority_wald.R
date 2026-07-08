# =============================================================================
# Wald test on final MIMIC (script 83) — constrain R20 == R23
# =============================================================================
# Re-fits the final DIF-adjusted MIMIC model from script 83 with labeled
# structural-path coefficients so the Wald constraint can be expressed as
# 'R20 == R23'. Labels:
#   R20 = coefficient on D_R20  (Russian 2020 vs E20 reference)
#   E23 = coefficient on D_E23  (Estonian 2023 vs E20 reference)
#   R23 = coefficient on D_R23  (Russian 2023 vs E20 reference)
# =============================================================================

suppressPackageStartupMessages({
  library(lavaan)
})

ROOT <- "/Users/brianwiggins/Desktop/Claude Code/EIM2"
d <- read.csv(file.path(ROOT, "data/EIM_stacked.csv"), stringsAsFactors = FALSE)

d$D_R20 <- as.integer(d$group_num == 1 & d$year == 2020)
d$D_E23 <- as.integer(d$group_num == 0 & d$year == 2023)
d$D_R23 <- as.integer(d$group_num == 1 & d$year == 2023)

d <- d[, c("D_R20","D_E23","D_R23","ms1","ms2","ms3")]
d <- d[rowSums(!is.na(d[, c("ms1","ms2","ms3")])) > 0, ]

# Final MIMIC model from script 83 with labeled structural paths
mod_final <- '
  # Measurement model
  F =~ ms1 + ms2 + ms3

  # Structural model (labeled coefficients)
  F ~ R20*D_R20 + E23*D_E23 + R23*D_R23

  # DIF paths selected in script 83 (LRT p < .05; cap of 2 paths per dummy)
  ms1 ~ D_R20
  ms2 ~ D_R20
  ms1 ~ D_E23
  ms3 ~ D_E23
  ms3 ~ D_R23
  ms1 ~ D_R23
'

fit_mimic <- cfa(mod_final, data = d, missing = "fiml", estimator = "MLR")

cat("Converged:", lavInspect(fit_mimic, "converged"), "\n")

cat("\nLabeled structural paths (verify the labels match):\n")
pe <- parameterEstimates(fit_mimic)
print(pe[pe$op == "~" & pe$lhs == "F",
         c("lhs","op","rhs","label","est","se","z","pvalue","ci.lower","ci.upper")])

# -----------------------------------------------------------------------------
# Wald test: R20 == R23
# -----------------------------------------------------------------------------
cat("\n", strrep("=", 70), "\n", sep = "")
cat("lavTestWald(fit_mimic, constraints = 'R20 == R23')\n")
cat(strrep("=", 70), "\n", sep = "")
w <- lavTestWald(fit_mimic, constraints = "R20 == R23")
print(w)

cat("\nNumeric summary:\n")
cat(sprintf("  Wald X^2 = %.4f\n", w$stat))
cat(sprintf("  df       = %d\n", w$df))
cat(sprintf("  p-value  = %.6f\n", w$p.value))

# Difference between coefficients for context
b_R20 <- pe$est[pe$label == "R20"]
b_R23 <- pe$est[pe$label == "R23"]
cat(sprintf("\nFor reference:\n"))
cat(sprintf("  R20 coefficient = %.4f\n", b_R20))
cat(sprintf("  R23 coefficient = %.4f\n", b_R23))
cat(sprintf("  Difference (R23 - R20) = %+.4f\n", b_R23 - b_R20))
