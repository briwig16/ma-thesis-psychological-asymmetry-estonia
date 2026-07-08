"""
APA-formatted master regression doc extended to include all 10 variables —
6 multi-item composites + 2 contact composites + 2 single-item variables
(Group ID Patterns and Territorial Attachment).

Same three-model structure as script 92:
  Model 1 — Year only
  Model 2 — Year × Contact moderation
  Model 3 — Full three-way Year × Contact × Language

For single-item variables, the regressions use the single item value (with DK
codes recoded to NaN) as the dependent variable, just like for the composite
outcomes. Sample sizes will be slightly smaller because of single-item
missingness vs. the composite's pairwise-deletion approach.

Output: reports/Master_Regression_APA_All_Variables.docx
"""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

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


def single_item(df, var, dk_code=9):
    s = pd.to_numeric(df[var], errors="coerce")
    return s.where(s != dk_code).astype(float)


def to_num(s, dk=9):
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s != dk).astype(float)


CONTACT_2023 = {0: [f"Q52_{i}" for i in range(1, 7)], 1: [f"Q51_{i}" for i in range(1, 7)]}
CONTACT_2020 = {0: [f"K4X2_{i}" for i in range(1, 7)], 1: [f"K4X1_{i}" for i in range(1, 7)]}
LANG_2023 = {0: "Q71_2", 1: "Q71_1"}
LANG_2020 = {0: "K5_2",  1: "K5_1"}


