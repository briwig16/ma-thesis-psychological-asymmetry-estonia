#!/usr/bin/env python3
"""
Referee 2 — Round 4 Spot-Check
Verify _within_group_year_regression.tsv: composite ~ year_2023 OLS
per (variable × group). Independent re-derivation.

Reads composites directly from raw data via author's documented item lists,
then runs statsmodels OLS to reproduce B0/B1/SE/CI/t/df/p/R2.
"""
import os, sys, math
import pandas as pd, numpy as np
import statsmodels.api as sm
import pyreadstat

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CANON = os.path.join(ROOT, "code", "_within_group_year_regression.tsv")

df23 = pd.read_csv(os.path.join(ROOT, "data", "EIM23.csv"), low_memory=False)
df23 = df23[pd.to_numeric(df23["ethnicity_binary"], errors="coerce").isin([0, 1])].copy()

df20, _ = pyreadstat.read_sav(os.path.join(ROOT, "data", "EIM 2020_20.10.25.sav copy"),
                              encoding="latin1")
df20["ethnicity_binary"] = np.where(df20["T9_1"]==1, 0,
                            np.where(df20["T9_2"]==1, 1, np.nan))
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy()

def comp(df, items, dk=9, smax=None, reverse=None, invert_composite=False):
    sub = df[items].apply(pd.to_numeric, errors="coerce")
    sub = sub.where(sub != dk)
    if reverse:
        for it in reverse:
            sub[it] = (smax + 1) - sub[it]
    m = sub.mean(axis=1, skipna=True)
    if invert_composite:
        m = (smax + 1) - m
    return m

# Composite definitions matching CLAUDE.md spec.
# `inv`: composite is inverted (visualization-scale convention) — script 79
# applies this for SI, Comp.Opp., Minority Inclusion Support.
COMPS = {
    "Superordinate Identity": {
        "smax": 4, "inv": True,
        "23_items": ["Q67_2","Q67_4","Q67_5"], "23_rev": ["Q67_4"],
        "20_items": ["K6X5_2","K6X5_3","K6X5_4"], "20_rev": ["K6X5_3"],
    },
    "Belief in Inevitable Conflict": {
        "smax": 4, "inv": False,
        "23_items": ["Q63_1","Q63_2","Q63_3","Q63_4"], "23_rev": ["Q63_1","Q63_2"],
        "20_items": ["K6X1_1","K6X1_2","K6X1_3","K6X1_4"], "20_rev": ["K6X1_1","K6X1_2"],
    },
    "Minority Inclusion Support": {
        "smax": 4, "inv": True,
        "23_items": ["Q68_1","Q68_2","Q68_3"], "23_rev": [],
        "20_items": ["K6X6_1","K6X6_2","K6X6_3"], "20_rev": [],
    },
    "Comparative Opportunity Assessment": {
        "smax": 5, "inv": True,
        "23_items": [f"Q44_{i}" for i in range(1,13)], "23_rev": [],
        "20_items": [f"K3X1_{i}" for i in range(1,13)], "20_rev": [],
    },
    "SD: General Out-group": {
        "smax": 5, "inv": False,
        "23_items": ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"], "23_rev": [],
        "20_items": ["K4X7_3","K4X8_3","K4X9_3"], "20_rev": [],
    },
}

canon = pd.read_csv(CANON, sep="\t")
print(f"Canonical: {len(canon)} rows")
print(canon["variable"].unique())

passed, failed, fails = 0, 0, []

# Build replicated rows for the basic 6 composites (skip SD: Primary special-casing for spot-check)
rep = []
for name, spec in COMPS.items():
    c23 = comp(df23, spec["23_items"], smax=spec["smax"], reverse=spec["23_rev"],
               invert_composite=spec["inv"])
    c20 = comp(df20, spec["20_items"], smax=spec["smax"], reverse=spec["20_rev"],
               invert_composite=spec["inv"])
    e23 = c23[df23["ethnicity_binary"]==0]
    r23 = c23[df23["ethnicity_binary"]==1]
    e20 = c20[df20["ethnicity_binary"]==0]
    r20 = c20[df20["ethnicity_binary"]==1]
    for grp_name, c2020, c2023 in [("Estonian", e20, e23), ("Russian", r20, r23)]:
        y = pd.concat([c2020, c2023]).dropna()
        x = pd.Series(np.concatenate([np.zeros(c2020.dropna().shape[0]),
                                       np.ones(c2023.dropna().shape[0])]),
                      index=y.index)
        X = sm.add_constant(x.rename("year2023"))
        model = sm.OLS(y, X).fit()
        b0 = model.params["const"]; b1 = model.params["year2023"]
        se = model.bse["year2023"]
        ci = model.conf_int().loc["year2023"]
        t = model.tvalues["year2023"]; p = model.pvalues["year2023"]
        df_r = int(model.df_resid)
        r2 = model.rsquared
        rep.append({"variable": name, "group": grp_name,
                    "n_2020": int(c2020.dropna().shape[0]),
                    "n_2023": int(c2023.dropna().shape[0]),
                    "B0": b0, "B1": b1, "SE": se, "CI_lo": ci[0], "CI_hi": ci[1],
                    "t": t, "df": df_r, "p": p, "R2": r2})

rep_df = pd.DataFrame(rep)

# Match against canonical
canon_idx = canon.set_index(["variable","group"])
checks_pass, checks_fail = 0, 0
for _, r in rep_df.iterrows():
    key = (r["variable"], r["group"])
    if key not in canon_idx.index:
        print(f"  SKIP {key} (not in canonical)"); continue
    c = canon_idx.loc[key]
    for col_rep, col_canon, tol in [
        ("B0", "B0_intercept", 1e-3), ("B1", "B1_year2023", 1e-3),
        ("SE", "SE", 1e-3), ("CI_lo", "CI_low", 1e-3),
        ("CI_hi", "CI_high", 1e-3), ("t", "t", 1e-2),
        ("df", "df", 0), ("p", "p", 1e-3), ("R2", "R2", 1e-3),
        ("n_2020", "n_2020", 0), ("n_2023", "n_2023", 0),
    ]:
        cv = c[col_canon]; rv = r[col_rep]
        if pd.isna(cv) and pd.isna(rv):
            checks_pass += 1; continue
        if abs(float(cv) - float(rv)) > tol:
            checks_fail += 1
            fails.append(f"{key} {col_canon}: canon={cv:.6g} rep={rv:.6g} Δ={float(cv)-float(rv):+.4g}")
        else:
            checks_pass += 1

print(f"\n  {checks_pass}/{checks_pass+checks_fail} PASS, {checks_fail}/{checks_pass+checks_fail} FAIL")
for f in fails[:10]:
    print(f"  FAIL  {f}")
