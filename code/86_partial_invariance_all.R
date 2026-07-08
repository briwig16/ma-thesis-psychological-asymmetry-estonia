# =============================================================================
# Partial Scalar Invariance — All 8 Composites (v2: brute-force iterative)
# =============================================================================
# For each composite × year (multi-group: Estonian vs Russian), runs the
# following procedure:
#
#   1. Fit configural, metric, scalar models
#   2. Test scalar invariance (Cheung & Rensvold 2002):
#        SCALAR HOLDS if (ΔCFI ≥ -0.01) AND (ΔRMSEA ≤ 0.015) vs metric
#   3. If scalar fails, identify which item's intercept to free by:
#        For each currently-constrained item, refit the model with that
#        item's intercept freed (group.partial = "item~1"). Compute the
#        chi-square difference vs. the current model. Pick the item
#        producing the LARGEST chi-square drop.
#   4. Free that intercept. Repeat step 3 until either:
#        (a) Cheung & Rensvold thresholds are met, OR
#        (b) only the minimum (2) intercepts remain constrained
#           (required for identification of latent-mean comparison).
#   5. Extract latent means (Russian estimated; Estonian fixed at 0)
#      from the partial-scalar model and compare to fully-scalar means.
#
# Outputs:
#   code/_partial_invariance_summary.tsv
#   code/_partial_invariance_freed.tsv
#   code/_partial_invariance_means.tsv
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
revcode <- function(x, scale_max = 4) (scale_max + 1) - x

mk_2023 <- function(d) {
  out <- data.frame(group = factor(d$ethnicity_binary, levels = c(0, 1),
                                   labels = c("Estonian", "Russian")))
  est <- d$ethnicity_binary == 0
  out$si1 <- recode(d$Q67_2); out$si2 <- revcode(recode(d$Q67_4)); out$si3 <- recode(d$Q67_5)
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
  for (i in 1:6) out[[paste0("ce", i)]] <- recode(d[[paste0("Q51_", i)]])
  for (i in 1:6) out[[paste0("cr", i)]] <- recode(d[[paste0("Q52_", i)]])
  out
}
mk_2020 <- function(d) {
  out <- data.frame(group = factor(d$ethnicity_binary, levels = c(0, 1),
                                   labels = c("Estonian", "Russian")))
  est <- d$ethnicity_binary == 0
  out$si1 <- recode(d$K6X5_2); out$si2 <- revcode(recode(d$K6X5_3)); out$si3 <- recode(d$K6X5_4)
  out$sdp1 <- ifelse(est, recode(d$K4X7_1), recode(d$K4X7_2))
  out$sdp2 <- ifelse(est, recode(d$K4X8_1), recode(d$K4X8_2))
  out$sdp3 <- ifelse(est, recode(d$K4X9_1), recode(d$K4X9_2))
  out$sdg2020_1 <- recode(d$K4X7_3); out$sdg2020_2 <- recode(d$K4X8_3); out$sdg2020_3 <- recode(d$K4X9_3)
  for (i in 1:12) out[[paste0("co", i)]] <- recode(d[[paste0("K3X1_", i)]])
  out$bic1 <- revcode(recode(d$K6X1_1)); out$bic2 <- revcode(recode(d$K6X1_2))
  out$bic3 <- recode(d$K6X1_3); out$bic4 <- recode(d$K6X1_4)
  out$ms1 <- recode(d$K6X6_1); out$ms2 <- recode(d$K6X6_2); out$ms3 <- recode(d$K6X6_3)
  for (i in 1:6) out[[paste0("ce", i)]] <- recode(d[[paste0("K4X1_", i)]])
  for (i in 1:6) out[[paste0("cr", i)]] <- recode(d[[paste0("K4X2_", i)]])
  out
}

d23 <- mk_2023(df23); d20 <- mk_2020(df20)

