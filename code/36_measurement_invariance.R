# =============================================================================
# Measurement Invariance Testing — Multi-Group and Longitudinal CFA
# =============================================================================
# Tests configural / metric / scalar measurement invariance for the 8 multi-item
# composites used in the project, across:
#
#   - Multi-group: Estonian vs. Russian (within each wave)
#   - Longitudinal: 2020 vs. 2023 (within each group)
#
# Output: code/_invariance_results.tsv
#
# Each row corresponds to one composite × one comparison × one invariance level
# (configural, metric, scalar) and reports:
#   chi-square, df, p, CFI, TLI, RMSEA, SRMR
#   Δchi-square, Δdf, Δp, ΔCFI, ΔRMSEA  vs. previous (less constrained) level
#
# Decision criteria (Cheung & Rensvold 2002; Chen 2007):
#   Metric invariance holds if ΔCFI ≥ -.01 AND ΔRMSEA ≤ +.015
#   Scalar invariance holds if ΔCFI ≥ -.01 AND ΔRMSEA ≤ +.015
#
# Caveats:
#   - SD: Primary Out-group uses GROUP-SPECIFIC items (Q57/Q58/Q59 _1 for
#     Estonians vs _2 for Russians). Multi-group invariance is conceptually
#     awkward; only longitudinal invariance within each group is tested.
#   - SD: General Out-group has DIFFERENT item counts across waves (3 in 2020,
#     6 in 2023). Longitudinal invariance is not testable; only multi-group
#     invariance within each year.
#
# 3-indicator composites (Superordinate Identity, SD: Primary, Minority Support,
# SD: General 2020) are just-identified at the configural level (df = 0); the
# fit indices for that level are uninformative, but invariance tests via
# chi-square difference still work and are reported.
# =============================================================================

suppressPackageStartupMessages({
  library(lavaan)
  library(haven)
})

ROOT <- "/Users/brianwiggins/Desktop/Claude Code/EIM2"

# -----------------------------------------------------------------------------
# Load both waves
# -----------------------------------------------------------------------------
df23 <- read.csv(file.path(ROOT, "data/EIM23.csv"), stringsAsFactors = FALSE)
df23 <- df23[df23$ethnicity_binary %in% c(0, 1), ]

df20_raw <- read_sav(file.path(ROOT, "data/EIM 2020_20.10.25.sav copy"),
                     encoding = "latin1")
df20 <- as.data.frame(df20_raw)
df20$ethnicity_binary <- ifelse(df20$T9_1 == 1, 0,
                          ifelse(df20$T9_2 == 1, 1, NA))
df20 <- df20[!is.na(df20$ethnicity_binary), ]

# Convenience numeric coercion + DK→NA
recode <- function(x, dk = 9) {
  x <- suppressWarnings(as.numeric(as.character(x)))
  x[x == dk] <- NA
  x
}
revcode <- function(x, scale_max = 4) (scale_max + 1) - x

