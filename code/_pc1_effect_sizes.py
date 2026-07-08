"""
Compute Cohen's d (root-mean-square SD denominator) with 95% CIs and Welch's
t-test p-values on PC1 scores for each non-contact composite, paralleling
code/_effect_sizes.tsv (which uses composite means).

Caveats on comparability (carried over from _pc1_means.py):
- SD: Primary Out-group is fit per group (items differ by group). Between-group
  d on PC1 is therefore meaningless by construction (each group's PC1 has
  mean=0, SD=1 on its own fitting sample). Within-group d is valid.
- SD: General Out-group is fit per year (items differ across years). Within-
  group d (2020 vs 2023) on PC1 is meaningless. Between-group d within a
  given year is valid.
- For all other composites, PC1 is fit on the pooled (groups + years) sample,
  so all four comparisons are on a single metric.
"""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
from scipy import stats
from sklearn.decomposition import PCA

ROOT = Path(__file__).parent.parent

df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy().reset_index(drop=True)
df23["__year__"] = 2023

df20, _ = pyreadstat.read_sav(
    str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"), encoding="latin1"
)
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy().reset_index(drop=True)
df20["__year__"] = 2020


def clean(df, items, reverse_items=None, scale_max=None, dk_code=9):
    sub = df[items].apply(pd.to_numeric, errors="coerce").copy()
    sub = sub.where(sub != dk_code)
    if reverse_items:
        for it in reverse_items:
            sub[it] = (scale_max + 1) - sub[it]
    return sub


def pca_pc1(item_df):
    complete_mask = item_df.notna().all(axis=1)
    X = item_df[complete_mask].to_numpy()
    pca = PCA(n_components=min(item_df.shape[1], 5))
    pca.fit(X)
    scores = pca.transform(X)[:, 0]
    series = pd.Series(index=item_df.index, dtype=float)
    series.loc[complete_mask] = scores
    return series


def orient(pc1, composite_mean, invert=False):
    """Orient PC1 to match the direction of `composite_mean` (or its inversion
    if `invert=True`, matching the display convention in _effect_sizes.tsv)."""
    target = composite_mean
    if invert:
        target = -composite_mean
    paired = pd.concat([pc1, target], axis=1).dropna()
    r = paired.iloc[:, 0].corr(paired.iloc[:, 1])
    return pc1 if r >= 0 else -pc1


def m_sd_n(s):
    s = pd.Series(s).dropna().astype(float)
    return s.mean(), s.std(ddof=1), len(s)


def cohens_d_rms(m1, sd1, n1, m2, sd2, n2):
    s_rms = math.sqrt((sd1 ** 2 + sd2 ** 2) / 2)
    d = (m1 - m2) / s_rms
    se = math.sqrt((n1 + n2) / (n1 * n2) + d ** 2 / (2 * (n1 + n2 - 2)))
    return d, d - 1.96 * se, d + 1.96 * se


def welch_p(a, b):
    a = pd.Series(a).dropna().astype(float)
    b = pd.Series(b).dropna().astype(float)
    _, p = stats.ttest_ind(a, b, equal_var=False)
    return float(p)


def fmt_p(p):
    if p < 0.0001: return "<.0001"
    if p < 0.001:  return f"{p:.4f}"
    return f"{p:.3f}"


def stars(p):
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"


# Each entry stores the PC1 Series for the 4 group-year cells and any caveat
pc1_data = {}


# -- 1. Superordinate Identity (pooled fit) ---------------------------------
items23 = ["Q67_2", "Q67_4", "Q67_5"]
items20 = ["K6X5_2", "K6X5_3", "K6X5_4"]
sub23 = clean(df23, items23, ["Q67_4"], scale_max=4).rename(columns=dict(zip(items23, ["i1", "i2", "i3"])))
sub20 = clean(df20, items20, ["K6X5_3"], scale_max=4).rename(columns=dict(zip(items20, ["i1", "i2", "i3"])))
pool = pd.concat([sub23, sub20], ignore_index=True)
meta = pd.concat(
    [df23[["ethnicity_binary", "__year__"]], df20[["ethnicity_binary", "__year__"]]],
    ignore_index=True,
)
pc1 = orient(pca_pc1(pool), pool.mean(axis=1), invert=True)
pc1_data["Superordinate Identity"] = (pc1, meta, "pooled", None)