specs <- list(
  list(name = "Superordinate Identity",         items_2023 = c("si1","si2","si3"),               items_2020 = c("si1","si2","si3")),
  list(name = "SD: Primary Out-group",          items_2023 = c("sdp1","sdp2","sdp3"),            items_2020 = c("sdp1","sdp2","sdp3")),
  list(name = "SD: General Out-group",          items_2023 = paste0("sdg", 1:6),                 items_2020 = c("sdg2020_1","sdg2020_2","sdg2020_3")),
  list(name = "Comparative Opportunity Assessment", items_2023 = paste0("co", 1:12),             items_2020 = paste0("co", 1:12)),
  list(name = "Belief in Inevitable Conflict",  items_2023 = c("bic1","bic2","bic3","bic4"),     items_2020 = c("bic1","bic2","bic3","bic4")),
  list(name = "Minority Support Inclusion",     items_2023 = c("ms1","ms2","ms3"),               items_2020 = c("ms1","ms2","ms3")),
  list(name = "Contact: Estonian Speakers",     items_2023 = paste0("ce", 1:6),                  items_2020 = paste0("ce", 1:6)),
  list(name = "Contact: Russian Speakers",      items_2023 = paste0("cr", 1:6),                  items_2020 = paste0("cr", 1:6))
)

fit_indices <- function(f) {
  if (is.null(f)) return(c(chisq=NA,df=NA,pvalue=NA,cfi=NA,tli=NA,rmsea=NA,srmr=NA))
  fitMeasures(f, c("chisq","df","pvalue","cfi","tli","rmsea","srmr"))
}
passes_scalar <- function(d_cfi, d_rmsea) {
  !is.na(d_cfi) && !is.na(d_rmsea) && (d_cfi >= -0.01) && (d_rmsea <= 0.015)
}
extract_lm <- function(fit) {
  if (is.null(fit)) return(c(estonian = NA, russian = NA))
  pe <- parameterEstimates(fit)
  lm <- pe[pe$op == "~1" & pe$lhs == "F", ]
  labels <- lavInspect(fit, "group.label")
  est_idx <- which(labels == "Estonian"); rus_idx <- which(labels == "Russian")
  c(estonian = lm$est[lm$group == est_idx],
    russian  = lm$est[lm$group == rus_idx])
}

run_partial <- function(d, items, label_prefix) {
  cat("\n--- ", label_prefix, " ---\n", sep = "")
  d <- d[, c("group", items)]
  d <- d[rowSums(!is.na(d[, items, drop = FALSE])) > 0, ]
  model <- paste0("F =~ ", paste(items, collapse = " + "))
  base_args <- list(model = model, data = d, group = "group",
                    group.label = c("Estonian", "Russian"),
                    missing = "fiml", estimator = "MLR")

  cfg <- tryCatch(do.call(cfa, base_args), error = function(e) NULL)
  args_m <- base_args; args_m$group.equal <- "loadings"
  met <- tryCatch(do.call(cfa, args_m), error = function(e) NULL)
  args_s <- base_args; args_s$group.equal <- c("loadings", "intercepts")
  sca <- tryCatch(do.call(cfa, args_s), error = function(e) NULL)

  fm <- fit_indices(met); fs <- fit_indices(sca)
  d_cfi   <- unname(fs["cfi"]   - fm["cfi"])
  d_rmsea <- unname(fs["rmsea"] - fm["rmsea"])
  cat(sprintf("  Metric  CFI=%.3f RMSEA=%.3f\n",  fm["cfi"], fm["rmsea"]))
  cat(sprintf("  Scalar  CFI=%.3f RMSEA=%.3f   ΔCFI=%+.3f  ΔRMSEA=%+.3f\n",
              fs["cfi"], fs["rmsea"], d_cfi, d_rmsea))

  scalar_passes <- passes_scalar(d_cfi, d_rmsea)
  freed <- character(0)
  partial <- sca
  k <- length(items)
  max_to_free <- max(0, k - 2)

  iter <- 0
  while (!scalar_passes && length(freed) < max_to_free) {
    iter <- iter + 1
    constrained <- setdiff(items, freed)
    # Try freeing each constrained intercept; pick the one with largest
    # chi-square drop vs current partial model.
    best_item <- NA; best_chi_drop <- -Inf; best_fit <- NULL
    cur_chi <- fitMeasures(partial, "chisq")
    for (it in constrained) {
      trial_args <- args_s
      trial_args$group.partial <- paste0(c(freed, it), "~1")
      f_trial <- tryCatch(do.call(cfa, trial_args), error = function(e) NULL)
      if (is.null(f_trial) || !lavInspect(f_trial, "converged")) next
      drop <- unname(cur_chi - fitMeasures(f_trial, "chisq"))
      if (drop > best_chi_drop) {
        best_chi_drop <- drop; best_item <- it; best_fit <- f_trial
      }
    }
    if (is.na(best_item) || is.null(best_fit)) break

    freed <- c(freed, best_item)
    partial <- best_fit
    fp <- fit_indices(partial)
    d_cfi_p   <- unname(fp["cfi"]   - fm["cfi"])
    d_rmsea_p <- unname(fp["rmsea"] - fm["rmsea"])
    cat(sprintf("  Iter %d: freed %s (Δχ²=%.2f)   PartialCFI=%.3f RMSEA=%.3f   ΔCFI=%+.3f  ΔRMSEA=%+.3f\n",
                iter, best_item, best_chi_drop, fp["cfi"], fp["rmsea"], d_cfi_p, d_rmsea_p))
    scalar_passes <- passes_scalar(d_cfi_p, d_rmsea_p)
  }

  fp <- fit_indices(partial)
  d_cfi_p   <- unname(fp["cfi"]   - fm["cfi"])
  d_rmsea_p <- unname(fp["rmsea"] - fm["rmsea"])

  lm_full    <- extract_lm(sca)
  lm_partial <- extract_lm(partial)

  list(
    metric_fit = fm, scalar_fit = fs, partial_fit = fp,
    d_cfi_scalar = d_cfi, d_rmsea_scalar = d_rmsea,
    d_cfi_partial = d_cfi_p, d_rmsea_partial = d_rmsea_p,
    freed = freed, n_freed = length(freed), n_items = k,
    scalar_passes_initial = passes_scalar(d_cfi, d_rmsea),
    final_passes = passes_scalar(d_cfi_p, d_rmsea_p),
    lm_scalar = lm_full, lm_partial = lm_partial
  )
}

