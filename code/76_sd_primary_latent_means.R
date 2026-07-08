# =============================================================================
# SD: Primary Out-group — Latent Means via Multi-Group CFA
# =============================================================================
# Test of latent-mean group comparison for the SD: Primary Out-group construct.
#
# Items (group-specific referent):
#   Estonians rate Russian-speakers:  Q57_1, Q58_1, Q59_1  (2023)
#                                     K4X7_1, K4X8_1, K4X9_1 (2020)
#   Russians  rate Estonian-speakers: Q57_2, Q58_2, Q59_2  (2023)
#                                     K4X7_2, K4X8_2, K4X9_2 (2020)
#   Items map to: sdp1 (live near), sdp2 (work with), sdp3 (be friends with)
#   Scale: 1 = no objection / very willing ... 5 = strongly object / unwilling
#   (Higher composite = more social distance)
#
# Procedure:
#   1. Cronbach's alpha for the 3 items, computed for each group × year cell
#   2. Multi-group CFA (Est vs Rus) within each year — configural/metric/scalar
#   3. Latent-mean estimates from scalar (or partial-scalar) model
#      Reference group: Estonian (latent mean fixed at 0)
#   4. Estonian − Russian latent-mean gap, 2020 vs 2023
# =============================================================================

suppressPackageStartupMessages({
  library(lavaan)
  library(haven)
})

ROOT <- "/Users/brianwiggins/Desktop/Claude Code/EIM2"

# -----------------------------------------------------------------------------
# Load data
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# Build SD: Primary item dataframes
# -----------------------------------------------------------------------------
build_sdp_2023 <- function(d) {
  out <- data.frame(group = d$ethnicity_binary)
  est <- d$ethnicity_binary == 0
  out$sdp1 <- ifelse(est, recode(d$Q57_1), recode(d$Q57_2))
  out$sdp2 <- ifelse(est, recode(d$Q58_1), recode(d$Q58_2))
  out$sdp3 <- ifelse(est, recode(d$Q59_1), recode(d$Q59_2))
  out
}
build_sdp_2020 <- function(d) {
  out <- data.frame(group = d$ethnicity_binary)
  est <- d$ethnicity_binary == 0
  out$sdp1 <- ifelse(est, recode(d$K4X7_1), recode(d$K4X7_2))
  out$sdp2 <- ifelse(est, recode(d$K4X8_1), recode(d$K4X8_2))
  out$sdp3 <- ifelse(est, recode(d$K4X9_1), recode(d$K4X9_2))
  out
}

sdp23 <- build_sdp_2023(df23)
sdp20 <- build_sdp_2020(df20)

cat(sprintf("2023 N: %d Est, %d Rus\n",
            sum(sdp23$group == 0), sum(sdp23$group == 1)))
cat(sprintf("2020 N: %d Est, %d Rus\n",
            sum(sdp20$group == 0), sum(sdp20$group == 1)))


# =============================================================================
# STEP 1 — Cronbach's Alpha
# =============================================================================
cat("\n", strrep("=", 80), "\n", sep = "")
cat("STEP 1 — CRONBACH'S ALPHA (3 items: sdp1, sdp2, sdp3)\n")
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
  list(label = "2023 Estonian (rates Russian-speakers)", df = sdp23, g = 0),
  list(label = "2023 Russian  (rates Estonian-speakers)", df = sdp23, g = 1),
  list(label = "2020 Estonian (rates Russian-speakers)", df = sdp20, g = 0),
  list(label = "2020 Russian  (rates Estonian-speakers)", df = sdp20, g = 1)
)
for (c1 in cells) {
  X <- c1$df[c1$df$group == c1$g, c("sdp1","sdp2","sdp3")]
  res <- cronbach_alpha(X)
  cat(sprintf("  %-46s  alpha = %.3f   N = %d\n",
              c1$label, res["alpha"], res["n"]))
}


