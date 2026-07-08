# =============================================================================
# Referee 2 — Round 3: Cross-Language Replication in R
# =============================================================================
# Independent verification of the entire Round 3 effect-size pipeline (means,
# SDs, Ns, Cohen's d, 95% CIs, p-values) using R + base R + haven for SPSS
# import. Cross-language replication exploits orthogonality of potential bugs.
#
# Compares each cell of code/_effect_sizes.tsv against an independent R
# computation. Reports PASS/FAIL count.
#
# Does NOT modify any author code.
# =============================================================================

suppressPackageStartupMessages({
  library(haven)
})

ROOT <- "/Users/brianwiggins/Desktop/Claude Code/EIM2"
PASS <- 0
FAIL <- 0
ISSUES <- character()

check <- function(label, computed, expected, tol = 0.01) {
  if (is.na(computed) || is.na(expected)) {
    ISSUES <<- c(ISSUES, sprintf("  NaN in %s", label))
    FAIL <<- FAIL + 1
    return(invisible(NULL))
  }
  if (abs(computed - expected) <= tol) {
    PASS <<- PASS + 1
  } else {
    FAIL <<- FAIL + 1
    ISSUES <<- c(ISSUES, sprintf("  FAIL %s: R=%.4f  TSV=%.4f  diff=%.4f",
                                 label, computed, expected,
                                 abs(computed - expected)))
  }
}

# Replace numeric DK code with NA
recode <- function(x, dk = 9) {
  x <- suppressWarnings(as.numeric(as.character(x)))
  x[x == dk] <- NA
  x
}

# Pairwise-deletion composite (mean of available items per row)
composite <- function(df, items, reverse_items = NULL, scale_max = NULL, dk = 9) {
  mat <- sapply(items, function(c) recode(df[[c]], dk = dk))
  if (!is.null(reverse_items)) {
    for (it in reverse_items) {
      mat[, it] <- (scale_max + 1) - mat[, it]
    }
  }
  rowMeans(mat, na.rm = TRUE)
}

m_sd_n <- function(s) {
  s <- s[!is.na(s) & is.finite(s)]
  list(m = mean(s), sd = sd(s), n = length(s))
}

cohens_d_rms <- function(m1, sd1, n1, m2, sd2, n2) {
  s <- sqrt((sd1^2 + sd2^2) / 2)
  d <- (m1 - m2) / s
  se <- sqrt((n1 + n2) / (n1 * n2) + d^2 / (2 * (n1 + n2 - 2)))
  list(d = d, lo = d - 1.96 * se, hi = d + 1.96 * se)
}

welch_p <- function(a, b) {
  a <- a[!is.na(a) & is.finite(a)]
  b <- b[!is.na(b) & is.finite(b)]
  t.test(a, b, var.equal = FALSE)$p.value
}

invert <- function(s, scale_max) (scale_max + 1) - s

# -----------------------------------------------------------------------------
# Load data
# -----------------------------------------------------------------------------
cat(strrep("=", 72), "\n")
cat("Referee 2 — Round 3: R Cross-Language Replication\n")
cat(strrep("=", 72), "\n")

df23 <- read.csv(file.path(ROOT, "data/EIM23.csv"), stringsAsFactors = FALSE)
df23 <- df23[df23$ethnicity_binary %in% c(0, 1), ]

df20_raw <- read_sav(file.path(ROOT, "data/EIM 2020_20.10.25.sav copy"),
                     encoding = "latin1")
df20 <- as.data.frame(df20_raw)
df20$ethnicity_binary <- ifelse(df20$T9_1 == 1, 0,
                          ifelse(df20$T9_2 == 1, 1, NA))
df20 <- df20[!is.na(df20$ethnicity_binary), ]

cat(sprintf("\n  2023: %d rows (%d Est, %d Rus)\n",
            nrow(df23), sum(df23$ethnicity_binary == 0), sum(df23$ethnicity_binary == 1)))
cat(sprintf("  2020: %d rows (%d Est, %d Rus)\n",
            nrow(df20), sum(df20$ethnicity_binary == 0), sum(df20$ethnicity_binary == 1)))

