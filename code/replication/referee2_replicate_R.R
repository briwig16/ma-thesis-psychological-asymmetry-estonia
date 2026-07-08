# =============================================================================
# Referee 2 — Cross-Language Replication in R
# =============================================================================
# Independent verification of all composite variables, reliability statistics,
# group means, and Cohen's d values using R (psych, haven, base R).
#
# This script replicates results originally computed in Python (pandas, sklearn,
# pingouin) to exploit orthogonality of potential errors across languages.
#
# Does NOT modify any author code or data files.
# =============================================================================

library(haven)
library(psych)
library(dplyr, warn.conflicts = FALSE)

PASS <- 0
FAIL <- 0

check <- function(label, computed, expected, tol = 0.015) {
  diff <- abs(computed - expected)
  if (diff <= tol) {
    PASS <<- PASS + 1
    cat(sprintf("    PASS  %s: %.4f (expected %.2f, diff=%.4f)\n", label, computed, expected, diff))
  } else {
    FAIL <<- FAIL + 1
    cat(sprintf("    FAIL  %s: %.4f (expected %.2f, diff=%.4f)\n", label, computed, expected, diff))
  }
}

cohens_d_rms <- function(g1, g2) {
  # Root-mean-square SD denominator (author's documented formula)
  s1 <- sd(g1, na.rm = TRUE)
  s2 <- sd(g2, na.rm = TRUE)
  denom <- sqrt((s1^2 + s2^2) / 2)
  (mean(g1, na.rm = TRUE) - mean(g2, na.rm = TRUE)) / denom
}

cronbach_r <- function(items_df) {
  # Using psych::alpha for independent computation
  result <- psych::alpha(items_df, check.keys = FALSE, warnings = FALSE)
  list(alpha = result$total$raw_alpha, n = nrow(na.omit(items_df)))
}

pca_var_r <- function(items_df) {
  # PCA on complete cases, return PC1 variance explained %
  complete <- na.omit(items_df)
  scaled <- scale(complete)
  pca <- prcomp(scaled, center = FALSE, scale. = FALSE)
  var_explained <- pca$sdev^2 / sum(pca$sdev^2)
  list(var_pct = var_explained[1] * 100, n = nrow(complete))
}

recode_9 <- function(x) {
  x <- as.numeric(x)
  x[x == 9] <- NA
  x
}


# =============================================================================
# LOAD 2023 DATA
# =============================================================================
cat(strrep("=", 70), "\n")
cat("LOADING 2023 DATA\n")
cat(strrep("=", 70), "\n")

df23 <- read.csv("/Users/brianwiggins/Desktop/Claude Code/EIM2/data/EIM23.csv")
df23 <- df23[df23$ethnicity_binary %in% c(0, 1), ]
est23 <- df23[df23$ethnicity_binary == 0, ]
rus23 <- df23[df23$ethnicity_binary == 1, ]
cat(sprintf("  2023: %d total, %d Estonian, %d Russian\n", nrow(df23), nrow(est23), nrow(rus23)))


# =============================================================================
# LOAD 2020 DATA
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("LOADING 2020 DATA\n")
cat(strrep("=", 70), "\n")

df20 <- read_sav("/Users/brianwiggins/Desktop/Claude Code/EIM2/data/EIM 2020_20.10.25.sav copy",
                 encoding = "latin1")
df20 <- as.data.frame(df20)
# Ethnicity via T9_1/T9_2 (self-identified nationality, matches 2023 T8)
df20$ethnicity_binary <- ifelse(df20$T9_1 == 1, 0, ifelse(df20$T9_2 == 1, 1, NA))
df20 <- df20[!is.na(df20$ethnicity_binary), ]
est20 <- df20[df20$ethnicity_binary == 0, ]
rus20 <- df20[df20$ethnicity_binary == 1, ]
cat(sprintf("  2020: %d total, %d Estonian, %d Russian\n", nrow(df20), nrow(est20), nrow(rus20)))


# =============================================================================
# COMPOSITE 1: SUPERORDINATE IDENTITY (2023)
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("COMPOSITE 1: SUPERORDINATE IDENTITY (2023)\n")
cat(strrep("=", 70), "\n")

df23$Q67_2r <- recode_9(df23$Q67_2)
df23$Q67_4r <- recode_9(df23$Q67_4)
df23$Q67_5r <- recode_9(df23$Q67_5)
df23$Q67_4_inv <- 5 - df23$Q67_4r

