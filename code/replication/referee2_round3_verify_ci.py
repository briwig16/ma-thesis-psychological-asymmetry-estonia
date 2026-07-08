"""
Referee 2 — Round 3 Independent Verification
==============================================
Independently re-implements the entire effect-size pipeline added in Round 3
(2026-04-28/29) and compares cell-by-cell against the canonical
`code/_effect_sizes.tsv`.

Verifies for every variable × group × year (44 cells across 11 variables and
both within-group and between-group comparisons):
  • Composite (or single-item) means, SDs, and N's using pairwise deletion
  • Cohen's d (root-mean-square SD denominator)
  • 95% CI on d via Hedges & Olkin (1985) asymptotic SE
  • Welch's t-test p-value

Total: ~440 numeric checks plus 4 declared significance-flip claims from
SESSION_LOG §26.

Per protocol:
  - Reads raw data and the author's TSV; does NOT call author code
  - Does NOT modify any author file
"""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
from scipy import stats

ROOT = Path(__file__).parent.parent.parent
TSV  = ROOT / "code" / "_effect_sizes.tsv"

PASS = 0
FAIL = 0
ISSUES = []

def check(label, computed, expected, tol=0.005):
    """Compare computed vs expected within tolerance."""
    global PASS, FAIL
    if pd.isna(computed) or pd.isna(expected):
        ISSUES.append(f"  NaN encountered for {label}")
        FAIL += 1
        return
    diff = abs(computed - expected)
    if diff <= tol:
        PASS += 1
    else:
        FAIL += 1
        ISSUES.append(f"  FAIL {label}: computed={computed:.4f}  expected={expected:.4f}  diff={diff:.4f}")


# -------- Independent re-implementation of composite/d/CI machinery --------
def to_numeric_safe(s, dk=9):
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s != dk)

def composite(df, items, reverse_items=None, scale_max=None, dk=9):
    sub = df[items].apply(pd.to_numeric, errors="coerce")
    sub = sub.where(sub != dk)
    if reverse_items:
        for it in reverse_items:
            sub[it] = (scale_max + 1) - sub[it]
    return sub.mean(axis=1, skipna=True)

def single_item(df, var, dk=9):
    s = pd.to_numeric(df[var], errors="coerce")
    return s.where(s != dk).astype(float)

def invert(s, scale_max):
    return (scale_max + 1) - s.astype(float)

def m_sd_n(s):
    s = s.dropna().astype(float)
    return s.mean(), s.std(ddof=1), len(s)

def cohens_d_rms(m1, sd1, n1, m2, sd2, n2):
    s = math.sqrt((sd1**2 + sd2**2) / 2)
    d = (m1 - m2) / s
    se = math.sqrt((n1 + n2)/(n1*n2) + d**2/(2*(n1+n2-2)))
    return d, d - 1.96*se, d + 1.96*se

def welch_p(a, b):
    a = pd.Series(a).dropna().astype(float)
    b = pd.Series(b).dropna().astype(float)
    return float(stats.ttest_ind(a, b, equal_var=False).pvalue)


# -------- Load raw data --------
print("="*72)
print("Referee 2 — Round 3: Independent Verification of Effect Sizes + CIs")
print("="*72)

df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy()

df20, _ = pyreadstat.read_sav(str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"),
                              encoding="latin1")
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy()

print(f"\n  2023 (after T8 filter): {len(df23)} respondents — "
      f"{(df23['ethnicity_binary']==0).sum()} Est, {(df23['ethnicity_binary']==1).sum()} Rus")
print(f"  2020 (after T9_1/T9_2 filter): {len(df20)} respondents — "
      f"{(df20['ethnicity_binary']==0).sum()} Est, {(df20['ethnicity_binary']==1).sum()} Rus")

