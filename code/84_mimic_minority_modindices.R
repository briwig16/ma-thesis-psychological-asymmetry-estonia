# =============================================================================
# Modification Indices for the Step-2 baseline MIMIC (script 83)
# =============================================================================
# Re-fits the baseline MIMIC and pulls modification indices for direct
# covariate → indicator paths. Reports MI (expected chi-square drop if
# the path is added), EPC (expected parameter change), and standardized EPC.
# Compared side-by-side with the Step-3 LRT chi-square from script 83.
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

mod_base <- '
  F =~ ms1 + ms2 + ms3
  F ~ D_R20 + D_E23 + D_R23
'
fit_base <- cfa(mod_base, data = d, missing = "fiml", estimator = "MLR")

# All modification indices, then filter to direct covariate→item paths
mi_all <- modindices(fit_base, sort = TRUE, free.remove = FALSE)
cat("\n--- All MI rows (top 20 by mi) ---\n")
print(head(mi_all[order(-mi_all$mi), c("lhs","op","rhs","mi","epc","sepc.all")], 20))

mi_dif <- mi_all[mi_all$op == "~" &
                 mi_all$lhs %in% c("ms1","ms2","ms3") &
                 mi_all$rhs %in% c("D_R20","D_E23","D_R23"), ]
mi_dif <- mi_dif[order(-mi_dif$mi), ]

cat("\n--- Modification indices: direct covariate -> item paths ---\n")
if (nrow(mi_dif) == 0) {
  cat("(none returned by modindices for these paths)\n")
} else {
  print(mi_dif[, c("lhs","op","rhs","mi","epc","sepc.all")])
}

# Try lavTestScore as an alternative — request specific parameters
cat("\n--- lavTestScore: univariate score tests for the same 9 paths ---\n")
# Build parameter labels via partable
pt <- parTable(fit_base)
# Need to add the constraints (these paths fixed at 0 in baseline). We use
# lavTestScore with `add` to specify candidate paths.
add_str <- "
  ms1 ~ D_R20
  ms1 ~ D_E23
  ms1 ~ D_R23
  ms2 ~ D_R20
  ms2 ~ D_E23
  ms2 ~ D_R23
  ms3 ~ D_R20
  ms3 ~ D_E23
  ms3 ~ D_R23
"
sc <- lavTestScore(fit_base, add = add_str, univariate = TRUE,
                   cumulative = FALSE)
print(sc)
