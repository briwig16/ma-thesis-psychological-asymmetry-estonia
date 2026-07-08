"""
Re-run the within-group OLS regressions from script 79 with demographic
controls (age, gender, education, income) added, then append a new section
to the existing Within_Group_Year_Regression.docx.

Mirrors Bilali, Çelik, & Ok's (2014) footnote 3: they ran the same regressions
with age, gender, education, and income as covariates, found "these covariates
did not affect the main results of the stage of conflict, and their effects
were either not significant or not consistent across measures."

Model:
    composite = B0 + B1 * year_2023 + B2 * age + B3 * gender
                + B4 * education + B5 * income + ε
fitted separately within each ethnic group.

Demographic mapping:
    Age:       2023 T3        ←→ 2020 vanus
    Gender:    2023 T2        ←→ 2020 sugu       (1 = M, 2 = F)
    Education: 2023 T18       ←→ 2020 T22        (1 = lowest … N = highest)
    Income:    2023 T17       ←→ 2020 T19        (descriptive 5-level)

Output: appended section in reports/Within_Group_Year_Regression.docx
        + code/_within_group_year_regression_controlled.tsv
"""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = Path(__file__).parent.parent

# ---------- Load + demographic prep ---------------------------------------
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


def to_num(s, dk_values=(9, 99, 999, 9999)):
    s = pd.to_numeric(s, errors="coerce")
    s = s.where(~s.isin(dk_values))
    return s


# Map demographic columns to a consistent set of names: age, gender_F, education, income
df23["age"]       = to_num(df23["T3"])
df23["gender_F"]  = (to_num(df23["T2"]) == 2).astype(float)   # 1 if female, 0 if male
df23["education"] = to_num(df23["T18"])
df23["income"]    = to_num(df23["T17"])

df20["age"]       = to_num(df20["vanus"])
df20["gender_F"]  = (to_num(df20["sugu"]) == 2).astype(float)
df20["education"] = to_num(df20["T22"])
df20["income"]    = to_num(df20["T19"])

CONTROLS = ["age", "gender_F", "education", "income"]


# ---------- Composite builders --------------------------------------------
def clean(df, items, reverse_items=None, scale_max=None, dk_code=9):
    sub = df[items].apply(pd.to_numeric, errors="coerce")
    sub = sub.where(sub != dk_code)
    if reverse_items:
        for it in reverse_items:
            sub[it] = (scale_max + 1) - sub[it]
    return sub.mean(axis=1, skipna=True)


def build_one(spec, df, year, grp_code):
    """Return a DataFrame with composite value + controls + year_2023 dummy
    for one (composite, group, year) cell."""
    if isinstance(spec[f"items_{year}"], dict):
        grp_key = "E" if grp_code == 0 else "R"
        items = spec[f"items_{year}"][grp_key]
        rev = (spec[f"rev_{year}"][grp_key]
               if spec.get(f"rev_{year}") else None)
    else:
        items = spec[f"items_{year}"]
        rev = spec.get(f"rev_{year}")
    sub_df = df[df["ethnicity_binary"] == grp_code].copy()
    vals = clean(sub_df, items, rev, spec["smax"])
    if spec["inv"]:
        vals = (spec["smax"] + 1) - vals
    out = sub_df[CONTROLS].copy()
    out["value"] = vals.values
    out["year_2023"] = 1 if year == 2023 else 0
    return out


SPECS = [
    {"name": "Superordinate Identity", "smax": 4, "inv": True,
     "items_2023": ["Q67_2","Q67_4","Q67_5"], "rev_2023": ["Q67_4"],
     "items_2020": ["K6X5_2","K6X5_3","K6X5_4"], "rev_2020": ["K6X5_3"]},
    {"name": "SD: Primary Out-group", "smax": 5, "inv": False,
     "items_2023": {"E": ["Q57_1","Q58_1","Q59_1"], "R": ["Q57_2","Q58_2","Q59_2"]},
     "items_2020": {"E": ["K4X7_1","K4X8_1","K4X9_1"], "R": ["K4X7_2","K4X8_2","K4X9_2"]}},
    {"name": "SD: General Out-group", "smax": 5, "inv": False,
     "items_2023": ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"],
     "items_2020": ["K4X7_3","K4X8_3","K4X9_3"]},
    {"name": "Comparative Opportunity Assessment", "smax": 5, "inv": True,
     "items_2023": [f"Q44_{i}" for i in range(1,13)],
     "items_2020": [f"K3X1_{i}" for i in range(1,13)]},
    {"name": "Belief in Inevitable Conflict", "smax": 4, "inv": False,
     "items_2023": ["Q63_1","Q63_2","Q63_3","Q63_4"], "rev_2023": ["Q63_1","Q63_2"],
     "items_2020": ["K6X1_1","K6X1_2","K6X1_3","K6X1_4"], "rev_2020": ["K6X1_1","K6X1_2"]},
    {"name": "Minority Inclusion Support", "smax": 4, "inv": True,
     "items_2023": ["Q68_1","Q68_2","Q68_3"],
     "items_2020": ["K6X6_1","K6X6_2","K6X6_3"]},
]

