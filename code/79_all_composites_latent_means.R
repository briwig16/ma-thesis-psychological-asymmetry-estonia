# =============================================================================
# All Composites — Latent Means via Multi-Group CFA (Estonian as reference)
# =============================================================================
# For each of the 8 multi-item composites, runs:
#   Step 1: Cronbach's alpha for each group × year cell
#   Step 2: Multi-group CFA invariance (configural / metric / scalar) per year
#   Step 3: Latent-factor intercepts from scalar model (Estonian fixed at 0)
#   Step 4: Estonian − Russian latent-mean gap, by year, plus change in gap
#
# Estonian = reference group (latent mean fixed at 0) — forced via group.label
#
# Outputs:
#   code/_latent_means_alpha.tsv      — Step 1 alphas
#   code/_latent_means_fit.tsv        — Step 2 fit indices
#   code/_latent_means_intercepts.tsv — Step 3 latent means
#   code/_latent_means_gaps.tsv       — Step 4 gaps
#
# Caveats:
#   - SD: Primary uses GROUP-SPECIFIC items (different referent per group);
#     multi-group invariance is still computable but conceptually asymmetric
#   - SD: General Out-group has different item counts per wave (6 in 2023,
#     3 in 2020); each year is tested separately
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

recode  <- function(x, dk = 9) {
  x <- suppressWarnings(as.numeric(as.character(x)))
  x[x == dk] <- NA; x
}
revcode <- function(x, scale_max = 4) (scale_max + 1) - x


# -----------------------------------------------------------------------------
# Build item dataframes (one row per respondent, one column per item),
# including reverse coding where required. Group is a factor with
# Estonian as the FIRST level so it becomes lavaan's reference group
# (when combined with group.label).
# -----------------------------------------------------------------------------
mk_2023 <- function(d) {
  out <- data.frame(group = factor(d$ethnicity_binary, levels = c(0, 1),
                                   labels = c("Estonian", "Russian")))
  est <- d$ethnicity_binary == 0
  # Superordinate Identity (Q67_4 reversed)
  out$si1 <- recode(d$Q67_2)
  out$si2 <- revcode(recode(d$Q67_4))
  out$si3 <- recode(d$Q67_5)
  # SD: Primary — group-specific
  out$sdp1 <- ifelse(est, recode(d$Q57_1), recode(d$Q57_2))
  out$sdp2 <- ifelse(est, recode(d$Q58_1), recode(d$Q58_2))
  out$sdp3 <- ifelse(est, recode(d$Q59_1), recode(d$Q59_2))
  # SD: General (6 items)
  out$sdg1 <- recode(d$Q57_4); out$sdg2 <- recode(d$Q57_5)
  out$sdg3 <- recode(d$Q58_4); out$sdg4 <- recode(d$Q58_5)
  out$sdg5 <- recode(d$Q59_4); out$sdg6 <- recode(d$Q59_5)
  # Comparative Opportunity (12 items)
  for (i in 1:12) out[[paste0("co", i)]] <- recode(d[[paste0("Q44_", i)]])
  # Belief in Inevitable Conflict (Option B: reverse Q63_1, Q63_2)
  out$bic1 <- revcode(recode(d$Q63_1))
  out$bic2 <- revcode(recode(d$Q63_2))
  out$bic3 <- recode(d$Q63_3)
  out$bic4 <- recode(d$Q63_4)
  # Minority Support
  out$ms1 <- recode(d$Q68_1); out$ms2 <- recode(d$Q68_2); out$ms3 <- recode(d$Q68_3)
  # Contact: Estonian Speakers (6 items)
  for (i in 1:6) out[[paste0("ce", i)]] <- recode(d[[paste0("Q51_", i)]])
  # Contact: Russian Speakers (6 items)
  for (i in 1:6) out[[paste0("cr", i)]] <- recode(d[[paste0("Q52_", i)]])
  out
}

mk_2020 <- function(d) {
  out <- data.frame(group = factor(d$ethnicity_binary, levels = c(0, 1),
                                   labels = c("Estonian", "Russian")))
  est <- d$ethnicity_binary == 0
  out$si1 <- recode(d$K6X5_2)
  out$si2 <- revcode(recode(d$K6X5_3))
  out$si3 <- recode(d$K6X5_4)
  out$sdp1 <- ifelse(est, recode(d$K4X7_1), recode(d$K4X7_2))
  out$sdp2 <- ifelse(est, recode(d$K4X8_1), recode(d$K4X8_2))
  out$sdp3 <- ifelse(est, recode(d$K4X9_1), recode(d$K4X9_2))
  # SD: General — 3 items in 2020
  out$sdg2020_1 <- recode(d$K4X7_3)
  out$sdg2020_2 <- recode(d$K4X8_3)
  out$sdg2020_3 <- recode(d$K4X9_3)
  for (i in 1:12) out[[paste0("co", i)]] <- recode(d[[paste0("K3X1_", i)]])
  out$bic1 <- revcode(recode(d$K6X1_1))
  out$bic2 <- revcode(recode(d$K6X1_2))
  out$bic3 <- recode(d$K6X1_3)
  out$bic4 <- recode(d$K6X1_4)
  out$ms1 <- recode(d$K6X6_1); out$ms2 <- recode(d$K6X6_2); out$ms3 <- recode(d$K6X6_3)
  for (i in 1:6) out[[paste0("ce", i)]] <- recode(d[[paste0("K4X1_", i)]])
  for (i in 1:6) out[[paste0("cr", i)]] <- recode(d[[paste0("K4X2_", i)]])
  out
}