def build_cell(spec, df, year, grp_code):
    """Build composite/single-item value plus moderators (contact, language)
    plus year dummy. Returns a DataFrame ready for OLS."""
    if spec.get("single_item"):
        item = spec[f"items_{year}"]
        dk = spec.get(f"dk_{year}", 9)
        sub_df = df[df["ethnicity_binary"] == grp_code]
        outcome = single_item(sub_df, item, dk_code=dk)
    elif isinstance(spec[f"items_{year}"], dict):
        grp_key = "E" if grp_code == 0 else "R"
        items = spec[f"items_{year}"][grp_key]
        rev = (spec[f"rev_{year}"][grp_key] if spec.get(f"rev_{year}") else None)
        sub_df = df[df["ethnicity_binary"] == grp_code]
        outcome = clean(sub_df, items, rev, spec["smax"])
    else:
        items = spec[f"items_{year}"]
        rev = spec.get(f"rev_{year}")
        sub_df = df[df["ethnicity_binary"] == grp_code]
        outcome = clean(sub_df, items, rev, spec["smax"])

    if spec["inv"]:
        outcome = (spec["smax"] + 1) - outcome

    contact_items = CONTACT_2023[grp_code] if year == 2023 else CONTACT_2020[grp_code]
    contact = 6 - clean(sub_df, contact_items)
    lang_col = LANG_2023[grp_code] if year == 2023 else LANG_2020[grp_code]
    lang = 7 - to_num(sub_df[lang_col])

    return pd.DataFrame({
        "value": outcome.values, "contact": contact.values,
        "language": lang.values, "year_2023": 1 if year == 2023 else 0,
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
    {"name": "Contact: Estonian Speakers", "smax": 5, "inv": True,
     "items_2023": [f"Q51_{i}" for i in range(1,7)],
     "items_2020": [f"K4X1_{i}" for i in range(1,7)]},
    {"name": "Contact: Russian Speakers", "smax": 5, "inv": True,
     "items_2023": [f"Q52_{i}" for i in range(1,7)],
     "items_2020": [f"K4X2_{i}" for i in range(1,7)]},
    {"name": "Group ID Patterns", "smax": 5, "inv": False, "single_item": True,
     "items_2023": "Q66", "items_2020": "K6X4",
     "dk_2023": 9, "dk_2020": 6},
    {"name": "Territorial Attachment", "smax": 4, "inv": True, "single_item": True,
     "items_2023": "Q67_1", "items_2020": "K6X5_1",
     "dk_2023": 9, "dk_2020": 9},
]


def fit_models(spec, grp_code):
    s20 = build_cell(spec, df20, 2020, grp_code)
    s23 = build_cell(spec, df23, 2023, grp_code)
    long = pd.concat([s20, s23], ignore_index=True).dropna()
    long["contact_c"]  = long["contact"]  - long["contact"].mean()
    long["language_c"] = long["language"] - long["language"].mean()
    long["yearXcontact"]  = long["year_2023"] * long["contact_c"]
    long["yearXlanguage"] = long["year_2023"] * long["language_c"]
    long["contactXlanguage"]      = long["contact_c"] * long["language_c"]
    long["yearXcontactXlanguage"] = long["year_2023"] * long["contact_c"] * long["language_c"]
    sd_y = long["value"].std(ddof=1)
    sd_c = long["contact_c"].std(ddof=1)
    sd_l = long["language_c"].std(ddof=1)
    m1 = sm.OLS(long["value"], sm.add_constant(long[["year_2023"]])).fit()
    m2 = sm.OLS(long["value"], sm.add_constant(long[["year_2023","contact_c","yearXcontact"]])).fit(cov_type="HC3")
    m3 = sm.OLS(long["value"], sm.add_constant(long[["year_2023","contact_c","language_c",
                                                       "yearXcontact","yearXlanguage",
                                                       "contactXlanguage","yearXcontactXlanguage"]])).fit(cov_type="HC3")
    return {"M1": m1, "M2": m2, "M3": m3,
            "sd_y": sd_y, "sd_contact": sd_c, "sd_language": sd_l}


fits = {}
for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        fits[(spec["name"], grp_name)] = fit_models(spec, grp_code)


def stars(p):
    if pd.isna(p): return ""
    if p < .001: return "***"
    if p < .01:  return "**"
    if p < .05:  return "*"
    if p < .10:  return "⁺"
    return ""


def coef_cell(m, key):
    if key not in m.params: return "—"
    b = m.params[key]; se = m.bse[key]; p = m.pvalues[key]
    return f"{b:+.3f} ({se:.3f}){stars(p)}"


def beta_cell(m, key, sd_x, sd_y):
    if key not in m.params: return "—"
    b = m.params[key]; p = m.pvalues[key]
    if sd_y <= 0: return "—"
    return f"{b * sd_x/sd_y:+.3f}{stars(p)}"


# APA styling helpers
def _set_cell_border(cell, **kwargs):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.find(qn("w:tcBorders"))
    if tcBorders is None:
        tcBorders = OxmlElement("w:tcBorders"); tcPr.append(tcBorders)
    for side in ("top","left","bottom","right"):
        spec_ = kwargs.get(side)
        elem = tcBorders.find(qn(f"w:{side}"))
        if elem is None:
            elem = OxmlElement(f"w:{side}"); tcBorders.append(elem)
        if spec_ is None:
            elem.set(qn("w:val"), "nil")
        else:
            elem.set(qn("w:val"), spec_.get("val","single"))
            elem.set(qn("w:sz"),  str(spec_.get("sz", 8)))
            elem.set(qn("w:color"), spec_.get("color","auto"))


def apply_apa_borders(table, header_rows=1):
    n = len(table.rows)
    for r_idx, row in enumerate(table.rows):
        for cell in row.cells:
            top = bottom = None
            if r_idx == 0:
                top = {"sz": 12, "val":"single", "color":"000000"}
            if r_idx == header_rows - 1:
                bottom = {"sz": 6, "val":"single", "color":"000000"}
            if r_idx == n - 1:
                bottom = {"sz": 12, "val":"single", "color":"000000"}
            _set_cell_border(cell, top=top, bottom=bottom, left=None, right=None)


def remove_table_style(table):
    tblPr = table._tbl.find(qn("w:tblPr"))
    if tblPr is not None:
        tblStyle = tblPr.find(qn("w:tblStyle"))
        if tblStyle is not None:
            tblPr.remove(tblStyle)
    for row in table.rows:
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            shd = tcPr.find(qn("w:shd"))
            if shd is not None: tcPr.remove(shd)


doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Cm(1.5)
sec.top_margin = sec.bottom_margin = Cm(2.0)
sec.orientation = 1
sec.page_width  = Cm(29.7); sec.page_height = Cm(21.0)
doc.styles["Normal"].font.name = "Times New Roman"
doc.styles["Normal"].font.size = Pt(11)


def set_cell(cell, text, *, bold=False, italic=False, size=10,
              align=WD_ALIGN_PARAGRAPH.LEFT, vcenter=False):
    cell.text = ""
    para = cell.paragraphs[0]; para.alignment = align
    if vcenter: cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    lines = str(text).split("\n")
    for i, line in enumerate(lines):
        r = para.add_run(line)
        r.font.size = Pt(size); r.font.name = "Times New Roman"
        r.bold = bold; r.italic = italic
        if i < len(lines) - 1: r.add_break()


def set_cell_italics(cell, segments, *, size=10, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    para = cell.paragraphs[0]; para.alignment = align
    for text, bold, italic in segments:
        r = para.add_run(text)
        r.font.size = Pt(size); r.font.name = "Times New Roman"
        r.bold = bold; r.italic = italic


def H_table_number(text):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = True; r.font.size = Pt(11); r.font.name = "Times New Roman"


def H_table_title(text):
    p = doc.add_paragraph()
    r = p.add_run(text); r.italic = True; r.font.size = Pt(11); r.font.name = "Times New Roman"


def table_note(segments, size=9):
    p = doc.add_paragraph()
    for text, bold, italic in segments:
        r = p.add_run(text)
        r.font.size = Pt(size); r.font.name = "Times New Roman"
        r.bold = bold; r.italic = italic


p = doc.add_paragraph()
r = p.add_run("Master Regression Results — All 10 Variables")
r.bold = True; r.font.size = Pt(16); r.font.name = "Times New Roman"

p = doc.add_paragraph()
r = p.add_run(
    "Within-group OLS regressions for all 10 outcome variables: six multi-"
    "item attitudinal composites, two contact composites (behavioral "
    "indicators), and two single-item variables (Group ID Patterns and "
    "Territorial Attachment). Same three-model hierarchical structure as "
    "Master_Regression_APA.docx; β reported for continuous main effects "
    "(Contact in Tables 2 and 3; Language in Table 3). APA-7 formatting."
)
r.italic = True; r.font.size = Pt(10); r.font.name = "Times New Roman"
doc.add_paragraph()


# -------------- TABLE 1: Model 1 (Year only) -----------------------------
H_table_number("Table 1")
H_table_title(
    "Within-group year-only regressions (Model 1: composite = B₀ + B₁ × Year + ε)."
)
header1 = ["Variable", "Group", "n", "B₀ (SE)", "B₁ (SE)", "R²"]
tbl1 = doc.add_table(rows=1, cols=len(header1))
for i, h in enumerate(header1):
    if h == "n":
        set_cell_italics(tbl1.rows[0].cells[i], [("n", True, True)], size=10,
                          align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h == "R²":
        set_cell_italics(tbl1.rows[0].cells[i],
                          [("R", True, True), ("²", True, False)],
                          size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    else:
        set_cell(tbl1.rows[0].cells[i], h, bold=True, size=10,
                  align=WD_ALIGN_PARAGRAPH.CENTER)

for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        m1 = fits[(spec["name"], grp_name)]["M1"]
        row = tbl1.add_row().cells
        set_cell(row[0], spec["name"], size=10)
        set_cell(row[1], grp_name, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[2], str(int(m1.nobs)), size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[3], coef_cell(m1, "const"),     size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[4], coef_cell(m1, "year_2023"), size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[5], f"{m1.rsquared:.3f}", size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
remove_table_style(tbl1); apply_apa_borders(tbl1)
table_note([
    ("Note. ", False, True),
    ("Year coded 0 = 2020, 1 = 2023. ", False, False),
    ("B", False, True), ("₀ = implied 2020 mean composite (or single-item) "
                          "value; ", False, False),
    ("B", False, True), ("₁ = within-group mean shift from 2020 to 2023. "
                          "*** ", False, False),
    ("p", False, True), (" < .001, ** ", False, False),
    ("p", False, True), (" < .01, * ", False, False),
    ("p", False, True), (" < .05, ⁺ ", False, False),
    ("p", False, True), (" < .10.", False, False),
])
doc.add_paragraph(); doc.add_page_break()


# -------------- TABLE 2: Model 2 (Year × Contact) ------------------------
H_table_number("Table 2")
H_table_title(
    "Within-group year × contact moderation regressions "
    "(Model 2: composite = B₀ + B₁ × Year + B₂ × Contact_c "
    "+ B₃ × (Year × Contact_c) + ε)."
)
header2 = ["Variable", "Group", "n",
           "B₁ Year (SE)", "B₂ Contact (SE)", "β Contact",
           "B₃ Year × Contact (SE)", "R²"]
tbl2 = doc.add_table(rows=1, cols=len(header2))
for i, h in enumerate(header2):
    if h == "n":
        set_cell_italics(tbl2.rows[0].cells[i], [("n", True, True)], size=10,
                          align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h == "R²":
        set_cell_italics(tbl2.rows[0].cells[i],
                          [("R", True, True), ("²", True, False)],
                          size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    elif "β" in h:
        before, _, after = h.partition("β")
        set_cell_italics(tbl2.rows[0].cells[i],
                          [(before, True, False), ("β", True, True),
                           (after, True, False)],
                          size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    else:
        set_cell(tbl2.rows[0].cells[i], h, bold=True, size=10,
                  align=WD_ALIGN_PARAGRAPH.CENTER)

for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        f = fits[(spec["name"], grp_name)]
        m2 = f["M2"]
        row = tbl2.add_row().cells
        set_cell(row[0], spec["name"], size=10)
        set_cell(row[1], grp_name, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[2], str(int(m2.nobs)), size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[3], coef_cell(m2, "year_2023"),     size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[4], coef_cell(m2, "contact_c"),     size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[5], beta_cell(m2, "contact_c", f["sd_contact"], f["sd_y"]),
                  size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[6], coef_cell(m2, "yearXcontact"),  size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[7], f"{m2.rsquared:.3f}", size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
remove_table_style(tbl2); apply_apa_borders(tbl2)
table_note([
    ("Note. ", False, True),
    ("Contact mean-centered within group; inverted so higher = more "
     "frequent contact. ", False, False),
    ("B", False, True), ("₁ = year effect at average contact level. ", False, False),
    ("β", False, True), (" Contact = standardized regression coefficient "
                          "for the contact main effect. HC3 robust SEs. "
                          "Significance as above.", False, False),
])
doc.add_paragraph(); doc.add_page_break()


# -------------- TABLE 3: Model 3 (Full three-way) ------------------------
H_table_number("Table 3")
H_table_title("Full three-way Year × Contact × Language moderation "
               "regressions (Model 3, saturated).")
header3 = ["Variable", "Group", "n",
           "B₁ Year (SE)",
           "B₂ Contact (SE)", "β Cont.",
           "B₃ Lang (SE)",    "β Lang.",
           "B₄ Y×C (SE)", "B₅ Y×L (SE)",
           "B₆ C×L (SE)", "B₇ Y×C×L (SE)", "R²"]
tbl3 = doc.add_table(rows=1, cols=len(header3))
for i, h in enumerate(header3):
    if h == "n":
        set_cell_italics(tbl3.rows[0].cells[i], [("n", True, True)], size=9,
                          align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h == "R²":
        set_cell_italics(tbl3.rows[0].cells[i],
                          [("R", True, True), ("²", True, False)], size=9,
                          align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h.startswith("β"):
        before, _, after = h.partition("β")
        set_cell_italics(tbl3.rows[0].cells[i],
                          [(before, True, False), ("β", True, True),
                           (after, True, False)],
                          size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    else:
        set_cell(tbl3.rows[0].cells[i], h, bold=True, size=9,
                  align=WD_ALIGN_PARAGRAPH.CENTER)

for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        f = fits[(spec["name"], grp_name)]
        m3 = f["M3"]
        row = tbl3.add_row().cells
        set_cell(row[0], spec["name"], size=9)
        set_cell(row[1], grp_name, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[2], str(int(m3.nobs)), size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[3],  coef_cell(m3, "year_2023"),                size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[4],  coef_cell(m3, "contact_c"),                size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[5],  beta_cell(m3, "contact_c",  f["sd_contact"],  f["sd_y"]), size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[6],  coef_cell(m3, "language_c"),               size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[7],  beta_cell(m3, "language_c", f["sd_language"], f["sd_y"]), size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[8],  coef_cell(m3, "yearXcontact"),             size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[9],  coef_cell(m3, "yearXlanguage"),            size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[10], coef_cell(m3, "contactXlanguage"),         size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[11], coef_cell(m3, "yearXcontactXlanguage"),    size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[12], f"{m3.rsquared:.3f}",                      size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
remove_table_style(tbl3); apply_apa_borders(tbl3)
table_note([
    ("Note. ", False, True),
    ("Saturated linear-additive moderation model. All centered predictors. "
     "HC3 robust SEs. Significance as above.", False, False),
])

out = ROOT / "reports" / "Master_Regression_APA_All_Variables.docx"
doc.save(out)
print(f"Saved: {out}")
