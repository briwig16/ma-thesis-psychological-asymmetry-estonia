# =============================================================================
# Multi-group CFA factor scores for each non-contact composite.
# Strategy parallels _pc1_means.py:
#   - For composites whose item set is identical across groups AND years
#     (SI, Comparative Opportunity, BiC, Minority Support): fit a 2-group
#     CFA (Est vs Rus), with metric invariance (loadings equal across groups,
#     intercepts free), pooled across years. This yields a single comparable
#     factor metric.
#   - For SD: Primary Out-group (items differ by group): fit a single-group
#     CFA per group, pooled across years. Between-group factor-score means
#     are NOT comparable.
#   - For SD: General Out-group (items differ across years): fit a 2-group CFA
#     per year. Within-group cross-year means are NOT comparable.
#
# Output: code/_cfa_factor_scores.csv  (one row per respondent with factor
#   scores for each composite, plus group and wave).
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

recode  <- function(x, dk = 9) { x <- suppressWarnings(as.numeric(as.character(x))); x[x == dk] <- NA; x }
revcode <- function(x, smax = 4) (smax + 1) - x

# Build long-format dataframe with all items, reverse-coded as needed
mk23 <- function(d) {
  out <- data.frame(rid = seq_len(nrow(d)),
                    group = d$ethnicity_binary, wave = 2023L)
  out$si1 <- recode(d$Q67_2); out$si2 <- revcode(recode(d$Q67_4)); out$si3 <- recode(d$Q67_5)
  est <- d$ethnicity_binary == 0
  out$sdp1 <- ifelse(est, recode(d$Q57_1), recode(d$Q57_2))
  out$sdp2 <- ifelse(est, recode(d$Q58_1), recode(d$Q58_2))
  out$sdp3 <- ifelse(est, recode(d$Q59_1), recode(d$Q59_2))
  out$sdg1 <- recode(d$Q57_4); out$sdg2 <- recode(d$Q57_5)
  out$sdg3 <- recode(d$Q58_4); out$sdg4 <- recode(d$Q58_5)
  out$sdg5 <- recode(d$Q59_4); out$sdg6 <- recode(d$Q59_5)
  for (i in 1:12) out[[paste0("co", i)]] <- recode(d[[paste0("Q44_", i)]])
  out$bic1 <- revcode(recode(d$Q63_1)); out$bic2 <- revcode(recode(d$Q63_2))
  out$bic3 <- recode(d$Q63_3); out$bic4 <- recode(d$Q63_4)
  out$ms1 <- recode(d$Q68_1); out$ms2 <- recode(d$Q68_2); out$ms3 <- recode(d$Q68_3)
  out
}

mk20 <- function(d) {
  out <- data.frame(rid = seq_len(nrow(d)),
                    group = d$ethnicity_binary, wave = 2020L)
  out$si1 <- recode(d$K6X5_2); out$si2 <- revcode(recode(d$K6X5_3)); out$si3 <- recode(d$K6X5_4)
  est <- d$ethnicity_binary == 0
  out$sdp1 <- ifelse(est, recode(d$K4X7_1), recode(d$K4X7_2))
  out$sdp2 <- ifelse(est, recode(d$K4X8_1), recode(d$K4X8_2))
  out$sdp3 <- ifelse(est, recode(d$K4X9_1), recode(d$K4X9_2))
  out$sdg2020_1 <- recode(d$K4X7_3); out$sdg2020_2 <- recode(d$K4X8_3); out$sdg2020_3 <- recode(d$K4X9_3)
  for (i in 1:12) out[[paste0("co", i)]] <- recode(d[[paste0("K3X1_", i)]])
  out$bic1 <- revcode(recode(d$K6X1_1)); out$bic2 <- revcode(recode(d$K6X1_2))
  out$bic3 <- recode(d$K6X1_3); out$bic4 <- recode(d$K6X1_4)
  out$ms1 <- recode(d$K6X6_1); out$ms2 <- recode(d$K6X6_2); out$ms3 <- recode(d$K6X6_3)
  out
}

d23 <- mk23(df23); d20 <- mk20(df20)

# Use a unique respondent id across pooled data
d23$uid <- paste0("y23_", d23$rid)
d20$uid <- paste0("y20_", d20$rid)

cat(sprintf("2023: %d Est, %d Rus | 2020: %d Est, %d Rus\n",
            sum(d23$group==0), sum(d23$group==1), sum(d20$group==0), sum(d20$group==1)))

# Container for factor scores keyed by uid
fs_all <- data.frame(uid = c(d23$uid, d20$uid),
                     group = c(d23$group, d20$group),
                     wave = c(d23$wave, d20$wave),
                     stringsAsFactors = FALSE)

fit_mg_metric <- function(model, data, items) {
  data_use <- data[, c("uid", "group", items)]
  data_use <- data_use[complete.cases(data_use[, items]), ]
  fit <- cfa(model, data = data_use, group = "group",
             group.equal = c("loadings"),
             missing = "fiml.x",
             estimator = "MLR")
  list(fit = fit,
       scores = data.frame(uid = data_use$uid,
                           score = as.numeric(lavPredict(fit, type = "lv",
                                                        method = "regression")[[1]])))
}

# lavPredict returns a list with one matrix per group when fitted multi-group.
# Need to merge into a single vector aligned with data rows. Re-implement:

