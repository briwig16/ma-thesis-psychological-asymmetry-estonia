"""
Compute Cohen's d on CFA factor scores produced by _cfa_factor_scores.R,
paralleling _pc1_effect_sizes.py. Then build a comparison table:
   composite-mean d  vs.  PC1 d  vs.  CFA d
across both between-group and within-group comparisons.

Sign convention is matched to _effect_sizes.tsv (positive d = more of the
construct after the display-direction inversion).
"""

import math
from pathlib import Path

import pandas as pd
from scipy import stats

ROOT = Path(__file__).parent.parent
fs = pd.read_csv(ROOT / "code" / "_cfa_factor_scores.csv")

VARS = {
    "Superordinate Identity":            ("si_score",  True,  "pooled"),
    "SD: Primary Out-group":             ("sdp_score", False, "per group"),
    "SD: General Out-group":             ("sdg_score", False, "per year"),
    "Comparative Opportunity Assessment":("co_score",  True,  "pooled"),
    "Belief in Inevitable Conflict":     ("bic_score", False, "pooled"),
    "Minority Inclusion Support":        ("ms_score",  True,  "pooled"),
}


def m_sd_n(s):
    s = pd.Series(s).dropna().astype(float)
    return s.mean(), s.std(ddof=1), len(s)

def cohens_d(m1, sd1, n1, m2, sd2, n2):
    s = math.sqrt((sd1**2 + sd2**2) / 2)
    d = (m1 - m2) / s
    se = math.sqrt((n1 + n2) / (n1 * n2) + d**2 / (2 * (n1 + n2 - 2)))
    return d, d - 1.96*se, d + 1.96*se

def welch(a, b):
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    return float(stats.ttest_ind(a, b, equal_var=False).pvalue)

def stars(p):
    return "***" if p<.001 else "**" if p<.01 else "*" if p<.05 else "ns"


# Sign-orient the CFA scores. lavaan picks an arbitrary sign for the latent
# variable; we flip so positive = "more of the construct" matching the
# composite-mean-d convention (which inverts SI, CompOpp, MinSupp).
COMPOSITE_D_SIGN = {
    "Superordinate Identity":             +1,   # Est > Rus (more belonging)
    "SD: Primary Out-group":              +1,   # Est > Rus (more distance)
    "SD: General Out-group":              -1,   # 2020 Est < Rus
    "Comparative Opportunity Assessment": -1,   # Est < Rus (perceives more Est-advantage)
    "Belief in Inevitable Conflict":      +1,   # Est > Rus
    "Minority Inclusion Support":         -1,   # Est < Rus (less supportive)
}

# Reference: 2020 between-group d signs from _effect_sizes.tsv.
# Estimate sign of current CFA scores by computing 2020 between-group d, then
# flip to match the reference sign.
for var, (col, _, _) in VARS.items():
    e20 = fs.loc[(fs["group"]==0) & (fs["wave"]==2020), col]
    r20 = fs.loc[(fs["group"]==1) & (fs["wave"]==2020), col]
    me, sde, ne = m_sd_n(e20); mr, sdr, nr = m_sd_n(r20)
    if ne < 5 or nr < 5: continue
    raw_sign = 1 if (me - mr) >= 0 else -1
    target = COMPOSITE_D_SIGN[var]
    if var == "SD: Primary Out-group":
        # Per-group fit — orient EACH GROUP independently to its own
        # sign-stable direction. Use within-group 2023-2020 sign to ensure
        # consistency? Easier: orient to make within-group Est sign match
        # composite (Est 2023>2020 → +0.42, so Est 2023 score should be > Est 2020 score).
        # Russian within-group is not significant either way; just keep sign as-is.
        # For SD Primary, the sign of the latent is determined per group, so we
        # cannot meaningfully flip group 0 and group 1 independently and still
        # compare them. Just keep raw scores.
        continue
    if raw_sign != target:
        fs[col] = -fs[col]

# For SD: Primary Out-group, orient per group using the within-group sign.
# Composite within-group d: Estonian +0.42, Russian -0.08. The sign of CFA
# for each group should be chosen so the within-group d matches that direction.
for g, target_sign in [(0, +1), (1, -1)]:
    col = "sdp_score"
    s20 = fs.loc[(fs["group"]==g) & (fs["wave"]==2020), col]
    s23 = fs.loc[(fs["group"]==g) & (fs["wave"]==2023), col]
    m20, *_ = m_sd_n(s20); m23, *_ = m_sd_n(s23)
    raw_sign = 1 if (m23 - m20) >= 0 else -1
    if raw_sign != target_sign:
        fs.loc[fs["group"]==g, col] = -fs.loc[fs["group"]==g, col]

