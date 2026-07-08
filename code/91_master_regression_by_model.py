"""
Master regression tables organized BY MODEL rather than by variable.

Each table corresponds to one model specification and shows all 6 composites
× 2 groups (12 rows) so the reader can compare composites on the same model
specification side by side.

Models:
  Table 1 — Model 1: composite = B0 + B1*Year + ε
  Table 2 — Model 2: composite = B0 + B1*Year + B2*Contact + B3*(Year×Contact) + ε
  Table 3 — Model 3: composite = B0 + B1*Year + B2*Contact + B3*Language
                                + B4*(Year×Contact) + B5*(Year×Language)
                                + B6*(Contact×Language)
                                + B7*(Year×Contact×Language) + ε

This complements `Master_Regression_Table.docx` (which organizes by variable).
Both views share the same underlying regression fits.

Output: reports/Master_Regression_By_Model.docx
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = Path(__file__).parent.parent

# ---------- Load + helpers -------------------------------------------------
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


def to_num(s, dk=9):
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s != dk).astype(float)


CONTACT_2023 = {0: [f"Q52_{i}" for i in range(1, 7)], 1: [f"Q51_{i}" for i in range(1, 7)]}
CONTACT_2020 = {0: [f"K4X2_{i}" for i in range(1, 7)], 1: [f"K4X1_{i}" for i in range(1, 7)]}
LANG_2023 = {0: "Q71_2", 1: "Q71_1"}
LANG_2020 = {0: "K5_2",  1: "K5_1"}


def build_cell(spec, df, year, grp_code):
    if isinstance(spec[f"items_{year}"], dict):
        grp_key = "E" if grp_code == 0 else "R"
        items = spec[f"items_{year}"][grp_key]
        rev = (spec[f"rev_{year}"][grp_key] if spec.get(f"rev_{year}") else None)
    else:
        items = spec[f"items_{year}"]
        rev = spec.get(f"rev_{year}")
    sub_df = df[df["ethnicity_binary"] == grp_code]
    composite_vals = clean(sub_df, items, rev, spec["smax"])
    if spec["inv"]:
        composite_vals = (spec["smax"] + 1) - composite_vals
    contact_items = (CONTACT_2023[grp_code] if year == 2023 else CONTACT_2020[grp_code])
    contact_vals = 6 - clean(sub_df, contact_items)
    lang_col = LANG_2023[grp_code] if year == 2023 else LANG_2020[grp_code]
    lang_vals = 7 - to_num(sub_df[lang_col])
    return pd.DataFrame({
        "value": composite_vals.values, "contact": contact_vals.values,
        "language": lang_vals.values, "year_2023": 1 if year == 2023 else 0,
    })


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


def fit_models(spec, grp_code):
    s20 = build_cell(spec, df20, 2020, grp_code)
    s23 = build_cell(spec, df23, 2023, grp_code)
    long = pd.concat([s20, s23], ignore_index=True).dropna()
    long["contact_c"]   = long["contact"]  - long["contact"].mean()
    long["language_c"]  = long["language"] - long["language"].mean()
    long["yearXcontact"]  = long["year_2023"] * long["contact_c"]
    long["yearXlanguage"] = long["year_2023"] * long["language_c"]
    long["contactXlanguage"]      = long["contact_c"] * long["language_c"]
    long["yearXcontactXlanguage"] = long["year_2023"] * long["contact_c"] * long["language_c"]

    X1 = sm.add_constant(long[["year_2023"]])
    m1 = sm.OLS(long["value"], X1).fit()

    X2 = sm.add_constant(long[["year_2023", "contact_c", "yearXcontact"]])
    m2 = sm.OLS(long["value"], X2).fit(cov_type="HC3")

    X3 = sm.add_constant(long[["year_2023", "contact_c", "language_c",
                                "yearXcontact", "yearXlanguage",
                                "contactXlanguage", "yearXcontactXlanguage"]])
    m3 = sm.OLS(long["value"], X3).fit(cov_type="HC3")

    return m1, m2, m3


# ---------- Fit all 12 cells × 3 models -----------------------------------
fits = {}
for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        m1, m2, m3 = fit_models(spec, grp_code)
        fits[(spec["name"], grp_name)] = {"M1": m1, "M2": m2, "M3": m3}


def stars(p):
    if pd.isna(p): return ""
    if p < .001: return "***"
    if p < .01:  return "**"
    if p < .05:  return "*"
    if p < .10:  return "⁺"
    return ""


def coef_cell(m, key):
    if key not in m.params:
        return "—"
    b  = m.params[key]
    se = m.bse[key]
    p  = m.pvalues[key]
    return f"{b:+.3f}\n({se:.3f}){stars(p)}"


# ============================================================================
#                                 WORD DOC
# ============================================================================
doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Cm(1.2)
sec.top_margin = sec.bottom_margin = Cm(1.8)
sec.orientation = 1  # landscape
sec.page_width  = Cm(29.7)
sec.page_height = Cm(21.0)
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(9)


def H(text, size=14, color=None):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = True; r.font.size = Pt(size)
    if color: r.font.color.rgb = color


def body(text, italic=False, size=10):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.size = Pt(size); r.italic = italic


def set_cell(cell, text, *, bold=False, italic=False, size=8,
             align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    para = cell.paragraphs[0]
    para.alignment = align
    text = str(text)
    for i, line in enumerate(text.split("\n")):
        r = para.add_run(line)
        r.font.size = Pt(size)
        r.bold = bold
        r.italic = italic
        if i < len(text.split("\n")) - 1:
            r.add_break()


def merge_v(table, rows, col):
    cells = [table.rows[r].cells[col] for r in rows]
    merged = cells[0]
    for c in cells[1:]:
        merged = merged.merge(c)
    return merged


# ----- Title + intro --------------------------------------------------------
H("Master Regression Results — By Model",
  size=18, color=RGBColor(0x1f, 0x29, 0x37))

body(
    "This document organizes the within-group regression results by MODEL "
    "specification rather than by variable. Each table corresponds to one "
    "model and lists all six non-contact composites × two ethnic groups "
    "(12 rows), so the reader can compare composites at the same level of "
    "modeling complexity. This is the complement to "
    "`Master_Regression_Table.docx`, which organizes by variable.",
    italic=True
)

body(
    "Cell format: B (SE) with significance star. Year is binary (0 = 2020, "
    "1 = 2023). Contact and Language are mean-centered within group. HC3 "
    "robust standard errors for Models 2 and 3. *** p < .001, ** p < .01, "
    "* p < .05, ⁺ p < .10. Predictors not in the model are marked '—'.",
    italic=True, size=9
)

doc.add_paragraph()


# ============================================================================
#                              TABLE 1 — MODEL 1
# ============================================================================
H("Table 1. Model 1 — Year-only within-group regressions", size=13)
body(
    "composite = B₀ + B₁·Year + ε.  "
    "B₁ is the within-group mean shift from 2020 to 2023 on the original "
    "Likert scale. With a binary 0/1 predictor and no covariates, B₁ is "
    "mathematically equal to (M₂₀₂₃ − M₂₀₂₀) for that cell.",
    italic=True, size=10
)
doc.add_paragraph()

header1 = ["Composite", "Group", "N", "B₀ (Intercept)", "B₁ (Year)", "R²"]
tbl1 = doc.add_table(rows=1, cols=len(header1))
tbl1.style = "Light Grid Accent 1"
for i, h in enumerate(header1):
    set_cell(tbl1.rows[0].cells[i], h, bold=True, size=9,
             align=WD_ALIGN_PARAGRAPH.CENTER)

for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        m1 = fits[(spec["name"], grp_name)]["M1"]
        row = tbl1.add_row().cells
        set_cell(row[0], spec["name"], bold=True, size=9)
        set_cell(row[1], grp_name, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[2], str(int(m1.nobs)), size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[3], coef_cell(m1, "const"), size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[4], coef_cell(m1, "year_2023"), size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[5], f"{m1.rsquared:.3f}", size=9, align=WD_ALIGN_PARAGRAPH.CENTER)


doc.add_paragraph()
body(
    "Reading note. Rows alternate Estonian / Russian within each composite, "
    "so each composite's asymmetric-divergence pattern is visible in adjacent "
    "rows. Same-signed Estonian and Russian B₁'s = parallel change (both groups "
    "moved together). Opposite-signed = asymmetric divergence in opposite "
    "directions. One-group-only significant = asymmetric divergence with one "
    "group unchanged. Cohen's d for each row is in the summary table of "
    "Master_Regression_Table.docx.",
    italic=True, size=8
)

doc.add_paragraph()
doc.add_page_break()


# ============================================================================
#                              TABLE 2 — MODEL 2
# ============================================================================
H("Table 2. Model 2 — Year × Out-group Contact moderation", size=13)
body(
    "composite = B₀ + B₁·Year + B₂·Contact_c + B₃·(Year × Contact_c) + ε.  "
    "Contact mean-centered within group, inverted so higher = more frequent. "
    "B₁ is the year effect AT AVERAGE CONTACT. B₂ is the contact-attitude "
    "slope at 2020. B₃ is the change in that contact slope from 2020 to 2023 "
    "(the moderation effect). HC3 robust SEs.",
    italic=True, size=10
)
doc.add_paragraph()

header2 = ["Composite", "Group", "N",
           "B₀ Intercept", "B₁ Year", "B₂ Contact",
           "B₃ Year × Contact", "R²"]
tbl2 = doc.add_table(rows=1, cols=len(header2))
tbl2.style = "Light Grid Accent 1"
for i, h in enumerate(header2):
    set_cell(tbl2.rows[0].cells[i], h, bold=True, size=9,
             align=WD_ALIGN_PARAGRAPH.CENTER)

for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        m2 = fits[(spec["name"], grp_name)]["M2"]
        row = tbl2.add_row().cells
        set_cell(row[0], spec["name"], bold=True, size=9)
        set_cell(row[1], grp_name, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[2], str(int(m2.nobs)), size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[3], coef_cell(m2, "const"),         size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[4], coef_cell(m2, "year_2023"),     size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[5], coef_cell(m2, "contact_c"),     size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[6], coef_cell(m2, "yearXcontact"),  size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[7], f"{m2.rsquared:.3f}",           size=9,   align=WD_ALIGN_PARAGRAPH.CENTER)


doc.add_paragraph()
body(
    "Reading note. The B₂ column gives the contact–attitude slope at 2020. "
    "A positive B₂ on a positive-attitude composite (Superordinate Identity, "
    "Comparative Opportunity, Minority Inclusion Support) supports classical "
    "contact theory. A negative B₂ on a distance/conflict composite "
    "(SD: Primary, SD: General, Belief in Inevitable Conflict) also supports "
    "classical contact theory. The B₃ column flags moderation: when "
    "significant, the contact-attitude slope CHANGED between 2020 and 2023.",
    italic=True, size=8
)

doc.add_paragraph()
doc.add_page_break()


# ============================================================================
#                              TABLE 3 — MODEL 3
# ============================================================================
H("Table 3. Model 3 — Full three-way Year × Contact × Language moderation",
  size=13)
body(
    "composite = B₀ + B₁·Year + B₂·Contact_c + B₃·Language_c "
    "+ B₄·(Year × Contact_c) + B₅·(Year × Language_c) "
    "+ B₆·(Contact_c × Language_c) + B₇·(Year × Contact_c × Language_c) + ε. "
    "Saturated linear-additive moderation model for three predictors. HC3 "
    "robust SEs. Out-group language reverse-coded so higher = more proficient.",
    italic=True, size=10
)

doc.add_paragraph()

header3 = ["Composite", "Group", "N",
           "B₁ Year", "B₂ Contact", "B₃ Lang",
           "B₄ Y×C", "B₅ Y×L", "B₆ C×L", "B₇ Y×C×L", "R²"]
tbl3 = doc.add_table(rows=1, cols=len(header3))
tbl3.style = "Light Grid Accent 1"
for i, h in enumerate(header3):
    set_cell(tbl3.rows[0].cells[i], h, bold=True, size=8.5,
             align=WD_ALIGN_PARAGRAPH.CENTER)

for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        m3 = fits[(spec["name"], grp_name)]["M3"]
        row = tbl3.add_row().cells
        set_cell(row[0], spec["name"], bold=True, size=8.5)
        set_cell(row[1], grp_name,                size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[2], str(int(m3.nobs)),       size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[3], coef_cell(m3, "year_2023"),             size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[4], coef_cell(m3, "contact_c"),             size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[5], coef_cell(m3, "language_c"),            size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[6], coef_cell(m3, "yearXcontact"),          size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[7], coef_cell(m3, "yearXlanguage"),         size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[8], coef_cell(m3, "contactXlanguage"),      size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[9], coef_cell(m3, "yearXcontactXlanguage"), size=7.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[10], f"{m3.rsquared:.3f}",                  size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)


doc.add_paragraph()
body(
    "Reading note. The B₁ column shows the year effect for the 'typical' "
    "respondent — at average contact AND average language. Differences between "
    "Table 1's B₁ and this B₁ reflect controlling for contact and language "
    "composition. The B₆ column directly tests 'does language affect the impact "
    "of contact?' (significant in only 1 of 12 cells — Estonian × Comparative "
    "Opportunity). The B₇ column tests whether the Year × Contact moderation "
    "itself depends on language (no significant cells).",
    italic=True, size=8
)


# ============================================================================
#                       CLOSING — How the three views compare
# ============================================================================
doc.add_paragraph()
H("How to use these three model tables", size=12)
body(
    "Reading vertically within a single table compares composites at a fixed "
    "level of model complexity. For example, scanning Table 1's B₁ column "
    "shows that Estonian respondents shifted negatively (toward more distance / "
    "less inclusion) on most composites while Russian respondents stayed put "
    "or shifted in different directions — the asymmetric-divergence pattern "
    "is directly readable at a glance.",
    italic=True
)
body(
    "Reading horizontally within a row (one composite × one group), compare "
    "B₁ across Tables 1, 2, and 3: a stable B₁ indicates the year effect is "
    "independent of contact and language; a shifting B₁ indicates the added "
    "predictors absorb some year-related variance.",
    italic=True
)
body(
    "This document and Master_Regression_Table.docx contain the SAME regression "
    "fits viewed from two angles: by-model (here) lets you compare composites "
    "at a given level of complexity; by-variable (the other doc) lets you "
    "follow one composite's coefficient progression across all three models. "
    "Use both side-by-side when interpreting any single result.",
    italic=True
)

out = ROOT / "reports" / "Master_Regression_By_Model.docx"
doc.save(out)
print(f"Saved: {out}")