d23 <- mk_2023(df23)
d20 <- mk_2020(df20)


# -----------------------------------------------------------------------------
# Composite specifications
# Each composite has items_2023, items_2020 (may differ for SD: General)
# -----------------------------------------------------------------------------
specs <- list(
  list(name  = "Superordinate Identity",
       items_2023 = c("si1","si2","si3"),
       items_2020 = c("si1","si2","si3"),
       note = "Q67_4 / K6X5_3 reverse-coded"),

  list(name  = "SD: Primary Out-group",
       items_2023 = c("sdp1","sdp2","sdp3"),
       items_2020 = c("sdp1","sdp2","sdp3"),
       note = "Group-specific items (Estonians rate Russian-speakers; Russians rate Estonian-speakers)"),

  list(name  = "SD: General Out-group",
       items_2023 = c("sdg1","sdg2","sdg3","sdg4","sdg5","sdg6"),
       items_2020 = c("sdg2020_1","sdg2020_2","sdg2020_3"),
       note = "2023 = 6 items (other Europeans + non-Europeans); 2020 = 3 items (new immigrants). Item set differs across waves."),

  list(name  = "Comparative Opportunity Assessment",
       items_2023 = paste0("co", 1:12),
       items_2020 = paste0("co", 1:12),
       note = "12 items"),

  list(name  = "Belief in Inevitable Conflict",
       items_2023 = c("bic1","bic2","bic3","bic4"),
       items_2020 = c("bic1","bic2","bic3","bic4"),
       note = "Q63_1 + Q63_2 reverse-coded (Option B)"),

  list(name  = "Minority Support Inclusion",
       items_2023 = c("ms1","ms2","ms3"),
       items_2020 = c("ms1","ms2","ms3"),
       note = ""),

  list(name  = "Contact: Estonian Speakers",
       items_2023 = paste0("ce", 1:6),
       items_2020 = paste0("ce", 1:6),
       note = "Lower = more contact"),

  list(name  = "Contact: Russian Speakers",
       items_2023 = paste0("cr", 1:6),
       items_2020 = paste0("cr", 1:6),
       note = "Lower = more contact")
)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
cronbach_alpha <- function(X) {
  X <- X[complete.cases(X), , drop = FALSE]
  k <- ncol(X)
  if (k < 2 || nrow(X) < 2) return(c(alpha = NA_real_, n = nrow(X)))
  item_var  <- apply(X, 2, var)
  total_var <- var(rowSums(X))
  alpha     <- (k / (k - 1)) * (1 - sum(item_var) / total_var)
  c(alpha = alpha, n = nrow(X))
}

run_mg_cfa <- function(d, items, year) {
  d <- d[, c("group", items), drop = FALSE]
  d <- d[rowSums(!is.na(d[, items, drop = FALSE])) > 0, ]
  model <- paste0("F =~ ", paste(items, collapse = " + "))
  args <- list(model = model, data = d, group = "group",
               group.label = c("Estonian", "Russian"),
               missing = "fiml", estimator = "MLR")
  cfg <- tryCatch(do.call(cfa, args), error = function(e) NULL)
  args$group.equal <- "loadings"
  met <- tryCatch(do.call(cfa, args), error = function(e) NULL)
  args$group.equal <- c("loadings","intercepts")
  sca <- tryCatch(do.call(cfa, args), error = function(e) NULL)
  list(cfg = cfg, met = met, sca = sca)
}

fit_indices <- function(f) {
  if (is.null(f)) return(rep(NA_real_, 7))
  fitMeasures(f, c("chisq","df","pvalue","cfi","tli","rmsea","srmr"))
}

lrt_chisq_diff <- function(prior, current) {
  if (is.null(prior) || is.null(current)) return(c(NA, NA, NA))
  a <- tryCatch(anova(prior, current), error = function(e) NULL)
  if (is.null(a)) return(c(NA, NA, NA))
  c(a$"Chisq diff"[2], a$"Df diff"[2], a$"Pr(>Chisq)"[2])
}

extract_latent_intercepts <- function(scalar_fit) {
  if (is.null(scalar_fit)) {
    return(data.frame(group_label = c("Estonian","Russian"),
                      est = NA_real_, se = NA_real_, z = NA_real_,
                      p = NA_real_, ci_lower = NA_real_, ci_upper = NA_real_))
  }
  labels <- lavInspect(scalar_fit, "group.label")
  pe <- parameterEstimates(scalar_fit)
  lm <- pe[pe$op == "~1" & pe$lhs == "F", ]
  data.frame(
    group_label = labels[lm$group],
    est = lm$est, se = lm$se, z = lm$z,
    p = lm$pvalue, ci_lower = lm$ci.lower, ci_upper = lm$ci.upper
  )
}


