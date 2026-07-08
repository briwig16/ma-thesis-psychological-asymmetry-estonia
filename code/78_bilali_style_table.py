"""
Bilali-style ANOVA Table 1.
Layout matches Bilali, Çelik & Ok (2014) Table 1 directly:
  - Each variable spans 2 rows (one per wave)
  - Columns: Variable | Wave | Estonian M | Estonian SD | Russian M | Russian SD
             | Ethnicity F, p | Year F, p | Year × Ethnicity F, p
  - Within-group significance is marked by superscripts (a, b) on the M values
    when the within-group year change is significant at p < .05
  - ANOVA F/p values appear once per variable (on the top row)

Output: reports/ANOVA_2x2_Bilali_Style.docx
"""

from pathlib import Path

import pandas as pd
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).parent.parent

an = pd.read_csv(ROOT / "code" / "_anova_2x2_composites.tsv", sep="\t")
es = pd.read_csv(ROOT / "code" / "_effect_sizes.tsv", sep="\t")
es_within = es[es["table"] == "within"].copy()

# Map between ANOVA TSV variable names and effect_sizes TSV variable names
ANOVA_TO_ES = {
    "Superordinate Identity":             "Superordinate Identity",
    "SD: Primary Out-group":              "SD: Primary Out-group",
    "SD: General Out-group":              "SD: General Out-group",
    "Comparative Opportunity Assessment": "Comparative Opportunity Assessment",
    "Belief in Inevitable Conflict":      "Belief in Inevitable Conflict",
    "Minority Inclusion Support":         "Minority Support Inclusion",
}


def within_p(anova_name, group):
    """Return within-group p-value for 2020 vs 2023 from _effect_sizes.tsv."""
    es_name = ANOVA_TO_ES[anova_name]
    row = es_within[(es_within["variable"] == es_name) &
                    (es_within["comparison"] == group)]
    if row.empty:
        return None
    return float(row["p"].iloc[0])


def fmt_p_table(p):
    """Format p exactly like Bilali Table 1: 0.00, 0.001, 0.06, 0.354 — bare decimals.
    Show '0.00' for very small, otherwise three decimals."""
    if p < 0.001: return "0.00"
    if p < 0.01:  return f"{p:.3f}".rstrip("0").rstrip(".") or "0.00"
    return f"{p:.2f}" if p >= 0.1 else f"{p:.3f}"


def superscript_letter(year_label, group_p):
    """Return 'a' / 'b' / '+' / '' for the year label depending on within-group p."""
    if group_p is None:
        return ""
    if group_p < 0.05:
        return "a" if year_label == 2020 else "b"
    if group_p < 0.10:
        return "+"   # marginal — Bilali uses "+" for the PKK-represents-Kurds row
    return ""


# --- Build Word doc -------------------------------------------------------
doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Cm(1.5)
sec.top_margin = sec.bottom_margin = Cm(2.0)
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(10)


def H(text, size=14, color=None):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = True; r.font.size = Pt(size)
    if color: r.font.color.rgb = color


def body(text, italic=False, size=9):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.size = Pt(size); r.italic = italic


def set_cell_text(cell, text, *, bold=False, italic=False, size=9,
                  align=WD_ALIGN_PARAGRAPH.LEFT, runs=None):
    """Write to a cell. If `runs` is provided, write a list of (text, bold,
    italic, superscript) tuples instead of plain text."""
    cell.text = ""
    para = cell.paragraphs[0]
    para.alignment = align
    if runs:
        for r_text, r_bold, r_italic, r_super in runs:
            r = para.add_run(r_text)
            r.font.size = Pt(size)
            r.bold = r_bold
            r.italic = r_italic
            if r_super:
                r.font.superscript = True
    else:
        r = para.add_run(text)
        r.font.size = Pt(size)
        r.bold = bold
        r.italic = italic


def merge_vertical(table, rows, col):
    """Vertically merge a range of cells in one column."""
    cells = [table.rows[r].cells[col] for r in rows]
    merged = cells[0].merge(cells[-1])
    return merged


# Title
H("Table 1", size=11)
body(
    "Means, standard deviations of all outcome measures, and the results of "
    "2 × 2 univariate analyses of variance (Ethnicity × Year).",
    italic=True, size=10,
)
doc.add_paragraph()

# Compute table dimensions
# Columns: Outcome | Wave | Est M | Est SD | Rus M | Rus SD | Eth F | Eth p | Year F | Year p | Eth×Year F | Eth×Year p
ncols = 12
nrows = 1 + 1 + len(an) * 2     # super-header + header + 2 rows per variable

