"""
APA-7-formatted version of the 2 × 2 factorial ANOVA tables previously
produced as `ANOVA_2x2_Bilali_Style.docx`.

Three tables, all in APA style:
  Table 1. Cell means, SDs, and 2 × 2 ANOVA F-tests (Ethnicity × Year)
  Table 2. Simple-effect Cohen's d decomposing the 2 × 2 design
  Table 3. Levene's tests of variance homogeneity across waves, per group

APA formatting conventions applied throughout:
  - Times New Roman font
  - Table number bold + table title italic on separate lines
  - Horizontal rules only (heavy top, thin under header, heavy bottom)
  - No vertical lines, no shading, no internal horizontal lines
  - Italicized statistical symbols (M, SD, n, F, p, η², d)
  - Notes below tables starting with italic "Note."

Output: reports/ANOVA_2x2_APA.docx
"""

from pathlib import Path

import pandas as pd
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).parent.parent

an = pd.read_csv(ROOT / "code" / "_anova_2x2_composites.tsv", sep="\t")
es = pd.read_csv(ROOT / "code" / "_effect_sizes.tsv", sep="\t")
es_within  = es[es["table"] == "within"].copy()
es_between = es[es["table"] == "between"].copy()

# Mapping for effect-sizes TSV names
ANOVA_TO_ES = {
    "Superordinate Identity":             "Superordinate Identity",
    "SD: Primary Out-group":              "SD: Primary Out-group",
    "SD: General Out-group":              "SD: General Out-group",
    "Comparative Opportunity Assessment": "Comparative Opportunity Assessment",
    "Belief in Inevitable Conflict":      "Belief in Inevitable Conflict",
    "Minority Inclusion Support":         "Minority Support Inclusion",
}


def stars(p):
    if pd.isna(p): return ""
    if p < .001: return "***"
    if p < .01:  return "**"
    if p < .05:  return "*"
    if p < .10:  return "⁺"
    return ""


def fmt_p_apa(p):
    """APA-7 p-value: drop leading zero, two decimals, '< .001' for very small."""
    if pd.isna(p): return "—"
    if p < .001:   return "< .001"
    formatted = f"{p:.3f}".lstrip("0")
    return formatted


def fmt_F(F, df1=1, df2=None):
    if pd.isna(F): return "—"
    return f"{F:.2f}"


def fmt_eta(eta):
    if pd.isna(eta): return "—"
    return f"{eta:.3f}".lstrip("0")


def within_p(varname, group):
    row = es_within[(es_within["variable"] == ANOVA_TO_ES[varname]) &
                    (es_within["comparison"] == group)]
    return float(row["p"].iloc[0]) if len(row) else None


def superscript(year, group_p):
    if group_p is None: return ""
    if group_p < .05: return "a" if year == 2020 else "b"
    if group_p < .10: return "⁺"
    return ""


# ============================================================================
#                          APA TABLE STYLING HELPERS
# ============================================================================
def _set_cell_border(cell, **kwargs):
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


def apply_apa_borders(table, header_rows=1):
    """APA-style horizontal rules. header_rows = number of header rows
    (top set gets the heavy rule above, thin rule below the bottom-most header)."""
    n_rows = len(table.rows)
    for r_idx, row in enumerate(table.rows):
        for cell in row.cells:
            top = bottom = None
            if r_idx == 0:
                top = {"sz": 12, "val": "single", "color": "000000"}
            if r_idx == header_rows - 1:
                bottom = {"sz": 6, "val": "single", "color": "000000"}
            if r_idx == n_rows - 1:
                bottom = {"sz": 12, "val": "single", "color": "000000"}
            _set_cell_border(cell,
                              top=top, bottom=bottom, left=None, right=None)


def remove_table_style(table):
    tblPr = table._tbl.find(qn("w:tblPr"))
    tblStyle = tblPr.find(qn("w:tblStyle")) if tblPr is not None else None
    if tblStyle is not None:
        tblPr.remove(tblStyle)
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
style.font.name = "Times New Roman"
style.font.size = Pt(11)


