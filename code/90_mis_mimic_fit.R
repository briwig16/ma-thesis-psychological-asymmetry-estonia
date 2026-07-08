# =============================================================================
# Minority Inclusion Support — MIMIC fit indices
# =============================================================================
# 3 items × 3 cell-dummies → MIMIC baseline has only 6 df. Each direct
# (DIF) path consumes 1 df, so the "final" model from script 83 (6 DIF
# paths) is saturated. We walk the model from baseline outward, adding
# DIF paths in order of script-83's significance ranking, and report
# CFI / TLI / RMSEA / SRMR at every step until df = 0.
#
# Estimator: MLR, FIML.
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


fit_row <- function(fit, label) {
  fm <- fitMeasures(fit, c("chisq.scaled","df.scaled","pvalue.scaled",
                           "cfi.scaled","tli.scaled",
                           "rmsea.scaled","rmsea.ci.lower.scaled",
                           "rmsea.ci.upper.scaled","srmr"))
  data.frame(
    model    = label,
    chisq    = round(unname(fm["chisq.scaled"]), 3),
    df       = unname(fm["df.scaled"]),
    p        = round(unname(fm["pvalue.scaled"]), 4),
    CFI      = round(unname(fm["cfi.scaled"]), 4),
    TLI      = round(unname(fm["tli.scaled"]), 4),
    RMSEA    = round(unname(fm["rmsea.scaled"]), 4),
    RMSEA_lo = round(unname(fm["rmsea.ci.lower.scaled"]), 4),
    RMSEA_hi = round(unname(fm["rmsea.ci.upper.scaled"]), 4),
    SRMR     = round(unname(fm["srmr"]), 4),
    row.names = NULL
  )
}

base <- 'F =~ ms1 + ms2 + ms3
         F ~ D_R20 + D_E23 + D_R23'

# Sequence of DIF paths (script 83's selection order — top 2 per dummy
# by χ² / LRT, dropped ms3~D_R20 because ns):
#   ms1~D_R20, ms2~D_R20, ms1~D_E23, ms3~D_E23, ms3~D_R23, ms1~D_R23
#
# We add them one at a time and record fit at each step.
paths <- c(
  "ms1 ~ D_R20",
  "ms2 ~ D_R20",
  "ms1 ~ D_E23",
  "ms3 ~ D_E23",
  "ms3 ~ D_R23",
  "ms1 ~ D_R23"
)

fits <- list()
labels <- character(0)

# Baseline (no DIF)
fits[[1]] <- cfa(base, data = d, missing = "fiml", estimator = "MLR")
labels[1] <- "(0) Baseline MIMIC — 0 DIF paths"

# Add paths one by one
for (i in seq_along(paths)) {
  m <- paste(c(base, paths[1:i]), collapse = "\n")
  fits[[i + 1]] <- cfa(m, data = d, missing = "fiml", estimator = "MLR")
  labels[i + 1] <- sprintf("(%d) + %s", i, paths[i])
}

tab <- do.call(rbind, Map(fit_row, fits, labels))

cat("\n", strrep("=", 90), "\n", sep = "")
cat("MINORITY INCLUSION SUPPORT — MIMIC fit, DIF paths added sequentially\n")
cat(strrep("=", 90), "\n\n", sep = "")
print(tab, row.names = FALSE)

# Cumulative LRT: each added path vs. baseline
cat("\n--- Cumulative LRT vs. baseline (Satorra-Bentler) ---\n")
print(do.call(lavTestLRT,
              c(fits, list(method = "satorra.bentler.2001"))))

write.table(tab, file.path(ROOT, "code/_mis_mimic_fit.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE)
cat("\nWrote: code/_mis_mimic_fit.tsv\n")
