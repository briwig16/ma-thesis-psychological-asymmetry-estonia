"""
Print the full Welch's t-test values (t, df, p) for every comparison currently
summarized as Cohen's d + stars in Table 2 of ANOVA_2x2_Bilali_Style.docx.
Useful as a reference for when the underlying test statistics are needed.
"""

import math
from pathlib import Path

import pandas as pd
import pyreadstat
from scipy import stats

ROOT = Path(__file__).parent.parent

df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy().reset_index(drop=True)

df20, _ = pyreadstat.read_sav(
    str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"), encoding="latin1"
)
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy().reset_index(drop=True)


def clean(df, items, reverse_items=None, scale_max=None, dk_code=9):
    sub = df[items].apply(pd.to_numeric, errors="coerce")
    sub = sub.where(sub != dk_code)
    if reverse_items:
        for it in reverse_items:
            sub[it] = (scale_max + 1) - sub[it]
    return sub.mean(axis=1, skipna=True)


def invert(s, smax): return (smax + 1) - s.astype(float)


SPECS = [
    {"name": "Superordinate Identity", "smax": 4, "inv": True,
     "items_23": ["Q67_2","Q67_4","Q67_5"], "rev_23": ["Q67_4"],
     "items_20": ["K6X5_2","K6X5_3","K6X5_4"], "rev_20": ["K6X5_3"],
     "group_split": False},
    {"name": "SD: Primary Out-group", "smax": 5, "inv": False,
     "items_23": {"E": ["Q57_1","Q58_1","Q59_1"], "R": ["Q57_2","Q58_2","Q59_2"]},
     "items_20": {"E": ["K4X7_1","K4X8_1","K4X9_1"], "R": ["K4X7_2","K4X8_2","K4X9_2"]},
     "group_split": True},
    {"name": "SD: General Out-group", "smax": 5, "inv": False,
     "items_23": ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"],
     "items_20": ["K4X7_3","K4X8_3","K4X9_3"],
     "group_split": False},
    {"name": "Comparative Opportunity Assessment", "smax": 5, "inv": True,
     "items_23": [f"Q44_{i}" for i in range(1, 13)],
     "items_20": [f"K3X1_{i}" for i in range(1, 13)],
     "group_split": False},
    {"name": "Belief in Inevitable Conflict", "smax": 4, "inv": False,
     "items_23": ["Q63_1","Q63_2","Q63_3","Q63_4"], "rev_23": ["Q63_1","Q63_2"],
     "items_20": ["K6X1_1","K6X1_2","K6X1_3","K6X1_4"], "rev_20": ["K6X1_1","K6X1_2"],
     "group_split": False},
    {"name": "Minority Inclusion Support", "smax": 4, "inv": True,
     "items_23": ["Q68_1","Q68_2","Q68_3"],
     "items_20": ["K6X6_1","K6X6_2","K6X6_3"],
     "group_split": False},
]


def build(spec):
    out = {}
    for df, year in [(df23, 2023), (df20, 2020)]:
        if spec["group_split"]:
            for grp_code, grp_key in [(0, "E"), (1, "R")]:
                sub = df[df["ethnicity_binary"] == grp_code]
                vals = clean(sub, spec[f"items_{str(year)[-2:]}"][grp_key],
                             spec.get(f"rev_{str(year)[-2:]}"), spec["smax"])
                if spec["inv"]: vals = invert(vals, spec["smax"])
                out[("Estonian" if grp_code == 0 else "Russian", year)] = vals.dropna()
        else:
            for grp_code in (0, 1):
                sub = df[df["ethnicity_binary"] == grp_code]
                vals = clean(sub, spec[f"items_{str(year)[-2:]}"],
                             spec.get(f"rev_{str(year)[-2:]}"), spec["smax"])
                if spec["inv"]: vals = invert(vals, spec["smax"])
                out[("Estonian" if grp_code == 0 else "Russian", year)] = vals.dropna()
    return out


def fmt_p(p):
    if p < .0001: return "< .0001"
    if p < .001:  return f"{p:.4f}"
    return f"{p:.3f}"


print(f"{'Composite':<37}{'Comparison':<35}{'t':>10}{'df':>10}{'p':>12}")
print("=" * 104)
for spec in SPECS:
    data = build(spec)
    comps = [
        ("Est 2020 vs Rus 2020", data[("Estonian",2020)], data[("Russian",2020)]),
        ("Est 2023 vs Rus 2023", data[("Estonian",2023)], data[("Russian",2023)]),
        ("Est 2023 vs Est 2020", data[("Estonian",2023)], data[("Estonian",2020)]),
        ("Rus 2023 vs Rus 2020", data[("Russian",2023)],  data[("Russian",2020)]),
    ]
    for label, a, b in comps:
        t, p = stats.ttest_ind(a, b, equal_var=False)
        # Welch–Satterthwaite df
        vA, vB = a.var(ddof=1), b.var(ddof=1)
        nA, nB = len(a), len(b)
        num = (vA/nA + vB/nB) ** 2
        den = (vA/nA)**2 / (nA-1) + (vB/nB)**2 / (nB-1)
        df = num / den
        print(f"{spec['name']:<37}{label:<35}{t:>+10.3f}{df:>10.1f}{fmt_p(p):>12}")
    print()
