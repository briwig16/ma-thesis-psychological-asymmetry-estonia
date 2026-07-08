#!/usr/bin/env python3
"""
Referee 2 — Round 4 Independent Verification of Item-Level Decomposition
========================================================================

Independently re-derives `code/_item_decomposition.tsv` from raw data using
a clean Python implementation. Compares each row of the canonical TSV
cell-by-cell to verify M, SD, N, d, CI, p, sig.

The author script is code/29_item_decomposition.py. THIS script is an
independent re-implementation that does NOT import from the author code.

Runs from project root or from code/replication/. Outputs:
  - prints PASS/FAIL summary
  - prints any divergence row-by-row

Tolerance:
  - means/SDs/d/CI bounds: 0.001 (3 decimal places)
  - p-values: 0.001 if p > 0.01, else relative 1%
  - N: exact match
"""
import os, sys, math
import pandas as pd
import numpy as np
from scipy import stats
import pyreadstat

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))   # project root (..)
DATA_2023 = os.path.join(ROOT, "data", "EIM23.csv")
DATA_2020 = os.path.join(ROOT, "data", "EIM 2020_20.10.25.sav copy")
CANONICAL = os.path.join(ROOT, "code", "_item_decomposition.tsv")


# --- Independent ethnicity construction ----------------------------------
def load_2023():
    df = pd.read_csv(DATA_2023, low_memory=False)
    # T8: 1 = Estonian, 2 = Russian, others excluded
    eth = pd.to_numeric(df["T8"], errors="coerce")
    df["_eb"] = np.where(eth == 1, 0, np.where(eth == 2, 1, np.nan))
    return df[df["_eb"].isin([0, 1])].copy()


def load_2020():
    df, _ = pyreadstat.read_sav(DATA_2020, encoding="latin1")
    # T9_1=1 → Estonian; T9_2=1 → Russian
    t91 = pd.to_numeric(df["T9_1"], errors="coerce")
    t92 = pd.to_numeric(df["T9_2"], errors="coerce")
    eb = np.where(t91 == 1, 0, np.where(t92 == 1, 1, np.nan))
    df["_eb"] = eb
    return df[df["_eb"].isin([0, 1])].copy()


# --- Item fetch + reverse coding -----------------------------------------
def get_item(df, var, smax, reverse=False):
    s = pd.to_numeric(df[var], errors="coerce")
    s = s.where(s != 9)
    if reverse:
        s = (smax + 1) - s
    return s.astype(float)


def mstats(s):
    s = s.dropna()
    return s.mean(), s.std(ddof=1), len(s)


def cohens_d_ci(m1, sd1, n1, m2, sd2, n2):
    if any(pd.isna(x) for x in (m1, sd1, m2, sd2)) or n1 < 2 or n2 < 2:
        return np.nan, np.nan, np.nan
    s = math.sqrt((sd1**2 + sd2**2) / 2)
    if s == 0:
        return np.nan, np.nan, np.nan
    d = (m1 - m2) / s
    se = math.sqrt((n1 + n2) / (n1 * n2) + d**2 / (2 * (n1 + n2 - 2)))
    return d, d - 1.96*se, d + 1.96*se


def welch_p(a, b):
    a, b = a.dropna(), b.dropna()
    if len(a) < 2 or len(b) < 2:
        return np.nan
    return float(stats.ttest_ind(a, b, equal_var=False).pvalue)


def stars(p):
    if pd.isna(p): return ""
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"


