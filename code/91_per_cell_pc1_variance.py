"""
Per-cell PC1 % variance for all 8 composites.

For each composite × cell (Estonian/Russian × 2020/2023), runs PCA
(listwise deletion) and reports:
  - N (complete cases)
  - PC1 eigenvalue
  - PC1 % of total variance

Output: code/_per_cell_pc1.tsv
"""

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

ROOT = Path("/Users/brianwiggins/Desktop/Claude Code/EIM2")
df = pd.read_csv(ROOT / "data" / "EIM_stacked.csv")

COMPOSITES_2023 = {
    "Superordinate Identity":            ["si1", "si2", "si3"],
    "SD: Primary Out-group":             ["sdp1", "sdp2", "sdp3"],
    "SD: General Out-group":             ["sdg1", "sdg2", "sdg3", "sdg4", "sdg5", "sdg6"],
    "Comparative Opportunity Assessment": [f"co{i}" for i in range(1, 13)],
    "Belief in Inevitable Conflict":     ["bic1", "bic2", "bic3", "bic4"],
    "Minority Support Inclusion":        ["ms1", "ms2", "ms3"],
    "Contact: Estonian Speakers":        [f"ce{i}" for i in range(1, 7)],
    "Contact: Russian Speakers":         [f"cr{i}" for i in range(1, 7)],
}
COMPOSITES_2020 = dict(COMPOSITES_2023)
COMPOSITES_2020["SD: General Out-group"] = ["sdg2020_1", "sdg2020_2", "sdg2020_3"]


def pc1(items, sub):
    cols = [c for c in items if c in sub.columns]
    X = sub[cols].dropna()
    if len(X) < len(cols) + 1:
        return np.nan, np.nan, len(X), len(cols)
    Xs = StandardScaler().fit_transform(X)
    p = PCA().fit(Xs)
    return p.explained_variance_[0], p.explained_variance_ratio_[0] * 100, len(X), len(cols)


rows = []
for year in (2020, 2023):
    spec = COMPOSITES_2023 if year == 2023 else COMPOSITES_2020
    for group in ("Estonian", "Russian"):
        sub = df[(df["year"] == year) & (df["group"] == group)]
        for cname, items in spec.items():
            eig, pct, n, k = pc1(items, sub)
            rows.append({
                "composite": cname,
                "year": year,
                "group": group,
                "n_items": k,
                "n": n,
                "pc1_eigenvalue": round(eig, 4) if not np.isnan(eig) else np.nan,
                "pc1_pct_variance": round(pct, 2) if not np.isnan(pct) else np.nan,
            })

out = pd.DataFrame(rows)
out.to_csv(ROOT / "code" / "_per_cell_pc1.tsv", sep="\t", index=False)
print(f"Wrote: code/_per_cell_pc1.tsv ({len(out)} rows)")
print(out.to_string(index=False))