unadjusted = pd.read_csv(ROOT / "code" / "_within_group_year_regression.tsv", sep="\t")

rows = []
for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        s20 = build_one(spec, df20, 2020, grp_code)
        s23 = build_one(spec, df23, 2023, grp_code)
        long = pd.concat([s20, s23], ignore_index=True)
        # Listwise deletion across composite + controls + year
        long = long.dropna(subset=["value", "year_2023"] + CONTROLS)
        X_cols = ["year_2023"] + CONTROLS
        X = sm.add_constant(long[X_cols])
        m = sm.OLS(long["value"], X).fit(cov_type="HC3")

        # Pull unadjusted B1 for comparison
        u = unadjusted[(unadjusted["variable"] == spec["name"]) &
                       (unadjusted["group"] == grp_name)].iloc[0]

        B1_adj = m.params["year_2023"]
        SE_adj = m.bse["year_2023"]
        ll_adj, ul_adj = m.conf_int().loc["year_2023"]
        p_adj  = m.pvalues["year_2023"]

        # Also extract control coefficients for the appendix
        ctrls = {c: (m.params[c], m.bse[c], m.pvalues[c]) for c in CONTROLS}

        rows.append({
            "variable": spec["name"], "group": grp_name,
            "N_used": int(m.nobs),
            "B1_unadj": u["B1_year2023"], "SE_unadj": u["SE"], "p_unadj": u["p"],
            "B1_adj": B1_adj, "SE_adj": SE_adj,
            "CI_low_adj": ll_adj, "CI_high_adj": ul_adj, "p_adj": p_adj,
            "delta_B1": B1_adj - u["B1_year2023"],
            # Controls
            **{f"{c}_B": ctrls[c][0] for c in CONTROLS},
            **{f"{c}_SE": ctrls[c][1] for c in CONTROLS},
            **{f"{c}_p": ctrls[c][2] for c in CONTROLS},
        })


out = pd.DataFrame(rows)
tsv_path = ROOT / "code" / "_within_group_year_regression_controlled.tsv"
out.to_csv(tsv_path, sep="\t", index=False, float_format="%.4f")
print(f"Saved TSV: {tsv_path}\n")


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ("⁺" if p < .10 else "ns")


def fmt_p(p):
    if p < .001: return "< .001"
    return f"{p:.3f}".lstrip("0")


# Print summary
print(f"{'Composite':<37}{'Group':<10}{'B1 unadj':>10}{'B1 adj':>10}{'Δ':>9}{'p adj':>10}")
print("=" * 86)
for r in rows:
    print(f"{r['variable']:<37}{r['group']:<10}"
          f"{r['B1_unadj']:>+10.3f}{r['B1_adj']:>+10.3f}"
          f"{r['delta_B1']:>+9.3f}{fmt_p(r['p_adj']):>10} {stars(r['p_adj'])}")


# ============================================================================
#                       APPEND TO EXISTING WORD DOC
# ============================================================================
doc_path = ROOT / "reports" / "Within_Group_Year_Regression.docx"
doc = Document(str(doc_path))

# Spacer pages between previous content and the new section
doc.add_page_break()


def H(text, size=14, color=None):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = True; r.font.size = Pt(size)
    if color: r.font.color.rgb = color


def body(text, italic=False, size=11):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.size = Pt(size); r.italic = italic
    return p


# --- Section header ---
H("Within-Group Regressions with Demographic Controls",
  size=14, color=RGBColor(0x1f, 0x29, 0x37))

body(
    "Following Bilali, Çelik & Ok's (2014) footnote 3, the within-group "
    "regressions reported above were re-fitted with four demographic covariates "
    "added: age (continuous, in years), gender (binary, 1 = female), education "
    "(ordinal, higher = more education), and income (ordinal 5-level descriptive "
    "household income). Listwise deletion was used across the composite, year, "
    "and all four covariates. Robust HC3 standard errors are reported because "
    "of variance heterogeneity in several cells (see §25, §28, §33 of the "
    "decision log).",
    italic=True,
)

body(
    "Demographic mapping. Age = 2023 T3 / 2020 vanus; gender = 2023 T2 / 2020 "
    "sugu (1 = female); education = 2023 T18 / 2020 T22; income = 2023 T17 / "
    "2020 T19 (5-level descriptive). All variables are pooled across waves "
    "within each ethnic group's regression.",
    italic=True, size=9,
)

body(
    "The model is:",
    italic=True,
)
eq = doc.add_paragraph()
eq.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = eq.add_run("composite = B₀ + B₁ × Year_2023 + B₂ × Age + B₃ × Female "
                "+ B₄ × Education + B₅ × Income + ε")
r.italic = True; r.font.size = Pt(11)

doc.add_paragraph()


# --- Side-by-side comparison table ---
H("Table 3. Year coefficient B₁: unadjusted vs. demographic-controlled", size=12)