# =============================================================================
# STEP 2 — CFA: Multi-Group Invariance (Est vs Rus), per year
# =============================================================================
cat("\n", strrep("=", 80), "\n", sep = "")
cat("STEP 2 — MULTI-GROUP CFA INVARIANCE (configural / metric / scalar)\n")
cat(strrep("=", 80), "\n", sep = "")

model_sdp <- "F =~ sdp1 + sdp2 + sdp3"

run_mg_invariance <- function(d, label) {
  cat("\n--- ", label, " ---\n", sep = "")
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
  fc <- fits(cfg); fm <- fits(met); fs <- fits(sca)
  tab <- rbind(
    configural = fc, metric = fm, scalar = fs
  )
  print(round(tab, 3))

  cat("\nLikelihood-ratio tests (chi-square difference, scaled):\n")
  print(anova(cfg, met, sca))

  list(cfg = cfg, met = met, sca = sca)
}

fits_2023 <- run_mg_invariance(sdp23, "2023 Multi-group: Estonian (0) vs Russian (1)")
fits_2020 <- run_mg_invariance(sdp20, "2020 Multi-group: Estonian (0) vs Russian (1)")


# =============================================================================
# STEP 3 — LATENT MEANS (from scalar model)
# =============================================================================
cat("\n", strrep("=", 80), "\n", sep = "")
cat("STEP 3 — LATENT MEANS (Estonian fixed at 0; Russian estimated)\n")
cat(strrep("=", 80), "\n", sep = "")

extract_latent_means <- function(scalar_fit, label) {
  cat("\n--- ", label, " ---\n", sep = "")
  pe <- parameterEstimates(scalar_fit, standardized = TRUE)
  lm <- pe[pe$op == "~1" & pe$lhs == "F", ]
  cat("Latent-factor intercepts (alpha):\n")
  print(lm[, c("group", "lhs", "op", "est", "se", "z", "pvalue", "ci.lower", "ci.upper")])
  invisible(lm)
}

lm23 <- extract_latent_means(fits_2023$sca, "2023 SCALAR model")
lm20 <- extract_latent_means(fits_2020$sca, "2020 SCALAR model")


# =============================================================================
# STEP 4 — GAP CALCULATION (Estonian − Russian) by year
# =============================================================================
cat("\n", strrep("=", 80), "\n", sep = "")
cat("STEP 4 — LATENT-MEAN GAP: Estonian − Russian, by year\n")
cat(strrep("=", 80), "\n", sep = "")

gap_from_lm <- function(lm) {
  est_mean <- lm$est[lm$group == 1]   # group=1 in lavaan = first group = Estonian (group=0 in data, but lavaan reorders alphabetically by group code 0,1: 1st=0 Est, 2nd=1 Rus)
  rus_mean <- lm$est[lm$group == 2]
  list(estonian = est_mean, russian = rus_mean,
       gap = est_mean - rus_mean)
}

g23 <- gap_from_lm(lm23)
g20 <- gap_from_lm(lm20)

cat(sprintf("\n2023:  Estonian latent mean = %.4f   Russian latent mean = %.4f   Gap (Est − Rus) = %+.4f\n",
            g23$estonian, g23$russian, g23$gap))
cat(sprintf("2020:  Estonian latent mean = %.4f   Russian latent mean = %.4f   Gap (Est − Rus) = %+.4f\n",
            g20$estonian, g20$russian, g20$gap))
cat(sprintf("\nChange in gap (2023 − 2020): %+.4f\n", g23$gap - g20$gap))


# =============================================================================
# Save output
# =============================================================================
out_path <- file.path(ROOT, "code", "_sd_primary_latent_means.tsv")
out_df <- data.frame(
  year = c(2023, 2023, 2020, 2020),
  group = c("Estonian", "Russian", "Estonian", "Russian"),
  latent_mean = c(g23$estonian, g23$russian, g20$estonian, g20$russian),
  gap_est_minus_rus = c(g23$gap, g23$gap, g20$gap, g20$gap)
)
write.table(out_df, out_path, sep = "\t", row.names = FALSE, quote = FALSE)
cat(sprintf("\nSaved: %s\n", out_path))
