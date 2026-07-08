"""
Regress SD: Primary Out-group PC1 on out-group language ability, per group.

Variables:
  DV:  SD Primary PC1 (sign-oriented so higher = more social distance from primary out-group).
       Fit per group (Est on Q57/58/59_1; Rus on Q57/58/59_2) pooled across years.
  IV:  Out-group language ability, reverse-coded so higher = more proficient.
         Estonians: Russian ability  — 2023: Q71_2, 2020: K5_2
         Russians:  Estonian ability — 2023: Q71_1, 2020: K5_1
       Raw scale 1=native, 2=fluent, 3=u/s/w, 4=u/s a little, 5=understand a little/no speak,
       6=none. 9=DK→NaN. Recoded as (7 - raw) so 1=none, 6=native.
  Controls: 2023 indicator (year fixed effect), pooled-within-group sample.

Each model reports raw and standardized coefficients, n, R^2, and significance.
"""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
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


def to_num(s):
    return pd.to_numeric(s, errors="coerce")


def clean_items(df, items, dk=9):
    sub = df[items].apply(to_num).copy()
    return sub.where(sub != dk)


def recode_lang(s):
    """1=native..6=none, 9=DK→NaN. Reverse so 1=none..6=native (higher=better)."""
    s = to_num(s)
    s = s.where(s != 9)
    return 7 - s


# Build PC1 for SD Primary per group, pooled across years
def fit_pc1(items):
    sub = items.dropna()
    pca = PCA(n_components=1).fit(sub.to_numpy())
    scores = pca.transform(sub.to_numpy())[:, 0]
    pc1 = pd.Series(index=items.index, dtype=float)
    pc1.loc[sub.index] = scores
    # Orient so higher = more distance (positive correlation with item mean,
    # since raw items are 1=very pleasant ... 5=very unpleasant)
    item_mean = items.mean(axis=1)
    r = pc1.corr(item_mean)
    if r < 0:
        pc1 = -pc1
    return pc1, float(pca.explained_variance_ratio_[0])


rows = []          # for results table
detail_models = {} # store full OLS results for the doc

for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
    # Per-group item sets
    if grp_code == 0:
        items23 = ["Q57_1", "Q58_1", "Q59_1"]
        items20 = ["K4X7_1", "K4X8_1", "K4X9_1"]
        lang23, lang20 = "Q71_2", "K5_2"   # Russian ability
        out_lang_label = "Russian language ability"
    else:
        items23 = ["Q57_2", "Q58_2", "Q59_2"]
        items20 = ["K4X7_2", "K4X8_2", "K4X9_2"]
        lang23, lang20 = "Q71_1", "K5_1"   # Estonian ability
        out_lang_label = "Estonian language ability"

    sub23 = df23[df23["ethnicity_binary"] == grp_code].copy()
    sub20 = df20[df20["ethnicity_binary"] == grp_code].copy()

    pc_items_23 = clean_items(sub23, items23).rename(columns=dict(zip(items23, ["i1","i2","i3"])))
    pc_items_20 = clean_items(sub20, items20).rename(columns=dict(zip(items20, ["i1","i2","i3"])))
    pc_items = pd.concat([pc_items_23, pc_items_20], ignore_index=True)

    sub23["__lang__"] = recode_lang(sub23[lang23])
    sub20["__lang__"] = recode_lang(sub20[lang20])

    meta = pd.concat(
        [sub23[["__year__", "__lang__", "ethnicity_binary"]],
         sub20[["__year__", "__lang__", "ethnicity_binary"]]],
        ignore_index=True,
    )
    pc1, ve = fit_pc1(pc_items)
    meta["pc1"] = pc1

    # Drop rows missing either variable
    reg = meta.dropna(subset=["pc1", "__lang__"]).copy()
    reg["year_2023"] = (reg["__year__"] == 2023).astype(int)
    reg["lang_z"] = (reg["__lang__"] - reg["__lang__"].mean()) / reg["__lang__"].std(ddof=0)
    reg["pc1_z"]  = (reg["pc1"]      - reg["pc1"].mean())      / reg["pc1"].std(ddof=0)

    # Model 1: PC1 ~ lang (no controls)
    X = sm.add_constant(reg[["__lang__"]])
    m1 = sm.OLS(reg["pc1"], X).fit(cov_type="HC3")

    # Model 2: PC1 ~ lang + year_2023
    X = sm.add_constant(reg[["__lang__", "year_2023"]])
    m2 = sm.OLS(reg["pc1"], X).fit(cov_type="HC3")

    # Model 3: standardized — pc1_z ~ lang_z + year_2023
    X = sm.add_constant(reg[["lang_z", "year_2023"]])
    m3 = sm.OLS(reg["pc1_z"], X).fit(cov_type="HC3")

    for label, m, lang_var in [
        ("unadjusted (pooled years)", m1, "__lang__"),
        ("adjusted for year", m2, "__lang__"),
        ("standardized (β)", m3, "lang_z"),
    ]:
        b = m.params[lang_var]
        se = m.bse[lang_var]
        p = m.pvalues[lang_var]
        ll, ul = m.conf_int().loc[lang_var]
        rows.append((grp_name, out_lang_label, label, m.nobs, m.rsquared,
                     b, ll, ul, p))
    detail_models[grp_name] = {"m1": m1, "m2": m2, "m3": m3,
                                "n": int(m1.nobs), "ve": ve,
                                "lang_label": out_lang_label,
                                "lang_mean": reg["__lang__"].mean(),
                                "lang_sd":   reg["__lang__"].std(ddof=0),
                                "pc1_mean":  reg["pc1"].mean(),
                                "pc1_sd":    reg["pc1"].std(ddof=0)}


# -------- Print summary table -----------------------------------------
out = pd.DataFrame(rows, columns=[
    "group", "predictor", "spec", "N", "R2", "b", "CI_low", "CI_high", "p"
])
tsv = ROOT / "code" / "_sd_primary_language_regression.tsv"
out.to_csv(tsv, sep="\t", index=False, float_format="%.4f")
print(f"Saved: {tsv}\n")


def stars(p):
    return "***" if p<.001 else "**" if p<.01 else "*" if p<.05 else "ns"

print("=" * 110)
print("SD Primary Out-group PC1 regressed on out-group language ability")
print("(higher PC1 = more social distance; higher language = more proficient)")
print("=" * 110)
print(f"{'Group':<10}{'Predictor':<32}{'Spec':<28}{'N':>5}{'R²':>7}{'b':>9}{'95% CI':>20}{'p':>10}")
for _, r in out.iterrows():
    p = r["p"]
    print(f"{r['group']:<10}{r['predictor']:<32}{r['spec']:<28}{int(r['N']):>5}"
          f"{r['R2']:>7.3f}{r['b']:>+9.3f}  [{r['CI_low']:>+6.3f}, {r['CI_high']:>+6.3f}]"
          f"  {p:>.4f} {stars(p)}")

# ------- Full OLS summaries for the model with year control ------------
print()
for grp in ("Estonian", "Russian"):
    m = detail_models[grp]
    print("=" * 110)
    print(f"{grp.upper()} — PC1 ~ {m['lang_label']} + year_2023  (HC3 SE)")
    print(f"Lang mean={m['lang_mean']:.2f}, SD={m['lang_sd']:.2f}; "
          f"PC1 mean={m['pc1_mean']:.2f}, SD={m['pc1_sd']:.2f}; "
          f"PC1 var explained={m['ve']*100:.1f}%; N={m['n']}")
    print(m["m2"].summary().tables[1])
