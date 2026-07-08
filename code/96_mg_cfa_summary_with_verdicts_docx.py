"""
Build Word document: multi-group CFA fit indices + Δχ²/Δdf/Δp/ΔCFI/ΔRMSEA
+ per-cell PC1 variance + invariance verdict (HOLDS / PARTIAL / FAILS).

Verdict rubric (Cheung & Rensvold 2002; Chen 2007):
  Metric  (configural → metric):
    HOLDS  if ΔCFI ≥ -0.010 AND ΔRMSEA ≤ +0.015
    FAILS  otherwise
  Scalar  (metric → scalar):
    HOLDS  if ΔCFI ≥ -0.010 AND ΔRMSEA ≤ +0.015
    PARTIAL if initial scalar fails AND iterative intercept-freeing recovers
            ΔCFI ≥ -0.010 AND ΔRMSEA ≤ +0.015 within k-2 freed intercepts
            (between-group: code/86; within-group: code/95)
    FAILS  if partial-invariance procedure does not reach thresholds

Reads:
  code/_latent_means_fit.tsv                       (between-group MG-CFA)
  code/_within_group_mg_cfa.tsv                    (within-group MG-CFA)
  code/_latent_means_alpha.tsv                     (per-cell N and α)
  code/_per_cell_pc1.tsv                           (per-cell PC1 % variance)
  code/_partial_invariance_summary.tsv             (between-group partial)
  code/_partial_invariance_within_summary.tsv      (within-group partial)

Output: reports/MG_CFA_Fit_PCA_with_Verdicts.docx
"""

from pathlib import Path
import pandas as pd
from docx import Document
from docx.shared import Pt, Inches, RGBColor

ROOT = Path("/Users/brianwiggins/Desktop/Claude Code/EIM2")
FIT     = pd.read_csv(ROOT / "code" / "_latent_means_fit.tsv",                  sep="\t")
WIN     = pd.read_csv(ROOT / "code" / "_within_group_mg_cfa.tsv",               sep="\t")
ALPHA   = pd.read_csv(ROOT / "code" / "_latent_means_alpha.tsv",                sep="\t")
PCA     = pd.read_csv(ROOT / "code" / "_per_cell_pc1.tsv",                      sep="\t")
PI_BTW  = pd.read_csv(ROOT / "code" / "_partial_invariance_summary.tsv",        sep="\t")
PI_WIN  = pd.read_csv(ROOT / "code" / "_partial_invariance_within_summary.tsv", sep="\t")

OUT = ROOT / "reports" / "MG_CFA_Fit_PCA_with_Verdicts.docx"

COMPOSITES = [
    "Superordinate Identity",
    "SD: Primary Out-group",
    "SD: General Out-group",
    "Comparative Opportunity Assessment",
    "Belief in Inevitable Conflict",
    "Minority Support Inclusion",
    "Contact: Estonian Speakers",
    "Contact: Russian Speakers",
]

ITEMS_2023 = {
    "Superordinate Identity":            "Q67_2, Q67_4 (rev), Q67_5",
    "SD: Primary Out-group":             "Q57_1/2, Q58_1/2, Q59_1/2 (group-specific referent)",
    "SD: General Out-group":             "Q57_4, Q57_5, Q58_4, Q58_5, Q59_4, Q59_5",
    "Comparative Opportunity Assessment": "Q44_1 – Q44_12",
    "Belief in Inevitable Conflict":     "Q63_1 (rev), Q63_2 (rev), Q63_3, Q63_4",
    "Minority Support Inclusion":        "Q68_1, Q68_2, Q68_3",
    "Contact: Estonian Speakers":        "Q51_1 – Q51_6",
    "Contact: Russian Speakers":         "Q52_1 – Q52_6",
}
ITEMS_2020 = {
    "Superordinate Identity":            "K6X5_2, K6X5_3 (rev), K6X5_4",
    "SD: Primary Out-group":             "K4X7_1/2, K4X8_1/2, K4X9_1/2 (group-specific referent)",
    "SD: General Out-group":             "K4X7_3, K4X8_3, K4X9_3",
    "Comparative Opportunity Assessment": "K3X1_1 – K3X1_12",
    "Belief in Inevitable Conflict":     "K6X1_1 (rev), K6X1_2 (rev), K6X1_3, K6X1_4",
    "Minority Support Inclusion":        "K6X6_1, K6X6_2, K6X6_3",
    "Contact: Estonian Speakers":        "K4X1_1 – K4X1_6",
    "Contact: Russian Speakers":         "K4X2_1 – K4X2_6",
}