table = doc.add_table(rows=nrows, cols=ncols)
table.style = "Light Grid Accent 1"

# ----- Super-header (row 0) ---------------------------------------------
super_header = [
    ("Outcomes", 0, 1),
    ("Wave", 1, 1),
    ("Estonian", 2, 2),
    ("Russian", 4, 2),
    ("Ethnicity", 6, 2),
    ("Year", 8, 2),
    ("Year × Ethnicity", 10, 2),
]
for label, start_col, span in super_header:
    cells = [table.rows[0].cells[c] for c in range(start_col, start_col + span)]
    if span > 1:
        merged = cells[0]
        for c in cells[1:]:
            merged = merged.merge(c)
        set_cell_text(merged, label, bold=True, size=9,
                      align=WD_ALIGN_PARAGRAPH.CENTER)
    else:
        set_cell_text(cells[0], label, bold=True, size=9,
                      align=WD_ALIGN_PARAGRAPH.CENTER)

# ----- Sub-header (row 1) -----------------------------------------------
sub_header = ["", "", "M", "SD", "M", "SD", "F", "p", "F", "p", "F", "p"]
for i, label in enumerate(sub_header):
    set_cell_text(table.rows[1].cells[i], label,
                  italic=True if label in ("M", "SD", "F", "p") else False,
                  bold=True, size=9,
                  align=WD_ALIGN_PARAGRAPH.CENTER)

# Vertically merge the empty "Outcomes" / "Wave" cells with the super-header
merge_vertical(table, [0, 1], 0)
set_cell_text(table.rows[0].cells[0], "Outcomes", bold=True, size=9,
              align=WD_ALIGN_PARAGRAPH.LEFT)
merge_vertical(table, [0, 1], 1)
set_cell_text(table.rows[0].cells[1], "Wave", bold=True, size=9,
              align=WD_ALIGN_PARAGRAPH.CENTER)

