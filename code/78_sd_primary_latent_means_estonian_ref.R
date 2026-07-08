# =============================================================================
# SD: Primary Out-group — Latent Means with ESTONIAN as Reference Group
# =============================================================================
# Estonian latent mean fixed at 0; Russian latent mean estimated relative to it.
# Forces group ordering by passing a factor with Estonian as the first level.
# Verifies the ordering with lavInspect(fit, "group.label").
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
  est <- d$ethnicity_binary == 0
  data.frame(
    group = factor(d$ethnicity_binary, levels = c(0, 1),
                   labels = c("Estonian", "Russian")),
    sdp1 = ifelse(est, recode(d$Q57_1), recode(d$Q57_2)),
    sdp2 = ifelse(est, recode(d$Q58_1), recode(d$Q58_2)),
    sdp3 = ifelse(est, recode(d$Q59_1), recode(d$Q59_2))
  )
}
build_sdp_2020 <- function(d) {
  est <- d$ethnicity_binary == 0
  data.frame(
    group = factor(d$ethnicity_binary, levels = c(0, 1),
                   labels = c("Estonian", "Russian")),
    sdp1 = ifelse(est, recode(d$K4X7_1), recode(d$K4X7_2)),
    sdp2 = ifelse(est, recode(d$K4X8_1), recode(d$K4X8_2)),
    sdp3 = ifelse(est, recode(d$K4X9_1), recode(d$K4X9_2))
  )
}

sdp23 <- build_sdp_2023(df23)
sdp20 <- build_sdp_2020(df20)


# =============================================================================
# STEP 1 — Cronbach's Alpha
# =============================================================================
cat(strrep("=", 80), "\n", sep = "")
cat("STEP 1 — CRONBACH'S ALPHA\n")
cat("Items: sdp1 (live near), sdp2 (work with), sdp3 (be friends with)\n")
cat(strrep("=", 80), "\n", sep = "")

cronbach_alpha <- function(X) {
  X <- X[complete.cases(X), , drop = FALSE]
  k <- ncol(X)
  if (k < 2 || nrow(X) < 2) return(c(alpha = NA, n = nrow(X)))
  item_var <- apply(X, 2, var)
  total_var <- var(rowSums(X))
  alpha <- (k / (k - 1)) * (1 - sum(item_var) / total_var)
  c(alpha = alpha, n = nrow(X))
}

cells <- list(
  list(label = "2023 Estonian (rates Russian-speakers)", df = sdp23, g = "Estonian"),
  list(label = "2023 Russian  (rates Estonian-speakers)", df = sdp23, g = "Russian"),
  list(label = "2020 Estonian (rates Russian-speakers)", df = sdp20, g = "Estonian"),
  list(label = "2020 Russian  (rates Estonian-speakers)", df = sdp20, g = "Russian")
)
for (c1 in cells) {
  X <- c1$df[c1$df$group == c1$g, c("sdp1","sdp2","sdp3")]
  res <- cronbach_alpha(X)
  cat(sprintf("  %-46s  alpha = %.3f   N = %d\n",
              c1$label, res["alpha"], res["n"]))
}


# =============================================================================
# STEP 2 — CFA: Multi-Group Invariance (Estonian as reference)
# =============================================================================
cat("\n", strrep("=", 80), "\n", sep = "")
cat("STEP 2 — MULTI-GROUP CFA INVARIANCE\n")
cat("Reference group: Estonian (latent mean fixed at 0)\n")
cat(strrep("=", 80), "\n", sep = "")

model_sdp <- "F =~ sdp1 + sdp2 + sdp3"