CFI_TH   = -0.010
RMSEA_TH =  0.015


def passes(d_cfi, d_rmsea):
    if pd.isna(d_cfi) or pd.isna(d_rmsea):
        return False
    return (d_cfi >= CFI_TH) and (d_rmsea <= RMSEA_TH)


def fmt(x, d=3):
    if pd.isna(x) or x == "":
        return "—"
    try:
        return f"{float(x):.{d}f}"
    except (TypeError, ValueError):
        return str(x)


def fmt_signed(x, d=3):
    if pd.isna(x) or x == "":
        return "—"
    try:
        v = float(x)
    except (TypeError, ValueError):
        return str(x)
    return f"{v:+.{d}f}"


def fmt_p(x):
    if pd.isna(x) or x == "":
        return "—"
    try:
        v = float(x)
    except (TypeError, ValueError):
        return str(x)
    return "<.001" if v < 0.001 else f"{v:.3f}"


def fmt_int(x):
    if pd.isna(x):
        return "—"
    try:
        return str(int(float(x)))
    except (TypeError, ValueError):
        return str(x)


def metric_verdict(d_cfi, d_rmsea):
    if pd.isna(d_cfi) and pd.isna(d_rmsea):
        return "—"
    return "HOLDS" if passes(d_cfi, d_rmsea) else "FAILS"


def scalar_verdict(d_cfi, d_rmsea, partial_row):
    """partial_row is one row from the partial-invariance summary, or None."""
    if pd.isna(d_cfi) and pd.isna(d_rmsea):
        return "—"
    if passes(d_cfi, d_rmsea):
        return "HOLDS"
    if partial_row is None or len(partial_row) == 0:
        return "FAILS"
    pr = partial_row.iloc[0] if hasattr(partial_row, "iloc") else partial_row
    if bool(pr["final_passes"]):
        n_freed = int(pr["n_freed_intercepts"])
        return f"PARTIAL ({n_freed} intercept{'s' if n_freed != 1 else ''} freed)"
    return "FAILS"


# Document setup
doc = Document()
section = doc.sections[0]
section.left_margin = Inches(0.5)
section.right_margin = Inches(0.5)
section.top_margin = Inches(0.6)
section.bottom_margin = Inches(0.6)
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(10)


def add_table(headers, rows, verdict_col=None):
    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.style = "Light Grid Accent 1"
    for j, h in enumerate(headers):
        c = tbl.rows[0].cells[j]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(8)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = tbl.rows[i + 1].cells[j]
            c.text = ""
            r = c.paragraphs[0].add_run(str(val))
            r.font.size = Pt(8)
            if verdict_col is not None and j == verdict_col:
                r.bold = True
                v = str(val)
                if v.startswith("HOLDS"):
                    r.font.color.rgb = RGBColor(0x16, 0x80, 0x3D)   # green
                elif v.startswith("PARTIAL"):
                    r.font.color.rgb = RGBColor(0xC2, 0x6B, 0x00)   # amber
                elif v.startswith("FAILS"):
                    r.font.color.rgb = RGBColor(0xB1, 0x1A, 0x1A)   # red
    return tbl


# -----------------------------------------------------------------------------
# Title and intro
# -----------------------------------------------------------------------------
doc.add_heading("Multi-Group CFA: Fit, Invariance Δ, PC1, and Verdicts", level=0)

