"""
APA-7-formatted master regression tables with β added for continuous main
effects.

Differences from script 91:
  - APA-style table formatting: no grid lines, just horizontal rules above the
    header, below the header, and below the last row; bold headers; no shading.
  - β (standardized regression coefficient) added for the continuous main
    effects: Contact (Models 2 and 3) and Language (Model 3 only). Not added
    for binary Year, the intercept, or any interaction term — see methods
    chapter for rationale.

β formula for a continuous predictor in raw-units regression:
    β = B × (SD_predictor / SD_outcome)
SE(β) is approximated as SE(B) × (SD_predictor / SD_outcome). p-values are
the same as for the raw B coefficient (the test statistic doesn't change).

Output: reports/Master_Regression_APA.docx
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

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

    sd_y = long["value"].std(ddof=1)
    sd_contact  = long["contact_c"].std(ddof=1)
    sd_language = long["language_c"].std(ddof=1)

    X1 = sm.add_constant(long[["year_2023"]])
    m1 = sm.OLS(long["value"], X1).fit()

    X2 = sm.add_constant(long[["year_2023", "contact_c", "yearXcontact"]])
    m2 = sm.OLS(long["value"], X2).fit(cov_type="HC3")

    X3 = sm.add_constant(long[["year_2023", "contact_c", "language_c",
                                "yearXcontact", "yearXlanguage",
                                "contactXlanguage", "yearXcontactXlanguage"]])
    m3 = sm.OLS(long["value"], X3).fit(cov_type="HC3")

    return {"M1": m1, "M2": m2, "M3": m3,
            "sd_y": sd_y, "sd_contact": sd_contact, "sd_language": sd_language}


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
    if key not in m.params:
        return "—"
    b  = m.params[key]
    se = m.bse[key]
    p  = m.pvalues[key]
    return f"{b:+.3f} ({se:.3f}){stars(p)}"


def beta_cell(m, key, sd_x, sd_y):
    if key not in m.params:
        return "—"
    b  = m.params[key]
    se = m.bse[key]
    p  = m.pvalues[key]
    scale = sd_x / sd_y if sd_y > 0 else float("nan")
    return f"{b * scale:+.3f}{stars(p)}"


# ============================================================================
#                          APA TABLE STYLING HELPERS
# ============================================================================
def _set_cell_border(cell, **kwargs):
    """Set individual borders on a cell.
    kwargs: top, bottom, left, right — each None or a dict
            {sz: half-points, val: "single", color: "auto"|hex}.
    """
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.find(qn("w:tcBorders"))
    if tcBorders is None:
        tcBorders = OxmlElement("w:tcBorders")
        tcPr.append(tcBorders)
    for side in ("top", "left", "bottom", "right"):
        spec = kwargs.get(side)
        elem = tcBorders.find(qn(f"w:{side}"))
        if elem is None:
            elem = OxmlElement(f"w:{side}")
            tcBorders.append(elem)
        if spec is None:
            elem.set(qn("w:val"), "nil")
        else:
            elem.set(qn("w:val"), spec.get("val", "single"))
            elem.set(qn("w:sz"),  str(spec.get("sz", 8)))
            elem.set(qn("w:color"), spec.get("color", "auto"))


def apply_apa_borders(table):
    """Strip all borders, then apply APA-style rules:
       - top rule above header (heavy)
       - thin rule below header
       - bottom rule below last row (heavy)
       No vertical lines anywhere. No internal horizontal lines between data rows.
    """
    n_rows = len(table.rows)
    for r_idx, row in enumerate(table.rows):
        for cell in row.cells:
            top = bottom = None
            if r_idx == 0:
                top    = {"sz": 12, "val": "single", "color": "000000"}
                bottom = {"sz": 6,  "val": "single", "color": "000000"}
            elif r_idx == n_rows - 1:
                bottom = {"sz": 12, "val": "single", "color": "000000"}
            _set_cell_border(cell,
                              top=top, bottom=bottom, left=None, right=None)


def remove_table_style(table):
    """Remove all table style + shading."""
    tblPr = table._tbl.find(qn("w:tblPr"))
    tblStyle = tblPr.find(qn("w:tblStyle")) if tblPr is not None else None
    if tblStyle is not None:
        tblPr.remove(tblStyle)
    # Clear cell shading
    for row in table.rows:
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            shd = tcPr.find(qn("w:shd"))
            if shd is not None:
                tcPr.remove(shd)


# ============================================================================
#                                 WORD DOC
# ============================================================================
doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Cm(1.5)
sec.top_margin = sec.bottom_margin = Cm(2.0)
sec.orientation = 1
sec.page_width  = Cm(29.7)
sec.page_height = Cm(21.0)
style = doc.styles["Normal"]
style.font.name = "Times New Roman"   # APA convention
style.font.size = Pt(11)


def set_cell(cell, text, *, bold=False, italic=False, size=10,
             align=WD_ALIGN_PARAGRAPH.LEFT,
             vcenter=False):
    """Write text to a cell. If italic_segments is provided, set those substrings italic."""
    cell.text = ""
    para = cell.paragraphs[0]
    para.alignment = align
    if vcenter:
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    text = str(text)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        r = para.add_run(line)
        r.font.size = Pt(size)
        r.font.name = "Times New Roman"
        r.bold = bold
        r.italic = italic
        if i < len(lines) - 1:
            r.add_break()


def set_cell_with_italics(cell, segments, *, size=10,
                           align=WD_ALIGN_PARAGRAPH.LEFT):
    """segments = list of (text, bold, italic) tuples."""
    cell.text = ""
    para = cell.paragraphs[0]
    para.alignment = align
    for text, bold, italic in segments:
        r = para.add_run(text)
        r.font.size = Pt(size)
        r.font.name = "Times New Roman"
        r.bold = bold
        r.italic = italic


def section_break():
    doc.add_paragraph()


def H_table_number(text):
    """APA table number: bold, on its own line."""
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = True; r.font.size = Pt(11)
    r.font.name = "Times New Roman"


def H_table_title(text):
    """APA table title: italic, on its own line."""
    p = doc.add_paragraph()
    r = p.add_run(text); r.italic = True; r.font.size = Pt(11)
    r.font.name = "Times New Roman"


def table_note(segments, size=9):
    """APA note row: starts with italic 'Note.' then regular prose."""
    p = doc.add_paragraph()
    for text, bold, italic in segments:
        r = p.add_run(text)
        r.font.size = Pt(size)
        r.font.name = "Times New Roman"
        r.bold = bold
        r.italic = italic


# ----- Title page material --------------------------------------------------
p = doc.add_paragraph()
r = p.add_run("Master Regression Results")
r.bold = True; r.font.size = Pt(16); r.font.name = "Times New Roman"

p = doc.add_paragraph()
r = p.add_run(
    "Within-group OLS regressions for the six non-contact composite outcomes, "
    "organized by model specification. All tables follow APA-7 formatting "
    "conventions: minimal horizontal rules, no vertical lines, italicized "
    "statistical symbols, table number bold above an italicized title."
)
r.italic = True; r.font.size = Pt(10); r.font.name = "Times New Roman"

section_break()


# ============================================================================
#                              TABLE 1 — MODEL 1
# ============================================================================
H_table_number("Table 1")
H_table_title(
    "Within-group year-only regressions for six composite outcomes "
    "(Model 1: composite = B₀ + B₁ × Year + ε)."
)

header1 = ["Composite", "Group", "n", "B₀ (SE)", "B₁ (SE)", "R²"]
tbl1 = doc.add_table(rows=1, cols=len(header1))
for i, h in enumerate(header1):
    # Italicize n, R²; bold all
    if h == "n":
        set_cell_with_italics(tbl1.rows[0].cells[i],
                              [("n", True, True)], size=10,
                              align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h == "R²":
        set_cell_with_italics(tbl1.rows[0].cells[i],
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

remove_table_style(tbl1)
apply_apa_borders(tbl1)

table_note([
    ("Note. ", False, True),
    ("Year coded 0 = 2020, 1 = 2023. ", False, False),
    ("B", False, True), ("₀ is the implied 2020 mean composite score; ", False, False),
    ("B", False, True), ("₁ is the within-group mean shift on the original Likert scale, "
                          "mathematically identical to ", False, False),
    ("M", False, True), ("₂₀₂₃ − ", False, False),
    ("M", False, True), ("₂₀₂₀. ", False, False),
    ("SE in parentheses. Significance: *** ", False, False),
    ("p", False, True), (" < .001, ** ", False, False),
    ("p", False, True), (" < .01, * ", False, False),
    ("p", False, True), (" < .05, ⁺ ", False, False),
    ("p", False, True), (" < .10.", False, False),
])

section_break()
doc.add_page_break()


# ============================================================================
#                              TABLE 2 — MODEL 2
# ============================================================================
H_table_number("Table 2")
H_table_title(
    "Within-group year × out-group contact moderation regressions "
    "(Model 2: composite = B₀ + B₁ × Year + B₂ × Contact_c "
    "+ B₃ × (Year × Contact_c) + ε)."
)

header2 = ["Composite", "Group", "n",
           "B₁ Year (SE)", "B₂ Contact (SE)", "β Contact",
           "B₃ Year × Contact (SE)", "R²"]
tbl2 = doc.add_table(rows=1, cols=len(header2))
for i, h in enumerate(header2):
    # Italicize the β symbol and n / R² / "Year" "Contact" etc.
    if h == "n":
        set_cell_with_italics(tbl2.rows[0].cells[i],
                              [("n", True, True)], size=10,
                              align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h == "R²":
        set_cell_with_italics(tbl2.rows[0].cells[i],
                              [("R", True, True), ("²", True, False)],
                              size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    elif "β" in h:
        # split: β symbol italic, rest plain
        before, _, after = h.partition("β")
        set_cell_with_italics(tbl2.rows[0].cells[i],
                              [(before, True, False),
                               ("β", True, True),
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
        set_cell(row[7], f"{m2.rsquared:.3f}",           size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

remove_table_style(tbl2)
apply_apa_borders(tbl2)

table_note([
    ("Note. ", False, True),
    ("Contact mean-centered within group; inverted so higher = more frequent. ", False, False),
    ("B", False, True), ("₁ is the year effect at average contact level. ", False, False),
    ("β", False, True), (" Contact is the standardized regression coefficient for "
                          "the contact main effect, computed as ", False, False),
    ("B", False, True), ("₂ × ", False, False),
    ("SD", False, True), ("(Contact) / ", False, False),
    ("SD", False, True), ("(outcome). HC3 robust standard errors. "
                           "*** ", False, False),
    ("p", False, True), (" < .001, ** ", False, False),
    ("p", False, True), (" < .01, * ", False, False),
    ("p", False, True), (" < .05, ⁺ ", False, False),
    ("p", False, True), (" < .10.", False, False),
])

section_break()
doc.add_page_break()


# ============================================================================
#                              TABLE 3 — MODEL 3
# ============================================================================
H_table_number("Table 3")
H_table_title(
    "Within-group full three-way Year × Contact × Language moderation "
    "regressions (Model 3, saturated)."
)

header3 = ["Composite", "Group", "n",
           "B₁ Year (SE)",
           "B₂ Contact (SE)", "β Cont.",
           "B₃ Lang (SE)",    "β Lang.",
           "B₄ Y×C (SE)", "B₅ Y×L (SE)",
           "B₆ C×L (SE)", "B₇ Y×C×L (SE)", "R²"]
tbl3 = doc.add_table(rows=1, cols=len(header3))
for i, h in enumerate(header3):
    if h == "n":
        set_cell_with_italics(tbl3.rows[0].cells[i],
                              [("n", True, True)], size=9,
                              align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h == "R²":
        set_cell_with_italics(tbl3.rows[0].cells[i],
                              [("R", True, True), ("²", True, False)],
                              size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h.startswith("β"):
        before, _, after = h.partition("β")
        set_cell_with_italics(tbl3.rows[0].cells[i],
                              [(before, True, False),
                               ("β", True, True),
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
        set_cell(row[3], coef_cell(m3, "year_2023"),                size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[4], coef_cell(m3, "contact_c"),                size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[5], beta_cell(m3, "contact_c",  f["sd_contact"],  f["sd_y"]),
                 size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[6], coef_cell(m3, "language_c"),               size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[7], beta_cell(m3, "language_c", f["sd_language"], f["sd_y"]),
                 size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[8],  coef_cell(m3, "yearXcontact"),            size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[9],  coef_cell(m3, "yearXlanguage"),           size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[10], coef_cell(m3, "contactXlanguage"),        size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[11], coef_cell(m3, "yearXcontactXlanguage"),   size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell(row[12], f"{m3.rsquared:.3f}",                     size=9, align=WD_ALIGN_PARAGRAPH.CENTER)

remove_table_style(tbl3)
apply_apa_borders(tbl3)

table_note([
    ("Note. ", False, True),
    ("Saturated linear-additive moderation model. Contact and Language "
     "mean-centered within group. Out-group language reverse-coded so "
     "higher = more proficient. ", False, False),
    ("β", False, True), (" Contact and ", False, False),
    ("β", False, True), (" Language are standardized regression coefficients "
                          "for the main effects, computed as ", False, False),
    ("B", False, True), (" × ", False, False),
    ("SD", False, True), ("(predictor) / ", False, False),
    ("SD", False, True), ("(outcome). HC3 robust standard errors. "
                           "Interactions and three-way term reported in raw "
                           "units only (standardized product terms have no "
                           "clean interpretation). *** ", False, False),
    ("p", False, True), (" < .001, ** ", False, False),
    ("p", False, True), (" < .01, * ", False, False),
    ("p", False, True), (" < .05, ⁺ ", False, False),
    ("p", False, True), (" < .10.", False, False),
])

section_break()


# ============================================================================
#                       CLOSING — How to read these tables
# ============================================================================
H_table_number("How to read these tables")
table_note([
    ("Each table lists 12 rows corresponding to six composite outcomes × two "
     "ethnic groups. Reading vertically within a single table compares "
     "composites at a fixed level of model complexity. Reading the same "
     "composite × group across Tables 1, 2, and 3 traces how each coefficient "
     "is qualified as additional predictors enter the model.\n\n", False, False),
    ("β is reported only for the continuous main effects (Contact in Tables 2 "
     "and 3; Language in Table 3). It is omitted for the binary Year "
     "predictor (where Cohen's ", False, False),
    ("d", False, True), (" provides the standardized effect-size benchmark) "
                          "and for all interaction terms (where standardized "
                          "product terms lack a clean interpretation).", False, False),
], size=10)

out = ROOT / "reports" / "Master_Regression_APA.docx"
doc.save(out)
print(f"Saved: {out}")