def set_cell_plain(cell, text, *, bold=False, italic=False, size=10,
                    align=WD_ALIGN_PARAGRAPH.LEFT, vcenter=False):
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


def set_cell_italics(cell, segments, *, size=10,
                      align=WD_ALIGN_PARAGRAPH.LEFT):
    """segments = list of (text, bold, italic, superscript) tuples."""
    cell.text = ""
    para = cell.paragraphs[0]
    para.alignment = align
    for tup in segments:
        if len(tup) == 3:
            text, bold, italic = tup
            superscript_flag = False
        else:
            text, bold, italic, superscript_flag = tup
        r = para.add_run(text)
        r.font.size = Pt(size)
        r.font.name = "Times New Roman"
        r.bold = bold
        r.italic = italic
        if superscript_flag:
            r.font.superscript = True


def merge_v(table, rows, col):
    cells = [table.rows[r].cells[col] for r in rows]
    merged = cells[0]
    for c in cells[1:]:
        merged = merged.merge(c)
    return merged


def merge_h(table, row, cols):
    cells = [table.rows[row].cells[c] for c in cols]
    merged = cells[0]
    for c in cells[1:]:
        merged = merged.merge(c)
    return merged


def H_table_number(text):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = True; r.font.size = Pt(11)
    r.font.name = "Times New Roman"


def H_table_title(text):
    p = doc.add_paragraph()
    r = p.add_run(text); r.italic = True; r.font.size = Pt(11)
    r.font.name = "Times New Roman"


def table_note(segments, size=9):
    p = doc.add_paragraph()
    for text, bold, italic in segments:
        r = p.add_run(text)
        r.font.size = Pt(size)
        r.font.name = "Times New Roman"
        r.bold = bold
        r.italic = italic


# Title page material
p = doc.add_paragraph()
r = p.add_run("2 × 2 Factorial ANOVA Results — Ethnicity × Year")
r.bold = True; r.font.size = Pt(16); r.font.name = "Times New Roman"

p = doc.add_paragraph()
r = p.add_run(
    "ANOVA tables for the six non-contact composite outcomes, with associated "
    "simple-effect Cohen's d decomposition (Table 2) and Levene's tests of "
    "variance homogeneity across waves (Table 3). All tables follow APA-7 "
    "formatting: bold table number, italic title, minimal horizontal rules, "
    "italicized statistical symbols."
)
r.italic = True; r.font.size = Pt(10); r.font.name = "Times New Roman"

doc.add_paragraph()


# ============================================================================
#                              TABLE 1 — ANOVA
# ============================================================================
H_table_number("Table 1")
H_table_title(
    "Means and standard deviations of all outcome measures and the results "
    "of 2 × 2 univariate analyses of variance (Ethnicity × Year)."
)

# Layout: Outcome | Wave | Est M | Est SD | Rus M | Rus SD | Eth F | Eth p | Year F | Year p | Eth×Year F | Eth×Year p
ncols = 12
nrows = 2 + len(an) * 2     # 2 header rows + 2 rows per variable

tbl1 = doc.add_table(rows=nrows, cols=ncols)

