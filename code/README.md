# EIM2 Code Directory

## Quick Start

```bash
pip install -r ../requirements.txt
cd code
python3 build_all.py
```

This runs the full pipeline from raw data to final composites and diagnostics.

## Script Execution Order

Scripts are numbered to indicate logical order. **Bold** scripts modify the CSV — all others are diagnostic (print-only).

### Stage 1: Data Preparation (must run first, in order)

These add derived columns to `data/EIM23.csv`. Each depends on the previous.

| Script | Purpose | Writes to CSV? |
|--------|---------|---------------|
| **01_create_ethnicity_binary.py** | Creates `ethnicity_binary` from T8 (Estonian=0, Russian=1) | Yes |
| **02_create_parents_birthplace.py** | Creates `parents_birthplace` from T12 | Yes |
| **03_create_edu_language.py** | Creates `edu_language` from T19 | Yes |

### Stage 2: Composite Construction (depends on Stage 1)

| Script | Purpose | Writes to CSV? |
|--------|---------|---------------|
| **04_composite_and_pca.py** | Builds 3-item `composite_belonging` (DV) + PCA validation | Yes |
| **17_build_2020_composites.py** | Builds all 8 composites from 2020 SPSS file | Yes (new file) |

### Stage 2b: Comparison Tables (depends on Stage 2)

| Script | Purpose | Writes to CSV? |
|--------|---------|---------------|
| 19_comparison_tables.py | Between-group and within-group comparisons for all 8 composites | No (print) |

### Stage 3: PCA/Reliability Diagnostics (print-only, any order)

These validate composite variables. They read from CSV but do not modify it.

| Script | Purpose | Year | Notes |
|--------|---------|------|-------|
| 05_sd_split_pca.py | SD Primary/General two-factor split (varimax) | 2023 | Key analysis — justifies the split |
| 06_outgroup_composite_pca.py | SD pooled 11-item PCA | 2023 | Preliminary/exploratory, superseded by 05 |
| 07_q44_composite_pca.py | Comparative Opportunity PCA | 2023 | |
| 08_q63_composite_pca.py | Belief in Conflict PCA | 2023 | |
| 09_q68_composite_pca.py | Minority Support PCA | 2023 | |
| 10_pca_by_ethnicity.py | Superordinate Identity by group | 2023 | |
| 11_pca_2020_by_ethnicity.py | Superordinate Identity by group | 2020 | Uses T9 ethnicity* |
| 12_outgroup_2020_pca.py | SD out-group PCA | 2020 | Uses T9 ethnicity* |
| 13_outgroup_russian_pca.py | SD Russian-only PCA | 2023 | |
| 14_q44_2020_pca.py | Comparative Opportunity PCA | 2020 | Uses T9 ethnicity* |
| 15_q63_2020_pca.py | Belief in Conflict PCA | 2020 | Uses T9 ethnicity* |
| 16_q68_2020_pca.py | Minority Support PCA | 2020 | Uses T9 ethnicity* |
| 18_pca_full_analysis.py | Full pooled PCA (all respondents) | 2023 | |

*\*All 2020 scripts (11-16 and 17) now use T9_1/T9_2 (self-identified nationality) for ethnicity classification, consistent with the 2023 analysis which uses T8 (self-identified nationality). T7 (communication language) was used in earlier sessions but has been replaced.*

### Regression (in `regression/` subdirectory) — LEGACY

*Regression analysis has been dropped from thesis scope. These scripts use the old 4-item DV and are not part of the active pipeline.*

| Script | Purpose | Notes |
|--------|---------|-------|
| regression_analysis.py | Pooled OLS | Uses composite_belonging as DV |
| regression_estonian.py | Estonian-only OLS | |
| regression_russian.py | Russian-only OLS | |
| visualize_regressions.py | Forest plots, comparison, R-squared | |

### Replication (in `replication/` subdirectory)

| Script | Purpose |
|--------|---------|
| referee2_replicate_composites.py | Round 1: Independent verification of all 8 composites (2023) |
| referee2_round2_verify.py | Round 2: Verify 3-item DV, 2020 composites, SD split (33/33 pass) |
| referee2_replicate_R.R | Cross-language replication in R: alphas, PCA, means, Cohen's d (70/80 pass) |

## Dependencies

See `../requirements.txt`. Install with `pip install -r ../requirements.txt`.

## Data Files

| File | Source | Modified by scripts? |
|------|--------|---------------------|
| `data/EIM23.csv` | 2023 EIM survey | Yes — scripts 01-04 add derived columns |
| `data/EIM 2020_20.10.25.sav copy` | 2020 EIM survey (SPSS) | No — read-only, requires `encoding='latin1'` |
| `data/EIM2020_composites.csv` | Script 17 output | Yes — rebuilt each run |
