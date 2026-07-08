"""
Compute PC1 scores (standardized to mean 0, SD 1 on the fitting sample) for each
non-contact composite and report mean PC1 by group x year.

Fitting strategy (note this affects comparability):
- Superordinate Identity, Comparative Opportunity, Belief in Conflict,
  Minority Support Inclusion: item set is identical across both groups and
  both years -> fit ONE PCA on the pooled Est+Rus, 2020+2023 sample.
- SD: Primary Out-group: item set DIFFERS by group (Estonians rate Russian-
  speakers; Russians rate Estonian-speakers) -> fit one PCA per group, pooled
  across 2020+2023. Cross-group PC1 means are NOT directly comparable.
- SD: General Out-group: item set differs across waves (3 items in 2020,
  6 items in 2023) -> fit one PCA per year, pooled across groups. Cross-year
  PC1 means are NOT directly comparable.

PC1 sign is oriented so positive = "more of the construct" by matching the
sign of the correlation between PC1 and the composite mean. Reverse-coding
applied before fitting (Q67_4, Q63_1, Q63_2).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
from sklearn.decomposition import PCA

ROOT = Path(__file__).parent.parent

df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy()
df23["__year__"] = 2023

df20, _ = pyreadstat.read_sav(
    str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"), encoding="latin1"
)
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy()
df20["__year__"] = 2020


def clean(df, items, reverse_items=None, scale_max=None, dk_code=9):
    sub = df[items].apply(pd.to_numeric, errors="coerce").copy()
    sub = sub.where(sub != dk_code)
    if reverse_items:
        for it in reverse_items:
            sub[it] = (scale_max + 1) - sub[it]
    return sub


def pca_pc1(item_df):
    """Fit PCA on listwise-complete rows of item_df. Return PC1 scores indexed by item_df.index (NaN where listwise-incomplete) and the explained-variance ratio of PC1."""
    complete_mask = item_df.notna().all(axis=1)
    X = item_df[complete_mask].to_numpy()
    pca = PCA(n_components=min(item_df.shape[1], 5))
    pca.fit(X)
    scores = pca.transform(X)[:, 0]
    series = pd.Series(index=item_df.index, dtype=float)
    series.loc[complete_mask] = scores
    return series, float(pca.explained_variance_ratio_[0]), pca


def orient(pc1, composite_mean):
    """Flip sign of PC1 so it correlates positively with the composite mean."""
    paired = pd.concat([pc1, composite_mean], axis=1).dropna()
    if len(paired) < 5:
        return pc1
    r = paired.iloc[:, 0].corr(paired.iloc[:, 1])
    return pc1 if r >= 0 else -pc1


def summarize(pc1, df, label):
    rows = []
    for year in (2020, 2023):
        for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
            mask = (df["__year__"] == year) & (df["ethnicity_binary"] == grp_code)
            s = pc1[mask].dropna()
            rows.append((label, year, grp_name, s.mean(), s.std(ddof=1), len(s)))
    return rows


# Build per-respondent item frames in a SINGLE pooled DataFrame (df23 + df20)
# only when item sets allow it; otherwise compute per group / per year and
# slot PC1 back into the right rows.

results = []  # (variable, fit_scope, year, group, mean_PC1, SD_PC1, N, var_explained)

# -- 1. Superordinate Identity (pooled fit) ---------------------------------
items23 = ["Q67_2", "Q67_4", "Q67_5"]
items20 = ["K6X5_2", "K6X5_3", "K6X5_4"]
pool = pd.concat(
    [
        clean(df23, items23, ["Q67_4"], scale_max=4).rename(
            columns=dict(zip(items23, ["i1", "i2", "i3"]))
        ),
        clean(df20, items20, ["K6X5_3"], scale_max=4).rename(
            columns=dict(zip(items20, ["i1", "i2", "i3"]))
        ),
    ]
)
pool_meta = pd.concat([df23[["ethnicity_binary", "__year__"]], df20[["ethnicity_binary", "__year__"]]])
pc1, ve, _ = pca_pc1(pool)
pc1 = orient(pc1, pool.mean(axis=1))
for r in summarize(pc1, pool_meta, "Superordinate Identity"):
    results.append(r + ("pooled (groups + years)", ve))

# -- 2. SD: Primary Out-group (per group, pooled across years) --------------
group_specs = {
    0: (["Q57_1", "Q58_1", "Q59_1"], ["K4X7_1", "K4X8_1", "K4X9_1"]),
    1: (["Q57_2", "Q58_2", "Q59_2"], ["K4X7_2", "K4X8_2", "K4X9_2"]),
}
for grp_code, (it23, it20) in group_specs.items():
    grp_name = "Estonian" if grp_code == 0 else "Russian"
    sub23 = clean(df23[df23["ethnicity_binary"] == grp_code], it23).rename(
        columns=dict(zip(it23, ["i1", "i2", "i3"]))
    )
    sub20 = clean(df20[df20["ethnicity_binary"] == grp_code], it20).rename(
        columns=dict(zip(it20, ["i1", "i2", "i3"]))
    )
    pool = pd.concat([sub23, sub20])
    pool_meta = pd.concat(
        [
            df23.loc[df23["ethnicity_binary"] == grp_code, ["ethnicity_binary", "__year__"]],
            df20.loc[df20["ethnicity_binary"] == grp_code, ["ethnicity_binary", "__year__"]],
        ]
    )
    pc1, ve, _ = pca_pc1(pool)
    pc1 = orient(pc1, pool.mean(axis=1))
    for year in (2020, 2023):
        mask = pool_meta["__year__"] == year
        s = pc1[mask].dropna()
        results.append(
            ("SD: Primary Out-group", year, grp_name, s.mean(), s.std(ddof=1), len(s),
             f"per group ({grp_name}), pooled across years", ve)
        )

# -- 3. SD: General Out-group (per year, pooled across groups) --------------
year_specs = {
    2020: (df20, ["K4X7_3", "K4X8_3", "K4X9_3"]),
    2023: (df23, ["Q57_4", "Q57_5", "Q58_4", "Q58_5", "Q59_4", "Q59_5"]),
}
for year, (df, items) in year_specs.items():
    sub = clean(df, items)
    pc1, ve, _ = pca_pc1(sub)
    pc1 = orient(pc1, sub.mean(axis=1))
    meta = df[["ethnicity_binary"]]
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        s = pc1[meta["ethnicity_binary"] == grp_code].dropna()
        results.append(
            ("SD: General Out-group", year, grp_name, s.mean(), s.std(ddof=1), len(s),
             f"per year ({year}), pooled across groups", ve)
        )

# -- 4. Comparative Opportunity (pooled fit) --------------------------------
items23 = [f"Q44_{i}" for i in range(1, 13)]
items20 = [f"K3X1_{i}" for i in range(1, 13)]
pool = pd.concat(
    [
        clean(df23, items23).rename(columns=dict(zip(items23, [f"i{i}" for i in range(1, 13)]))),
        clean(df20, items20).rename(columns=dict(zip(items20, [f"i{i}" for i in range(1, 13)]))),
    ]
)
pool_meta = pd.concat([df23[["ethnicity_binary", "__year__"]], df20[["ethnicity_binary", "__year__"]]])
pc1, ve, _ = pca_pc1(pool)
pc1 = orient(pc1, pool.mean(axis=1))
for r in summarize(pc1, pool_meta, "Comparative Opportunity Assessment"):
    results.append(r + ("pooled (groups + years)", ve))

# -- 5. Belief in Inevitable Conflict (pooled fit) --------------------------
items23 = ["Q63_1", "Q63_2", "Q63_3", "Q63_4"]
items20 = ["K6X1_1", "K6X1_2", "K6X1_3", "K6X1_4"]
pool = pd.concat(
    [
        clean(df23, items23, ["Q63_1", "Q63_2"], scale_max=4).rename(
            columns=dict(zip(items23, ["i1", "i2", "i3", "i4"]))
        ),
        clean(df20, items20, ["K6X1_1", "K6X1_2"], scale_max=4).rename(
            columns=dict(zip(items20, ["i1", "i2", "i3", "i4"]))
        ),
    ]
)
pool_meta = pd.concat([df23[["ethnicity_binary", "__year__"]], df20[["ethnicity_binary", "__year__"]]])
pc1, ve, _ = pca_pc1(pool)
pc1 = orient(pc1, pool.mean(axis=1))
for r in summarize(pc1, pool_meta, "Belief in Inevitable Conflict"):
    results.append(r + ("pooled (groups + years)", ve))

# -- 6. Minority Inclusion Support (pooled fit) -----------------------------
items23 = ["Q68_1", "Q68_2", "Q68_3"]
items20 = ["K6X6_1", "K6X6_2", "K6X6_3"]
pool = pd.concat(
    [
        clean(df23, items23).rename(columns=dict(zip(items23, ["i1", "i2", "i3"]))),
        clean(df20, items20).rename(columns=dict(zip(items20, ["i1", "i2", "i3"]))),
    ]
)
pool_meta = pd.concat([df23[["ethnicity_binary", "__year__"]], df20[["ethnicity_binary", "__year__"]]])
pc1, ve, _ = pca_pc1(pool)
pc1 = orient(pc1, pool.mean(axis=1))
for r in summarize(pc1, pool_meta, "Minority Inclusion Support"):
    results.append(r + ("pooled (groups + years)", ve))


# --- Output ----------------------------------------------------------------
out = pd.DataFrame(
    results,
    columns=["variable", "year", "group", "mean_PC1", "SD_PC1", "N", "fit_scope", "PC1_var_explained"],
)
out["mean_PC1"] = out["mean_PC1"].round(3)
out["SD_PC1"] = out["SD_PC1"].round(3)
out["PC1_var_explained"] = out["PC1_var_explained"].round(3)
out_path = ROOT / "code" / "_pc1_means.tsv"
out.to_csv(out_path, sep="\t", index=False)
print(f"Saved: {out_path}\n")

# Print pivot for quick reading
for var in out["variable"].unique():
    sub = out[out["variable"] == var]
    print(f"\n{var}  (PC1 explains {sub['PC1_var_explained'].iloc[0]*100:.1f}% of variance; scope: {sub['fit_scope'].iloc[0]})")
    pivot = sub.pivot_table(index="year", columns="group", values="mean_PC1")
    n_pivot = sub.pivot_table(index="year", columns="group", values="N")
    for year in pivot.index:
        e = pivot.loc[year, "Estonian"]
        r = pivot.loc[year, "Russian"]
        ne = n_pivot.loc[year, "Estonian"]
        nr = n_pivot.loc[year, "Russian"]
        print(f"  {year}:  Estonian PC1 = {e:+.3f} (N={int(ne)})   Russian PC1 = {r:+.3f} (N={int(nr)})")