# -----------------------------------------------------------------------------
# Build a long-format dataframe with all relevant items, preprocessed
# (reverse-coded where needed) so all items in each composite face the same
# direction. We add a `wave` column (2020 or 2023) and `group` (0=Est, 1=Rus).
# -----------------------------------------------------------------------------
mk_2023 <- function(d) {
  out <- data.frame(group = d$ethnicity_binary, wave = 2023L)
  # Superordinate Identity (Q67_4 reversed)
  out$si1 <- recode(d$Q67_2)
  out$si2 <- revcode(recode(d$Q67_4))
  out$si3 <- recode(d$Q67_5)
  # SD: Primary — group-specific. Use est columns for Est rows, rus columns for Rus rows.
  est_mask <- d$ethnicity_binary == 0
  out$sdp1 <- ifelse(est_mask, recode(d$Q57_1), recode(d$Q57_2))
  out$sdp2 <- ifelse(est_mask, recode(d$Q58_1), recode(d$Q58_2))
  out$sdp3 <- ifelse(est_mask, recode(d$Q59_1), recode(d$Q59_2))
  # SD: General (6 items in 2023)
  out$sdg1 <- recode(d$Q57_4); out$sdg2 <- recode(d$Q57_5)
  out$sdg3 <- recode(d$Q58_4); out$sdg4 <- recode(d$Q58_5)
  out$sdg5 <- recode(d$Q59_4); out$sdg6 <- recode(d$Q59_5)
  # Comparative Opportunity
  for (i in 1:12) out[[paste0("co", i)]] <- recode(d[[paste0("Q44_", i)]])
  # Belief in Inevitable Conflict (Option B: reverse Q63_1, Q63_2)
  out$bic1 <- revcode(recode(d$Q63_1))
  out$bic2 <- revcode(recode(d$Q63_2))
  out$bic3 <- recode(d$Q63_3)
  out$bic4 <- recode(d$Q63_4)
  # Minority Support
  out$ms1 <- recode(d$Q68_1); out$ms2 <- recode(d$Q68_2); out$ms3 <- recode(d$Q68_3)
  # Contact: Estonian Speakers
  for (i in 1:6) out[[paste0("ce", i)]] <- recode(d[[paste0("Q51_", i)]])
  # Contact: Russian Speakers
  for (i in 1:6) out[[paste0("cr", i)]] <- recode(d[[paste0("Q52_", i)]])
  out
}