summary_rows <- data.frame(); freed_rows <- data.frame(); mean_rows <- data.frame()
for (sp in specs) {
  cat("\n========================================\n", sp$name,
      "\n========================================\n", sep = "")
  for (yr in c(2023, 2020)) {
    d <- if (yr == 2023) d23 else d20
    items <- if (yr == 2023) sp$items_2023 else sp$items_2020
    res <- run_partial(d, items, sprintf("%s — %d", sp$name, yr))

    summary_rows <- rbind(summary_rows, data.frame(
      composite = sp$name, year = yr, n_items = res$n_items,
      metric_cfi  = unname(res$metric_fit["cfi"]),
      scalar_cfi  = unname(res$scalar_fit["cfi"]),
      partial_cfi = unname(res$partial_fit["cfi"]),
      d_cfi_scalar = res$d_cfi_scalar, d_cfi_partial = res$d_cfi_partial,
      metric_rmsea = unname(res$metric_fit["rmsea"]),
      scalar_rmsea = unname(res$scalar_fit["rmsea"]),
      partial_rmsea = unname(res$partial_fit["rmsea"]),
      d_rmsea_scalar = res$d_rmsea_scalar, d_rmsea_partial = res$d_rmsea_partial,
      n_freed_intercepts = res$n_freed,
      scalar_holds_initial = res$scalar_passes_initial,
      final_passes = res$final_passes
    ))
    if (length(res$freed) > 0) {
      freed_rows <- rbind(freed_rows, data.frame(
        composite = sp$name, year = yr,
        order = seq_along(res$freed), item_freed = res$freed
      ))
    }
    mean_rows <- rbind(mean_rows, data.frame(
      composite = sp$name, year = yr,
      lm_scalar_estonian  = unname(res$lm_scalar["estonian"]),
      lm_scalar_russian   = unname(res$lm_scalar["russian"]),
      gap_scalar          = unname(res$lm_scalar["estonian"]  - res$lm_scalar["russian"]),
      lm_partial_estonian = unname(res$lm_partial["estonian"]),
      lm_partial_russian  = unname(res$lm_partial["russian"]),
      gap_partial         = unname(res$lm_partial["estonian"] - res$lm_partial["russian"]),
      gap_change          = unname((res$lm_partial["estonian"] - res$lm_partial["russian"]) -
                                   (res$lm_scalar["estonian"]  - res$lm_scalar["russian"]))
    ))
  }
}

write.table(summary_rows, file.path(ROOT, "code", "_partial_invariance_summary.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE, na = "")
write.table(freed_rows, file.path(ROOT, "code", "_partial_invariance_freed.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE, na = "")
write.table(mean_rows, file.path(ROOT, "code", "_partial_invariance_means.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE, na = "")

cat("\nSaved:\n  code/_partial_invariance_summary.tsv\n  code/_partial_invariance_freed.tsv\n  code/_partial_invariance_means.tsv\n")
