# EIM2 — Ethnic Identity & Intergroup Relations in Estonia

A quantitative social-science project analyzing survey data on identity,
intergroup attitudes, and contact between Estonia's ethnic-majority
(Estonian) and Russian-speaking-minority populations, across two survey
waves (2020 and 2023).

The codebase covers the full analysis pipeline: variable construction,
scale validation, measurement invariance testing, group comparisons, and
publication-style reporting — written primarily in **Python** with an
**R (`lavaan`)** layer for confirmatory factor analysis and latent-means work.

> **Data availability.** The underlying survey data are owned by the
> Estonian government and used under a restricted-access agreement. **No raw
> data, codebook, or individual-level files are included in this repository.**
> The figures and reports here present only *aggregated, derived results*; the
> scripts expect a local `data/` directory that is not distributed.

## What the analysis does

- **Variable construction** — derives ethnicity, parental birthplace, and
  education-language variables; builds eight theoretically-motivated composite
  scales (e.g. superordinate identity, comparative opportunity, belief in
  intergroup conflict, minority support, and social-distance measures).
- **Scale validation** — PCA, Cronbach's alpha, and item-level diagnostics to
  justify each composite, separately for the 2020 and 2023 waves.
- **Measurement invariance** — multi-group and MIMIC CFA models (in R/`lavaan`)
  testing whether the scales measure the same construct across ethnic groups
  and across years, with partial-invariance follow-ups.
- **Group comparisons** — between- and within-group contrasts, 2×2 ANOVAs,
  effect sizes with confidence intervals (Cohen's *d*), and latent-mean
  comparisons.
- **Contact theory** — regression models testing whether intergroup contact
  predicts attitudes, with moderation and control-variable sensitivity checks.
- **Independent replication** — a cross-language replication track
  (`code/replication/`) re-implements key results in R to catch
  language-specific coding errors.

## Repository structure

| Path | Contents |
|------|----------|
| `code/` | Analysis scripts — numbered Python pipeline + R CFA/invariance scripts |
| `code/regression/` | Regression models (pooled and by group) |
| `code/replication/` | Independent cross-language verification scripts |
| `reports/` | Generated APA-style result tables and summaries (aggregated) |
| `reports/generators/` | Node scripts that build the `.docx` report tables |
| `viz/` | Figures — forest plots, dumbbell/gap charts, density and item plots |
| `requirements.txt` | Python dependencies |

## Running it

The pipeline expects a local `data/` directory (not distributed). With data
in place:

```bash
pip install -r requirements.txt
cd code
python3 build_all.py     # runs prep -> composites -> diagnostics
```

Scripts are numbered to indicate execution order; those that construct
variables run first and in sequence, and the rest are largely
print-only diagnostics.

## Tools

Python (pandas, numpy, statsmodels, scipy, matplotlib) ·
R (`lavaan`, `psych`) · CFA & measurement invariance · PCA & reliability ·
ANOVA · multiple regression · effect sizes · survey methodology ·
reproducible reporting