si_items_est <- data.frame(Q67_2 = est23$Q67_2, Q67_4 = est23$Q67_4, Q67_5 = est23$Q67_5)
si_items_est <- data.frame(lapply(si_items_est, recode_9))
si_items_est$Q67_4 <- 5 - si_items_est$Q67_4
si_items_rus <- data.frame(Q67_2 = rus23$Q67_2, Q67_4 = rus23$Q67_4, Q67_5 = rus23$Q67_5)
si_items_rus <- data.frame(lapply(si_items_rus, recode_9))
si_items_rus$Q67_4 <- 5 - si_items_rus$Q67_4

# Cronbach's alpha
cat("\n  Reliability:\n")
a_e <- cronbach_r(si_items_est)
check("Alpha Est", a_e$alpha, 0.698)
cat(sprintf("    N (listwise) = %d\n", a_e$n))
a_r <- cronbach_r(si_items_rus)
check("Alpha Rus", a_r$alpha, 0.760)
cat(sprintf("    N (listwise) = %d\n", a_r$n))

# PCA variance
pca_e <- pca_var_r(si_items_est)
check("PCA Var% Est", pca_e$var_pct, 63.1)
pca_r <- pca_var_r(si_items_rus)
check("PCA Var% Rus", pca_r$var_pct, 68.4)

# Composite means
comp_e <- rowMeans(si_items_est, na.rm = TRUE)
comp_e[rowSums(!is.na(si_items_est)) == 0] <- NA
comp_r <- rowMeans(si_items_rus, na.rm = TRUE)
comp_r[rowSums(!is.na(si_items_rus)) == 0] <- NA

cat("\n  Group means:\n")
check("Est M", mean(comp_e, na.rm = TRUE), 1.50)
check("Rus M", mean(comp_r, na.rm = TRUE), 2.05)
check("d (RMS)", cohens_d_rms(comp_e[!is.na(comp_e)], comp_r[!is.na(comp_r)]), -0.79)


# =============================================================================
# COMPOSITE 2: SD PRIMARY OUT-GROUP (2023)
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("COMPOSITE 2: SD PRIMARY OUT-GROUP (2023)\n")
cat(strrep("=", 70), "\n")

# Estonian: rate Russian-speakers Q57_1, Q58_1, Q59_1
sd_est <- data.frame(
  Q57_1 = recode_9(est23$Q57_1),
  Q58_1 = recode_9(est23$Q58_1),
  Q59_1 = recode_9(est23$Q59_1)
)
# Russian: rate Estonian-speakers Q57_2, Q58_2, Q59_2
sd_rus <- data.frame(
  Q57_2 = recode_9(rus23$Q57_2),
  Q58_2 = recode_9(rus23$Q58_2),
  Q59_2 = recode_9(rus23$Q59_2)
)

cat("\n  Reliability:\n")
a_e <- cronbach_r(sd_est); check("Alpha Est", a_e$alpha, 0.827)
a_r <- cronbach_r(sd_rus); check("Alpha Rus", a_r$alpha, 0.772)
pca_e <- pca_var_r(sd_est); check("PCA Var% Est", pca_e$var_pct, 74.4)
pca_r <- pca_var_r(sd_rus); check("PCA Var% Rus", pca_r$var_pct, 68.7)

comp_e <- rowMeans(sd_est, na.rm = TRUE); comp_e[rowSums(!is.na(sd_est)) == 0] <- NA
comp_r <- rowMeans(sd_rus, na.rm = TRUE); comp_r[rowSums(!is.na(sd_rus)) == 0] <- NA

cat("\n  Group means:\n")
check("Est M", mean(comp_e, na.rm = TRUE), 2.91)
check("Rus M", mean(comp_r, na.rm = TRUE), 1.83)
check("d (RMS)", cohens_d_rms(comp_e[!is.na(comp_e)], comp_r[!is.na(comp_r)]), 1.18)


# =============================================================================
# COMPOSITE 3: SD GENERAL OUT-GROUP (2023, 6 items)
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("COMPOSITE 3: SD GENERAL OUT-GROUP (2023)\n")
cat(strrep("=", 70), "\n")

gen_cols <- c("Q57_4", "Q57_5", "Q58_4", "Q58_5", "Q59_4", "Q59_5")
gen_est <- data.frame(lapply(est23[gen_cols], recode_9))
gen_rus <- data.frame(lapply(rus23[gen_cols], recode_9))

