# =============================================================================
# SD: Primary Out-group — Latent Means with RUSSIAN as Reference Group
# =============================================================================
# Same design as code/76 but with the reference group flipped:
#   Russian latent mean fixed at 0
#   Estonian latent mean estimated (relative to Russian)
#
# Implementation: convert `group` to a factor with "Russian" as the first
# level, so lavaan uses it as the reference group.
# =============================================================================

suppressPackageStartupMessages({
  library(lavaan)
  library(haven)
})

ROOT <- "/Users/brianwiggins/Desktop/Claude Code/EIM2"

df23 <- read.csv(file.path(ROOT, "data/EIM23.csv"), stringsAsFactors = FALSE)
df23 <- df23[df23$ethnicity_binary %in% c(0, 1), ]

df20_raw <- read_sav(file.path(ROOT, "data/EIM 2020_20.10.25.sav copy"),
                     encoding = "latin1")
df20 <- as.data.frame(df20_raw)
df20$ethnicity_binary <- ifelse(df20$T9_1 == 1, 0,
                          ifelse(df20$T9_2 == 1, 1, NA))
df20 <- df20[!is.na(df20$ethnicity_binary), ]

recode <- function(x, dk = 9) {
  x <- suppressWarnings(as.numeric(as.character(x)))
  x[x == dk] <- NA
  x
}

build_sdp_2023 <- function(d) {
  out <- data.frame(group = d$ethnicity_binary)
  est <- d$ethnicity_binary == 0
  out$sdp1 <- ifelse(est, recode(d$Q57_1), recode(d$Q57_2))
  out$sdp2 <- ifelse(est, recode(d$Q58_1), recode(d$Q58_2))
  out$sdp3 <- ifelse(est, recode(d$Q59_1), recode(d$Q59_2))
  # Convert to factor with Russian first → Russian becomes reference
  out$group <- factor(out$group, levels = c(1, 0), labels = c("Russian", "Estonian"))
  out
}
build_sdp_2020 <- function(d) {
  out <- data.frame(group = d$ethnicity_binary)
  est <- d$ethnicity_binary == 0
  out$sdp1 <- ifelse(est, recode(d$K4X7_1), recode(d$K4X7_2))
  out$sdp2 <- ifelse(est, recode(d$K4X8_1), recode(d$K4X8_2))
  out$sdp3 <- ifelse(est, recode(d$K4X9_1), recode(d$K4X9_2))
  out$group <- factor(out$group, levels = c(1, 0), labels = c("Russian", "Estonian"))
  out
}

sdp23 <- build_sdp_2023(df23)
sdp20 <- build_sdp_2020(df20)

model_sdp <- "F =~ sdp1 + sdp2 + sdp3"

run_scalar <- function(d, label) {
  cat("\n--- ", label, " (Russian = reference, latent mean fixed at 0) ---\n", sep = "")
  d <- d[, c("group", "sdp1", "sdp2", "sdp3")]
  d <- d[rowSums(!is.na(d[, c("sdp1","sdp2","sdp3")])) > 0, ]

  cfg <- cfa(model_sdp, data = d, group = "group",
             missing = "fiml", estimator = "MLR")
  met <- cfa(model_sdp, data = d, group = "group", group.equal = "loadings",
             missing = "fiml", estimator = "MLR")
  sca <- cfa(model_sdp, data = d, group = "group",
             group.equal = c("loadings", "intercepts"),
             missing = "fiml", estimator = "MLR")

  fits <- function(f) fitMeasures(f, c("chisq","df","pvalue","cfi","tli","rmsea","srmr"))
  tab <- rbind(configural = fits(cfg), metric = fits(met), scalar = fits(sca))
  print(round(tab, 3))

  pe <- parameterEstimates(sca)
  lm <- pe[pe$op == "~1" & pe$lhs == "F", ]
  cat("\nLatent-factor intercepts:\n")
  print(lm[, c("group", "lhs", "op", "est", "se", "z", "pvalue", "ci.lower", "ci.upper")])
  invisible(lm)
}

cat(strrep("=", 80), "\n", sep = "")
cat("LATENT MEANS — RUSSIAN AS REFERENCE GROUP\n")
cat(strrep("=", 80), "\n", sep = "")

lm23 <- run_scalar(sdp23, "2023")
lm20 <- run_scalar(sdp20, "2020")

# group=1 in lavaan output = first factor level = Russian (fixed at 0)
# group=2 in lavaan output = second factor level = Estonian (estimated)
g23_rus <- lm23$est[lm23$group == 1]
g23_est <- lm23$est[lm23$group == 2]
g20_rus <- lm20$est[lm20$group == 1]
g20_est <- lm20$est[lm20$group == 2]

cat("\n", strrep("=", 80), "\n", sep = "")
cat("GAP CALCULATION (Estonian − Russian, with Russian as reference)\n")
cat(strrep("=", 80), "\n", sep = "")
cat(sprintf("\n2023:  Russian = %.4f   Estonian = %+.4f   Gap (Est − Rus) = %+.4f\n",
            g23_rus, g23_est, g23_est - g23_rus))
cat(sprintf("2020:  Russian = %.4f   Estonian = %+.4f   Gap (Est − Rus) = %+.4f\n",
            g20_rus, g20_est, g20_est - g20_rus))
cat(sprintf("\nChange in gap (2023 − 2020): %+.4f\n",
            (g23_est - g23_rus) - (g20_est - g20_rus)))