# -----------------------------------------------------------------------------
# Main loop
# -----------------------------------------------------------------------------
alpha_rows     <- data.frame()
fit_rows       <- data.frame()
intercept_rows <- data.frame()
gap_rows       <- data.frame()

for (sp in specs) {
  cat("\n========================================\n")
  cat(sp$name, "\n")
  cat("========================================\n")

  for (yr in c(2023, 2020)) {
    d <- if (yr == 2023) d23 else d20
    items <- if (yr == 2023) sp$items_2023 else sp$items_2020

    # Step 1: alpha per group
    for (g in c("Estonian","Russian")) {
      X <- d[d$group == g, items, drop = FALSE]
      a <- cronbach_alpha(X)
      alpha_rows <- rbind(alpha_rows, data.frame(
        composite = sp$name, year = yr, group = g,
        n_items = length(items),
        alpha = unname(a["alpha"]), n = unname(a["n"])
      ))
    }

    # Step 2: invariance
    fits <- run_mg_cfa(d, items, yr)
    fc <- fit_indices(fits$cfg); fm <- fit_indices(fits$met); fs <- fit_indices(fits$sca)
    lr_met <- lrt_chisq_diff(fits$cfg, fits$met)
    lr_sca <- lrt_chisq_diff(fits$met, fits$sca)

    fit_rows <- rbind(fit_rows, data.frame(
      composite = sp$name, year = yr, level = "configural",
      chisq = fc[1], df = fc[2], p = fc[3],
      cfi = fc[4], tli = fc[5], rmsea = fc[6], srmr = fc[7],
      d_chisq = NA, d_df = NA, d_p = NA,
      d_cfi = NA, d_rmsea = NA
    ))
    fit_rows <- rbind(fit_rows, data.frame(
      composite = sp$name, year = yr, level = "metric",
      chisq = fm[1], df = fm[2], p = fm[3],
      cfi = fm[4], tli = fm[5], rmsea = fm[6], srmr = fm[7],
      d_chisq = lr_met[1], d_df = lr_met[2], d_p = lr_met[3],
      d_cfi = fm[4] - fc[4], d_rmsea = fm[6] - fc[6]
    ))
    fit_rows <- rbind(fit_rows, data.frame(
      composite = sp$name, year = yr, level = "scalar",
      chisq = fs[1], df = fs[2], p = fs[3],
      cfi = fs[4], tli = fs[5], rmsea = fs[6], srmr = fs[7],
      d_chisq = lr_sca[1], d_df = lr_sca[2], d_p = lr_sca[3],
      d_cfi = fs[4] - fm[4], d_rmsea = fs[6] - fm[6]
    ))

    # Step 3: latent intercepts
    li <- extract_latent_intercepts(fits$sca)
    li$composite <- sp$name; li$year <- yr
    intercept_rows <- rbind(intercept_rows, li)

    # Step 4: gap
    est_mean <- li$est[li$group_label == "Estonian"]
    rus_mean <- li$est[li$group_label == "Russian"]
    if (length(est_mean) == 0) est_mean <- NA
    if (length(rus_mean) == 0) rus_mean <- NA
    gap_rows <- rbind(gap_rows, data.frame(
      composite = sp$name, year = yr,
      estonian_lm = est_mean, russian_lm = rus_mean,
      gap_est_minus_rus = est_mean - rus_mean
    ))
  }

  # Compute change in gap (2023 − 2020)
  g23 <- gap_rows$gap_est_minus_rus[gap_rows$composite == sp$name & gap_rows$year == 2023]
  g20 <- gap_rows$gap_est_minus_rus[gap_rows$composite == sp$name & gap_rows$year == 2020]
  cat(sprintf("  alpha range = (see TSV)   gap_2023=%+.3f   gap_2020=%+.3f   delta=%+.3f\n",
              g23, g20, g23 - g20))
}


# -----------------------------------------------------------------------------
# Write TSVs
# -----------------------------------------------------------------------------
write.table(alpha_rows, file.path(ROOT, "code", "_latent_means_alpha.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE, na = "")
write.table(fit_rows, file.path(ROOT, "code", "_latent_means_fit.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE, na = "")
write.table(intercept_rows, file.path(ROOT, "code", "_latent_means_intercepts.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE, na = "")
write.table(gap_rows, file.path(ROOT, "code", "_latent_means_gaps.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE, na = "")

cat("\nSaved 4 TSVs:\n")
cat("  code/_latent_means_alpha.tsv\n")
cat("  code/_latent_means_fit.tsv\n")
cat("  code/_latent_means_intercepts.tsv\n")
cat("  code/_latent_means_gaps.tsv\n")