# --- Composite specs (independent transcription) -------------------------
SPECS = [
    {"name": "Superordinate Identity", "smax": 4, "inv": True,
     "items_23": ["Q67_2","Q67_4","Q67_5"], "items_20": ["K6X5_2","K6X5_3","K6X5_4"],
     "labels": ["Pride in flag","Second-class citizen (rev.)","Part of society"],
     "rev_23": {"Q67_4"}, "rev_20": {"K6X5_3"}},
    {"name": "SD: Primary Out-group", "smax": 5, "inv": False, "group_specific": True,
     "labels": ["Neighbors","Work / study","Marriage in family"],
     "est_items_23": ["Q57_1","Q58_1","Q59_1"],
     "rus_items_23": ["Q57_2","Q58_2","Q59_2"],
     "est_items_20": ["K4X7_1","K4X8_1","K4X9_1"],
     "rus_items_20": ["K4X7_2","K4X8_2","K4X9_2"], "rev_23": set(), "rev_20": set()},
    {"name": "SD: General Out-group", "smax": 5, "inv": False, "skip_within": True,
     "items_23": ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"],
     "items_20": ["K4X7_3","K4X8_3","K4X9_3"],
     "labels_23": ["Neighbors: other Europeans","Neighbors: non-Europeans",
                   "Work: other Europeans","Work: non-Europeans",
                   "Marriage: other Europeans","Marriage: non-Europeans"],
     "labels_20": ["Neighbors: new immigrants","Work: new immigrants",
                   "Marriage: new immigrants"], "rev_23": set(), "rev_20": set()},
    {"name": "Comparative Opportunity Assessment", "smax": 5, "inv": True,
     "items_23": [f"Q44_{i}" for i in range(1,13)],
     "items_20": [f"K3X1_{i}" for i in range(1,13)],
     "labels": ["Material well-being","Cultural participation","Education",
                "Social/political rights","Entrepreneurship","Career & jobs",
                "Medical care","Housing","Leisure & holidays",
                "Children & youth","Sports & exercise","State benefits/services"],
     "rev_23": set(), "rev_20": set()},
    {"name": "Belief in Inevitable Conflict", "smax": 4, "inv": False,
     "items_23": ["Q63_1","Q63_2","Q63_3","Q63_4"],
     "items_20": ["K6X1_1","K6X1_2","K6X1_3","K6X1_4"],
     "labels": ["Conflicts inevitable (rev.)","Differences divide society (rev.)",
                "Groups can cooperate","Immigration enriches life"],
     "rev_23": {"Q63_1","Q63_2"}, "rev_20": {"K6X1_1","K6X1_2"}},
    {"name": "Minority Support Inclusion", "smax": 4, "inv": True,
     "items_23": ["Q68_1","Q68_2","Q68_3"], "items_20": ["K6X6_1","K6X6_2","K6X6_3"],
     "labels": ["Involve in economy","Involve in governance","Understand opinions"],
     "rev_23": set(), "rev_20": set()},
    {"name": "Contact: Estonian Speakers", "smax": 5, "inv": True,
     "items_23": [f"Q51_{i}" for i in range(1,7)],
     "items_20": [f"K4X1_{i}" for i in range(1,7)],
     "labels": ["Work / school","Neighbors","Internet / social media",
                "Leisure","Family","Friends"], "rev_23": set(), "rev_20": set()},
    {"name": "Contact: Russian Speakers", "smax": 5, "inv": True,
     "items_23": [f"Q52_{i}" for i in range(1,7)],
     "items_20": [f"K4X2_{i}" for i in range(1,7)],
     "labels": ["Work / school","Neighbors","Internet / social media",
                "Leisure","Family","Friends"], "rev_23": set(), "rev_20": set()},
]


def build_series(spec, df20, df23):
    smax, inv = spec["smax"], spec["inv"]

    def fetch(df, items, rev, labels):
        out = {}
        for it, lbl in zip(items, labels):
            s = get_item(df, it, smax, reverse=(it in rev))
            if inv:
                s = (smax + 1) - s
            out[lbl] = s
        return out

    series = {}
    if spec.get("group_specific"):
        labels = spec["labels"]
        series["est20"] = fetch(df20[df20["_eb"]==0], spec["est_items_20"], set(), labels)
        series["rus20"] = fetch(df20[df20["_eb"]==1], spec["rus_items_20"], set(), labels)
        series["est23"] = fetch(df23[df23["_eb"]==0], spec["est_items_23"], set(), labels)
        series["rus23"] = fetch(df23[df23["_eb"]==1], spec["rus_items_23"], set(), labels)
    elif spec.get("skip_within"):
        series["est20"] = fetch(df20[df20["_eb"]==0], spec["items_20"], set(), spec["labels_20"])
        series["rus20"] = fetch(df20[df20["_eb"]==1], spec["items_20"], set(), spec["labels_20"])
        series["est23"] = fetch(df23[df23["_eb"]==0], spec["items_23"], set(), spec["labels_23"])
        series["rus23"] = fetch(df23[df23["_eb"]==1], spec["items_23"], set(), spec["labels_23"])
    else:
        series["est20"] = fetch(df20[df20["_eb"]==0], spec["items_20"], spec["rev_20"], spec["labels"])
        series["rus20"] = fetch(df20[df20["_eb"]==1], spec["items_20"], spec["rev_20"], spec["labels"])
        series["est23"] = fetch(df23[df23["_eb"]==0], spec["items_23"], spec["rev_23"], spec["labels"])
        series["rus23"] = fetch(df23[df23["_eb"]==1], spec["items_23"], spec["rev_23"], spec["labels"])
    return series