p = doc.add_paragraph()
p.add_run(
    "Per-composite multi-group confirmatory factor analysis at three invariance levels "
    "(configural, metric, scalar). Two grouping structures are reported:"
).font.size = Pt(10)

p = doc.add_paragraph()
p.add_run("    • Between-group: Estonian vs. Russian, fit separately within each year.\n").font.size = Pt(10)
p.add_run("    • Within-group: 2020 vs. 2023, fit separately within each ethnic group.").font.size = Pt(10)

p = doc.add_paragraph()
p.add_run(
    "Estimator: MLR. Missing data: FIML. Fit indices: scaled χ², df, p, CFI, TLI, "
    "RMSEA, SRMR. Δχ² and Δp computed via Satorra-Bentler scaled difference test "
    "(lavTestLRT, method = satorra.bentler.2001); ΔCFI and ΔRMSEA are simple "
    "level-vs-previous-level differences."
).font.size = Pt(10)

p = doc.add_paragraph()
r = p.add_run("Verdict rubric: ")
r.bold = True
r.font.size = Pt(10)
p.add_run(
    "Metric and scalar invariance are flagged HOLDS when ΔCFI ≥ -0.010 and "
    "ΔRMSEA ≤ +0.015 (Cheung & Rensvold 2002; Chen 2007). For scalar invariance, "
    "if the initial test fails, an iterative partial-invariance procedure frees "
    "intercepts one at a time (largest χ² drop first) until the thresholds are "
    "met or only k-2 intercepts remain constrained. PARTIAL means thresholds "
    "are met after freeing some intercepts; FAILS means thresholds remain unmet "
    "even after partial-invariance attempts. Partial-invariance procedure: "
    "code/86_partial_invariance_all.R (between-group), "
    "code/95_partial_invariance_within.R (within-group)."
).font.size = Pt(10)

p = doc.add_paragraph()
p.add_run(
    "SD: Primary Out-group uses group-specific items (Estonians rate Russian-speakers; "
    "Russians rate Estonian-speakers). SD: General Out-group has different item sets "
    "in 2020 (3 items) and 2023 (6 items); between-group MG-CFA fit per year, "
    "within-group MG-CFA not defined."
).font.size = Pt(10)


def render_fit_table(df_in, partial_lookup):
    """partial_lookup: function(level) -> partial row or None."""
    rows = []
    for _, row in df_in.iterrows():
        level = row["level"]
        if level == "configural":
            v = "—"
        elif level == "metric":
            v = metric_verdict(row["d_cfi"], row["d_rmsea"])
        else:  # scalar
            v = scalar_verdict(row["d_cfi"], row["d_rmsea"], partial_lookup())
        rows.append([
            level,
            fmt(row["chisq"], 3), fmt_int(row["df"]), fmt_p(row["p"]),
            fmt(row["cfi"], 4), fmt(row["tli"], 4),
            fmt(row["rmsea"], 4), fmt(row["srmr"], 4),
            fmt(row["d_chisq"], 3), fmt_int(row["d_df"]), fmt_p(row["d_p"]),
            fmt_signed(row["d_cfi"], 4), fmt_signed(row["d_rmsea"], 4),
            v,
        ])
    add_table(
        ["Level", "χ²", "df", "p", "CFI", "TLI", "RMSEA", "SRMR",
         "Δχ²", "Δdf", "Δp", "ΔCFI", "ΔRMSEA", "Verdict"],
        rows, verdict_col=13,
    )