# Super-header (row 0)
super_header = [
    ("Outcomes", 0, 1),
    ("Wave",     1, 1),
    ("Estonian", 2, 2),
    ("Russian",  4, 2),
    ("Ethnicity",       6, 2),
    ("Year",            8, 2),
    ("Ethnicity × Year", 10, 2),
]
for label, start_col, span in super_header:
    if span > 1:
        merged = merge_h(tbl1, 0, range(start_col, start_col + span))
        set_cell_plain(merged, label, bold=True, size=10,
                       align=WD_ALIGN_PARAGRAPH.CENTER)
    else:
        set_cell_plain(tbl1.rows[0].cells[start_col], label, bold=True,
                       size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

# Sub-header (row 1)
sub_header = ["", "", "M", "SD", "M", "SD", "F", "p", "F", "p", "F", "p"]
for i, label in enumerate(sub_header):
    if label in ("M", "SD", "F", "p"):
        set_cell_italics(tbl1.rows[1].cells[i],
                         [(label, True, True)],
                         size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    elif label:
        set_cell_plain(tbl1.rows[1].cells[i], label, bold=True, size=10,
                       align=WD_ALIGN_PARAGRAPH.CENTER)

# Merge Outcomes / Wave columns across the two header rows
merge_v(tbl1, [0, 1], 0)
set_cell_plain(tbl1.rows[0].cells[0], "Outcomes", bold=True, size=10,
                align=WD_ALIGN_PARAGRAPH.LEFT)
merge_v(tbl1, [0, 1], 1)
set_cell_plain(tbl1.rows[0].cells[1], "Wave", bold=True, size=10,
                align=WD_ALIGN_PARAGRAPH.CENTER)

# Data rows
row_idx = 2
for _, r in an.iterrows():
    varname = r["variable"]
    pE = within_p(varname, "Estonian")
    pR = within_p(varname, "Russian")

    # Merge Outcomes column across two rows
    merge_v(tbl1, [row_idx, row_idx + 1], 0)
    set_cell_plain(tbl1.rows[row_idx].cells[0], varname, bold=False, size=10)

    # Merge ANOVA cols across two rows
    for col_start in (6, 8, 10):
        F_val = {6: r["F_ethnicity"], 8: r["F_year"], 10: r["F_interaction"]}[col_start]
        p_val = {6: r["p_ethnicity"], 8: r["p_year"], 10: r["p_interaction"]}[col_start]
        eta_val = {6: r["eta2p_ethnicity"], 8: r["eta2p_year"],
                   10: r["eta2p_interaction"]}[col_start]

        merge_v(tbl1, [row_idx, row_idx + 1], col_start)
        merge_v(tbl1, [row_idx, row_idx + 1], col_start + 1)
        # F + p
        set_cell_plain(tbl1.rows[row_idx].cells[col_start], fmt_F(F_val),
                       size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        # p column shows both p and η²p
        set_cell_plain(tbl1.rows[row_idx].cells[col_start + 1],
                       f"{fmt_p_apa(p_val)}\nη²ₚ = {fmt_eta(eta_val)}",
                       size=9, align=WD_ALIGN_PARAGRAPH.CENTER)

    # Year sub-rows
    for offset, year in enumerate([2020, 2023]):
        rr = row_idx + offset
        set_cell_plain(tbl1.rows[rr].cells[1], str(year),
                       size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        # Estonian
        m_est = r[f"Est_{year}_M"]; sd_est = r[f"Est_{year}_SD"]
        sup_est = superscript(year, pE)
        set_cell_italics(
            tbl1.rows[rr].cells[2],
            [(f"{m_est:.2f}", False, False, False)]
            + ([(sup_est, False, False, True)] if sup_est else []),
            size=10, align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        set_cell_plain(tbl1.rows[rr].cells[3], f"{sd_est:.2f}",
                       size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        # Russian
        m_rus = r[f"Rus_{year}_M"]; sd_rus = r[f"Rus_{year}_SD"]
        sup_rus = superscript(year, pR)
        set_cell_italics(
            tbl1.rows[rr].cells[4],
            [(f"{m_rus:.2f}", False, False, False)]
            + ([(sup_rus, False, False, True)] if sup_rus else []),
            size=10, align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        set_cell_plain(tbl1.rows[rr].cells[5], f"{sd_rus:.2f}",
                       size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

    row_idx += 2

remove_table_style(tbl1)
apply_apa_borders(tbl1, header_rows=2)

table_note([
    ("Note. ", False, True),
    ("Different superscripts (a, b) within a group's column indicate that "
     "the two waves' means differ significantly at ", False, False),
    ("p", False, True), (" < .05 by Welch's ", False, False),
    ("t", False, True), ("-test; ⁺ indicates a marginal difference (", False, False),
    ("p", False, True), (" < .10). ", False, False),
    ("M", False, True), (" = mean composite score on the original Likert "
                          "metric (after scale-inversion where applicable, "
                          "so higher = more of the construct). ", False, False),
    ("SD", False, True), (" = standard deviation. ", False, False),
    ("F", False, True), (" = Type III ANOVA ", False, False),
    ("F", False, True), ("-statistic with 1 numerator ", False, False),
    ("df", False, True), (". ", False, False),
    ("p", False, True), (" = exact p-value. η²ₚ = partial eta-squared "
                          "(small ≈ .01, medium ≈ .06, large ≈ .14).", False, False),
])

doc.add_paragraph()
doc.add_page_break()


# ============================================================================
#                       TABLE 2 — SIMPLE-EFFECT COHEN'S d
# ============================================================================
H_table_number("Table 2")
H_table_title(
    "Simple-effect Cohen's d with 95% confidence intervals decomposing the "
    "2 × 2 design into between-group (within wave) and within-group "
    "(across wave) comparisons."
)

header2 = ["Outcomes",
           "Between-group 2020\n(Estonian − Russian)",
           "Between-group 2023\n(Estonian − Russian)",
           "Estonian respondents\n(2023 − 2020)",
           "Russian respondents\n(2023 − 2020)"]
tbl2 = doc.add_table(rows=1, cols=len(header2))
for i, h in enumerate(header2):
    set_cell_plain(tbl2.rows[0].cells[i], h, bold=True, size=10,
                   align=WD_ALIGN_PARAGRAPH.CENTER)


def d_lookup(table_type, variable_es, comparison):
    sub = es_between if table_type == "between" else es_within
    row = sub[(sub["variable"] == variable_es) & (sub["comparison"] == comparison)]
    if row.empty: return None
    r = row.iloc[0]
    return float(r["d"]), float(r["CI_low"]), float(r["CI_high"]), float(r["p"])


def fmt_d(d, ll, ul, p):
    return f"{d:+.3f}{stars(p)}\n[{ll:+.3f}, {ul:+.3f}]"


for _, r in an.iterrows():
    varname = r["variable"]
    es_name = ANOVA_TO_ES[varname]
    row = tbl2.add_row().cells
    set_cell_plain(row[0], varname, size=10)
    for i, comp_key in enumerate(
        [("between", "2020"), ("between", "2023"),
         ("within",  "Estonian"), ("within",  "Russian")], start=1
    ):
        result = d_lookup(comp_key[0], es_name, comp_key[1])
        if result:
            d_val, ll, ul, p_val = result
            set_cell_plain(row[i], fmt_d(d_val, ll, ul, p_val), size=10,
                            align=WD_ALIGN_PARAGRAPH.CENTER)
        else:
            set_cell_plain(row[i], "—", size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

remove_table_style(tbl2)
apply_apa_borders(tbl2)

table_note([
    ("Note. ", False, True),
    ("d", False, True), (" = Cohen's d using the root-mean-square SD "
                          "denominator: ", False, False),
    ("d", False, True), (" = (", False, False),
    ("M", False, True), ("₁ − ", False, False),
    ("M", False, True), ("₂) / √[(", False, False),
    ("SD", False, True), ("₁² + ", False, False),
    ("SD", False, True), ("₂²) / 2]. 95% CIs use the asymptotic standard error "
                           "(Hedges & Olkin, 1985). ", False, False),
    ("p", False, True), (" from Welch's ", False, False),
    ("t", False, True), ("-tests on the underlying composite scores. "
                          "Between-group columns: positive ", False, False),
    ("d", False, True), (" means Estonians scored higher than Russians "
                          "(after any scale-inversion noted in Table 1). "
                          "Within-group columns: positive ", False, False),
    ("d", False, True), (" means 2023 scored higher than 2020 within that "
                          "group. *** ", False, False),
    ("p", False, True), (" < .001, ** ", False, False),
    ("p", False, True), (" < .01, * ", False, False),
    ("p", False, True), (" < .05, ⁺ ", False, False),
    ("p", False, True), (" < .10.", False, False),
])

doc.add_paragraph()
doc.add_page_break()


# ============================================================================
#                       TABLE 3 — LEVENE'S TESTS
# ============================================================================
H_table_number("Table 3")
H_table_title(
    "Levene's tests (Brown–Forsythe variant) of variance homogeneity across "
    "waves, conducted separately within each ethnic group."
)

header3 = ["Outcomes",
           "Estonian respondents\nF, p,  var(2020) → var(2023)",
           "Russian respondents\nF, p,  var(2020) → var(2023)"]
tbl3 = doc.add_table(rows=1, cols=len(header3))
for i, h in enumerate(header3):
    set_cell_plain(tbl3.rows[0].cells[i], h, bold=True, size=10,
                   align=WD_ALIGN_PARAGRAPH.CENTER)


def fmt_lev(F, p, v20, v23):
    arrow = "↑" if v23 > v20 else "↓"
    return f"F = {F:.2f}, p = {fmt_p_apa(p)}{stars(p)}\n{v20:.3f} → {v23:.3f} {arrow}"


for _, r in an.iterrows():
    row = tbl3.add_row().cells
    set_cell_plain(row[0], r["variable"], size=10)
    set_cell_plain(row[1],
                   fmt_lev(r["Levene_Est_F"], r["Levene_Est_p"],
                           r["Levene_Est_var_2020"], r["Levene_Est_var_2023"]),
                   size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell_plain(row[2],
                   fmt_lev(r["Levene_Rus_F"], r["Levene_Rus_p"],
                           r["Levene_Rus_var_2020"], r["Levene_Rus_var_2023"]),
                   size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

remove_table_style(tbl3)
apply_apa_borders(tbl3)

table_note([
    ("Note. ", False, True),
    ("Levene's tests use the median-centered (Brown–Forsythe) variant, "
     "which is more robust to non-normality than the mean-centered original. "
     "var(2020) → var(2023) shows the within-group variance at each wave. "
     "↑ = increased dispersion (community fragmenting on this attitude); "
     "↓ = decreased dispersion (community converging). ", False, False),
    ("p", False, True), (" < .05 indicates a statistically reliable change "
                          "in within-group variance between waves. "
                          "*** ", False, False),
    ("p", False, True), (" < .001, ** ", False, False),
    ("p", False, True), (" < .01, * ", False, False),
    ("p", False, True), (" < .05, ⁺ ", False, False),
    ("p", False, True), (" < .10.", False, False),
])

doc.add_paragraph()


# ============================================================================
#                       CLOSING NOTE — How the tables connect
# ============================================================================
H_table_number("How to read these tables together")
table_note([
    ("Table 1 tests whether ", False, False),
    ("mean", False, True), (" scores differ across the 2 × 2 design (omnibus "
                             "tests of ethnicity, year, and the interaction). "
                             "Significant interactions in Table 1 should be "
                             "decomposed by reading Table 2, which gives the "
                             "Cohen's d for each simple-effect comparison "
                             "(between-group within wave; within-group across "
                             "waves). Table 3 tests whether the ", False, False),
    ("variance", False, True), (" of responses changed across waves within "
                                  "each group — a substantively distinct "
                                  "finding from any mean comparison. A composite "
                                  "can show ns mean change with significant "
                                  "variance change (community polarized "
                                  "without moving on average) or significant "
                                  "mean change with stable variance (uniform "
                                  "shift, no polarization). The three tables "
                                  "together cover the four possible "
                                  "mean × variance combinations.", False, False),
], size=10)

out = ROOT / "reports" / "ANOVA_2x2_APA.docx"
doc.save(out)
print(f"Saved: {out}")
