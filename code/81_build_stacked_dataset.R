# =============================================================================
# Build stacked 2020 + 2023 dataset for MIMIC modeling
# =============================================================================
# Each row = one respondent. Adds:
#   year   : 2020 or 2023 (integer)
#   group  : Estonian / Russian (factor; matches existing pipeline coding)
#   group_num : 0 = Estonian, 1 = Russian (numeric)
#
# Item naming uses the same conventions as the existing R pipeline so the
# stacked file slots into MIMIC models without further recoding:
#
#   si1, si2, si3                  Superordinate Identity (si2 = reverse-coded)
#   sdp1, sdp2, sdp3               SD: Primary (group-specific referent)
#   sdg1..sdg6                     SD: General — 2023 items only
#   sdg2020_1..sdg2020_3           SD: General — 2020 items only
#   co1..co12                      Comparative Opportunity Assessment
#   bic1..bic4                     Belief in Inevitable Conflict (bic1, bic2 reversed)
#   ms1, ms2, ms3                  Minority Support Inclusion
#   ce1..ce6                       Contact: Estonian Speakers
#   cr1..cr6                       Contact: Russian Speakers
#
# Items present in only one wave (e.g. sdg1..sdg6 only in 2023, sdg2020_*
# only in 2020) are filled with NA in the other wave's rows.
#
# All "Don't know" codes (9) are recoded to NA. Reverse-coded items use
# (scale_max + 1) - x; scale_max = 4 for Q67_4 / K6X5_3 / Q63_1 / Q63_2.
#
# Output: data/EIM_stacked.csv
# =============================================================================

suppressPackageStartupMessages({
  library(haven)
})

ROOT <- "/Users/brianwiggins/Desktop/Claude Code/EIM2"

# -----------------------------------------------------------------------------
# Load
# -----------------------------------------------------------------------------
df23 <- read.csv(file.path(ROOT, "data/EIM23.csv"), stringsAsFactors = FALSE)
df23 <- df23[df23$ethnicity_binary %in% c(0, 1), ]

df20_raw <- read_sav(file.path(ROOT, "data/EIM 2020_20.10.25.sav copy"),
                     encoding = "latin1")
df20 <- as.data.frame(df20_raw)
df20$ethnicity_binary <- ifelse(df20$T9_1 == 1, 0,
                          ifelse(df20$T9_2 == 1, 1, NA))
df20 <- df20[!is.na(df20$ethnicity_binary), ]

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
recode <- function(x, dk = 9) {
  x <- suppressWarnings(as.numeric(as.character(x)))
  x[x == dk] <- NA
  x
}
revcode <- function(x, scale_max = 4) (scale_max + 1) - x

# -----------------------------------------------------------------------------
# Build per-wave dataframes with consistent column names
# -----------------------------------------------------------------------------
build_2023 <- function(d) {
  est <- d$ethnicity_binary == 0
  out <- data.frame(
    year = 2023L,
    group_num = d$ethnicity_binary,
    group = factor(d$ethnicity_binary, levels = c(0, 1),
                   labels = c("Estonian", "Russian")),
    # Superordinate Identity
    si1 = recode(d$Q67_2),
    si2 = revcode(recode(d$Q67_4)),
    si3 = recode(d$Q67_5),
    # SD: Primary (group-specific)
    sdp1 = ifelse(est, recode(d$Q57_1), recode(d$Q57_2)),
    sdp2 = ifelse(est, recode(d$Q58_1), recode(d$Q58_2)),
    sdp3 = ifelse(est, recode(d$Q59_1), recode(d$Q59_2)),
    # SD: General — 2023 items
    sdg1 = recode(d$Q57_4), sdg2 = recode(d$Q57_5),
    sdg3 = recode(d$Q58_4), sdg4 = recode(d$Q58_5),
    sdg5 = recode(d$Q59_4), sdg6 = recode(d$Q59_5),
    # SD: General — 2020 items (NA in 2023 rows)
    sdg2020_1 = NA_real_, sdg2020_2 = NA_real_, sdg2020_3 = NA_real_,
    # Belief in Inevitable Conflict
    bic1 = revcode(recode(d$Q63_1)),
    bic2 = revcode(recode(d$Q63_2)),
    bic3 = recode(d$Q63_3),
    bic4 = recode(d$Q63_4),
    # Minority Support
    ms1 = recode(d$Q68_1), ms2 = recode(d$Q68_2), ms3 = recode(d$Q68_3)
  )
  # Comparative Opportunity (12 items)
  for (i in 1:12) out[[paste0("co", i)]] <- recode(d[[paste0("Q44_", i)]])
  # Contact: Estonian Speakers (6 items)
  for (i in 1:6) out[[paste0("ce", i)]] <- recode(d[[paste0("Q51_", i)]])
  # Contact: Russian Speakers (6 items)
  for (i in 1:6) out[[paste0("cr", i)]] <- recode(d[[paste0("Q52_", i)]])
  out
}