mk_2020 <- function(d) {
  out <- data.frame(group = d$ethnicity_binary, wave = 2020L)
  out$si1 <- recode(d$K6X5_2)
  out$si2 <- revcode(recode(d$K6X5_3))
  out$si3 <- recode(d$K6X5_4)
  est_mask <- d$ethnicity_binary == 0
  out$sdp1 <- ifelse(est_mask, recode(d$K4X7_1), recode(d$K4X7_2))
  out$sdp2 <- ifelse(est_mask, recode(d$K4X8_1), recode(d$K4X8_2))
  out$sdp3 <- ifelse(est_mask, recode(d$K4X9_1), recode(d$K4X9_2))
  # SD: General has only 3 items in 2020 (one item per context, "new immigrants")
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

cat(sprintf("2023: N=%d (%d Est, %d Rus)\n",
            nrow(d23), sum(d23$group==0), sum(d23$group==1)))
cat(sprintf("2020: N=%d (%d Est, %d Rus)\n",
            nrow(d20), sum(d20$group==0), sum(d20$group==1)))


# -----------------------------------------------------------------------------
# Composite specifications
# -----------------------------------------------------------------------------
specs <- list(
  list(name = "Superordinate Identity",
       items = c("si1","si2","si3"),
       cross_wave_items = c("si1","si2","si3"),
       cross_group = TRUE, cross_wave = TRUE),
  list(name = "SD: Primary Out-group",
       items = c("sdp1","sdp2","sdp3"),
       cross_wave_items = c("sdp1","sdp2","sdp3"),
       cross_group = FALSE,            # group-specific items
       cross_wave = TRUE),
  list(name = "SD: General Out-group",
       items_23 = c("sdg1","sdg2","sdg3","sdg4","sdg5","sdg6"),
       items_20 = c("sdg2020_1","sdg2020_2","sdg2020_3"),
       cross_group = TRUE, cross_wave = FALSE),  # different items each wave
  list(name = "Comparative Opportunity Assessment",
       items = paste0("co", 1:12),
       cross_wave_items = paste0("co", 1:12),
       cross_group = TRUE, cross_wave = TRUE),
  list(name = "Belief in Inevitable Conflict",
       items = c("bic1","bic2","bic3","bic4"),
       cross_wave_items = c("bic1","bic2","bic3","bic4"),
       cross_group = TRUE, cross_wave = TRUE),
  list(name = "Minority Support Inclusion",
       items = c("ms1","ms2","ms3"),
       cross_wave_items = c("ms1","ms2","ms3"),
       cross_group = TRUE, cross_wave = TRUE),
  list(name = "Contact: Estonian Speakers",
       items = paste0("ce", 1:6),
       cross_wave_items = paste0("ce", 1:6),
       cross_group = TRUE, cross_wave = TRUE),
  list(name = "Contact: Russian Speakers",
       items = paste0("cr", 1:6),
       cross_wave_items = paste0("cr", 1:6),
       cross_group = TRUE, cross_wave = TRUE)
)


# -----------------------------------------------------------------------------
# Helper: extract fit indices and chi-square diff vs prior model
# -----------------------------------------------------------------------------
fit_row <- function(model_name, level, fit_obj, prior = NULL) {
  fit <- fitMeasures(fit_obj,
    c("chisq","df","pvalue","cfi","tli","rmsea","srmr","aic","bic"))
  out <- list(
    composite = model_name, level = level,
    chisq = unname(fit["chisq"]), df = unname(fit["df"]),
    p = unname(fit["pvalue"]), cfi = unname(fit["cfi"]),
    tli = unname(fit["tli"]), rmsea = unname(fit["rmsea"]),
    srmr = unname(fit["srmr"])
  )
  if (!is.null(prior)) {
    a <- anova(prior, fit_obj)
    out$d_chisq <- a$"Chisq diff"[2]
    out$d_df    <- a$"Df diff"[2]
    out$d_p     <- a$"Pr(>Chisq)"[2]
    fit_p <- fitMeasures(prior, c("cfi","rmsea"))
    out$d_cfi   <- unname(fit["cfi"]) - unname(fit_p["cfi"])
    out$d_rmsea <- unname(fit["rmsea"]) - unname(fit_p["rmsea"])
  } else {
    out$d_chisq <- NA; out$d_df <- NA; out$d_p <- NA
    out$d_cfi <- NA; out$d_rmsea <- NA
  }
  data.frame(out, stringsAsFactors = FALSE)
}

invariance_verdict <- function(d_cfi, d_rmsea) {
  # Cheung & Rensvold 2002, Chen 2007 thresholds
  if (is.na(d_cfi) || is.na(d_rmsea)) return("")
  if (d_cfi >= -0.01 && d_rmsea <= 0.015) return("HOLDS"  )
  if (d_cfi >= -0.02 && d_rmsea <= 0.030) return("PARTIAL")
  return("FAILS")
}


# -----------------------------------------------------------------------------
# Run invariance test for one (data, group_var, items, label) configuration
# Returns a data frame of fit rows + verdicts.
# -----------------------------------------------------------------------------
run_invariance <- function(d, group_var, items, label) {
  out <- data.frame()
  # CFA model: single latent factor F loading on all items
  model <- paste0("F =~ ", paste(items, collapse = " + "))

  # Drop rows where ALL items missing (uninformative)
  valid <- rowSums(!is.na(d[, items, drop=FALSE])) > 0
  d <- d[valid, , drop=FALSE]

  fit_args <- list(model = model, data = d, group = group_var,
                   missing = "fiml", estimator = "MLR")

  # Configural: no equality constraints
  cfg <- tryCatch(do.call(cfa, fit_args), error = function(e) NULL)
  if (is.null(cfg)) {
    out <- rbind(out, data.frame(composite = label, level = "configural",
      chisq=NA,df=NA,p=NA,cfi=NA,tli=NA,rmsea=NA,srmr=NA,
      d_chisq=NA,d_df=NA,d_p=NA,d_cfi=NA,d_rmsea=NA, verdict="ERROR"))
    return(out)
  }
  r1 <- fit_row(label, "configural", cfg)
  r1$verdict <- "—"
  out <- rbind(out, r1)

  # Metric (loadings equal)
  fit_args$group.equal <- "loadings"
  met <- tryCatch(do.call(cfa, fit_args), error = function(e) NULL)
  if (!is.null(met)) {
    r2 <- fit_row(label, "metric", met, prior = cfg)
    r2$verdict <- invariance_verdict(r2$d_cfi, r2$d_rmsea)
    out <- rbind(out, r2)

    # Scalar (loadings + intercepts equal)
    fit_args$group.equal <- c("loadings","intercepts")
    sca <- tryCatch(do.call(cfa, fit_args), error = function(e) NULL)
    if (!is.null(sca)) {
      r3 <- fit_row(label, "scalar", sca, prior = met)
      r3$verdict <- invariance_verdict(r3$d_cfi, r3$d_rmsea)
      out <- rbind(out, r3)
    } else {
      out <- rbind(out, data.frame(composite=label, level="scalar",
        chisq=NA,df=NA,p=NA,cfi=NA,tli=NA,rmsea=NA,srmr=NA,
        d_chisq=NA,d_df=NA,d_p=NA,d_cfi=NA,d_rmsea=NA, verdict="ERROR"))
    }
  } else {
    out <- rbind(out, data.frame(composite=label, level="metric",
      chisq=NA,df=NA,p=NA,cfi=NA,tli=NA,rmsea=NA,srmr=NA,
      d_chisq=NA,d_df=NA,d_p=NA,d_cfi=NA,d_rmsea=NA, verdict="ERROR"))
  }
  out
}


# -----------------------------------------------------------------------------
# Run all configurations
# -----------------------------------------------------------------------------
all_rows <- data.frame()

for (sp in specs) {
  cat("\n========================================\n")
  cat(sp$name, "\n")
  cat("========================================\n")

  if (!is.null(sp$items)) {
    items <- sp$items

    # Multi-group invariance (Est vs Rus)
    if (isTRUE(sp$cross_group)) {
      for (yr in c(2023, 2020)) {
        d <- if (yr == 2023) d23 else d20
        cat(sprintf("\n  Multi-group (Est vs Rus), %d:\n", yr))
        rs <- run_invariance(d, "group", items,
                             sprintf("%s — multi-group %d", sp$name, yr))
        all_rows <- rbind(all_rows, rs)
      }
    }
    # Longitudinal invariance (2020 vs 2023) within each group
    if (isTRUE(sp$cross_wave)) {
      for (g in c(0, 1)) {
        gname <- if (g == 0) "Estonian" else "Russian"
        d_combined <- rbind(
          d23[d23$group == g, c("wave", sp$cross_wave_items)],
          d20[d20$group == g, c("wave", sp$cross_wave_items)]
        )
        cat(sprintf("\n  Longitudinal (2020 vs 2023), %s:\n", gname))
        rs <- run_invariance(d_combined, "wave", sp$cross_wave_items,
                             sprintf("%s — longitudinal %s", sp$name, gname))
        all_rows <- rbind(all_rows, rs)
      }
    }
  }

  # Special-case: SD: General Out-group has different item sets per wave —
  # only multi-group invariance, run separately per wave.
  if (sp$name == "SD: General Out-group") {
    cat("\n  Multi-group (Est vs Rus), 2023 (6 items):\n")
    rs <- run_invariance(d23, "group", sp$items_23,
                         sprintf("%s — multi-group 2023", sp$name))
    all_rows <- rbind(all_rows, rs)
    cat("\n  Multi-group (Est vs Rus), 2020 (3 items):\n")
    rs <- run_invariance(d20, "group", sp$items_20,
                         sprintf("%s — multi-group 2020", sp$name))
    all_rows <- rbind(all_rows, rs)
  }
}

# -----------------------------------------------------------------------------
# Save TSV
# -----------------------------------------------------------------------------
out_path <- file.path(ROOT, "code", "_invariance_results.tsv")
write.table(all_rows, file = out_path, sep = "\t", row.names = FALSE,
            quote = FALSE, na = "")
cat(sprintf("\n\nSaved: %s  (%d rows)\n", out_path, nrow(all_rows)))


# -----------------------------------------------------------------------------
# Print summary
# -----------------------------------------------------------------------------
cat("\n\n", strrep("=", 90), "\n", sep="")
cat("SUMMARY — Measurement Invariance Verdicts\n")
cat(strrep("=", 90), "\n\n", sep="")

for (cmp in unique(all_rows$composite)) {
  rs <- all_rows[all_rows$composite == cmp, ]
  cat(sprintf("%-58s ", cmp))
  for (lvl in c("configural", "metric", "scalar")) {
    r <- rs[rs$level == lvl, ]
    if (nrow(r) == 0) {
      cat(sprintf("  %s: -",  lvl))
    } else {
      cat(sprintf("  %s: %s", lvl, r$verdict))
    }
  }
  cat("\n")
}