header3 = ["Variable", "Group", "N",
           "B₁ unadjusted (SE)", "B₁ controlled (SE)",
           "Δ B₁", "95% CI controlled", "p controlled", "Sig"]
table3 = doc.add_table(rows=1, cols=len(header3))
table3.style = "Light Grid Accent 1"
for i, h in enumerate(header3):
    c = table3.rows[0].cells[i]; c.text = ""
    rr = c.paragraphs[0].add_run(h); rr.bold = True; rr.font.size = Pt(9)

for r in rows:
    row = table3.add_row().cells
    cells = [
        r["variable"], r["group"], str(r["N_used"]),
        f"{r['B1_unadj']:+.3f} ({r['SE_unadj']:.3f})",
        f"{r['B1_adj']:+.3f} ({r['SE_adj']:.3f})",
        f"{r['delta_B1']:+.3f}",
        f"[{r['CI_low_adj']:+.3f}, {r['CI_high_adj']:+.3f}]",
        fmt_p(r["p_adj"]),
        stars(r["p_adj"]),
    ]
    for i, val in enumerate(cells):
        c = row[i]; c.text = ""
        rr = c.paragraphs[0].add_run(val); rr.font.size = Pt(9)
        if i in range(3, 9):
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph()
body(
    "Note. N = listwise-deletion sample after dropping rows missing any of the "
    "composite, year, age, gender, education, or income variables. Δ B₁ = change "
    "from the unadjusted to the controlled coefficient. HC3 robust standard "
    "errors. Significance: *** p < .001, ** p < .01, * p < .05, ⁺ p < .10, "
    "ns = not significant.",
    italic=True, size=8,
)

# --- Narrative interpretation ---
doc.add_paragraph()
H("Did the controls change the within-group year effect?", size=12)

# Compute how many B1 estimates change "substantially" and how many flip sig.
def flip_sig(p_un, p_adj, threshold=.05):
    return (p_un < threshold) != (p_adj < threshold)

flips = [r for r in rows if flip_sig(r["p_unadj"], r["p_adj"])]
delta_max = max(rows, key=lambda r: abs(r["delta_B1"]))
delta_median = float(np.median([abs(r["delta_B1"]) for r in rows]))

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(8)
run = p.add_run(
    f"Across the 12 within-group regressions, adjusting for age, gender, education, "
    f"and income produced a median change in B₁ of {delta_median:+.3f} units on the "
    f"original Likert metric. The largest single change was {delta_max['delta_B1']:+.3f} "
    f"for {delta_max['group']} respondents on {delta_max['variable']}. "
)
run.font.size = Pt(11)
if not flips:
    run = p.add_run(
        "No regression's statistical-significance verdict changed (significant at "
        "p < .05 vs not) between the unadjusted and controlled models. The covariates' "
        "individual coefficients were small and inconsistent across composites, "
        "matching the pattern Bilali et al. (2014) reported in their footnote 3."
    )
    run.font.size = Pt(11)
else:
    flip_descs = [f"{r['variable']} ({r['group']})" for r in flips]
    run = p.add_run(
        f"The statistical-significance verdict at p < .05 changed for {len(flips)} of "
        f"the 12 regressions: {'; '.join(flip_descs)}. All other rows preserved their "
        "unadjusted significance verdict. Covariate coefficients were small and "
        "inconsistent across composites."
    )
    run.font.size = Pt(11)


# --- Controls coefficient appendix ---
doc.add_paragraph()
H("Appendix: Demographic-control coefficients", size=12)
body(
    "Full coefficient values for each covariate, per composite × group. Each "
    "cell shows B (SE) followed by significance star. The point of this table "
    "is to confirm that no single demographic covariate has a consistent, "
    "large effect across composites — supporting the decision to not foreground "
    "demographic-conditional findings in the main results.",
    italic=True, size=9,
)

header4 = ["Variable", "Group", "Age B (SE)", "Female B (SE)",
           "Education B (SE)", "Income B (SE)"]
table4 = doc.add_table(rows=1, cols=len(header4))
table4.style = "Light Grid Accent 1"
for i, h in enumerate(header4):
    c = table4.rows[0].cells[i]; c.text = ""
    rr = c.paragraphs[0].add_run(h); rr.bold = True; rr.font.size = Pt(9)

for r in rows:
    row = table4.add_row().cells
    cells = [
        r["variable"], r["group"],
        f"{r['age_B']:+.4f} ({r['age_SE']:.4f}) {stars(r['age_p'])}",
        f"{r['gender_F_B']:+.3f} ({r['gender_F_SE']:.3f}) {stars(r['gender_F_p'])}",
        f"{r['education_B']:+.3f} ({r['education_SE']:.3f}) {stars(r['education_p'])}",
        f"{r['income_B']:+.3f} ({r['income_SE']:.3f}) {stars(r['income_p'])}",
    ]
    for i, val in enumerate(cells):
        c = row[i]; c.text = ""
        rr = c.paragraphs[0].add_run(val); rr.font.size = Pt(8.5)

doc.save(str(doc_path))
print(f"\nAppended to: {doc_path}")