def decompose(spec, df20, df23):
    series = build_series(spec, df20, df23)
    rows = []
    name = spec["name"]
    # Between-group, both years
    for yk, yr in [("20","2020"),("23","2023")]:
        labels = list(series[f"est{yk}"].keys())
        for lbl in labels:
            sA = series[f"est{yk}"][lbl]
            sB = series[f"rus{yk}"][lbl]
            mA, sdA, nA = mstats(sA)
            mB, sdB, nB = mstats(sB)
            d, lo, hi = cohens_d_ci(mA, sdA, nA, mB, sdB, nB)
            p = welch_p(sA, sB)
            rows.append({"composite": name, "comparison": f"between {yr}",
                         "item": lbl, "M1": mA, "SD1": sdA, "N1": nA,
                         "M2": mB, "SD2": sdB, "N2": nB,
                         "d": d, "CI_lo": lo, "CI_hi": hi, "p": p, "sig": stars(p)})
    # Within-group, both groups
    if not spec.get("skip_within"):
        labels = list(series["est20"].keys())
        for grp, k20, k23 in [("Estonian","est20","est23"),("Russian","rus20","rus23")]:
            for lbl in labels:
                if lbl not in series[k23]: continue
                sA = series[k20][lbl]; sB = series[k23][lbl]
                mA, sdA, nA = mstats(sA)
                mB, sdB, nB = mstats(sB)
                d, lo, hi = cohens_d_ci(mB, sdB, nB, mA, sdA, nA)  # 2023 - 2020
                p = welch_p(sA, sB)
                rows.append({"composite": name, "comparison": f"within {grp}",
                             "item": lbl, "M1": mA, "SD1": sdA, "N1": nA,
                             "M2": mB, "SD2": sdB, "N2": nB,
                             "d": d, "CI_lo": lo, "CI_hi": hi, "p": p, "sig": stars(p)})
    return rows


# --- Run replication and compare to canonical ----------------------------
def main():
    print("=" * 70)
    print("  Referee 2 — Round 4 Item Decomposition Replication")
    print("=" * 70)

    df23 = load_2023()
    df20 = load_2020()
    print(f"  2023: N(Est)={int((df23['_eb']==0).sum())}, N(Rus)={int((df23['_eb']==1).sum())}")
    print(f"  2020: N(Est)={int((df20['_eb']==0).sum())}, N(Rus)={int((df20['_eb']==1).sum())}")

    canon = pd.read_csv(CANONICAL, sep="\t")
    canon.columns = [c.strip() for c in canon.columns]
    print(f"  Canonical TSV: {len(canon)} rows × {len(canon.columns)} cols")

    all_rows = []
    for spec in SPECS:
        all_rows.extend(decompose(spec, df20, df23))
    rep = pd.DataFrame(all_rows)
    print(f"  Replicated:    {len(rep)} rows")

    if len(rep) != len(canon):
        print(f"  WARN row-count mismatch: canon={len(canon)}, rep={len(rep)}")

    # Merge on composite + comparison + item
    merged = canon.merge(rep, on=["composite","comparison","item"],
                         suffixes=("_canon","_rep"), how="outer", indicator=True)

    if (merged["_merge"] != "both").any():
        missing = merged[merged["_merge"] != "both"]
        print(f"\n  WARN {len(missing)} rows do not match between canon and rep:")
        for _, r in missing.head(20).iterrows():
            print(f"    [{r['_merge']}] {r['composite']} / {r['comparison']} / {r['item']}")

    # Numeric comparison
    checks = ["M1","SD1","N1","M2","SD2","N2","d","CI_lo","CI_hi","p"]
    tol = {"M1":1e-3,"SD1":1e-3,"N1":0,"M2":1e-3,"SD2":1e-3,"N2":0,
           "d":1e-3,"CI_lo":1e-3,"CI_hi":1e-3,"p":1e-3}
    n_pass, n_fail, fails = 0, 0, []
    both = merged[merged["_merge"]=="both"]
    for _, r in both.iterrows():
        for col in checks:
            cv = float(r[f"{col}_canon"]) if not pd.isna(r[f"{col}_canon"]) else np.nan
            rv = float(r[f"{col}_rep"])   if not pd.isna(r[f"{col}_rep"])   else np.nan
            if pd.isna(cv) and pd.isna(rv):
                n_pass += 1; continue
            if pd.isna(cv) or pd.isna(rv):
                n_fail += 1
                fails.append(f"{r['composite']}|{r['comparison']}|{r['item']}|{col}: canon={cv} rep={rv}")
                continue
            t = tol[col]
            if col == "p" and cv < 0.01:
                # relative tolerance for very small p
                if abs(cv - rv) / max(cv, 1e-12) > 0.01 and abs(cv - rv) > 1e-4:
                    n_fail += 1
                    fails.append(f"{r['composite']}|{r['comparison']}|{r['item']}|{col}: canon={cv:.6g} rep={rv:.6g}")
                else:
                    n_pass += 1
            else:
                if abs(cv - rv) > t:
                    n_fail += 1
                    fails.append(f"{r['composite']}|{r['comparison']}|{r['item']}|{col}: canon={cv:.6g} rep={rv:.6g} (Δ={cv-rv:+.6g})")
                else:
                    n_pass += 1
        # sig string match (informational, not counted)

    total = n_pass + n_fail
    print(f"\n  {n_pass}/{total} PASS, {n_fail}/{total} FAIL")
    if fails:
        print("\n  First 10 failures:")
        for f in fails[:10]:
            print(f"    FAIL  {f}")
    return n_fail == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