# For SD: General Out-group, orient per year using between-group sign.
# Composite: 2020 d = -0.207 (Est<Rus); 2023 d = +0.108 (Est>Rus).
for y, target_sign in [(2020, -1), (2023, +1)]:
    col = "sdg_score"
    e = fs.loc[(fs["group"]==0) & (fs["wave"]==y), col]
    r = fs.loc[(fs["group"]==1) & (fs["wave"]==y), col]
    me, *_ = m_sd_n(e); mr, *_ = m_sd_n(r)
    raw_sign = 1 if (me - mr) >= 0 else -1
    if raw_sign != target_sign:
        fs.loc[fs["wave"]==y, col] = -fs.loc[fs["wave"]==y, col]


# ---------------- Build effect-size rows ----------------------------------
rows = []
for var, (col, _, scope) in VARS.items():
    cells = {}
    for y in (2020, 2023):
        for g, gname in [(0, "Estonian"), (1, "Russian")]:
            s = fs.loc[(fs["group"]==g) & (fs["wave"]==y), col]
            cells[(gname, y)] = s

    # Between-group d
    for y in (2020, 2023):
        e = cells[("Estonian", y)]; r = cells[("Russian", y)]
        me, sde, ne = m_sd_n(e); mr, sdr, nr = m_sd_n(r)
        d, ll, ul = cohens_d(me, sde, ne, mr, sdr, nr)
        p = welch(e, r)
        flag = "invalid (per-group fit)" if scope=="per group" else ""
        rows.append(("between", var, str(y), me, sde, ne, mr, sdr, nr,
                     d, ll, ul, p, stars(p), flag))

    # Within-group d
    for g in ("Estonian", "Russian"):
        s20 = cells[(g, 2020)]; s23 = cells[(g, 2023)]
        m20, sd20, n20 = m_sd_n(s20); m23, sd23, n23 = m_sd_n(s23)
        d, ll, ul = cohens_d(m23, sd23, n23, m20, sd20, n20)
        p = welch(s23, s20)
        flag = "invalid (per-year fit)" if scope=="per year" else ""
        rows.append(("within", var, g, m20, sd20, n20, m23, sd23, n23,
                     d, ll, ul, p, stars(p), flag))


out = pd.DataFrame(rows, columns=[
    "table","variable","comparison","M1","SD1","N1","M2","SD2","N2",
    "d","CI_low","CI_high","p","sig","flag"])
out_path = ROOT / "code" / "_cfa_effect_sizes.tsv"
out.to_csv(out_path, sep="\t", index=False, float_format="%.4f")
print(f"Saved: {out_path}\n")


# ---------------- Comparison table ----------------------------------------
es = pd.read_csv(ROOT / "code" / "_effect_sizes.tsv", sep="\t")
pc1 = pd.read_csv(ROOT / "code" / "_pc1_effect_sizes.tsv", sep="\t")

# Keep only the 6 non-contact composites
keep_vars = list(VARS.keys())
es = es[es["variable"].isin(keep_vars)]
pc1 = pc1[pc1["variable"].isin(keep_vars)]
cfa = out

def key(r):
    return (r["table"], r["variable"], str(r["comparison"]))

merge = (
    es[["table","variable","comparison","d","p"]].rename(columns={"d":"d_composite","p":"p_composite"})
    .merge(pc1[["table","variable","comparison","d","p"]].rename(columns={"d":"d_PC1","p":"p_PC1"}),
           on=["table","variable","comparison"])
    .merge(cfa[["table","variable","comparison","d","p","flag"]].rename(columns={"d":"d_CFA","p":"p_CFA"}),
           on=["table","variable","comparison"])
)

merge["Δ(CFA−composite)"] = merge["d_CFA"] - merge["d_composite"]
merge["Δ(CFA−PC1)"]       = merge["d_CFA"] - merge["d_PC1"]

cmp_path = ROOT / "code" / "_d_comparison_composite_pc1_cfa.tsv"
merge.to_csv(cmp_path, sep="\t", index=False, float_format="%.4f")
print(f"Saved: {cmp_path}\n")

# Pretty print
print("="*120)
print("Cohen's d comparison: composite-mean  vs  PC1  vs  CFA factor score")
print("="*120)
print(f"{'tbl':<8}{'variable':<37}{'comp':<10}{'compos.':>10}{'PC1':>10}{'CFA':>10}{'Δ CFA-comp':>14}{'Δ CFA-PC1':>14}  flag")
for _, r in merge.iterrows():
    print(f"{r['table']:<8}{r['variable']:<37}{r['comparison']:<10}"
          f"{r['d_composite']:>+10.3f}{r['d_PC1']:>+10.3f}{r['d_CFA']:>+10.3f}"
          f"{r['Δ(CFA−composite)']:>+14.3f}{r['Δ(CFA−PC1)']:>+14.3f}  {r['flag']}")