cat("\n  Reliability:\n")
a_e <- cronbach_r(gen_est); check("Alpha Est", a_e$alpha, 0.911)
a_r <- cronbach_r(gen_rus); check("Alpha Rus", a_r$alpha, 0.902)
pca_e <- pca_var_r(gen_est); check("PCA Var% Est", pca_e$var_pct, 69.3)
pca_r <- pca_var_r(gen_rus); check("PCA Var% Rus", pca_r$var_pct, 67.4)

comp_e <- rowMeans(gen_est, na.rm = TRUE); comp_e[rowSums(!is.na(gen_est)) == 0] <- NA
comp_r <- rowMeans(gen_rus, na.rm = TRUE); comp_r[rowSums(!is.na(gen_rus)) == 0] <- NA

cat("\n  Group means:\n")
check("Est M", mean(comp_e, na.rm = TRUE), 2.70)
check("Rus M", mean(comp_r, na.rm = TRUE), 2.60)
check("d (RMS)", cohens_d_rms(comp_e[!is.na(comp_e)], comp_r[!is.na(comp_r)]), 0.11)


# =============================================================================
# COMPOSITE 4: COMPARATIVE OPPORTUNITY (2023)
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("COMPOSITE 4: COMPARATIVE OPPORTUNITY (2023)\n")
cat(strrep("=", 70), "\n")

q44_cols <- paste0("Q44_", 1:12)
q44_est <- data.frame(lapply(est23[q44_cols], recode_9))
q44_rus <- data.frame(lapply(rus23[q44_cols], recode_9))

cat("\n  Reliability:\n")
a_e <- cronbach_r(q44_est); check("Alpha Est", a_e$alpha, 0.901)
a_r <- cronbach_r(q44_rus); check("Alpha Rus", a_r$alpha, 0.900)
pca_e <- pca_var_r(q44_est); check("PCA Var% Est", pca_e$var_pct, 49.1)
pca_r <- pca_var_r(q44_rus); check("PCA Var% Rus", pca_r$var_pct, 48.0)

comp_e <- rowMeans(q44_est, na.rm = TRUE); comp_e[rowSums(!is.na(q44_est)) == 0] <- NA
comp_r <- rowMeans(q44_rus, na.rm = TRUE); comp_r[rowSums(!is.na(q44_rus)) == 0] <- NA

cat("\n  Group means:\n")
check("Est M", mean(comp_e, na.rm = TRUE), 2.71)
check("Rus M", mean(comp_r, na.rm = TRUE), 2.32)
check("d (RMS)", cohens_d_rms(comp_e[!is.na(comp_e)], comp_r[!is.na(comp_r)]), 0.74)


# =============================================================================
# COMPOSITE 5: BELIEF IN INEVITABLE CONFLICT (2023)
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("COMPOSITE 5: BELIEF IN INEVITABLE CONFLICT (2023)\n")
cat(strrep("=", 70), "\n")

q63_est <- data.frame(
  Q63_1 = recode_9(est23$Q63_1),
  Q63_2 = recode_9(est23$Q63_2),
  Q63_3_inv = 5 - recode_9(est23$Q63_3),
  Q63_4_inv = 5 - recode_9(est23$Q63_4)
)
q63_rus <- data.frame(
  Q63_1 = recode_9(rus23$Q63_1),
  Q63_2 = recode_9(rus23$Q63_2),
  Q63_3_inv = 5 - recode_9(rus23$Q63_3),
  Q63_4_inv = 5 - recode_9(rus23$Q63_4)
)

cat("\n  Reliability:\n")
a_e <- cronbach_r(q63_est); check("Alpha Est", a_e$alpha, 0.766)
a_r <- cronbach_r(q63_rus); check("Alpha Rus", a_r$alpha, 0.681)
pca_e <- pca_var_r(q63_est); check("PCA Var% Est", pca_e$var_pct, 59.0)
pca_r <- pca_var_r(q63_rus); check("PCA Var% Rus", pca_r$var_pct, 51.6)

comp_e <- rowMeans(q63_est, na.rm = TRUE); comp_e[rowSums(!is.na(q63_est)) == 0] <- NA
comp_r <- rowMeans(q63_rus, na.rm = TRUE); comp_r[rowSums(!is.na(q63_rus)) == 0] <- NA

cat("\n  Group means:\n")
check("Est M", mean(comp_e, na.rm = TRUE), 2.72)
check("Rus M", mean(comp_r, na.rm = TRUE), 3.21)
check("d (RMS)", cohens_d_rms(comp_e[!is.na(comp_e)], comp_r[!is.na(comp_r)]), -0.78)