# Convenience: subset by group and year-of-data
e23 <- df23[df23$ethnicity_binary == 0, ]
r23 <- df23[df23$ethnicity_binary == 1, ]
e20 <- df20[df20$ethnicity_binary == 0, ]
r20 <- df20[df20$ethnicity_binary == 1, ]

# -----------------------------------------------------------------------------
# Build all 11 group-year series (mirrors author's spec; independent code)
# -----------------------------------------------------------------------------
build_var <- function(name, scale_max, inverted, e23_s, r23_s, e20_s, r20_s) {
  if (inverted) {
    e23_s <- invert(e23_s, scale_max)
    r23_s <- invert(r23_s, scale_max)
    e20_s <- invert(e20_s, scale_max)
    r20_s <- invert(r20_s, scale_max)
  }
  list(name = name, e23 = e23_s, r23 = r23_s, e20 = e20_s, r20 = r20_s)
}

V <- list()
V[["Superordinate Identity"]] <- build_var(
  "Superordinate Identity", 4, TRUE,
  composite(e23, c("Q67_2","Q67_4","Q67_5"), "Q67_4", scale_max = 4),
  composite(r23, c("Q67_2","Q67_4","Q67_5"), "Q67_4", scale_max = 4),
  composite(e20, c("K6X5_2","K6X5_3","K6X5_4"), "K6X5_3", scale_max = 4),
  composite(r20, c("K6X5_2","K6X5_3","K6X5_4"), "K6X5_3", scale_max = 4)
)
V[["SD: Primary Out-group"]] <- build_var(
  "SD: Primary Out-group", 5, FALSE,
  composite(e23, c("Q57_1","Q58_1","Q59_1")),
  composite(r23, c("Q57_2","Q58_2","Q59_2")),
  composite(e20, c("K4X7_1","K4X8_1","K4X9_1")),
  composite(r20, c("K4X7_2","K4X8_2","K4X9_2"))
)
V[["SD: General Out-group"]] <- build_var(
  "SD: General Out-group", 5, FALSE,
  composite(e23, c("Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5")),
  composite(r23, c("Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5")),
  composite(e20, c("K4X7_3","K4X8_3","K4X9_3")),
  composite(r20, c("K4X7_3","K4X8_3","K4X9_3"))
)
V[["Comparative Opportunity Assessment"]] <- build_var(
  "Comparative Opportunity Assessment", 5, TRUE,
  composite(e23, paste0("Q44_", 1:12)),
  composite(r23, paste0("Q44_", 1:12)),
  composite(e20, paste0("K3X1_", 1:12)),
  composite(r20, paste0("K3X1_", 1:12))
)
V[["Belief in Inevitable Conflict"]] <- build_var(
  "Belief in Inevitable Conflict", 4, FALSE,
  # 2026-04-30: composite reverse-coding flipped from Q63_3/Q63_4 to Q63_1/Q63_2
  composite(e23, c("Q63_1","Q63_2","Q63_3","Q63_4"), c("Q63_1","Q63_2"), scale_max = 4),
  composite(r23, c("Q63_1","Q63_2","Q63_3","Q63_4"), c("Q63_1","Q63_2"), scale_max = 4),
  composite(e20, c("K6X1_1","K6X1_2","K6X1_3","K6X1_4"), c("K6X1_1","K6X1_2"), scale_max = 4),
  composite(r20, c("K6X1_1","K6X1_2","K6X1_3","K6X1_4"), c("K6X1_1","K6X1_2"), scale_max = 4)
)
V[["Minority Support Inclusion"]] <- build_var(
  "Minority Support Inclusion", 4, TRUE,
  composite(e23, c("Q68_1","Q68_2","Q68_3")),
  composite(r23, c("Q68_1","Q68_2","Q68_3")),
  composite(e20, c("K6X6_1","K6X6_2","K6X6_3")),
  composite(r20, c("K6X6_1","K6X6_2","K6X6_3"))
)
V[["Contact: Estonian Speakers"]] <- build_var(
  "Contact: Estonian Speakers", 5, TRUE,
  composite(e23, paste0("Q51_", 1:6)),
  composite(r23, paste0("Q51_", 1:6)),
  composite(e20, paste0("K4X1_", 1:6)),
  composite(r20, paste0("K4X1_", 1:6))
)
V[["Contact: Russian Speakers"]] <- build_var(
  "Contact: Russian Speakers", 5, TRUE,
  composite(e23, paste0("Q52_", 1:6)),
  composite(r23, paste0("Q52_", 1:6)),
  composite(e20, paste0("K4X2_", 1:6)),
  composite(r20, paste0("K4X2_", 1:6))
)
V[["Group ID Patterns"]] <- build_var(
  "Group ID Patterns", 5, FALSE,
  recode(e23$Q66, dk = 9),
  recode(r23$Q66, dk = 9),
  recode(e20$K6X4, dk = 6),
  recode(r20$K6X4, dk = 6)
)
V[["Territorial Attachment"]] <- build_var(
  "Territorial Attachment", 4, TRUE,
  recode(e23$Q67_1),
  recode(r23$Q67_1),
  recode(e20$K6X5_1),
  recode(r20$K6X5_1)
)
V[["Contact: Out-group"]] <- build_var(
  "Contact: Out-group", 5, TRUE,
  composite(e23, paste0("Q52_", 1:6)),
  composite(r23, paste0("Q51_", 1:6)),
  composite(e20, paste0("K4X2_", 1:6)),
  composite(r20, paste0("K4X1_", 1:6))
)