# -----------------------------------------------------------------------------
# Per-composite sections
# -----------------------------------------------------------------------------
for comp in COMPOSITES:
    doc.add_heading(comp, level=1)

    p = doc.add_paragraph()
    r = p.add_run("Items (2023): "); r.bold = True; r.font.size = Pt(9)
    p.add_run(ITEMS_2023[comp]).font.size = Pt(9)
    p = doc.add_paragraph()
    r = p.add_run("Items (2020): "); r.bold = True; r.font.size = Pt(9)
    p.add_run(ITEMS_2020[comp]).font.size = Pt(9)

    # Per-cell descriptive table
    doc.add_heading("Per-cell sample, reliability, PC1 variance", level=3)
    rows = []
    for year in (2020, 2023):
        for group in ("Estonian", "Russian"):
            a = ALPHA[(ALPHA.composite == comp) & (ALPHA.year == year) & (ALPHA.group == group)]
            pca = PCA[(PCA.composite == comp) & (PCA.year == year) & (PCA.group == group)]
            n_items = a["n_items"].iloc[0] if len(a) else "—"
            alpha = a["alpha"].iloc[0] if len(a) else None
            n_alpha = a["n"].iloc[0] if len(a) else None
            n_pca = pca["n"].iloc[0] if len(pca) else None
            eig = pca["pc1_eigenvalue"].iloc[0] if len(pca) else None
            pct = pca["pc1_pct_variance"].iloc[0] if len(pca) else None
            rows.append([
                year, group, fmt_int(n_items),
                fmt_int(n_alpha), fmt(alpha, 3),
                fmt_int(n_pca), fmt(eig, 3), fmt(pct, 2),
            ])
    add_table(
        ["Year", "Group", "k items", "N (α)", "Cronbach α",
         "N (PCA)", "PC1 eigenvalue", "PC1 % variance"],
        rows,
    )

    # Between-group, 2020
    doc.add_heading("Between-group MG-CFA — 2020 (Estonian vs Russian)", level=3)
    sub = (FIT[(FIT.composite == comp) & (FIT.year == 2020)]
           .set_index("level").reindex(["configural", "metric", "scalar"]).dropna(how="all").reset_index())
    render_fit_table(
        sub,
        lambda: PI_BTW[(PI_BTW.composite == comp) & (PI_BTW.year == 2020)],
    )

    # Between-group, 2023
    doc.add_heading("Between-group MG-CFA — 2023 (Estonian vs Russian)", level=3)
    sub = (FIT[(FIT.composite == comp) & (FIT.year == 2023)]
           .set_index("level").reindex(["configural", "metric", "scalar"]).dropna(how="all").reset_index())
    render_fit_table(
        sub,
        lambda: PI_BTW[(PI_BTW.composite == comp) & (PI_BTW.year == 2023)],
    )

    # Within-group
    win_comp = WIN[WIN.composite == comp]
    if len(win_comp) > 0:
        for grp in ("Estonian", "Russian"):
            doc.add_heading(f"Within-group MG-CFA — {grp} (2020 vs 2023)", level=3)
            sub = (win_comp[win_comp.group == grp]
                   .set_index("level").reindex(["configural", "metric", "scalar"]).dropna(how="all").reset_index())
            render_fit_table(
                sub,
                lambda g=grp: PI_WIN[(PI_WIN.composite == comp) & (PI_WIN.group == g)],
            )
    else:
        p = doc.add_paragraph()
        r = p.add_run("Within-group MG-CFA not defined for this composite "
                      "(item set differs across waves).")
        r.italic = True
        r.font.size = Pt(9)

    doc.add_paragraph()

# Footer
doc.add_paragraph()
foot = doc.add_paragraph()
r = foot.add_run(
    "Sources: code/_latent_means_fit.tsv, code/_within_group_mg_cfa.tsv, "
    "code/_latent_means_alpha.tsv, code/_per_cell_pc1.tsv, "
    "code/_partial_invariance_summary.tsv, code/_partial_invariance_within_summary.tsv. "
    "Generated by code/96_mg_cfa_summary_with_verdicts_docx.py."
)
r.italic = True
r.font.size = Pt(8)

doc.save(OUT)
print(f"Wrote: {OUT.relative_to(ROOT)}")