# -- 2. SD: Primary Out-group (per group, pooled across years) --------------
# Build PC1 per group, then map back to a single series indexed by a synthetic
# (group, year) key so we can run the four comparisons uniformly.
si_pc1_parts = []
si_meta_parts = []
for grp_code, (it23, it20) in {
    0: (["Q57_1", "Q58_1", "Q59_1"], ["K4X7_1", "K4X8_1", "K4X9_1"]),
    1: (["Q57_2", "Q58_2", "Q59_2"], ["K4X7_2", "K4X8_2", "K4X9_2"]),
}.items():
    s23 = clean(df23[df23["ethnicity_binary"] == grp_code], it23).rename(
        columns=dict(zip(it23, ["i1", "i2", "i3"]))
    )
    s20 = clean(df20[df20["ethnicity_binary"] == grp_code], it20).rename(
        columns=dict(zip(it20, ["i1", "i2", "i3"]))
    )
    pool_g = pd.concat([s23, s20], ignore_index=True)
    meta_g = pd.concat(
        [
            df23.loc[df23["ethnicity_binary"] == grp_code, ["ethnicity_binary", "__year__"]],
            df20.loc[df20["ethnicity_binary"] == grp_code, ["ethnicity_binary", "__year__"]],
        ],
        ignore_index=True,
    )
    pc1_g = orient(pca_pc1(pool_g), pool_g.mean(axis=1))
    si_pc1_parts.append(pc1_g)
    si_meta_parts.append(meta_g)
pc1_data["SD: Primary Out-group"] = (
    pd.concat(si_pc1_parts, ignore_index=True),
    pd.concat(si_meta_parts, ignore_index=True),
    "per group",
    "between_group_invalid",
)


# -- 3. SD: General Out-group (per year, pooled across groups) --------------
sg_pc1_parts = []
sg_meta_parts = []
for year, (df, items) in {
    2020: (df20, ["K4X7_3", "K4X8_3", "K4X9_3"]),
    2023: (df23, ["Q57_4", "Q57_5", "Q58_4", "Q58_5", "Q59_4", "Q59_5"]),
}.items():
    sub = clean(df, items).reset_index(drop=True)
    pc1_y = orient(pca_pc1(sub), sub.mean(axis=1))
    sg_pc1_parts.append(pc1_y)
    sg_meta_parts.append(df[["ethnicity_binary", "__year__"]].reset_index(drop=True))
pc1_data["SD: General Out-group"] = (
    pd.concat(sg_pc1_parts, ignore_index=True),
    pd.concat(sg_meta_parts, ignore_index=True),
    "per year",
    "within_group_invalid",
)


# -- 4. Comparative Opportunity (pooled fit) --------------------------------
items23 = [f"Q44_{i}" for i in range(1, 13)]
items20 = [f"K3X1_{i}" for i in range(1, 13)]
sub23 = clean(df23, items23).rename(columns=dict(zip(items23, [f"i{i}" for i in range(1, 13)])))
sub20 = clean(df20, items20).rename(columns=dict(zip(items20, [f"i{i}" for i in range(1, 13)])))
pool = pd.concat([sub23, sub20], ignore_index=True)
meta = pd.concat(
    [df23[["ethnicity_binary", "__year__"]], df20[["ethnicity_binary", "__year__"]]],
    ignore_index=True,
)
pc1 = orient(pca_pc1(pool), pool.mean(axis=1), invert=True)
pc1_data["Comparative Opportunity Assessment"] = (pc1, meta, "pooled", None)


# -- 5. Belief in Inevitable Conflict (pooled fit) --------------------------
items23 = ["Q63_1", "Q63_2", "Q63_3", "Q63_4"]
items20 = ["K6X1_1", "K6X1_2", "K6X1_3", "K6X1_4"]
sub23 = clean(df23, items23, ["Q63_1", "Q63_2"], scale_max=4).rename(
    columns=dict(zip(items23, ["i1", "i2", "i3", "i4"]))
)
sub20 = clean(df20, items20, ["K6X1_1", "K6X1_2"], scale_max=4).rename(
    columns=dict(zip(items20, ["i1", "i2", "i3", "i4"]))
)
pool = pd.concat([sub23, sub20], ignore_index=True)
meta = pd.concat(
    [df23[["ethnicity_binary", "__year__"]], df20[["ethnicity_binary", "__year__"]]],
    ignore_index=True,
)
pc1 = orient(pca_pc1(pool), pool.mean(axis=1))
pc1_data["Belief in Inevitable Conflict"] = (pc1, meta, "pooled", None)


# -- 6. Minority Inclusion Support (pooled fit) -----------------------------
items23 = ["Q68_1", "Q68_2", "Q68_3"]
items20 = ["K6X6_1", "K6X6_2", "K6X6_3"]
sub23 = clean(df23, items23).rename(columns=dict(zip(items23, ["i1", "i2", "i3"])))
sub20 = clean(df20, items20).rename(columns=dict(zip(items20, ["i1", "i2", "i3"])))
pool = pd.concat([sub23, sub20], ignore_index=True)
meta = pd.concat(
    [df23[["ethnicity_binary", "__year__"]], df20[["ethnicity_binary", "__year__"]]],
    ignore_index=True,
)
pc1 = orient(pca_pc1(pool), pool.mean(axis=1), invert=True)
pc1_data["Minority Inclusion Support"] = (pc1, meta, "pooled", None)