fit_and_predict_mg <- function(model_str, data, items) {
  data_use <- data[, c("uid", "group", items)]
  data_use <- data_use[complete.cases(data_use[, items]), ]
  fit <- cfa(model_str, data = data_use, group = "group",
             group.equal = c("loadings","intercepts"),
             estimator = "MLR")
  preds <- lavPredict(fit, type = "lv", method = "regression")
  # `preds` is a list with one matrix per group (named "0" and "1")
  score_vec <- numeric(nrow(data_use))
  for (g in names(preds)) {
    idx <- which(data_use$group == as.numeric(g))
    score_vec[idx] <- preds[[g]][, 1]
  }
  data.frame(uid = data_use$uid, score = score_vec)
}

fit_and_predict_single <- function(model_str, data, items) {
  data_use <- data[, c("uid", "group", items)]
  data_use <- data_use[complete.cases(data_use[, items]), ]
  fit <- cfa(model_str, data = data_use, estimator = "MLR")
  preds <- lavPredict(fit, type = "lv", method = "regression")
  data.frame(uid = data_use$uid, score = as.numeric(preds[, 1]))
}

# -----------------------------------------------------------------------------
# 1. Superordinate Identity — 3 items, identical across groups+years
# -----------------------------------------------------------------------------
pool <- rbind(d23[, c("uid","group","si1","si2","si3")],
              d20[, c("uid","group","si1","si2","si3")])
model <- "SI =~ si1 + si2 + si3"
sc <- fit_and_predict_mg(model, pool, c("si1","si2","si3"))
sc$variable <- "Superordinate Identity"
fs_all <- merge(fs_all, setNames(sc[,c("uid","score")], c("uid","si_score")),
                by = "uid", all.x = TRUE)
cat("SI done\n")

# -----------------------------------------------------------------------------
# 2. SD: Primary Out-group — fit SINGLE-group CFA per group, pooled years
# -----------------------------------------------------------------------------
sdp_scores <- list()
for (g in c(0, 1)) {
  pool_g <- rbind(d23[d23$group == g, c("uid","group","sdp1","sdp2","sdp3")],
                  d20[d20$group == g, c("uid","group","sdp1","sdp2","sdp3")])
  model <- "SDP =~ sdp1 + sdp2 + sdp3"
  sdp_scores[[as.character(g)]] <- fit_and_predict_single(model, pool_g, c("sdp1","sdp2","sdp3"))
}
sdp_all <- do.call(rbind, sdp_scores)
fs_all <- merge(fs_all, setNames(sdp_all[,c("uid","score")], c("uid","sdp_score")),
                by = "uid", all.x = TRUE)
cat("SD Primary done\n")

# -----------------------------------------------------------------------------
# 3. SD: General Out-group — fit multi-group CFA per year
# -----------------------------------------------------------------------------
sdg_scores <- list()
m23 <- "SDG =~ sdg1 + sdg2 + sdg3 + sdg4 + sdg5 + sdg6"
sdg_scores[["2023"]] <- fit_and_predict_mg(m23, d23,
                                            c("sdg1","sdg2","sdg3","sdg4","sdg5","sdg6"))
m20 <- "SDG =~ sdg2020_1 + sdg2020_2 + sdg2020_3"
sdg_scores[["2020"]] <- fit_and_predict_mg(m20, d20,
                                            c("sdg2020_1","sdg2020_2","sdg2020_3"))
sdg_all <- do.call(rbind, sdg_scores)
fs_all <- merge(fs_all, setNames(sdg_all[,c("uid","score")], c("uid","sdg_score")),
                by = "uid", all.x = TRUE)
cat("SD General done\n")

# -----------------------------------------------------------------------------
# 4. Comparative Opportunity — 12 items, identical across groups+years
# -----------------------------------------------------------------------------
items <- paste0("co", 1:12)
pool <- rbind(d23[, c("uid","group", items)], d20[, c("uid","group", items)])
model <- paste0("CO =~ ", paste(items, collapse = " + "))
sc <- fit_and_predict_mg(model, pool, items)
fs_all <- merge(fs_all, setNames(sc[,c("uid","score")], c("uid","co_score")),
                by = "uid", all.x = TRUE)
cat("Comparative Opportunity done\n")

# -----------------------------------------------------------------------------
# 5. Belief in Inevitable Conflict — 4 items
# -----------------------------------------------------------------------------
items <- c("bic1","bic2","bic3","bic4")
pool <- rbind(d23[, c("uid","group", items)], d20[, c("uid","group", items)])
model <- paste0("BIC =~ ", paste(items, collapse = " + "))
sc <- fit_and_predict_mg(model, pool, items)
fs_all <- merge(fs_all, setNames(sc[,c("uid","score")], c("uid","bic_score")),
                by = "uid", all.x = TRUE)
cat("BiC done\n")

# -----------------------------------------------------------------------------
# 6. Minority Inclusion Support — 3 items
# -----------------------------------------------------------------------------
items <- c("ms1","ms2","ms3")
pool <- rbind(d23[, c("uid","group", items)], d20[, c("uid","group", items)])
model <- paste0("MS =~ ", paste(items, collapse = " + "))
sc <- fit_and_predict_mg(model, pool, items)
fs_all <- merge(fs_all, setNames(sc[,c("uid","score")], c("uid","ms_score")),
                by = "uid", all.x = TRUE)
cat("Minority Support done\n")


# -----------------------------------------------------------------------------
out_path <- file.path(ROOT, "code/_cfa_factor_scores.csv")
write.csv(fs_all, out_path, row.names = FALSE)
cat(sprintf("\nSaved: %s  (%d rows)\n", out_path, nrow(fs_all)))
