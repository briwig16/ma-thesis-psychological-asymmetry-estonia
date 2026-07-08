#!/usr/bin/env Rscript
# Referee 2 — Round 4 Cross-Language Replication
# §51 Paired test: SD: Primary Out-group vs. SD: General Out-group
# Independent R re-implementation of the author's Python script.

suppressMessages(library(haven))

# Locate project root robustly
candidates <- c(getwd(),
                file.path(getwd(), ".."),
                file.path(getwd(), "..", ".."))
ROOT <- NULL
for (c in candidates) {
  if (file.exists(file.path(c, "data", "EIM23.csv"))) { ROOT <- normalizePath(c); break }
}
if (is.null(ROOT)) stop("Cannot locate project root with data/EIM23.csv")

df23 <- read.csv(file.path(ROOT, "data", "EIM23.csv"),
                 stringsAsFactors = FALSE, na.strings = c("", " ", "NA"))
df23$ethnicity_binary <- suppressWarnings(as.numeric(df23$ethnicity_binary))
df23 <- df23[df23$ethnicity_binary %in% c(0,1), ]

df20 <- read_sav(file.path(ROOT, "data", "EIM 2020_20.10.25.sav copy"),
                 encoding = "latin1")
df20$ethnicity_binary <- ifelse(df20$T9_1 == 1, 0,
                          ifelse(df20$T9_2 == 1, 1, NA))
df20 <- df20[!is.na(df20$ethnicity_binary) & df20$ethnicity_binary %in% c(0,1), ]

composite <- function(df, items) {
  M <- as.data.frame(lapply(df[, items, drop = FALSE], function(x) {
    v <- suppressWarnings(as.numeric(as.character(x)))
    v[v == 9] <- NA
    v
  }))
  rowMeans(M, na.rm = TRUE)
}

paired_test <- function(primary, general, label) {
  ok <- !is.na(primary) & !is.na(general)
  n <- sum(ok)
  if (n < 2) { cat(sprintf("\n  %s: N=%d\n", label, n)); return(invisible(NULL)) }
  p <- primary[ok]; g <- general[ok]
  diff <- p - g
  m_diff <- mean(diff); sd_diff <- sd(diff)
  d_z <- m_diff / sd_diff
  se_dz <- sqrt(1/n + d_z^2 / (2*n))
  ci_lo <- d_z - 1.96 * se_dz; ci_hi <- d_z + 1.96 * se_dz
  tt <- t.test(p, g, paired = TRUE)
  wt <- suppressWarnings(wilcox.test(p, g, paired = TRUE, exact = FALSE))
  cat(sprintf("\n  %s\n", label))
  cat(sprintf("    N            = %d\n", n))
  cat(sprintf("    M(Primary)   = %.3f  SD = %.3f\n",
              mean(p), sd(p)))
  cat(sprintf("    M(General)   = %.3f  SD = %.3f\n",
              mean(g), sd(g)))
  cat(sprintf("    Mean diff    = %+.3f  SD(diff) = %.3f\n", m_diff, sd_diff))
  cat(sprintf("    d_z          = %+.3f  95%% CI [%+.3f, %+.3f]\n",
              d_z, ci_lo, ci_hi))
  cat(sprintf("    t(%d)        = %+.3f   p = %.6f\n",
              n-1, tt$statistic, tt$p.value))
  cat(sprintf("    Wilcoxon     = %.1f      p = %.6f\n",
              wt$statistic, wt$p.value))
  invisible(list(n=n, d_z=d_z, ci=c(ci_lo,ci_hi), p_t=tt$p.value, p_w=wt$p.value))
}

cat(strrep("=", 80), "\n", sep="")
cat("R cross-language replication — §51 paired test\n")
cat(strrep("=", 80), "\n", sep="")

cat("\nESTONIAN respondents\n", strrep("-", 80), "\n", sep="")
est23 <- df23[df23$ethnicity_binary == 0, ]
r1 <- paired_test(composite(est23, c("Q57_1","Q58_1","Q59_1")),
                  composite(est23, c("Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5")),
                  "2023 — Estonian Primary vs General")

est20 <- df20[df20$ethnicity_binary == 0, ]
r2 <- paired_test(composite(est20, c("K4X7_1","K4X8_1","K4X9_1")),
                  composite(est20, c("K4X7_3","K4X8_3","K4X9_3")),
                  "2020 — Estonian Primary vs General")

cat("\nRUSSIAN respondents\n", strrep("-", 80), "\n", sep="")
rus23 <- df23[df23$ethnicity_binary == 1, ]
r3 <- paired_test(composite(rus23, c("Q57_2","Q58_2","Q59_2")),
                  composite(rus23, c("Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5")),
                  "2023 — Russian Primary vs General")

rus20 <- df20[df20$ethnicity_binary == 1, ]
r4 <- paired_test(composite(rus20, c("K4X7_2","K4X8_2","K4X9_2")),
                  composite(rus20, c("K4X7_3","K4X8_3","K4X9_3")),
                  "2020 — Russian Primary vs General")