# =============================================================================
# COMPOSITE 6: MINORITY SUPPORT INCLUSION (2023)
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("COMPOSITE 6: MINORITY SUPPORT INCLUSION (2023)\n")
cat(strrep("=", 70), "\n")

q68_cols <- c("Q68_1", "Q68_2", "Q68_3")
q68_est <- data.frame(lapply(est23[q68_cols], recode_9))
q68_rus <- data.frame(lapply(rus23[q68_cols], recode_9))

cat("\n  Reliability:\n")
a_e <- cronbach_r(q68_est); check("Alpha Est", a_e$alpha, 0.835)
a_r <- cronbach_r(q68_rus); check("Alpha Rus", a_r$alpha, 0.835)
pca_e <- pca_var_r(q68_est); check("PCA Var% Est", pca_e$var_pct, 75.2)
pca_r <- pca_var_r(q68_rus); check("PCA Var% Rus", pca_r$var_pct, 75.5)

comp_e <- rowMeans(q68_est, na.rm = TRUE); comp_e[rowSums(!is.na(q68_est)) == 0] <- NA
comp_r <- rowMeans(q68_rus, na.rm = TRUE); comp_r[rowSums(!is.na(q68_rus)) == 0] <- NA

cat("\n  Group means:\n")
check("Est M", mean(comp_e, na.rm = TRUE), 2.33)
check("Rus M", mean(comp_r, na.rm = TRUE), 1.54)
check("d (RMS)", cohens_d_rms(comp_e[!is.na(comp_e)], comp_r[!is.na(comp_r)]), 1.14)


# =============================================================================
# COMPOSITES 7 & 8: CONTACT FREQUENCY (2023)
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("COMPOSITE 7: CONTACT WITH ESTONIAN SPEAKERS (2023)\n")
cat(strrep("=", 70), "\n")

q51_cols <- paste0("Q51_", 1:6)
q51_est <- data.frame(lapply(est23[q51_cols], recode_9))
q51_rus <- data.frame(lapply(rus23[q51_cols], recode_9))

cat("\n  Reliability:\n")
a_e <- cronbach_r(q51_est); check("Alpha Est", a_e$alpha, 0.760)
a_r <- cronbach_r(q51_rus); check("Alpha Rus", a_r$alpha, 0.812)
pca_e <- pca_var_r(q51_est); check("PCA Var% Est", pca_e$var_pct, 48.2)
pca_r <- pca_var_r(q51_rus); check("PCA Var% Rus", pca_r$var_pct, 52.4)

comp_e <- rowMeans(q51_est, na.rm = TRUE); comp_e[rowSums(!is.na(q51_est)) == 0] <- NA
comp_r <- rowMeans(q51_rus, na.rm = TRUE); comp_r[rowSums(!is.na(q51_rus)) == 0] <- NA

cat("\n  Group means:\n")
check("Est M", mean(comp_e, na.rm = TRUE), 1.74)
check("Rus M", mean(comp_r, na.rm = TRUE), 3.29)
check("d (RMS)", cohens_d_rms(comp_e[!is.na(comp_e)], comp_r[!is.na(comp_r)]), -1.57)


cat("\n", strrep("=", 70), "\n")
cat("COMPOSITE 8: CONTACT WITH RUSSIAN SPEAKERS (2023)\n")
cat(strrep("=", 70), "\n")

q52_cols <- paste0("Q52_", 1:6)
q52_est <- data.frame(lapply(est23[q52_cols], recode_9))
q52_rus <- data.frame(lapply(rus23[q52_cols], recode_9))

cat("\n  Reliability:\n")
a_e <- cronbach_r(q52_est); check("Alpha Est", a_e$alpha, 0.854)
a_r <- cronbach_r(q52_rus); check("Alpha Rus", a_r$alpha, 0.737)
pca_e <- pca_var_r(q52_est); check("PCA Var% Est", pca_e$var_pct, 59.4)
pca_r <- pca_var_r(q52_rus); check("PCA Var% Rus", pca_r$var_pct, 44.7)

comp_e <- rowMeans(q52_est, na.rm = TRUE); comp_e[rowSums(!is.na(q52_est)) == 0] <- NA
comp_r <- rowMeans(q52_rus, na.rm = TRUE); comp_r[rowSums(!is.na(q52_rus)) == 0] <- NA

cat("\n  Group means:\n")
check("Est M", mean(comp_e, na.rm = TRUE), 3.87)
check("Rus M", mean(comp_r, na.rm = TRUE), 1.71)
check("d (RMS)", cohens_d_rms(comp_e[!is.na(comp_e)], comp_r[!is.na(comp_r)]), 2.25)


