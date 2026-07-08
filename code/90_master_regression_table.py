"""
Master regression results table consolidating all within-group regression
analyses from scripts 79, 81, 84, 88, and 89.

For each of the 6 non-contact composites, presents one APA-7-style
hierarchical regression table with three nested models per group:

  Model 1 — Year only (script 79)
              composite = B0 + B1*Year + ε

  Model 2 — Year + Contact moderation (script 84)
              composite = B0 + B1*Year + B2*Contact + B3*(Year × Contact) + ε

  Model 3 — Full three-way (script 89)
              composite = B0 + B1*Year + B2*Contact + B3*Language
                        + B4*(Year × Contact) + B5*(Year × Language)
                        + B6*(Contact × Language)
                        + B7*(Year × Contact × Language) + ε

Each cell reports B (SE) with significance stars. R², N, and F-statistic
appear at the bottom of each model column. Predictors run as rows; models
× groups run as columns.

Plus a leading summary table giving the headline B₁ (year effect) and Cohen's d
from `_effect_sizes.tsv` per composite × group for quick reference.

Output: reports/Master_Regression_Table.docx
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
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).parent.parent

# ---------- Load data + helpers --------------------------------------------
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

# Names of effect-sizes tsv variables (different for Minority Support)
ANOVA_TO_ES = {
    "Superordinate Identity":             "Superordinate Identity",
    "SD: Primary Out-group":              "SD: Primary Out-group",
    "SD: General Out-group":              "SD: General Out-group",
    "Comparative Opportunity Assessment": "Comparative Opportunity Assessment",
    "Belief in Inevitable Conflict":      "Belief in Inevitable Conflict",
    "Minority Inclusion Support":         "Minority Support Inclusion",
}

es_within = pd.read_csv(ROOT / "code" / "_effect_sizes.tsv", sep="\t")
es_within = es_within[es_within["table"] == "within"]


def stars(p):
    if pd.isna(p): return ""
    if p < .001: return "***"
    if p < .01:  return "**"
    if p < .05:  return "*"
    if p < .10:  return "⁺"
    return ""


def fmt_coef(b, se, p):
    if pd.isna(b): return "—"
    return f"{b:+.3f}\n({se:.3f}){stars(p)}"


def fmt_p(p):
    if pd.isna(p): return "—"
    if p < .001: return "< .001"
    return f"{p:.3f}".lstrip("0")


# ---------- Fit all three models per cell ----------------------------------
# Returns dict keyed (composite, group, model_id) → {coef: (B, SE, p), ...}
all_fits = {}

for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        s20 = build_cell(spec, df20, 2020, grp_code)
        s23 = build_cell(spec, df23, 2023, grp_code)
        long = pd.concat([s20, s23], ignore_index=True).dropna()
        # Center
        long["contact_c"]   = long["contact"]  - long["contact"].mean()
        long["language_c"]  = long["language"] - long["language"].mean()
        long["yearXcontact"]  = long["year_2023"] * long["contact_c"]
        long["yearXlanguage"] = long["year_2023"] * long["language_c"]
        long["contactXlanguage"]      = long["contact_c"] * long["language_c"]
        long["yearXcontactXlanguage"] = long["year_2023"] * long["contact_c"] * long["language_c"]

        # M1: year only
        X = sm.add_constant(long[["year_2023"]])
        m1 = sm.OLS(long["value"], X).fit()

        # M2: year + contact + year × contact
        X = sm.add_constant(long[["year_2023", "contact_c", "yearXcontact"]])
        m2 = sm.OLS(long["value"], X).fit(cov_type="HC3")

        # M3: full three-way
        X = sm.add_constant(long[["year_2023", "contact_c", "language_c",
                                   "yearXcontact", "yearXlanguage",
                                   "contactXlanguage", "yearXcontactXlanguage"]])
        m3 = sm.OLS(long["value"], X).fit(cov_type="HC3")

        for model_id, m in [("M1", m1), ("M2", m2), ("M3", m3)]:
            store = {}
            for name in m.params.index:
                store[name] = (m.params[name], m.bse[name], m.pvalues[name])
            store["__R2__"] = m.rsquared
            store["__N__"]  = int(m.nobs)
            store["__F__"]  = (m.fvalue, m.f_pvalue)
            all_fits[(spec["name"], grp_name, model_id)] = store


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
    if not isinstance(text, str):
        text = str(text)
    for line in text.split("\n"):
        r = para.add_run(line)
        r.font.size = Pt(size)
        r.bold = bold
        r.italic = italic
        if line != text.split("\n")[-1]:
            r.add_break()


def merge_vertical(table, rows, col):
    cells = [table.rows[r].cells[col] for r in rows]
    merged = cells[0]
    for c in cells[1:]:
        merged = merged.merge(c)
    return merged


# ----- Title + intro --------------------------------------------------------
H("Master Regression Results", size=18, color=RGBColor(0x1f, 0x29, 0x37))
body(
    "Consolidated within-group regression results for all six non-contact "
    "composite outcomes, presented as nested hierarchical models. The within-"
    "group year effect, Year × Contact moderation, and the full three-way "
    "Year × Contact × Language model are shown side by side per composite × "
    "group, allowing direct comparison of how the year effect (B₁) is "
    "qualified as additional predictors enter the model.",
    italic=True
)

body(
    "Model 1: composite = B₀ + B₁·Year + ε.  "
    "Model 2: composite = B₀ + B₁·Year + B₂·Contact + B₃·(Year × Contact) + ε.  "
    "Model 3 (saturated): composite = B₀ + B₁·Year + B₂·Contact + B₃·Language "
    "+ B₄·(Year × Contact) + B₅·(Year × Language) + B₆·(Contact × Language) "
    "+ B₇·(Year × Contact × Language) + ε.",
    italic=True, size=9
)

body(
    "Note. Year is binary (0 = 2020, 1 = 2023). Contact and Language are "
    "mean-centered within group. Out-group contact = communication frequency "
    "with the other ethnic group (Q51/Q52, K4X1/K4X2, inverted so higher = "
    "more frequent). Out-group language ability is reverse-coded so higher = "
    "more proficient (1 = none, 6 = native). HC3 robust standard errors for "
    "Models 2 and 3 (OLS standard errors for Model 1 to match the headline "
    "Bilali-style decomposition). Significance: *** p < .001, ** p < .01, "
    "* p < .05, ⁺ p < .10. Cell entries are B (SE) on the original Likert metric.",
    italic=True, size=8
)

doc.add_paragraph()


# ----- Summary table: B₁ from Model 1 + Cohen's d alongside ----------------
H("Summary: Year effect across all 6 composites (Model 1)", size=12)
body(
    "Side-by-side comparison of the unadjusted within-group year coefficient (B₁ on "
    "the Likert metric) and the corresponding Cohen's d (standardized effect size with "
    "95% CI) from `_effect_sizes.tsv`. The two quantities describe the same comparison "
    "in different units: B₁ in raw scale points, d in pooled-SD units.",
    italic=True, size=9
)

summary_header = ["Composite", "Group", "N", "B₁ (SE)", "d", "95% CI on d", "p"]
table_sum = doc.add_table(rows=1, cols=len(summary_header))
table_sum.style = "Light Grid Accent 1"
for i, h in enumerate(summary_header):
    set_cell(table_sum.rows[0].cells[i], h, bold=True, size=9,
             align=WD_ALIGN_PARAGRAPH.CENTER)

for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        m1 = all_fits[(spec["name"], grp_name, "M1")]
        B1, SE1, p1 = m1["year_2023"]
        # Lookup d
        es_row = es_within[
            (es_within["variable"] == ANOVA_TO_ES[spec["name"]]) &
            (es_within["comparison"] == grp_name)
        ].iloc[0]
        row_cells = table_sum.add_row().cells
        set_cell(row_cells[0], spec["name"], bold=True, size=9)
        set_cell(row_cells[1], grp_name, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row_cells[2], str(m1["__N__"]), size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row_cells[3], f"{B1:+.3f} ({SE1:.3f}){stars(p1)}",
                 size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row_cells[4], f"{es_row['d']:+.3f}{stars(es_row['p'])}",
                 size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row_cells[5], f"[{es_row['CI_low']:+.3f}, {es_row['CI_high']:+.3f}]",
                 size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row_cells[6], fmt_p(p1), size=9, align=WD_ALIGN_PARAGRAPH.CENTER)


# ----- One hierarchical table per composite --------------------------------
# Predictor display order (rows). __spacer__ used to add blank rows for fit stats.
PREDICTOR_ORDER = [
    ("Intercept",                              "const"),
    ("Year (2023 = 1)",                        "year_2023"),
    ("Contact (centered)",                     "contact_c"),
    ("Language (centered)",                    "language_c"),
    ("Year × Contact",                         "yearXcontact"),
    ("Year × Language",                        "yearXlanguage"),
    ("Contact × Language",                     "contactXlanguage"),
    ("Year × Contact × Language",              "yearXcontactXlanguage"),
]

for spec in SPECS:
    doc.add_paragraph()
    H(f"Hierarchical regression — {spec['name']}", size=12)

    body(
        "Models nested as defined above. Each cell shows B (unstandardized "
        "coefficient on the Likert metric) with SE in parentheses and "
        "significance star. Predictors that do not appear in a given model are "
        "marked '—'. R² and N reported at the bottom of each column.",
        italic=True, size=8
    )

    # Columns: Predictor | Est-M1 | Est-M2 | Est-M3 | Rus-M1 | Rus-M2 | Rus-M3
    n_data_rows = len(PREDICTOR_ORDER) + 3   # +R², +N, +F
    n_cols = 7

    tbl = doc.add_table(rows=2 + n_data_rows, cols=n_cols)
    tbl.style = "Light Grid Accent 1"

    # Header row 0: super-header
    set_cell(tbl.rows[0].cells[0], "Predictor", bold=True, size=9)
    # Estonian super-header spans cols 1–3
    est_header = tbl.rows[0].cells[1].merge(tbl.rows[0].cells[2]).merge(tbl.rows[0].cells[3])
    set_cell(est_header, "Estonian respondents", bold=True, size=9,
             align=WD_ALIGN_PARAGRAPH.CENTER)
    rus_header = tbl.rows[0].cells[4].merge(tbl.rows[0].cells[5]).merge(tbl.rows[0].cells[6])
    set_cell(rus_header, "Russian respondents", bold=True, size=9,
             align=WD_ALIGN_PARAGRAPH.CENTER)

    # Header row 1: model labels
    sub_headers = ["", "Model 1", "Model 2", "Model 3", "Model 1", "Model 2", "Model 3"]
    for i, h in enumerate(sub_headers):
        set_cell(tbl.rows[1].cells[i], h, bold=True, italic=True, size=8.5,
                 align=WD_ALIGN_PARAGRAPH.CENTER)
    # Merge the predictor column vertically across rows 0–1
    tbl.rows[0].cells[0].merge(tbl.rows[1].cells[0])

    # Data rows: one per predictor
    for r_idx, (label, key) in enumerate(PREDICTOR_ORDER, start=2):
        set_cell(tbl.rows[r_idx].cells[0], label, italic=False, size=8.5)

        for c_idx, (grp_name, model_id) in enumerate([
            ("Estonian", "M1"), ("Estonian", "M2"), ("Estonian", "M3"),
            ("Russian",  "M1"), ("Russian",  "M2"), ("Russian",  "M3"),
        ], start=1):
            fit = all_fits[(spec["name"], grp_name, model_id)]
            if key in fit:
                B, SE, p_val = fit[key]
                txt = f"{B:+.3f}\n({SE:.3f}){stars(p_val)}"
            else:
                txt = "—"
            set_cell(tbl.rows[r_idx].cells[c_idx], txt, size=8,
                     align=WD_ALIGN_PARAGRAPH.CENTER)

    # Fit statistics rows
    fit_row_start = 2 + len(PREDICTOR_ORDER)
    set_cell(tbl.rows[fit_row_start    ].cells[0], "R²",
             italic=True, size=8.5, bold=True)
    set_cell(tbl.rows[fit_row_start + 1].cells[0], "N",
             italic=True, size=8.5, bold=True)
    set_cell(tbl.rows[fit_row_start + 2].cells[0], "F (df1, df2)",
             italic=True, size=8.5, bold=True)

    for c_idx, (grp_name, model_id) in enumerate([
        ("Estonian", "M1"), ("Estonian", "M2"), ("Estonian", "M3"),
        ("Russian",  "M1"), ("Russian",  "M2"), ("Russian",  "M3"),
    ], start=1):
        fit = all_fits[(spec["name"], grp_name, model_id)]
        set_cell(tbl.rows[fit_row_start    ].cells[c_idx], f"{fit['__R2__']:.3f}",
                 size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(tbl.rows[fit_row_start + 1].cells[c_idx], str(fit["__N__"]),
                 size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        F, p_F = fit["__F__"]
        set_cell(tbl.rows[fit_row_start + 2].cells[c_idx],
                 f"{F:.2f}{stars(p_F)}", size=8,
                 align=WD_ALIGN_PARAGRAPH.CENTER)


# ----- Closing notes -------------------------------------------------------
doc.add_paragraph()
H("How to read the master regression tables", size=12)
body(
    "Each composite has its own hierarchical regression table. Reading "
    "left-to-right within a group, the columns show how the year effect (B₁) "
    "is qualified as additional predictors enter the model. When B₁ remains "
    "stable across Models 1, 2, and 3, the year effect is independent of "
    "contact and language. When B₁ shrinks substantially between models, "
    "the dropped variance is being absorbed by the added predictors — that's "
    "a mechanism-style finding. Comparing Estonian and Russian columns "
    "side-by-side highlights the asymmetric-divergence pattern.",
    italic=True
)
body(
    "Model 1 is the standard within-group decomposition reported in Tables 2 "
    "and 5 of the Bilali-style document. Model 2 introduces the moderation "
    "framework. Model 3 saturates the linear-additive moderation space with "
    "three predictors. Cohen's d for the headline year effect (Model 1) is "
    "shown in the summary table at the top for cross-composite comparison "
    "with conventional effect-size benchmarks (small ≈ 0.2, medium ≈ 0.5, "
    "large ≈ 0.8).",
    italic=True
)

out = ROOT / "reports" / "Master_Regression_Table.docx"
doc.save(out)
print(f"Saved: {out}")