run_mg_invariance <- function(d, label) {
  cat("\n--- ", label, " ---\n", sep = "")
  d <- d[, c("group", "sdp1", "sdp2", "sdp3")]
  d <- d[rowSums(!is.na(d[, c("sdp1","sdp2","sdp3")])) > 0, ]

  cfg <- cfa(model_sdp, data = d, group = "group",
             group.label = c("Estonian", "Russian"),
             missing = "fiml", estimator = "MLR")
  met <- cfa(model_sdp, data = d, group = "group", group.equal = "loadings",
             group.label = c("Estonian", "Russian"),
             missing = "fiml", estimator = "MLR")
  sca <- cfa(model_sdp, data = d, group = "group",
             group.equal = c("loadings", "intercepts"),
             group.label = c("Estonian", "Russian"),
             missing = "fiml", estimator = "MLR")

  cat("Group order lavaan used: ",
      paste(lavInspect(sca, "group.label"), collapse = " → "), "\n")

  fits <- function(f) fitMeasures(f, c("chisq","df","pvalue","cfi","tli","rmsea","srmr"))
  tab <- rbind(configural = fits(cfg), metric = fits(met), scalar = fits(sca))
  print(round(tab, 3))

  cat("\nLikelihood-ratio tests:\n")
  print(anova(cfg, met, sca))

  list(cfg = cfg, met = met, sca = sca)
}

fits_2023 <- run_mg_invariance(sdp23, "2023 Multi-group CFA")
fits_2020 <- run_mg_invariance(sdp20, "2020 Multi-group CFA")


# =============================================================================
# STEP 3 — LATENT MEANS (Estonian fixed at 0; Russian estimated)
# =============================================================================
cat("\n", strrep("=", 80), "\n", sep = "")
cat("STEP 3 — LATENT-FACTOR INTERCEPTS (from scalar model)\n")
cat(strrep("=", 80), "\n", sep = "")

extract_latent_means <- function(scalar_fit, label) {
  cat("\n--- ", label, " ---\n", sep = "")
  cat("Group order: ",
      paste(lavInspect(scalar_fit, "group.label"), collapse = " → "), "\n")
  pe <- parameterEstimates(scalar_fit)
  lm <- pe[pe$op == "~1" & pe$lhs == "F", ]
  print(lm[, c("group", "lhs", "op", "est", "se", "z", "pvalue", "ci.lower", "ci.upper")])
  invisible(lm)
}

lm23 <- extract_latent_means(fits_2023$sca, "2023 SCALAR model")
lm20 <- extract_latent_means(fits_2020$sca, "2020 SCALAR model")


# =============================================================================
# STEP 4 — GAP CALCULATION
# Majority − Minority = Estonian − Russian
# (Note: SD scale higher = more social distance)
# =============================================================================
cat("\n", strrep("=", 80), "\n", sep = "")
cat("STEP 4 — GAP: Majority (Estonian) − Minority (Russian)\n")
cat(strrep("=", 80), "\n", sep = "")

# group=1 row in lavaan output = first factor level = Estonian (fixed at 0)
# group=2 row in lavaan output = second factor level = Russian (estimated)
g23_est <- lm23$est[lm23$group == 1]
g23_rus <- lm23$est[lm23$group == 2]
g20_est <- lm20$est[lm20$group == 1]
g20_rus <- lm20$est[lm20$group == 2]

cat(sprintf("\n2023:  Estonian = %.4f   Russian = %+.4f   Gap (Est − Rus) = %+.4f\n",
            g23_est, g23_rus, g23_est - g23_rus))
cat(sprintf("2020:  Estonian = %.4f   Russian = %+.4f   Gap (Est − Rus) = %+.4f\n",
            g20_est, g20_rus, g20_est - g20_rus))

delta <- (g23_est - g23_rus) - (g20_est - g20_rus)
cat(sprintf("\nChange in gap (2023 − 2020): %+.4f\n", delta))
cat(sprintf("|Gap_2023| = %.4f   |Gap_2020| = %.4f\n",
            abs(g23_est - g23_rus), abs(g20_est - g20_rus)))


# =============================================================================
# Save output
# =============================================================================
out_path <- file.path(ROOT, "code", "_sd_primary_latent_means_estonian_ref.tsv")
out_df <- data.frame(
  year = c(2023, 2023, 2020, 2020),
  group = c("Estonian", "Russian", "Estonian", "Russian"),
  reference_group = "Estonian",
  latent_mean = c(g23_est, g23_rus, g20_est, g20_rus),
  gap_est_minus_rus = c(g23_est - g23_rus, g23_est - g23_rus,
                        g20_est - g20_rus, g20_est - g20_rus)
)
write.table(out_df, out_path, sep = "\t", row.names = FALSE, quote = FALSE)
cat(sprintf("\nSaved: %s\n", out_path))