# =============================================================================
# 2020 COMPOSITES — VERIFY ALL 8
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("2020 COMPOSITES — ALL 8\n")
cat(strrep("=", 70), "\n")

# Superordinate Identity
cat("\n  2020 Superordinate Identity:\n")
df20$K6X5_2r <- recode_9(df20$K6X5_2)
df20$K6X5_3r <- recode_9(df20$K6X5_3)
df20$K6X5_4r <- recode_9(df20$K6X5_4)
df20$K6X5_3_inv <- 5 - df20$K6X5_3r
si20 <- rowMeans(df20[, c("K6X5_2r", "K6X5_3_inv", "K6X5_4r")], na.rm = TRUE)
si20[rowSums(!is.na(df20[, c("K6X5_2r", "K6X5_3_inv", "K6X5_4r")])) == 0] <- NA
check("Est M", mean(si20[df20$ethnicity_binary == 0], na.rm = TRUE), 1.45)
check("Rus M", mean(si20[df20$ethnicity_binary == 1], na.rm = TRUE), 2.08)
check("d (RMS)", cohens_d_rms(si20[df20$ethnicity_binary == 0 & !is.na(si20)],
                               si20[df20$ethnicity_binary == 1 & !is.na(si20)]), -1.08)

# SD Primary
cat("\n  2020 SD Primary Out-group:\n")
for (col in c("K4X7_1", "K4X8_1", "K4X9_1", "K4X7_2", "K4X8_2", "K4X9_2")) {
  df20[[paste0(col, "r")]] <- recode_9(df20[[col]])
}
sdp20_e <- rowMeans(df20[df20$ethnicity_binary == 0, c("K4X7_1r", "K4X8_1r", "K4X9_1r")], na.rm = TRUE)
sdp20_r <- rowMeans(df20[df20$ethnicity_binary == 1, c("K4X7_2r", "K4X8_2r", "K4X9_2r")], na.rm = TRUE)
check("Est M", mean(sdp20_e, na.rm = TRUE), 2.51)
check("Rus M", mean(sdp20_r, na.rm = TRUE), 1.90)
check("d (RMS)", cohens_d_rms(sdp20_e[!is.na(sdp20_e)], sdp20_r[!is.na(sdp20_r)]), 0.74)

# SD General
cat("\n  2020 SD General Out-group:\n")
for (col in c("K4X7_3", "K4X8_3", "K4X9_3")) df20[[paste0(col, "r")]] <- recode_9(df20[[col]])
sdg20 <- rowMeans(df20[, c("K4X7_3r", "K4X8_3r", "K4X9_3r")], na.rm = TRUE)
sdg20[rowSums(!is.na(df20[, c("K4X7_3r", "K4X8_3r", "K4X9_3r")])) == 0] <- NA
check("Est M", mean(sdg20[df20$ethnicity_binary == 0], na.rm = TRUE), 2.91)
check("Rus M", mean(sdg20[df20$ethnicity_binary == 1], na.rm = TRUE), 3.12)
check("d (RMS)", cohens_d_rms(sdg20[df20$ethnicity_binary == 0 & !is.na(sdg20)],
                               sdg20[df20$ethnicity_binary == 1 & !is.na(sdg20)]), -0.21)

# Comparative Opportunity
cat("\n  2020 Comparative Opportunity:\n")
k3x1_cols <- paste0("K3X1_", 1:12)
for (col in k3x1_cols) df20[[paste0(col, "r")]] <- recode_9(df20[[col]])
k3x1_r_cols <- paste0(k3x1_cols, "r")
co20 <- rowMeans(df20[, k3x1_r_cols], na.rm = TRUE)
co20[rowSums(!is.na(df20[, k3x1_r_cols])) == 0] <- NA
check("Est M", mean(co20[df20$ethnicity_binary == 0], na.rm = TRUE), 2.56)
check("Rus M", mean(co20[df20$ethnicity_binary == 1], na.rm = TRUE), 2.14)
check("d (RMS)", cohens_d_rms(co20[df20$ethnicity_binary == 0 & !is.na(co20)],
                               co20[df20$ethnicity_binary == 1 & !is.na(co20)]), 0.79)

