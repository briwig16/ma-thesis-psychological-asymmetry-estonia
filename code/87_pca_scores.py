"""
Compute and save standardized PC1 scores for all 8 composites.

Reads data/EIM_stacked.csv. For each construct, fits PCA on the item set
pooled across both waves and both ethnic groups, extracts the first
principal component score per respondent, and saves all scores to
data/EIM_pca_scores.csv.

Specification:
- Single PC1 score per construct
- Standardized (mean 0, SD 1) — sklearn default
- Pooled PCA (single set of loadings across all respondents) for the
  7 composites with shared items across waves
- SD: General Out-group has different items in 2020 (3) vs 2023 (6),
  so its PC1 is computed separately within each wave; the resulting
  scores are stacked into a single column (pc_sdg)
- Sign convention: aligned so higher PC1 = higher composite mean
  (matches existing project direction conventions)
- Missing data: listwise deletion within each PCA fit (rows with any NA
  on the construct's items get NA for that construct's PC1)
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = Path("/Users/brianwiggins/Desktop/Claude Code/EIM2")
STACKED = ROOT / "data" / "EIM_stacked.csv"
OUT = ROOT / "data" / "EIM_pca_scores.csv"

df = pd.read_csv(STACKED)

# Composite specifications: (column name to write, list of item columns,
# whether items are wave-shared or wave-specific)
SPECS = [
    ("pc_si",  ["si1", "si2", "si3"],                          "shared"),
    ("pc_sdp", ["sdp1", "sdp2", "sdp3"],                       "shared"),
    ("pc_sdg", None,                                            "wave_specific"),  # handled separately
    ("pc_co",  [f"co{i}"  for i in range(1, 13)],              "shared"),
    ("pc_bic", ["bic1", "bic2", "bic3", "bic4"],               "shared"),
    ("pc_ms",  ["ms1", "ms2", "ms3"],                          "shared"),
    ("pc_ce",  [f"ce{i}"  for i in range(1, 7)],               "shared"),
    ("pc_cr",  [f"cr{i}"  for i in range(1, 7)],               "shared"),
]

# Wave-specific item sets for SD: General
SDG_ITEMS_2023 = [f"sdg{i}" for i in range(1, 7)]
SDG_ITEMS_2020 = ["sdg2020_1", "sdg2020_2", "sdg2020_3"]


def fit_pca_pc1(item_data: pd.DataFrame):
    """Fit PCA, return PC1 scores aligned with the composite mean direction.
    Returns:
        scores: pd.Series indexed by item_data.index, NA where any item is NA
        diagnostics: dict with loadings, variance_explained, sign_flip, n
    """
    valid = item_data.dropna()
    n = len(valid)
    if n < 3 or item_data.shape[1] < 2:
        return pd.Series(np.nan, index=item_data.index), {
            "loadings": None, "var_explained": None, "sign_flip": None, "n": n
        }

    # Standardize items
    scaler = StandardScaler()
    Z = scaler.fit_transform(valid.values)

    # PCA, take first component
    pca = PCA(n_components=1)
    scores_valid = pca.fit_transform(Z).ravel()
    loadings = pca.components_[0]
    var_explained = pca.explained_variance_ratio_[0]

    # Sign-align: ensure PC1 is positively correlated with the simple
    # composite mean (so higher PC1 = higher composite, matching project
    # direction conventions)
    composite_mean = valid.mean(axis=1).values
    corr = np.corrcoef(scores_valid, composite_mean)[0, 1]
    sign_flip = corr < 0
    if sign_flip:
        scores_valid = -scores_valid
        loadings = -loadings

    # Re-standardize the (possibly sign-flipped) scores to mean 0, SD 1
    scores_valid = (scores_valid - scores_valid.mean()) / scores_valid.std(ddof=0)

    # Map back to full-length series with NA for incomplete rows
    out = pd.Series(np.nan, index=item_data.index)
    out.loc[valid.index] = scores_valid

    return out, {
        "loadings": dict(zip(item_data.columns, loadings)),
        "var_explained": var_explained,
        "sign_flip": sign_flip,
        "n": n,
    }


# -----------------------------------------------------------------------------
# Compute PCA scores for the 7 wave-shared composites
# -----------------------------------------------------------------------------
diagnostics = {}
for col_name, items, kind in SPECS:
    if kind != "shared":
        continue
    scores, diag = fit_pca_pc1(df[items])
    df[col_name] = scores
    diagnostics[col_name] = {"items": items, **diag}

# -----------------------------------------------------------------------------
# SD: General — wave-specific PCA
# -----------------------------------------------------------------------------
df["pc_sdg"] = np.nan

# 2023
mask23 = df["year"] == 2023
scores23, diag23 = fit_pca_pc1(df.loc[mask23, SDG_ITEMS_2023])
df.loc[mask23, "pc_sdg"] = scores23.values
diagnostics["pc_sdg_2023"] = {"items": SDG_ITEMS_2023, **diag23}

# 2020
mask20 = df["year"] == 2020
scores20, diag20 = fit_pca_pc1(df.loc[mask20, SDG_ITEMS_2020])
df.loc[mask20, "pc_sdg"] = scores20.values
diagnostics["pc_sdg_2020"] = {"items": SDG_ITEMS_2020, **diag20}

# -----------------------------------------------------------------------------
# Save
# -----------------------------------------------------------------------------
score_cols = ["year", "group_num", "group",
              "pc_si", "pc_sdp", "pc_sdg", "pc_co", "pc_bic", "pc_ms",
              "pc_ce", "pc_cr"]
df[score_cols].to_csv(OUT, index=False)
print(f"Saved: {OUT}")
print(f"Rows: {len(df)}; PC score columns: {len([c for c in score_cols if c.startswith('pc_')])}")

# -----------------------------------------------------------------------------
# Print diagnostics
# -----------------------------------------------------------------------------
print("\n" + "=" * 80)
print("PCA DIAGNOSTICS")
print("=" * 80)
for name, diag in diagnostics.items():
    print(f"\n{name}  (N = {diag['n']}, var explained = {diag['var_explained']:.3f}, "
          f"sign_flipped = {diag['sign_flip']})")
    print("  Loadings (sign-aligned):")
    for it, ld in diag["loadings"].items():
        print(f"    {it:12s}  {ld:+.3f}")

# -----------------------------------------------------------------------------
# Quick descriptive table of saved scores
# -----------------------------------------------------------------------------
print("\n" + "=" * 80)
print("DESCRIPTIVE STATS — PC1 scores (should be ≈ mean 0, SD 1 per column)")
print("=" * 80)
desc = df[[c for c in score_cols if c.startswith("pc_")]].describe().T
print(desc[["count", "mean", "std", "min", "max"]].round(3))

# Means by group_year
print("\nMeans by group × year:")
df["group_year"] = df.apply(
    lambda r: ("E" if r["group_num"] == 0 else "R") +
              ("20" if r["year"] == 2020 else "23"),
    axis=1
)
print(df.groupby("group_year")[[c for c in score_cols if c.startswith("pc_")]]
        .mean().round(3))
