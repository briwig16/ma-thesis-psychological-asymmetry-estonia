"""
Compare reliability statistics computed on the pooled (stacked) dataset
vs. the per-cell (group × year) values already in _latent_means_alpha.tsv.

For each composite, computes:
  - Cronbach's alpha on the FULL pooled sample (all 2707 respondents)
  - PC1 variance explained on the FULL pooled sample
  - Side-by-side with cell-specific alphas already computed

For SD: General (different items per wave), pooling across waves is not
applicable; reports per-wave pooled values instead.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = Path("/Users/brianwiggins/Desktop/Claude Code/EIM2")
df = pd.read_csv(ROOT / "data" / "EIM_stacked.csv")
cell_alpha = pd.read_csv(ROOT / "code" / "_latent_means_alpha.tsv", sep="\t")


def cronbach_alpha(X: pd.DataFrame):
    X = X.dropna()
    n, k = X.shape
    if n < 2 or k < 2:
        return np.nan, n
    item_var = X.var(ddof=1, axis=0)
    total_var = X.sum(axis=1).var(ddof=1)
    alpha = (k / (k - 1)) * (1 - item_var.sum() / total_var)
    return alpha, n


def pc1_var_explained(X: pd.DataFrame):
    X = X.dropna()
    if len(X) < 3 or X.shape[1] < 2:
        return np.nan, len(X)
    Z = StandardScaler().fit_transform(X.values)
    pca = PCA(n_components=1).fit(Z)
    return pca.explained_variance_ratio_[0], len(X)


SPECS = [
    ("Superordinate Identity",            ["si1","si2","si3"]),
    ("SD: Primary Out-group",             ["sdp1","sdp2","sdp3"]),
    ("Comparative Opportunity Assessment", [f"co{i}" for i in range(1,13)]),
    ("Belief in Inevitable Conflict",     ["bic1","bic2","bic3","bic4"]),
    ("Minority Support Inclusion",        ["ms1","ms2","ms3"]),
    ("Contact: Estonian Speakers",        [f"ce{i}" for i in range(1,7)]),
    ("Contact: Russian Speakers",         [f"cr{i}" for i in range(1,7)]),
]

rows = []
for name, items in SPECS:
    a, n_a = cronbach_alpha(df[items])
    v, n_v = pc1_var_explained(df[items])
    rows.append({
        "composite": name,
        "k_items": len(items),
        "pooled_N": n_a,
        "pooled_alpha": a,
        "pooled_pc1_var": v,
    })

# SD: General — wave-specific pooling
for yr, sdg_items in [(2023, [f"sdg{i}" for i in range(1,7)]),
                       (2020, ["sdg2020_1","sdg2020_2","sdg2020_3"])]:
    sub = df[df["year"] == yr]
    a, n_a = cronbach_alpha(sub[sdg_items])
    v, n_v = pc1_var_explained(sub[sdg_items])
    rows.append({
        "composite": f"SD: General Out-group ({yr})",
        "k_items": len(sdg_items),
        "pooled_N": n_a,
        "pooled_alpha": a,
        "pooled_pc1_var": v,
    })

pooled = pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# Side-by-side comparison with cell-specific alphas
# -----------------------------------------------------------------------------
def cell_alpha_table(comp_name, year=None):
    sub = cell_alpha[cell_alpha["composite"].str.startswith(comp_name)]
    if year is not None:
        sub = sub[sub["year"] == year]
    return sub[["year", "group", "alpha", "n"]]


print("=" * 80)
print("POOLED-SAMPLE RELIABILITY SUMMARY")
print("=" * 80)
print(pooled.round(3).to_string(index=False))


print("\n" + "=" * 80)
print("SIDE-BY-SIDE: CELL-SPECIFIC vs POOLED CRONBACH'S α")
print("=" * 80)

for name, items in SPECS:
    print(f"\n--- {name} ---")
    cell = cell_alpha[cell_alpha["composite"] == name]
    cell = cell[["year", "group", "alpha", "n"]].copy()
    pooled_row = pooled[pooled["composite"] == name].iloc[0]
    print(cell.round(3).to_string(index=False))
    print(f"  POOLED across all 4 cells:  α = {pooled_row['pooled_alpha']:.3f}   N = {pooled_row['pooled_N']}")

# SD: General per wave
print(f"\n--- SD: General Out-group ---")
for yr in [2023, 2020]:
    sub = cell_alpha[(cell_alpha["composite"] == "SD: General Out-group") &
                     (cell_alpha["year"] == yr)]
    pooled_yr = pooled[pooled["composite"] == f"SD: General Out-group ({yr})"].iloc[0]
    print(f"\n  {yr}:")
    print(sub[["year","group","alpha","n"]].round(3).to_string(index=False))
    print(f"    POOLED across both groups within {yr}: α = {pooled_yr['pooled_alpha']:.3f}   N = {pooled_yr['pooled_N']}")


# -----------------------------------------------------------------------------
# Save TSV
# -----------------------------------------------------------------------------
out = ROOT / "code" / "_pooled_reliability.tsv"
pooled.to_csv(out, sep="\t", index=False)
print(f"\nSaved: {out}")