# Belief in Conflict
cat("\n  2020 Belief in Conflict:\n")
for (col in c("K6X1_1", "K6X1_2", "K6X1_3", "K6X1_4")) df20[[paste0(col, "r")]] <- recode_9(df20[[col]])
df20$K6X1_3_inv <- 5 - df20$K6X1_3r
df20$K6X1_4_inv <- 5 - df20$K6X1_4r
bc20 <- rowMeans(df20[, c("K6X1_1r", "K6X1_2r", "K6X1_3_inv", "K6X1_4_inv")], na.rm = TRUE)
bc20[rowSums(!is.na(df20[, c("K6X1_1r", "K6X1_2r", "K6X1_3_inv", "K6X1_4_inv")])) == 0] <- NA
check("Est M", mean(bc20[df20$ethnicity_binary == 0], na.rm = TRUE), 2.78)
check("Rus M", mean(bc20[df20$ethnicity_binary == 1], na.rm = TRUE), 3.03)
check("d (RMS)", cohens_d_rms(bc20[df20$ethnicity_binary == 0 & !is.na(bc20)],
                               bc20[df20$ethnicity_binary == 1 & !is.na(bc20)]), -0.44)

# Minority Support
cat("\n  2020 Minority Support:\n")
for (col in c("K6X6_1", "K6X6_2", "K6X6_3")) df20[[paste0(col, "r")]] <- recode_9(df20[[col]])
ms20 <- rowMeans(df20[, c("K6X6_1r", "K6X6_2r", "K6X6_3r")], na.rm = TRUE)
ms20[rowSums(!is.na(df20[, c("K6X6_1r", "K6X6_2r", "K6X6_3r")])) == 0] <- NA
check("Est M", mean(ms20[df20$ethnicity_binary == 0], na.rm = TRUE), 2.21)
check("Rus M", mean(ms20[df20$ethnicity_binary == 1], na.rm = TRUE), 1.57)
check("d (RMS)", cohens_d_rms(ms20[df20$ethnicity_binary == 0 & !is.na(ms20)],
                               ms20[df20$ethnicity_binary == 1 & !is.na(ms20)]), 1.00)

# Contact Estonian speakers
cat("\n  2020 Contact Estonian speakers:\n")
k4x1_cols <- paste0("K4X1_", 1:6)
for (col in k4x1_cols) df20[[paste0(col, "r")]] <- recode_9(df20[[col]])
k4x1_r_cols <- paste0(k4x1_cols, "r")
ce20 <- rowMeans(df20[, k4x1_r_cols], na.rm = TRUE)
ce20[rowSums(!is.na(df20[, k4x1_r_cols])) == 0] <- NA
check("Est M", mean(ce20[df20$ethnicity_binary == 0], na.rm = TRUE), 1.85)
check("Rus M", mean(ce20[df20$ethnicity_binary == 1], na.rm = TRUE), 3.86)
check("d (RMS)", cohens_d_rms(ce20[df20$ethnicity_binary == 0 & !is.na(ce20)],
                               ce20[df20$ethnicity_binary == 1 & !is.na(ce20)]), -1.89)

# Contact Russian speakers
cat("\n  2020 Contact Russian speakers:\n")
k4x2_cols <- paste0("K4X2_", 1:6)
for (col in k4x2_cols) df20[[paste0(col, "r")]] <- recode_9(df20[[col]])
k4x2_r_cols <- paste0(k4x2_cols, "r")
cr20 <- rowMeans(df20[, k4x2_r_cols], na.rm = TRUE)
cr20[rowSums(!is.na(df20[, k4x2_r_cols])) == 0] <- NA
check("Est M", mean(cr20[df20$ethnicity_binary == 0], na.rm = TRUE), 3.98)
check("Rus M", mean(cr20[df20$ethnicity_binary == 1], na.rm = TRUE), 1.79)
check("d (RMS)", cohens_d_rms(cr20[df20$ethnicity_binary == 0 & !is.na(cr20)],
                               cr20[df20$ethnicity_binary == 1 & !is.na(cr20)]), 2.25)


# =============================================================================
# FINAL SUMMARY
# =============================================================================
cat("\n", strrep("=", 70), "\n")
cat("R CROSS-LANGUAGE REPLICATION SUMMARY\n")
cat(strrep("=", 70), "\n")
cat(sprintf("\n  PASS: %d\n", PASS))
cat(sprintf("  FAIL: %d\n", FAIL))
cat(sprintf("  Total checks: %d\n", PASS + FAIL))
if (FAIL == 0) {
  cat("\n  ALL CHECKS PASSED — R replication matches Python results\n")
} else {
  cat(sprintf("\n  %d CHECK(S) FAILED — see details above\n", FAIL))
}
cat(strrep("=", 70), "\n")