# ----- Data rows --------------------------------------------------------
row_idx = 2
for _, r in an.iterrows():
    varname = r["variable"]
    pE = within_p(varname, "Estonian")
    pR = within_p(varname, "Russian")

    # Merge Outcomes column across the two rows for this variable
    merged_out = merge_vertical(table, [row_idx, row_idx + 1], 0)
    set_cell_text(merged_out, varname, bold=True, size=9)

    # Merge ANOVA columns across the two rows
    for col_start in (6, 8, 10):
        # F columns
        f_val = {6: r["F_ethnicity"], 8: r["F_year"], 10: r["F_interaction"]}[col_start]
        p_val = {6: r["p_ethnicity"], 8: r["p_year"], 10: r["p_interaction"]}[col_start]
        merged_F = merge_vertical(table, [row_idx, row_idx + 1], col_start)
        merged_p = merge_vertical(table, [row_idx, row_idx + 1], col_start + 1)
        set_cell_text(merged_F, f"{f_val:.2f}",
                      size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        set_cell_text(merged_p, fmt_p_table(p_val),
                      size=9, align=WD_ALIGN_PARAGRAPH.CENTER)

    # Year sub-rows
    for offset, year in enumerate([2020, 2023]):
        rr = row_idx + offset
        set_cell_text(table.rows[rr].cells[1], str(year),
                      size=9, align=WD_ALIGN_PARAGRAPH.CENTER)

        # Estonian M with superscript
        m_est = r[f"Est_{year}_M"]; sd_est = r[f"Est_{year}_SD"]
        sup_est = superscript_letter(year, pE)
        set_cell_text(
            table.rows[rr].cells[2], "",
            runs=[(f"{m_est:.2f}", False, False, False)]
                 + ([(sup_est, False, False, True)] if sup_est else []),
            size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        set_cell_text(table.rows[rr].cells[3], f"{sd_est:.2f}",
                      size=9, align=WD_ALIGN_PARAGRAPH.CENTER)

        # Russian M with superscript
        m_rus = r[f"Rus_{year}_M"]; sd_rus = r[f"Rus_{year}_SD"]
        sup_rus = superscript_letter(year, pR)
        set_cell_text(
            table.rows[rr].cells[4], "",
            runs=[(f"{m_rus:.2f}", False, False, False)]
                 + ([(sup_rus, False, False, True)] if sup_rus else []),
            size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        set_cell_text(table.rows[rr].cells[5], f"{sd_rus:.2f}",
                      size=9, align=WD_ALIGN_PARAGRAPH.CENTER)

    row_idx += 2


# Notes
doc.add_paragraph()
body(
    "Notes. The different superscripts (a, b) within a group's column indicate that "
    "the two waves' means differ significantly at p < .05 by Welch's t-test; ⁺ indicates "
    "a marginal difference (p < .10). M = mean composite score on the original Likert "
    "metric (after scale-inversion where applicable, so higher = more of the construct). "
    "SD = standard deviation. F = Type III ANOVA F-statistic. p = exact p-value. "
    "Cell Ns: Estonian 2020 ≈ 700, Estonian 2023 ≈ 870, Russian 2020 ≈ 600, "
    "Russian 2023 ≈ 520 (vary slightly by composite due to item-level missingness; "
    "see _anova_2x2_composites.tsv for exact cell Ns per composite).",
    italic=True, size=8,
)

body(
    "Caveats. SD: Primary Out-group: items differ across groups (Estonians rate "
    "Russian-speakers Q57/58/59_1; Russians rate Estonian-speakers Q57/58/59_2). The "
    "ethnicity main effect and interaction are on a mixed metric. SD: General Out-group: "
    "items differ across waves (3 items in 2020, 6 items in 2023). Year main effect "
    "and interaction confound year with item-set change.",
    italic=True, size=8,
)


# =============================================================================
#                                TABLE 2 — Simple-effect Cohen's d
# =============================================================================
doc.add_paragraph()
doc.add_paragraph()

H("Table 2", size=11)
body(
    "Simple-effect Cohen's d with 95% confidence intervals decomposing the 2 × 2 "
    "design. Between-group comparisons (Estonian vs. Russian) within each wave and "
    "within-group comparisons (2020 vs. 2023) within each group. Significant Year × "
    "Ethnicity interactions in Table 1 are decomposed by reading the within-group "
    "columns below.",
    italic=True, size=10,
)
doc.add_paragraph()

# Columns: Outcome | Between 2020 d [CI] | Between 2023 d [CI] | Within Est d [CI] | Within Rus d [CI]
header2 = [
    "Outcomes",
    "Between-group 2020\nEstonian − Russian",
    "Between-group 2023\nEstonian − Russian",
    "Within Estonian\n2023 − 2020",
    "Within Russian\n2023 − 2020",
]
table2 = doc.add_table(rows=1, cols=len(header2))
table2.style = "Light Grid Accent 1"
for i, h in enumerate(header2):
    set_cell_text(table2.rows[0].cells[i], h, bold=True, size=9,
                  align=WD_ALIGN_PARAGRAPH.CENTER)


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "ns"


def fmt_d_ci_p(d, ll, ul, p):
    """Format a single Cohen's d cell with CI and significance stars."""
    return f"{d:+.3f}{stars(p)}\n[{ll:+.3f}, {ul:+.3f}]"


# Lookup function for between-group d's
es_between = es[es["table"] == "between"].copy()


def d_lookup(table_type, variable_es, comparison):
    sub = (es_between if table_type == "between" else es_within)
    row = sub[(sub["variable"] == variable_es) & (sub["comparison"] == comparison)]
    if row.empty:
        return None, None, None, None
    r = row.iloc[0]
    return float(r["d"]), float(r["CI_low"]), float(r["CI_high"]), float(r["p"])


for _, r in an.iterrows():
    varname = r["variable"]
    es_name = ANOVA_TO_ES[varname]

    row_cells = table2.add_row().cells
    set_cell_text(row_cells[0], varname, bold=True, size=9)

    # Between 2020
    d, ll, ul, p = d_lookup("between", es_name, "2020")
    set_cell_text(row_cells[1], fmt_d_ci_p(d, ll, ul, p),
                  size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
    # Between 2023
    d, ll, ul, p = d_lookup("between", es_name, "2023")
    set_cell_text(row_cells[2], fmt_d_ci_p(d, ll, ul, p),
                  size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
    # Within Estonian
    d, ll, ul, p = d_lookup("within", es_name, "Estonian")
    set_cell_text(row_cells[3], fmt_d_ci_p(d, ll, ul, p),
                  size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
    # Within Russian
    d, ll, ul, p = d_lookup("within", es_name, "Russian")
    set_cell_text(row_cells[4], fmt_d_ci_p(d, ll, ul, p),
                  size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)


# Notes for Table 2
doc.add_paragraph()
body(
    "Notes. d = Cohen's d using the root-mean-square SD denominator: "
    "d = (M₁ − M₂) / √[(SD₁² + SD₂²) / 2]. 95% CIs use the asymptotic standard "
    "error: SE(d) = √[(n₁ + n₂) / (n₁n₂) + d² / (2(n₁ + n₂ − 2))]. p-values from "
    "Welch's t-tests; significance: *** p < .001, ** p < .01, * p < .05, "
    "ns = not significant. Between-group columns: positive d means Estonians > "
    "Russians on the composite (after any scale-inversion noted in Table 1). "
    "Within-group columns: positive d means 2023 > 2020 within that group.",
    italic=True, size=8,
)

body(
    "How to read Tables 1 and 2 together. Table 1 reports the omnibus 2 × 2 ANOVA: "
    "main effect of ethnicity (averaged across years), main effect of year (averaged "
    "across groups), and the Year × Ethnicity interaction (whether the gap changed). "
    "Table 2 decomposes each significant interaction into its constituent simple "
    "effects: which group changed, in which direction, by how much. Interactions "
    "flagged as significant in Table 1 should be interpreted by reading the two "
    "within-group columns of Table 2 for that variable. If those two within-group "
    "d's have different signs or substantially different magnitudes, the interaction "
    "describes asymmetric divergence between groups.",
    italic=True, size=8,
)


# =============================================================================
#                                TABLE 3 — Levene's variance comparisons
# =============================================================================
doc.add_paragraph()
doc.add_paragraph()

H("Table 3", size=11)
body(
    "Levene's tests of variance homogeneity (Brown–Forsythe / median-centered "
    "variant) comparing within-group response variance across waves. While the "
    "ANOVA in Table 1 tests whether MEAN scores differ, Levene's tests whether "
    "the SPREAD of scores within a group changed from 2020 to 2023 — i.e., "
    "whether the community became internally more heterogeneous (polarization) "
    "or more homogeneous (convergence). Reported separately per group, parallel "
    "to Bilali, Çelik & Ok (2014, p. 7).",
    italic=True, size=10,
)
doc.add_paragraph()

header3 = ["Outcomes",
           "Estonian Levene\nF, p,  var(2020) → var(2023)",
           "Russian Levene\nF, p,  var(2020) → var(2023)"]
table3 = doc.add_table(rows=1, cols=len(header3))
table3.style = "Light Grid Accent 1"
for i, h in enumerate(header3):
    set_cell_text(table3.rows[0].cells[i], h, bold=True, size=9,
                  align=WD_ALIGN_PARAGRAPH.CENTER)


def fmt_lev(F, p, v20, v23):
    arrow = "↑" if v23 > v20 else "↓"
    return f"F = {F:.2f}, p = {fmt_p_table(p)}    {v20:.3f} → {v23:.3f} {arrow}"


for _, r in an.iterrows():
    row = table3.add_row().cells
    set_cell_text(row[0], r["variable"], bold=True, size=9)
    set_cell_text(row[1],
                  fmt_lev(r["Levene_Est_F"], r["Levene_Est_p"],
                          r["Levene_Est_var_2020"], r["Levene_Est_var_2023"]),
                  size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_cell_text(row[2],
                  fmt_lev(r["Levene_Rus_F"], r["Levene_Rus_p"],
                          r["Levene_Rus_var_2020"], r["Levene_Rus_var_2023"]),
                  size=9, align=WD_ALIGN_PARAGRAPH.CENTER)


doc.add_paragraph()
body(
    "Note. Levene's tests use the median-centered (Brown–Forsythe) version, which is "
    "more robust to non-normality than the mean-centered original. var(2020) → "
    "var(2023) shows the within-group variance at each wave; ↑ = increased dispersion "
    "(community fragmenting on this attitude); ↓ = decreased dispersion (community "
    "converging). p < .05 indicates a statistically reliable change in within-group "
    "variance between waves. Significant variance increases on Superordinate Identity "
    "(Russian), Belief in Inevitable Conflict (Estonian), SD: Primary (Estonian), "
    "and Minority Inclusion Support (Estonian) are the documented §25 / §28 / §33 "
    "polarization findings.",
    italic=True, size=8,
)

body(
    "How Tables 1, 2, and 3 work together. Table 1 tests whether group means differ. "
    "Table 2 decomposes those mean differences into simple-effect Cohen's d. Table 3 "
    "tests whether the within-group spread of responses changed — a substantively "
    "distinct finding from any mean comparison. A composite can show ns mean change "
    "with significant variance change (e.g., the §29 / §33 framing: \"the community "
    "didn't move on average, but it polarized\"); conversely, a composite can show "
    "large mean change with stable variance (uniform shift, no polarization). The "
    "three tables together cover the four possible mean × variance combinations.",
    italic=True, size=8,
)

out_path = ROOT / "reports" / "ANOVA_2x2_Bilali_Style.docx"
doc.save(out_path)
print(f"Saved: {out_path}")
