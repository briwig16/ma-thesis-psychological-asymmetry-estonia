"""
Two MLR tables per cell — both with contact and language as predictors of the
attitudinal/contact outcomes, run separately for each ethnic group × wave.

Table 1 (Additive MLR):
    outcome = B0 + B1 * Contact_c + B2 * Language_c + ε
    Includes a "Bivariate B1 Contact" column from script 97 for direct
    partial-vs-total comparison.

Table 2 (Interaction MLR):
    outcome = B0 + B1 * Contact_c + B2 * Language_c + B3 * (Contact_c × Language_c) + ε

8 outcomes × 4 cells (Est 2020, Est 2023, Rus 2020, Rus 2023) = 32 regressions
per table, 64 total. Contact and Language are mean-centered within each cell.

Outputs:
  code/_mlr_contact_language_additive.tsv
  code/_mlr_contact_language_interaction.tsv
  reports/MLR_Contact_Language_APA.docx
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
    lang_col = LANG_2023[grp_code] if year == 2023 else LANG_2020[grp_code]
    lang = 7 - to_num(sub_df[lang_col])

    return pd.DataFrame({
        "value": outcome.values,
        "contact": contact.values,
        "language": lang.values,
    }).dropna()


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
    if p < .001:   return "< .001"
    return f"{p:.3f}".lstrip("0")


# Run both models for each cell
add_rows = []
int_rows = []
for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        for year in (2020, 2023):
            data = build_cell(spec, year, grp_code)
            if len(data) < 10:
                continue
            data["contact_c"]  = data["contact"]  - data["contact"].mean()
            data["language_c"] = data["language"] - data["language"].mean()
            data["cxl"] = data["contact_c"] * data["language_c"]

            sd_y    = data["value"].std(ddof=1)
            sd_cont = data["contact_c"].std(ddof=1)
            sd_lang = data["language_c"].std(ddof=1)
            sd_cxl  = data["cxl"].std(ddof=1)

            # ADDITIVE
            X_a = sm.add_constant(data[["contact_c", "language_c"]])
            m_a = sm.OLS(data["value"], X_a).fit(cov_type="HC3")
            B0a = m_a.params["const"]
            B1a = m_a.params["contact_c"];  SE1a = m_a.bse["contact_c"]
            p1a = m_a.pvalues["contact_c"]
            B2a = m_a.params["language_c"]; SE2a = m_a.bse["language_c"]
            p2a = m_a.pvalues["language_c"]
            beta1a = B1a * sd_cont / sd_y if sd_y > 0 else float("nan")
            beta2a = B2a * sd_lang / sd_y if sd_y > 0 else float("nan")

            # Bivariate B1 (contact only) for comparison column
            X_b = sm.add_constant(data[["contact_c"]])
            m_b = sm.OLS(data["value"], X_b).fit(cov_type="HC3")
            B1_biv = m_b.params["contact_c"]
            p1_biv = m_b.pvalues["contact_c"]

            add_rows.append({
                "variable": spec["name"], "group": grp_name, "year": year,
                "N": int(m_a.nobs), "B0": B0a,
                "B1_contact": B1a, "SE1": SE1a, "p1": p1a, "beta1": beta1a,
                "B2_language": B2a, "SE2": SE2a, "p2": p2a, "beta2": beta2a,
                "R2": m_a.rsquared,
                "B1_biv_contact": B1_biv, "p1_biv": p1_biv,
                "delta_B1": B1a - B1_biv,
            })

            # INTERACTION
            X_i = sm.add_constant(data[["contact_c", "language_c", "cxl"]])
            m_i = sm.OLS(data["value"], X_i).fit(cov_type="HC3")
            B0i = m_i.params["const"]
            B1i = m_i.params["contact_c"];  SE1i = m_i.bse["contact_c"];  p1i = m_i.pvalues["contact_c"]
            B2i = m_i.params["language_c"]; SE2i = m_i.bse["language_c"]; p2i = m_i.pvalues["language_c"]
            B3i = m_i.params["cxl"];        SE3i = m_i.bse["cxl"];        p3i = m_i.pvalues["cxl"]
            ll3, ul3 = m_i.conf_int().loc["cxl"]

            int_rows.append({
                "variable": spec["name"], "group": grp_name, "year": year,
                "N": int(m_i.nobs), "B0": B0i,
                "B1_contact": B1i, "SE1": SE1i, "p1": p1i,
                "B2_language": B2i, "SE2": SE2i, "p2": p2i,
                "B3_cxl": B3i, "SE3": SE3i, "CI3_low": ll3, "CI3_high": ul3, "p3": p3i,
                "R2": m_i.rsquared,
                "R2_additive_for_compare": m_a.rsquared,
                "delta_R2": m_i.rsquared - m_a.rsquared,
            })

df_add = pd.DataFrame(add_rows)
df_int = pd.DataFrame(int_rows)
df_add.to_csv(ROOT / "code" / "_mlr_contact_language_additive.tsv",
              sep="\t", index=False, float_format="%.4f")
df_int.to_csv(ROOT / "code" / "_mlr_contact_language_interaction.tsv",
              sep="\t", index=False, float_format="%.4f")
print(f"Saved TSVs.\n")


# ============================================================================
#                          APA WORD DOC HELPERS
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


# Title
p = doc.add_paragraph()
r = p.add_run("Multiple Linear Regression — Contact + Language as Predictors")
r.bold = True; r.font.size = Pt(16); r.font.name = "Times New Roman"

p = doc.add_paragraph()
r = p.add_run(
    "Two multiple-regression models per cell: an additive specification "
    "(Table 1) and an interactive specification including the Contact × "
    "Language interaction term (Table 2). Each table has 32 rows — eight "
    "outcomes × four group × wave cells. Contact and Language are mean-"
    "centered within each cell. HC3 robust standard errors. APA-7 formatting."
)
r.italic = True; r.font.size = Pt(10); r.font.name = "Times New Roman"
doc.add_paragraph()


# ============================================================================
#                              TABLE 1 — ADDITIVE
# ============================================================================
H_table_number("Table 1")
H_table_title(
    "Additive multiple regression of each outcome on out-group contact and "
    "out-group language ability, per ethnic group × wave "
    "(outcome = B₀ + B₁ × Contact_c + B₂ × Language_c + ε)."
)

header1 = ["Outcome", "Group", "Wave", "n",
           "B₁ Contact (SE)", "β Contact",
           "B₂ Language (SE)", "β Language",
           "R²",
           "Bivariate B₁ Contact", "Δ B₁\n(MLR − biv.)"]
tbl1 = doc.add_table(rows=1, cols=len(header1))
for i, h in enumerate(header1):
    if h == "n":
        set_cell_italics(tbl1.rows[0].cells[i], [("n", True, True)], size=9,
                          align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h == "R²":
        set_cell_italics(tbl1.rows[0].cells[i],
                          [("R", True, True), ("²", True, False)],
                          size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    elif "β" in h:
        before, _, after = h.partition("β")
        set_cell_italics(tbl1.rows[0].cells[i],
                          [(before, True, False), ("β", True, True),
                           (after, True, False)],
                          size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    else:
        set_cell(tbl1.rows[0].cells[i], h, bold=True, size=9,
                  align=WD_ALIGN_PARAGRAPH.CENTER)

# Order rows: by outcome, then Estonian 2020/2023, then Russian 2020/2023
ordered_add = []
for spec in SPECS:
    for grp in ("Estonian", "Russian"):
        for year in (2020, 2023):
            m = [r for r in add_rows if r["variable"] == spec["name"]
                                       and r["group"] == grp and r["year"] == year]
            if m: ordered_add.append(m[0])

row_idx = 1
outcome_starts = {}
for r in ordered_add:
    row = tbl1.add_row().cells
    set_cell(row[0], r["variable"], size=9)
    set_cell(row[1], r["group"], size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[2], str(r["year"]), size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[3], str(r["N"]), size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[4], f"{r['B1_contact']:+.3f} ({r['SE1']:.3f}){stars(r['p1'])}",
              size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[5], f"{r['beta1']:+.3f}{stars(r['p1'])}",
              size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[6], f"{r['B2_language']:+.3f} ({r['SE2']:.3f}){stars(r['p2'])}",
              size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[7], f"{r['beta2']:+.3f}{stars(r['p2'])}",
              size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[8], f"{r['R2']:.3f}", size=9,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[9], f"{r['B1_biv_contact']:+.3f}{stars(r['p1_biv'])}",
              size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[10], f"{r['delta_B1']:+.3f}", size=9,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    if r["variable"] not in outcome_starts:
        outcome_starts[r["variable"]] = row_idx
    row_idx += 1

# Merge outcome column across 4 rows per outcome
for spec in SPECS:
    start = outcome_starts.get(spec["name"])
    if start is None: continue
    end = start + 3
    if end < len(tbl1.rows):
        merge_v(tbl1, list(range(start, end + 1)), 0)
        set_cell(tbl1.rows[start].cells[0], spec["name"], size=9)

remove_table_style(tbl1); apply_apa_borders(tbl1)

table_note([
    ("Note. ", False, True),
    ("Each row is one MLR fit on a single ethnic group × wave cell. ", False, False),
    ("B", False, True), ("₁ Contact = partial slope of contact, controlling "
                          "for language. ", False, False),
    ("B", False, True), ("₂ Language = partial slope of language, controlling "
                          "for contact. ", False, False),
    ("β", False, True), (" = standardized partial slope. ", False, False),
    ("Bivariate ", False, False),
    ("B", False, True), ("₁ Contact = contact slope when language is NOT in "
                          "the model (script 97). Δ ", False, False),
    ("B", False, True), ("₁ shows how much the contact slope shrinks (or "
                          "grows) when language is added. Small Δ → contact "
                          "and language are independent predictors. Large "
                          "negative Δ → language absorbed part of contact's "
                          "bivariate effect. Mean-centered predictors; HC3 "
                          "robust SEs. *** ", False, False),
    ("p", False, True), (" < .001, ** ", False, False),
    ("p", False, True), (" < .01, * ", False, False),
    ("p", False, True), (" < .05, ⁺ ", False, False),
    ("p", False, True), (" < .10.", False, False),
])

doc.add_paragraph()
doc.add_page_break()


# ============================================================================
#                              TABLE 2 — INTERACTION
# ============================================================================
H_table_number("Table 2")
H_table_title(
    "Interactive multiple regression of each outcome on contact, language, "
    "and their interaction, per ethnic group × wave "
    "(outcome = B₀ + B₁ × Contact_c + B₂ × Language_c "
    "+ B₃ × (Contact_c × Language_c) + ε)."
)

header2 = ["Outcome", "Group", "Wave", "n",
           "B₁ Contact (SE)\n(at mean lang.)",
           "B₂ Language (SE)\n(at mean contact)",
           "B₃ C × L (SE)",
           "95% CI on B₃",
           "p (B₃)",
           "R²", "Δ R²\n(int. − add.)"]
tbl2 = doc.add_table(rows=1, cols=len(header2))
for i, h in enumerate(header2):
    if h == "n":
        set_cell_italics(tbl2.rows[0].cells[i], [("n", True, True)], size=9,
                          align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h == "R²":
        set_cell_italics(tbl2.rows[0].cells[i],
                          [("R", True, True), ("²", True, False)],
                          size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h.startswith("Δ R²"):
        set_cell_italics(tbl2.rows[0].cells[i],
                          [("Δ ", True, False), ("R", True, True),
                           ("²", True, False), ("\n(int. − add.)", True, False)],
                          size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    elif h == "p (B₃)":
        set_cell_italics(tbl2.rows[0].cells[i],
                          [("p", True, True), (" (", True, False),
                           ("B", True, True), ("₃)", True, False)],
                          size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    else:
        set_cell(tbl2.rows[0].cells[i], h, bold=True, size=9,
                  align=WD_ALIGN_PARAGRAPH.CENTER)

ordered_int = []
for spec in SPECS:
    for grp in ("Estonian", "Russian"):
        for year in (2020, 2023):
            m = [r for r in int_rows if r["variable"] == spec["name"]
                                       and r["group"] == grp and r["year"] == year]
            if m: ordered_int.append(m[0])

row_idx = 1
outcome_starts2 = {}
for r in ordered_int:
    row = tbl2.add_row().cells
    set_cell(row[0], r["variable"], size=9)
    set_cell(row[1], r["group"], size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[2], str(r["year"]), size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[3], str(r["N"]), size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[4], f"{r['B1_contact']:+.3f} ({r['SE1']:.3f}){stars(r['p1'])}",
              size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[5], f"{r['B2_language']:+.3f} ({r['SE2']:.3f}){stars(r['p2'])}",
              size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[6], f"{r['B3_cxl']:+.4f} ({r['SE3']:.4f}){stars(r['p3'])}",
              size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[7], f"[{r['CI3_low']:+.4f}, {r['CI3_high']:+.4f}]", size=9,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[8], fmt_p(r["p3"]), size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[9], f"{r['R2']:.3f}", size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell(row[10], f"{r['delta_R2']:+.4f}", size=9,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    if r["variable"] not in outcome_starts2:
        outcome_starts2[r["variable"]] = row_idx
    row_idx += 1

for spec in SPECS:
    start = outcome_starts2.get(spec["name"])
    if start is None: continue
    end = start + 3
    if end < len(tbl2.rows):
        merge_v(tbl2, list(range(start, end + 1)), 0)
        set_cell(tbl2.rows[start].cells[0], spec["name"], size=9)

remove_table_style(tbl2); apply_apa_borders(tbl2)

table_note([
    ("Note. ", False, True),
    ("B", False, True), ("₁ and ", False, False),
    ("B", False, True), ("₂ are evaluated at the centering point of the "
                          "respective other predictor: ", False, False),
    ("B", False, True), ("₁ = contact slope at average language; ", False, False),
    ("B", False, True), ("₂ = language slope at average contact. ", False, False),
    ("B", False, True), ("₃ tests whether the contact–outcome slope changes "
                          "as language increases (or equivalently, whether "
                          "the language–outcome slope changes as contact "
                          "increases). A positive ", False, False),
    ("B", False, True), ("₃ on a positive-direction outcome indicates "
                          "language amplifies contact's effect (the "
                          "'high-language people get more out of contact' "
                          "pattern). Δ ", False, False),
    ("R", False, True), ("² shows how much variance the interaction term "
                          "adds beyond the additive model. HC3 robust SEs. "
                          "*** ", False, False),
    ("p", False, True), (" < .001, ** ", False, False),
    ("p", False, True), (" < .01, * ", False, False),
    ("p", False, True), (" < .05, ⁺ ", False, False),
    ("p", False, True), (" < .10.", False, False),
])

out = ROOT / "reports" / "MLR_Contact_Language_APA.docx"
doc.save(out)
print(f"Saved: {out}")