# -----------------------------------------------------------------------------
# Load author's TSV and verify each row
# -----------------------------------------------------------------------------
tsv <- read.table(file.path(ROOT, "code/_effect_sizes.tsv"),
                  sep = "\t", header = TRUE, stringsAsFactors = FALSE,
                  check.names = FALSE)
cat(sprintf("\n  TSV: %d rows\n", nrow(tsv)))

cat("\n", strrep("=", 72), "\n")
cat("Verifying every cell of _effect_sizes.tsv against R recomputation ...\n")
cat(strrep("=", 72), "\n")

for (i in 1:nrow(tsv)) {
  row <- tsv[i, ]
  v <- V[[row$variable]]
  if (is.null(v)) { stop(paste("Unknown variable:", row$variable)) }

  if (row$table == "between") {
    if (row$comparison == "2020") { sA <- v$e20; sB <- v$r20 }
    else                           { sA <- v$e23; sB <- v$r23 }
    a <- m_sd_n(sA); b <- m_sd_n(sB)
    di <- cohens_d_rms(a$m, a$sd, a$n, b$m, b$sd, b$n)
    p <- welch_p(sA, sB)
    tag <- sprintf("[between %s] %s", row$comparison, row$variable)
  } else {
    if (row$comparison == "Estonian") { sA <- v$e20; sB <- v$e23 }
    else                                { sA <- v$r20; sB <- v$r23 }
    a <- m_sd_n(sA); b <- m_sd_n(sB)
    di <- cohens_d_rms(b$m, b$sd, b$n, a$m, a$sd, a$n)   # 2023 - 2020
    p <- welch_p(sA, sB)
    tag <- sprintf("[within %s] %s", row$comparison, row$variable)
  }

  check(paste(tag, "M1"),       a$m,    row$M1,      tol = 0.015)
  check(paste(tag, "SD1"),      a$sd,   row$SD1,     tol = 0.015)
  check(paste(tag, "N1"),       a$n,    row$N1,      tol = 0)
  check(paste(tag, "M2"),       b$m,    row$M2,      tol = 0.015)
  check(paste(tag, "SD2"),      b$sd,   row$SD2,     tol = 0.015)
  check(paste(tag, "N2"),       b$n,    row$N2,      tol = 0)
  check(paste(tag, "d"),        di$d,   row$d,       tol = 0.015)
  check(paste(tag, "CI_low"),   di$lo,  row$CI_low,  tol = 0.015)
  check(paste(tag, "CI_high"),  di$hi,  row$CI_high, tol = 0.015)
  check(paste(tag, "p"),        p,      row$p,       tol = 0.005)
}

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
total <- PASS + FAIL
cat("\n", strrep("=", 72), "\n")
cat(sprintf("R replication summary: %d/%d PASS, %d/%d FAIL\n", PASS, total, FAIL, total))
cat(strrep("=", 72), "\n")
if (length(ISSUES) > 0) {
  cat("\nIssues:\n")
  for (s in ISSUES) cat(s, "\n")
} else {
  cat("\nAll values match within tolerance.\n")
}