# -------- Build all 11 variable group-year series independently --------
def build():
    out = {}
    out["Superordinate Identity"] = {
        "scale_max": 4, "inverted": True,
        "e23": composite(df23[df23["ethnicity_binary"]==0],
                         ["Q67_2","Q67_4","Q67_5"], ["Q67_4"], scale_max=4),
        "r23": composite(df23[df23["ethnicity_binary"]==1],
                         ["Q67_2","Q67_4","Q67_5"], ["Q67_4"], scale_max=4),
        "e20": composite(df20[df20["ethnicity_binary"]==0],
                         ["K6X5_2","K6X5_3","K6X5_4"], ["K6X5_3"], scale_max=4),
        "r20": composite(df20[df20["ethnicity_binary"]==1],
                         ["K6X5_2","K6X5_3","K6X5_4"], ["K6X5_3"], scale_max=4),
    }
    out["SD: Primary Out-group"] = {
        "scale_max": 5, "inverted": False,
        "e23": composite(df23[df23["ethnicity_binary"]==0], ["Q57_1","Q58_1","Q59_1"]),
        "r23": composite(df23[df23["ethnicity_binary"]==1], ["Q57_2","Q58_2","Q59_2"]),
        "e20": composite(df20[df20["ethnicity_binary"]==0], ["K4X7_1","K4X8_1","K4X9_1"]),
        "r20": composite(df20[df20["ethnicity_binary"]==1], ["K4X7_2","K4X8_2","K4X9_2"]),
    }
    out["SD: General Out-group"] = {
        "scale_max": 5, "inverted": False,
        "e23": composite(df23[df23["ethnicity_binary"]==0],
                         ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"]),
        "r23": composite(df23[df23["ethnicity_binary"]==1],
                         ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"]),
        "e20": composite(df20[df20["ethnicity_binary"]==0], ["K4X7_3","K4X8_3","K4X9_3"]),
        "r20": composite(df20[df20["ethnicity_binary"]==1], ["K4X7_3","K4X8_3","K4X9_3"]),
    }
    out["Comparative Opportunity Assessment"] = {
        "scale_max": 5, "inverted": True,
        "e23": composite(df23[df23["ethnicity_binary"]==0], [f"Q44_{i}" for i in range(1,13)]),
        "r23": composite(df23[df23["ethnicity_binary"]==1], [f"Q44_{i}" for i in range(1,13)]),
        "e20": composite(df20[df20["ethnicity_binary"]==0], [f"K3X1_{i}" for i in range(1,13)]),
        "r20": composite(df20[df20["ethnicity_binary"]==1], [f"K3X1_{i}" for i in range(1,13)]),
    }
    out["Belief in Inevitable Conflict"] = {
        "scale_max": 4, "inverted": False,
        # 2026-04-30: composite reverse-coding flipped from Q63_3/Q63_4 to
        # Q63_1/Q63_2 so that higher composite = more conflict belief.
        "e23": composite(df23[df23["ethnicity_binary"]==0],
                         ["Q63_1","Q63_2","Q63_3","Q63_4"], ["Q63_1","Q63_2"], scale_max=4),
        "r23": composite(df23[df23["ethnicity_binary"]==1],
                         ["Q63_1","Q63_2","Q63_3","Q63_4"], ["Q63_1","Q63_2"], scale_max=4),
        "e20": composite(df20[df20["ethnicity_binary"]==0],
                         ["K6X1_1","K6X1_2","K6X1_3","K6X1_4"], ["K6X1_1","K6X1_2"], scale_max=4),
        "r20": composite(df20[df20["ethnicity_binary"]==1],
                         ["K6X1_1","K6X1_2","K6X1_3","K6X1_4"], ["K6X1_1","K6X1_2"], scale_max=4),
    }
    out["Minority Support Inclusion"] = {
        "scale_max": 4, "inverted": True,
        "e23": composite(df23[df23["ethnicity_binary"]==0], ["Q68_1","Q68_2","Q68_3"]),
        "r23": composite(df23[df23["ethnicity_binary"]==1], ["Q68_1","Q68_2","Q68_3"]),
        "e20": composite(df20[df20["ethnicity_binary"]==0], ["K6X6_1","K6X6_2","K6X6_3"]),
        "r20": composite(df20[df20["ethnicity_binary"]==1], ["K6X6_1","K6X6_2","K6X6_3"]),
    }
    out["Contact: Estonian Speakers"] = {
        "scale_max": 5, "inverted": True,
        "e23": composite(df23[df23["ethnicity_binary"]==0], [f"Q51_{i}" for i in range(1,7)]),
        "r23": composite(df23[df23["ethnicity_binary"]==1], [f"Q51_{i}" for i in range(1,7)]),
        "e20": composite(df20[df20["ethnicity_binary"]==0], [f"K4X1_{i}" for i in range(1,7)]),
        "r20": composite(df20[df20["ethnicity_binary"]==1], [f"K4X1_{i}" for i in range(1,7)]),
    }
    out["Contact: Russian Speakers"] = {
        "scale_max": 5, "inverted": True,
        "e23": composite(df23[df23["ethnicity_binary"]==0], [f"Q52_{i}" for i in range(1,7)]),
        "r23": composite(df23[df23["ethnicity_binary"]==1], [f"Q52_{i}" for i in range(1,7)]),
        "e20": composite(df20[df20["ethnicity_binary"]==0], [f"K4X2_{i}" for i in range(1,7)]),
        "r20": composite(df20[df20["ethnicity_binary"]==1], [f"K4X2_{i}" for i in range(1,7)]),
    }
    out["Group ID Patterns"] = {
        "scale_max": 5, "inverted": False,
        "e23": single_item(df23[df23["ethnicity_binary"]==0], "Q66", dk=9),
        "r23": single_item(df23[df23["ethnicity_binary"]==1], "Q66", dk=9),
        "e20": single_item(df20[df20["ethnicity_binary"]==0], "K6X4", dk=6),
        "r20": single_item(df20[df20["ethnicity_binary"]==1], "K6X4", dk=6),
    }
    out["Territorial Attachment"] = {
        "scale_max": 4, "inverted": True,
        "e23": single_item(df23[df23["ethnicity_binary"]==0], "Q67_1"),
        "r23": single_item(df23[df23["ethnicity_binary"]==1], "Q67_1"),
        "e20": single_item(df20[df20["ethnicity_binary"]==0], "K6X5_1"),
        "r20": single_item(df20[df20["ethnicity_binary"]==1], "K6X5_1"),
    }
    out["Contact: Out-group"] = {
        "scale_max": 5, "inverted": True,
        "e23": composite(df23[df23["ethnicity_binary"]==0], [f"Q52_{i}" for i in range(1,7)]),
        "r23": composite(df23[df23["ethnicity_binary"]==1], [f"Q51_{i}" for i in range(1,7)]),
        "e20": composite(df20[df20["ethnicity_binary"]==0], [f"K4X2_{i}" for i in range(1,7)]),
        "r20": composite(df20[df20["ethnicity_binary"]==1], [f"K4X1_{i}" for i in range(1,7)]),
    }
    return out

vars_data = build()


# -------- Load author's TSV and verify each row --------
tsv = pd.read_csv(TSV, sep="\t")
print(f"\n  Author's TSV: {len(tsv)} rows ({sum(tsv['table']=='between')} between, {sum(tsv['table']=='within')} within)")

print("\n" + "="*72)
print("Verifying each row of _effect_sizes.tsv ...")
print("="*72)

for _, row in tsv.iterrows():
    var = row["variable"]
    info = vars_data[var]
    inv = info["inverted"]
    smax = info["scale_max"]

    # Get inverted series (mirroring author's convention)
    e20 = invert(info["e20"], smax) if inv else info["e20"].astype(float)
    r20 = invert(info["r20"], smax) if inv else info["r20"].astype(float)
    e23 = invert(info["e23"], smax) if inv else info["e23"].astype(float)
    r23 = invert(info["r23"], smax) if inv else info["r23"].astype(float)

    if row["table"] == "between":
        # TSV stores M1 = Estonian, M2 = Russian; d = M_est − M_rus
        year = row["comparison"]
        if year == "2020":
            sA, sB = e20, r20
        else:
            sA, sB = e23, r23
        m1, sd1, n1 = m_sd_n(sA)
        m2, sd2, n2 = m_sd_n(sB)
        d, ll, ul = cohens_d_rms(m1, sd1, n1, m2, sd2, n2)
    else:  # within
        # TSV stores M1 = 2020, M2 = 2023; d = M_2023 − M_2020
        group = row["comparison"]
        if group == "Estonian":
            sA, sB = e20, e23
        else:
            sA, sB = r20, r23
        m1, sd1, n1 = m_sd_n(sA)
        m2, sd2, n2 = m_sd_n(sB)
        # d uses 2023 - 2020 (sB - sA)
        d, ll, ul = cohens_d_rms(m2, sd2, n2, m1, sd1, n1)

    p = welch_p(sA, sB)

    tag = f"[{row['table']:<7}] {var:<37} {row['comparison']:<10}"
    check(f"{tag} M1",      m1,   row["M1"],     tol=0.01)
    check(f"{tag} SD1",     sd1,  row["SD1"],    tol=0.01)
    check(f"{tag} N1",      n1,   row["N1"],     tol=0)
    check(f"{tag} M2",      m2,   row["M2"],     tol=0.01)
    check(f"{tag} SD2",     sd2,  row["SD2"],    tol=0.01)
    check(f"{tag} N2",      n2,   row["N2"],     tol=0)
    check(f"{tag} d",       d,    row["d"],      tol=0.01)
    check(f"{tag} CI_low",  ll,   row["CI_low"], tol=0.01)
    check(f"{tag} CI_high", ul,   row["CI_high"],tol=0.01)
    check(f"{tag} p",       p,    row["p"],      tol=0.005)


# -------- Verify the four declared significance flips from SESSION_LOG §26 --------
print("\n" + "="*72)
print("Verifying SESSION_LOG §26 significance-flip claims ...")
print("="*72)

# §26 originally listed four flips; Round 3 audit found that the fourth (SD
# General between-group 2023) was a transcription error — the canonical TSV
# value (.049) is unchanged from §12. Only three flips are real.
flips = [
    ("§26 flip 1: Superord Id Est within: ns @ p≈.059",
     "within", "Superordinate Identity", "Estonian", "p in [.05,.07]"),
    ("§26 flip 2: Contact Est Spkrs Est within: * @ p≈.016",
     "within", "Contact: Estonian Speakers", "Estonian", "p in [.01,.03]"),
    ("§26 flip 3: Contact Rus Spkrs Est within: * @ p≈.043",
     "within", "Contact: Russian Speakers", "Estonian", "p in [.03,.05]"),
    ("§26 non-flip: SD General between 2023: still * @ p≈.049",
     "between", "SD: General Out-group", "2023", "p in [.04,.05]"),
]
for label, tbl, var, comp, band in flips:
    row = tsv[(tsv["table"]==tbl) & (tsv["variable"]==var) & (tsv["comparison"]==comp)].iloc[0]
    p = row["p"]
    lo, hi = float(band.split("[")[1].split(",")[0]), float(band.split(",")[1].rstrip("]"))
    if lo <= p <= hi:
        PASS += 1
        print(f"  PASS  {label:<55}  p={p:.4f}")
    else:
        FAIL += 1
        ISSUES.append(f"  FAIL {label}: p={p:.4f} not in {band}")


# -------- Summary --------
total = PASS + FAIL
print("\n" + "="*72)
print(f"Summary: {PASS}/{total} PASS, {FAIL}/{total} FAIL")
print("="*72)
if ISSUES:
    print("\nIssues:")
    for issue in ISSUES:
        print(issue)
else:
    print("\nNo issues — all values match within tolerance.")
