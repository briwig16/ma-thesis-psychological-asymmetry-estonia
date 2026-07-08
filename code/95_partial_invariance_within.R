# =============================================================================
# Partial Scalar Invariance — Within-group (2020 vs 2023, by ethnicity)
# =============================================================================
# Mirror of code/86_partial_invariance_all.R, but with year as the grouping
# variable and ethnicity as the partition. For each composite × ethnicity:
#
#   1. Fit configural / metric / scalar models (year = group)
#   2. Test scalar invariance: HOLDS if (ΔCFI ≥ -0.01) AND (ΔRMSEA ≤ 0.015)
#   3. If scalar fails, iteratively free intercepts (largest χ² drop first)
#      until thresholds are met or only k-2 intercepts remain constrained.
#
# SD: General Out-group is skipped (item set differs across waves).
#
# Outputs:
#   code/_partial_invariance_within_summary.tsv
#   code/_partial_invariance_within_freed.tsv
# =============================================================================

suppressPackageStartupMessages({
  library(lavaan)
})

ROOT <- "/Users/brianwiggins/Desktop/Claude Code/EIM2"
d <- read.csv(file.path(ROOT, "data/EIM_stacked.csv"), stringsAsFactors = FALSE)

specs <- list(
  list(name = "Superordinate Identity",            items = c("si1","si2","si3")),
  list(name = "SD: Primary Out-group",             items = c("sdp1","sdp2","sdp3")),
  list(name = "Comparative Opportunity Assessment", items = paste0("co", 1:12)),
  list(name = "Belief in Inevitable Conflict",     items = c("bic1","bic2","bic3","bic4")),
  list(name = "Minority Support Inclusion",        items = c("ms1","ms2","ms3")),
  list(name = "Contact: Estonian Speakers",        items = paste0("ce", 1:6)),
  list(name = "Contact: Russian Speakers",         items = paste0("cr", 1:6))
)

fit_indices <- function(f) {
  if (is.null(f)) return(c(chisq=NA,df=NA,pvalue=NA,cfi=NA,tli=NA,rmsea=NA,srmr=NA))
  fitMeasures(f, c("chisq","df","pvalue","cfi","tli","rmsea","srmr"))
}
passes_scalar <- function(d_cfi, d_rmsea) {
  !is.na(d_cfi) && !is.na(d_rmsea) && (d_cfi >= -0.01) && (d_rmsea <= 0.015)
}

run_partial_within <- function(sub, items, label) {
  cat("\n--- ", label, " ---\n", sep = "")
  sub <- sub[, c("year", items)]
  sub <- sub[rowSums(!is.na(sub[, items, drop = FALSE])) > 0, ]
  model <- paste0("F =~ ", paste(items, collapse = " + "))
  base_args <- list(model = model, data = sub, group = "year",
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
  while (!scalar_passes && length(freed) < max_to_free && !is.null(partial)) {
    iter <- iter + 1
    constrained <- setdiff(items, freed)
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

  list(
    metric_fit = fm, scalar_fit = fs, partial_fit = fp,
    d_cfi_scalar = d_cfi, d_rmsea_scalar = d_rmsea,
    d_cfi_partial = d_cfi_p, d_rmsea_partial = d_rmsea_p,
    freed = freed, n_freed = length(freed), n_items = k,
    scalar_passes_initial = passes_scalar(d_cfi, d_rmsea),
    final_passes = passes_scalar(d_cfi_p, d_rmsea_p)
  )
}

summary_rows <- data.frame(); freed_rows <- data.frame()
for (sp in specs) {
  cat("\n========================================\n", sp$name,
      "\n========================================\n", sep = "")
  for (grp in c("Estonian", "Russian")) {
    sub <- d[d$group == grp, ]
    res <- run_partial_within(sub, sp$items, sprintf("%s — %s", sp$name, grp))

    summary_rows <- rbind(summary_rows, data.frame(
      composite = sp$name, group = grp, n_items = res$n_items,
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
        composite = sp$name, group = grp,
        order = seq_along(res$freed), item_freed = res$freed
      ))
    }
  }
}

write.table(summary_rows, file.path(ROOT, "code", "_partial_invariance_within_summary.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE, na = "")
write.table(freed_rows, file.path(ROOT, "code", "_partial_invariance_within_freed.tsv"),
            sep = "\t", row.names = FALSE, quote = FALSE, na = "")
cat("\nSaved:\n  code/_partial_invariance_within_summary.tsv\n  code/_partial_invariance_within_freed.tsv\n")
