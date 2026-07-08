"""
Fully APA-7-compliant version of the bivariate contact regression table
(parallel to script 97 / `Bivariate_Contact_Per_Cell_APA.docx`), now with all
the APA-required statistics for a simple linear regression:

  - n
  - F-statistic with degrees of freedom
  - p-value for the omnibus F-test
  - R²
  - b (unstandardized coefficient)
  - SE of b
  - t-statistic
  - p-value for the t-test
  - 95% CI on b
  - β (standardized coefficient, optional but useful)

These match the APA-7 reporting standards for simple linear regression as
shown in the example reference.

Also includes a worked example narrative paragraph at the bottom showing
how to write up one specific cell's results in standard APA prose.

Output: reports/Bivariate_Contact_APA_Complete.docx
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


CONTACT_2023 = {0: [f"Q52_{i}" for i in range(1, 7)], 1: [f"Q51_{i}" for i in range(1, 7)]}
CONTACT_2020 = {0: [f"K4X2_{i}" for i in range(1, 7)], 1: [f"K4X1_{i}" for i in range(1, 7)]}


def build_cell(spec, year, grp_code):
    df = df23 if year == 2023 else df20
    sub_df = df[df["ethnicity_binary"] == grp_code]
    if spec.get("single_item"):
        item = spec[f"items_{year}"]
        dk = spec.get(f"dk_{year}", 9)
        outcome = single_item(sub_df, item, dk_code=dk)
    elif isinstance(spec[f"items_{year}"], dict):
        grp_key = "E" if grp_code == 0 else "R"
        items = spec[f"items_{year}"][grp_key]
        rev = (spec[f"rev_{year}"][grp_key] if spec.get(f"rev_{year}") else None)
        outcome = clean(sub_df, items, rev, spec["smax"])
    else:
        items = spec[f"items_{year}"]
        rev = spec.get(f"rev_{year}")
        outcome = clean(sub_df, items, rev, spec["smax"])
    if spec["inv"]:
        outcome = (spec["smax"] + 1) - outcome
    contact_items = CONTACT_2023[grp_code] if year == 2023 else CONTACT_2020[grp_code]
    contact = 6 - clean(sub_df, contact_items)
    return pd.DataFrame({"value": outcome.values, "contact": contact.values}).dropna()


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
    {"name": "Group ID Patterns", "smax": 5, "inv": False, "single_item": True,
     "items_2023": "Q66", "items_2020": "K6X4",
     "dk_2023": 9, "dk_2020": 6},
    {"name": "Territorial Attachment", "smax": 4, "inv": True, "single_item": True,
     "items_2023": "Q67_1", "items_2020": "K6X5_1"},
]


def stars(p):
    if pd.isna(p): return ""
    if p < .001: return "***"
    if p < .01:  return "**"
    if p < .05:  return "*"
    if p < .10:  return "⁺"
    return ""


def fmt_p(p):
    if pd.isna(p): return "—"
    if p < .001: return "< .001"
    return f"{p:.3f}".lstrip("0")


# ---------- Run bivariate regressions per cell -----------------------------
rows = []
for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        for year in (2020, 2023):
            data = build_cell(spec, year, grp_code)
            if len(data) < 10: continue
            X = sm.add_constant(data["contact"])
            # Default OLS (homoscedastic) gives the standard APA-style F and t
            m = sm.OLS(data["value"], X).fit()
            b = m.params["contact"]
            SE_b = m.bse["contact"]
            t = m.tvalues["contact"]
            p_t = m.pvalues["contact"]
            ll, ul = m.conf_int().loc["contact"]
            sd_x = data["contact"].std(ddof=1)
            sd_y = data["value"].std(ddof=1)
            beta = b * sd_x / sd_y if sd_y > 0 else float("nan")
            rows.append({
                "variable": spec["name"], "group": grp_name, "year": year,
                "N": int(m.nobs),
                "F": m.fvalue, "df1": int(m.df_model), "df2": int(m.df_resid),
                "p_F": m.f_pvalue, "R2": m.rsquared,
                "b": b, "SE": SE_b, "t": t, "p_t": p_t,
                "CI_low": ll, "CI_high": ul,
                "beta": beta,
            })

df_out = pd.DataFrame(rows)
df_out.to_csv(ROOT / "code" / "_bivariate_contact_apa_complete.tsv",
               sep="\t", index=False, float_format="%.4f")
print(f"Saved TSV.\n")


# ============================================================================
#                          APA WORD DOC
# ============================================================================
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
        if tblStyle is not None: tblPr.remove(tblStyle)
    for row in table.rows:
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            shd = tcPr.find(qn("w:shd"))
            if shd is not None: tcPr.remove(shd)


doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Cm(1.2)
sec.top_margin = sec.bottom_margin = Cm(1.8)
sec.orientation = 1
sec.page_width  = Cm(29.7); sec.page_height = Cm(21.0)
doc.styles["Normal"].font.name = "Times New Roman"
doc.styles["Normal"].font.size = Pt(11)


def set_cell(cell, text, *, bold=False, italic=False, size=10,
              align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    para = cell.paragraphs[0]; para.alignment = align
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


def merge_v(table, rows, col):
    cells = [table.rows[r].cells[col] for r in rows]
    merged = cells[0]
    for c in cells[1:]: merged = merged.merge(c)
    return merged


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


def H_heading(text, size=14):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = True; r.font.size = Pt(size); r.font.name = "Times New Roman"


def body_para(text, italic=False, size=11):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.size = Pt(size); r.font.name = "Times New Roman"
    r.italic = italic


# ---------- Title --------------------------------------------------------
p = doc.add_paragraph()
r = p.add_run("Bivariate Regression of Each Outcome on Out-group Contact — Full APA-7 Reporting")
r.bold = True; r.font.size = Pt(15); r.font.name = "Times New Roman"

body_para(
    "Simple linear regression of each outcome on out-group contact frequency, "
    "run separately within each ethnic group × wave cell. This document "
    "expands the previous bivariate doc (Bivariate_Contact_Per_Cell_APA.docx) "
    "with the full set of APA-7-required regression statistics: the model-"
    "level omnibus F-test with degrees of freedom, the model R², the "
    "unstandardized coefficient b with its standard error, the t-statistic "
    "testing the coefficient, its p-value, and the 95% CI on b. The "
    "standardized coefficient β is included as a complement.",
    italic=True, size=10,
)
doc.add_paragraph()


# ---------- Table 1 --------------------------------------------------------
H_table_number("Table 1")
H_table_title(
    "Simple linear regression of each outcome on out-group contact, per "
    "ethnic group × wave (outcome = b₀ + b × Contact + ε)."
)

header = ["Outcome", "Group", "Wave", "n",
          "F (df₁, df₂)", "p (model)", "R²",
          "b (SE)", "β", "t",
          "95% CI on b", "p (b)"]
tbl = doc.add_table(rows=1, cols=len(header))
for i, h in enumerate(header):
    if h == "n":
        set_cell_italics(tbl.rows[0].cells[i], [("n", True, True)], size=9,
                          align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h == "R²":
        set_cell_italics(tbl.rows[0].cells[i],
                          [("R", True, True), ("²", True, False)],
                          size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h.startswith("β"):
        set_cell_italics(tbl.rows[0].cells[i], [("β", True, True)],
                          size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h == "t":
        set_cell_italics(tbl.rows[0].cells[i], [("t", True, True)],
                          size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h.startswith("F"):
        set_cell_italics(tbl.rows[0].cells[i],
                          [("F", True, True), (" (df₁, df₂)", True, False)],
                          size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    elif "p (" in h:
        # p (model) or p (b)
        rest = h.split("(", 1)[1].rstrip(")")
        set_cell_italics(tbl.rows[0].cells[i],
                          [("p", True, True), (f" ({rest})", True, False)],
                          size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h == "b (SE)":
        set_cell_italics(tbl.rows[0].cells[i],
                          [("b", True, True), (" (", True, False),
                           ("SE", True, True), (")", True, False)],
                          size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h.startswith("95"):
        set_cell_italics(tbl.rows[0].cells[i],
                          [("95% CI on ", True, False), ("b", True, True)],
                          size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    else:
        set_cell(tbl.rows[0].cells[i], h, bold=True, size=9,
                  align=WD_ALIGN_PARAGRAPH.CENTER)

ordered = []
for spec in SPECS:
    for grp in ("Estonian", "Russian"):
        for year in (2020, 2023):
            m = [r for r in rows if r["variable"] == spec["name"]
                                       and r["group"] == grp and r["year"] == year]
            if m: ordered.append(m[0])

row_idx = 1
outcome_starts = {}
for r in ordered:
    table_row = tbl.add_row().cells
    set_cell(table_row[0], r["variable"], size=9)
    set_cell(table_row[1], r["group"], size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(table_row[2], str(r["year"]), size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(table_row[3], str(r["N"]), size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(table_row[4], f"{r['F']:.2f} ({r['df1']}, {r['df2']})", size=9,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(table_row[5], fmt_p(r["p_F"]) + stars(r["p_F"]), size=9,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(table_row[6], f"{r['R2']:.3f}", size=9,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(table_row[7], f"{r['b']:+.3f} ({r['SE']:.3f})", size=9,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(table_row[8], f"{r['beta']:+.3f}{stars(r['p_t'])}", size=9,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(table_row[9], f"{r['t']:+.2f}", size=9,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(table_row[10], f"[{r['CI_low']:+.3f}, {r['CI_high']:+.3f}]",
              size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(table_row[11], fmt_p(r["p_t"]) + stars(r["p_t"]), size=9,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    if r["variable"] not in outcome_starts:
        outcome_starts[r["variable"]] = row_idx
    row_idx += 1

for spec in SPECS:
    start = outcome_starts.get(spec["name"])
    if start is None: continue
    end = start + 3
    if end < len(tbl.rows):
        merge_v(tbl, list(range(start, end + 1)), 0)
        set_cell(tbl.rows[start].cells[0], spec["name"], size=9)

remove_table_style(tbl); apply_apa_borders(tbl)

table_note([
    ("Note. ", False, True),
    ("Each row is one simple linear regression on a single ethnic group × "
     "wave cell. ", False, False),
    ("F", False, True), (" is the omnibus model F-statistic with numerator ", False, False),
    ("df", False, True), ("₁ = 1 (one predictor) and denominator ", False, False),
    ("df", False, True), ("₂ = ", False, False),
    ("n", False, True), (" − 2. ", False, False),
    ("p", False, True), (" (model) tests whether ", False, False),
    ("R", False, True), ("² differs reliably from zero. ", False, False),
    ("b", False, True), (" = unstandardized coefficient on the original "
                          "Likert scales. ", False, False),
    ("SE", False, True), (" = standard error of ", False, False),
    ("b", False, True), (". ", False, False),
    ("β", False, True), (" = standardized coefficient, computed as ", False, False),
    ("b", False, True), (" × ", False, False),
    ("SD", False, True), ("(Contact) / ", False, False),
    ("SD", False, True), ("(outcome). ", False, False),
    ("t", False, True), (" = ", False, False),
    ("b", False, True), (" / ", False, False),
    ("SE", False, True), (". 95% CIs use the asymptotic Student's-", False, False),
    ("t", False, True), (" distribution with ", False, False),
    ("df", False, True), ("₂. Default OLS standard errors. *** ", False, False),
    ("p", False, True), (" < .001, ** ", False, False),
    ("p", False, True), (" < .01, * ", False, False),
    ("p", False, True), (" < .05, ⁺ ", False, False),
    ("p", False, True), (" < .10.", False, False),
])

doc.add_paragraph(); doc.add_page_break()


# ============================================================================
#                  WORKED EXAMPLE — narrative APA paragraph
# ============================================================================
H_heading("Worked example — APA narrative reporting", size=13)

body_para(
    "Below is a sample APA-7 narrative paragraph for one of the 32 cells, "
    "demonstrating how the values in Table 1 are reported in prose. The "
    "example chosen is the cell with the largest standardized contact "
    "effect in the data: Russian respondents in 2020 on SD: Primary "
    "Out-group.",
    italic=True, size=10,
)

# Find the row to use
example_row = next(r for r in rows
                   if r["variable"] == "SD: Primary Out-group"
                   and r["group"] == "Russian" and r["year"] == 2020)

p = doc.add_paragraph()
p.paragraph_format.left_indent = Cm(1.0)
p.paragraph_format.right_indent = Cm(1.0)

def add_inline(p, text, italic=False, bold=False, size=11):
    r = p.add_run(text)
    r.font.size = Pt(size); r.font.name = "Times New Roman"
    r.italic = italic; r.bold = bold


# Build the narrative example
narrative_segments = [
    ("A simple linear regression was conducted to determine whether out-group "
     "contact significantly predicted Russian respondents' Social Distance "
     "from the Primary Out-group (Estonian-speakers) in 2020. The model "
     "explained a significant proportion of variance in social-distance "
     "scores, ", False, False),
    ("R", False, True), ("²", False, False),
    (f" = {example_row['R2']:.2f}, ", False, False),
    ("F", False, True),
    (f"(1, {example_row['df2']}) = {example_row['F']:.2f}, ", False, False),
    ("p", False, True),
    (f" = {fmt_p(example_row['p_F'])}. Furthermore, out-group contact was a "
     "significant negative predictor of social distance, ", False, False),
    ("b", False, True),
    (f" = {example_row['b']:.2f}, ", False, False),
    ("SE", False, True),
    (f" = {example_row['SE']:.2f}, ", False, False),
    ("t", False, True),
    (f" = {example_row['t']:.2f}, ", False, False),
    ("p", False, True),
    (f" {fmt_p(example_row['p_t'])}, 95% CI [{example_row['CI_low']:.2f}, "
     f"{example_row['CI_high']:.2f}]. The standardized coefficient was ", False, False),
    ("β", False, True),
    (f" = {example_row['beta']:.2f}, indicating that a one-standard-deviation "
     "increase in out-group contact was associated with a 0.29-standard-"
     "deviation decrease in social distance from Estonian-speakers, "
     "consistent with classical contact-theory predictions (Pettigrew & Tropp, "
     "2006).", False, False),
]
for text, bold, italic in narrative_segments:
    add_inline(p, text, italic=italic, bold=bold)

doc.add_paragraph()
body_para(
    "The same template applies to all 32 cells in Table 1. The numerical "
    "values for any cell can be read directly from the table and dropped into "
    "the prose pattern: \"R² = …, F(1, df₂) = …, p = …; b = …, SE = …, "
    "t = …, p = …, 95% CI […]; β = ….\"",
    italic=True, size=10,
)

out = ROOT / "reports" / "Bivariate_Contact_APA_Complete.docx"
doc.save(out)
print(f"Saved: {out}")