# ---------------- Build rows ----------------------------------------------
between_rows, within_rows = [], []

for var, (pc1, meta, scope, caveat) in pc1_data.items():
    e20 = pc1[(meta["ethnicity_binary"] == 0) & (meta["__year__"] == 2020)]
    r20 = pc1[(meta["ethnicity_binary"] == 1) & (meta["__year__"] == 2020)]
    e23 = pc1[(meta["ethnicity_binary"] == 0) & (meta["__year__"] == 2023)]
    r23 = pc1[(meta["ethnicity_binary"] == 1) & (meta["__year__"] == 2023)]

    mE20, sE20, nE20 = m_sd_n(e20)
    mR20, sR20, nR20 = m_sd_n(r20)
    mE23, sE23, nE23 = m_sd_n(e23)
    mR23, sR23, nR23 = m_sd_n(r23)

    # Between-group
    for year, (mE, sE, nE, mR, sR, nR, eS, rS) in [
        ("2020", (mE20, sE20, nE20, mR20, sR20, nR20, e20, r20)),
        ("2023", (mE23, sE23, nE23, mR23, sR23, nR23, e23, r23)),
    ]:
        d, ll, ul = cohens_d_rms(mE, sE, nE, mR, sR, nR)
        p = welch_p(eS, rS)
        flag = "INVALID (PC1 fit per group)" if caveat == "between_group_invalid" else ""
        between_rows.append((var, year, mE, sE, nE, mR, sR, nR, d, ll, ul, p, flag))

    # Within-group (2023 - 2020)
    for grp, (m20, s20, n20, m23, s23, n23, s20S, s23S) in [
        ("Estonian", (mE20, sE20, nE20, mE23, sE23, nE23, e20, e23)),
        ("Russian",  (mR20, sR20, nR20, mR23, sR23, nR23, r20, r23)),
    ]:
        d, ll, ul = cohens_d_rms(m23, s23, n23, m20, s20, n20)
        p = welch_p(s23S, s20S)
        flag = "INVALID (PC1 fit per year)" if caveat == "within_group_invalid" else ""
        within_rows.append((var, grp, m20, s20, n20, m23, s23, n23, d, ll, ul, p, flag))


# ---------------- Save TSV ------------------------------------------------
out_path = ROOT / "code" / "_pc1_effect_sizes.tsv"
with open(out_path, "w") as f:
    f.write("table\tvariable\tcomparison\tM1\tSD1\tN1\tM2\tSD2\tN2\td\tCI_low\tCI_high\tp\tflag\n")
    for r in between_rows:
        v, y, mE, sE, nE, mR, sR, nR, d, ll, ul, p, flag = r
        f.write(f"between\t{v}\t{y}\t{mE:.4f}\t{sE:.4f}\t{nE}\t{mR:.4f}\t{sR:.4f}\t{nR}\t{d:.4f}\t{ll:.4f}\t{ul:.4f}\t{p:.6f}\t{flag}\n")
    for r in within_rows:
        v, g, m20, s20, n20, m23, s23, n23, d, ll, ul, p, flag = r
        f.write(f"within\t{v}\t{g}\t{m20:.4f}\t{s20:.4f}\t{n20}\t{m23:.4f}\t{s23:.4f}\t{n23}\t{d:.4f}\t{ll:.4f}\t{ul:.4f}\t{p:.6f}\t{flag}\n")
print(f"Saved: {out_path}\n")


# ---------------- Print readable tables ------------------------------------
print("=" * 100)
print("BETWEEN-GROUP (Estonian vs Russian) — Cohen's d on PC1")
print("=" * 100)
print(f"{'Variable':<37}{'Year':<6}{'d':>8}{'95% CI':>20}{'p':>10}{'sig':>5}  flag")
for r in between_rows:
    v, y, mE, sE, nE, mR, sR, nR, d, ll, ul, p, flag = r
    print(f"{v:<37}{y:<6}{d:>+8.3f}  [{ll:>+6.3f}, {ul:>+6.3f}] {fmt_p(p):>10}{stars(p):>5}  {flag}")

print()
print("=" * 100)
print("WITHIN-GROUP (2023 vs 2020) — Cohen's d on PC1")
print("=" * 100)
print(f"{'Variable':<37}{'Group':<10}{'d':>8}{'95% CI':>20}{'p':>10}{'sig':>5}  flag")
for r in within_rows:
    v, g, m20, s20, n20, m23, s23, n23, d, ll, ul, p, flag = r
    print(f"{v:<37}{g:<10}{d:>+8.3f}  [{ll:>+6.3f}, {ul:>+6.3f}] {fmt_p(p):>10}{stars(p):>5}  {flag}")