build_2020 <- function(d) {
  est <- d$ethnicity_binary == 0
  out <- data.frame(
    year = 2020L,
    group_num = d$ethnicity_binary,
    group = factor(d$ethnicity_binary, levels = c(0, 1),
                   labels = c("Estonian", "Russian")),
    si1 = recode(d$K6X5_2),
    si2 = revcode(recode(d$K6X5_3)),
    si3 = recode(d$K6X5_4),
    sdp1 = ifelse(est, recode(d$K4X7_1), recode(d$K4X7_2)),
    sdp2 = ifelse(est, recode(d$K4X8_1), recode(d$K4X8_2)),
    sdp3 = ifelse(est, recode(d$K4X9_1), recode(d$K4X9_2)),
    # SD: General — 2023 items not present in 2020
    sdg1 = NA_real_, sdg2 = NA_real_, sdg3 = NA_real_,
    sdg4 = NA_real_, sdg5 = NA_real_, sdg6 = NA_real_,
    # SD: General — 2020 items
    sdg2020_1 = recode(d$K4X7_3),
    sdg2020_2 = recode(d$K4X8_3),
    sdg2020_3 = recode(d$K4X9_3),
    bic1 = revcode(recode(d$K6X1_1)),
    bic2 = revcode(recode(d$K6X1_2)),
    bic3 = recode(d$K6X1_3),
    bic4 = recode(d$K6X1_4),
    ms1 = recode(d$K6X6_1), ms2 = recode(d$K6X6_2), ms3 = recode(d$K6X6_3)
  )
  for (i in 1:12) out[[paste0("co", i)]] <- recode(d[[paste0("K3X1_", i)]])
  for (i in 1:6) out[[paste0("ce", i)]] <- recode(d[[paste0("K4X1_", i)]])
  for (i in 1:6) out[[paste0("cr", i)]] <- recode(d[[paste0("K4X2_", i)]])
  out
}

d23 <- build_2023(df23)
d20 <- build_2020(df20)

# Verify column alignment before stacking
stopifnot(identical(names(d23), names(d20)))

# -----------------------------------------------------------------------------
# Stack
# -----------------------------------------------------------------------------
stacked <- rbind(d20, d23)

cat("Stacked dataset summary:\n")
cat(sprintf("  Total N: %d rows, %d cols\n", nrow(stacked), ncol(stacked)))
cat(sprintf("  2020 N : %d (%d Est, %d Rus)\n",
            sum(stacked$year == 2020),
            sum(stacked$year == 2020 & stacked$group == "Estonian"),
            sum(stacked$year == 2020 & stacked$group == "Russian")))
cat(sprintf("  2023 N : %d (%d Est, %d Rus)\n",
            sum(stacked$year == 2023),
            sum(stacked$year == 2023 & stacked$group == "Estonian"),
            sum(stacked$year == 2023 & stacked$group == "Russian")))

cat("\nCross-tab of year × group:\n")
print(table(stacked$year, stacked$group))

cat("\nColumn names (first 25):\n")
print(head(names(stacked), 25))
cat("...\n")
cat(sprintf("Total columns: %d\n", ncol(stacked)))

# -----------------------------------------------------------------------------
# Save
# -----------------------------------------------------------------------------
out_path <- file.path(ROOT, "data", "EIM_stacked.csv")
write.csv(stacked, out_path, row.names = FALSE)
cat(sprintf("\nSaved: %s\n", out_path))

# Quick item-level non-NA counts to confirm wave-specific patterns
cat("\nNon-NA counts per year for SD: General items (sanity check):\n")
sd_items <- c("sdg1","sdg2","sdg3","sdg4","sdg5","sdg6",
              "sdg2020_1","sdg2020_2","sdg2020_3")
for (it in sd_items) {
  n23 <- sum(!is.na(stacked[[it]][stacked$year == 2023]))
  n20 <- sum(!is.na(stacked[[it]][stacked$year == 2020]))
  cat(sprintf("  %-12s  N(2020)=%4d   N(2023)=%4d\n", it, n20, n23))
}
