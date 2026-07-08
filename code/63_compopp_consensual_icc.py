"""
Sidanius & Pratto consensual-ICC analysis applied to Comparative Opportunity
==============================================================================
Tests whether the Comparative Opportunity Assessment composite functions as a
consensual legitimizing myth (high ICC) or a dissensual contested ideology
(low ICC) across Estonian and Russian respondent groups, in 2020 and 2023.

Variance decomposition (Sidanius & Pratto, "The Power of Consensual
Ideology," eqs. 1–5):

  σ²_Total       = σ²_Dissensual + σ²_Consensual + σ²_Error
  σ²_Dissensual  = between-group variance
  σ²_Consensual  = α × within-group variance        (reliable shared)
  σ²_Error       = (1 − α) × within-group variance  (random)

  ICC = 1 − σ²_Dissensual / (σ²_Dissensual + σ²_Consensual)
      = σ²_Consensual / (σ²_Dissensual + σ²_Consensual)

Reading:
  ICC near 1  → most reliable variance is within-group / shared across groups
                → ideology is CONSENSUAL → functions as a legitimizing myth
  ICC near 0  → most reliable variance is between-group
                → ideology is DISSENSUAL → ideological conflict between groups

Implementation notes:
  - Composite-level: Cronbach's α computed pooled across groups
  - Item-level: a "raw ICC" approximation treating all within-group variance
    as consensual (no α adjustment available for single items). This gives an
    upper bound on ICC at the item level.
  - Between-group variance computed via the unbiased estimator
    Σn_g(M_g − M_overall)² / (N − 1).

Output: console table + reports/Comparative_Opportunity_Consensual_ICC.docx
"""

from pathlib import Path
import pandas as pd
import numpy as np
import pyreadstat
from docx import Document
from docx.shared import Pt, Cm, RGBColor

ROOT = Path(__file__).parent.parent

ITEM_LABELS = [
    "Material well-being",
    "Cultural participation",
    "Education",
    "Social / political rights",
    "Entrepreneurship",
    "Career & jobs",
    "Medical care",
    "Housing",
    "Leisure & holidays",
    "Children & youth opportunities",
    "Sports & exercise",
    "State benefits / services",
]


# ---------- Load data -------------------------------------------------------
df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy()

df20, _ = pyreadstat.read_sav(str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"),
                              encoding="latin1")
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy()


def to_num(s, dk=9):
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s != dk).astype(float)


def cronbach_alpha(item_matrix):
    """Cronbach's α on a (N × k) item matrix, listwise-deleted."""
    M = item_matrix.dropna()
    k = M.shape[1]
    item_vars = M.var(axis=0, ddof=1).sum()
    total_var = M.sum(axis=1).var(ddof=1)
    return (k / (k - 1)) * (1 - item_vars / total_var)


def variance_decomposition(scores, group_labels):
    """Decompose total variance into between- and within-group components.

    Uses unbiased estimators:
      var_total   = Var(scores)                  (denominator N − 1)
      var_between = Σ n_g (M_g − M_overall)² / (N − 1)
      var_within  = pooled Σ n_g σ²_g / (N − 1)
    """
    df = pd.DataFrame({"x": scores, "g": group_labels}).dropna()
    N = len(df)
    overall_M = df["x"].mean()
    var_total = df["x"].var(ddof=1)
    grouped = df.groupby("g")["x"]
    n_g = grouped.count()
    M_g = grouped.mean()
    var_g = grouped.var(ddof=1)
    var_between = (n_g * (M_g - overall_M) ** 2).sum() / (N - 1)
    var_within = (n_g * var_g).sum() / (N - 1)
    return {
        "N": int(N),
        "var_total": float(var_total),
        "var_between": float(var_between),
        "var_within": float(var_within),
        "M_overall": float(overall_M),
        "group_means": M_g.to_dict(),
        "group_Ns": n_g.to_dict(),
    }


def sidanius_icc(var_between, var_within, alpha):
    """Sidanius & Pratto's consensual ICC.

    σ²_Dissensual = var_between
    σ²_Consensual = α × var_within
    σ²_Error      = (1 − α) × var_within
    ICC = σ²_Consensual / (σ²_Dissensual + σ²_Consensual)
    """
    var_consensual = alpha * var_within
    var_error = (1 - alpha) * var_within
    denom = var_between + var_consensual
    icc = var_consensual / denom if denom > 0 else float("nan")
    return {
        "var_dissensual": float(var_between),
        "var_consensual": float(var_consensual),
        "var_error":      float(var_error),
        "ICC":            float(icc),
        "alpha_used":     float(alpha),
    }


# ---------- Composite-level analysis ---------------------------------------
def compute_composite(df, items):
    sub = df[items].apply(pd.to_numeric, errors="coerce").where(lambda x: x != 9)
    return sub.mean(axis=1, skipna=True)


def composite_icc(df, items):
    composite = compute_composite(df, items)
    item_matrix = df[items].apply(pd.to_numeric, errors="coerce").where(lambda x: x != 9)
    alpha = cronbach_alpha(item_matrix)
    var_dec = variance_decomposition(composite, df["ethnicity_binary"])
    icc = sidanius_icc(var_dec["var_between"], var_dec["var_within"], alpha)
    return {**var_dec, **icc}


items_2020 = [f"K3X1_{i}" for i in range(1, 13)]
items_2023 = [f"Q44_{i}"  for i in range(1, 13)]

result_2020 = composite_icc(df20, items_2020)
result_2023 = composite_icc(df23, items_2023)


# ---------- Item-level analysis (raw ICC, no α) ----------------------------
def item_icc_raw(s, group_labels):
    """Single-item ICC treating ALL within-group variance as consensual.
    This is an UPPER BOUND because no random-error component is removed.
    """
    s_num = pd.to_numeric(s, errors="coerce").where(lambda x: x != 9)
    var_dec = variance_decomposition(s_num, group_labels)
    if var_dec["var_within"] + var_dec["var_between"] == 0:
        return {**var_dec, "ICC_raw": float("nan")}
    icc = var_dec["var_within"] / (var_dec["var_within"] + var_dec["var_between"])
    return {**var_dec, "ICC_raw": icc}


item_rows = []
for i, label in enumerate(ITEM_LABELS, start=1):
    r20 = item_icc_raw(df20[f"K3X1_{i}"], df20["ethnicity_binary"])
    r23 = item_icc_raw(df23[f"Q44_{i}"],  df23["ethnicity_binary"])
    item_rows.append({
        "idx": i, "label": label,
        "icc20": r20["ICC_raw"], "icc23": r23["ICC_raw"],
        "var_b_20": r20["var_between"], "var_w_20": r20["var_within"],
        "var_b_23": r23["var_between"], "var_w_23": r23["var_within"],
    })


# ---------- Console output --------------------------------------------------
print("=" * 100)
print("SIDANIUS & PRATTO CONSENSUAL-ICC — Comparative Opportunity Assessment")
print("=" * 100)
print()
print("Composite-level results:")
print(f"{'':<28s}  {'2020':>20s}  {'2023':>20s}")
print(f"{'Cronbach α':<28s}  {result_2020['alpha_used']:20.4f}  {result_2023['alpha_used']:20.4f}")
print(f"{'σ²_Total':<28s}  {result_2020['var_total']:20.4f}  {result_2023['var_total']:20.4f}")
print(f"{'σ²_Dissensual (between)':<28s}  {result_2020['var_dissensual']:20.4f}  {result_2023['var_dissensual']:20.4f}")
print(f"{'σ²_Consensual (α·within)':<28s}  {result_2020['var_consensual']:20.4f}  {result_2023['var_consensual']:20.4f}")
print(f"{'σ²_Error ((1−α)·within)':<28s}  {result_2020['var_error']:20.4f}  {result_2023['var_error']:20.4f}")
print(f"{'ICC (consensual)':<28s}  {result_2020['ICC']:20.4f}  {result_2023['ICC']:20.4f}")
print()
print("Item-level RAW ICCs (no α adjustment — upper bound):")
print(f"{'Item':<35s}  {'ICC_2020':>10s}  {'ICC_2023':>10s}")
for r in item_rows:
    print(f"  Q44_{r['idx']:<2d}  {r['label']:<27s}  "
          f"{r['icc20']:10.4f}  {r['icc23']:10.4f}")


# ---------- Word doc --------------------------------------------------------
doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Cm(2.0)
sec.top_margin = sec.bottom_margin = Cm(2.0)
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(10)


def H(text, size=14, color=None):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = True; r.font.size = Pt(size)
    if color: r.font.color.rgb = color


def H2(text):
    H(text, size=12)


def body(text, italic=False, size=10):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.size = Pt(size)
    if italic: r.italic = True


H("Consensual ICC Analysis — Comparative Opportunity Assessment",
  size=14, color=RGBColor(0x1f, 0x29, 0x37))
body(
    "Application of Sidanius & Pratto's variance-decomposition framework "
    "(\"The Power of Consensual Ideology,\" eqs. 1–5) to the Q44 / K3X1 "
    "Comparative Opportunity Assessment composite. Tests whether the perception "
    "of comparative opportunity functions as a CONSENSUAL legitimizing myth "
    "(shared across Estonian and Russian respondents) or as a DISSENSUAL "
    "contested ideology (where the two groups systematically disagree).",
    italic=True
)
body(
    "Decomposition: σ²_Total = σ²_Dissensual + σ²_Consensual + σ²_Error, "
    "where σ²_Dissensual = between-group variance, σ²_Consensual = α × within-"
    "group variance, σ²_Error = (1 − α) × within-group variance. "
    "ICC = σ²_Consensual / (σ²_Dissensual + σ²_Consensual). "
    "ICC near 1 → consensual / shared; ICC near 0 → dissensual / contested.",
    italic=True
)


# ----- Composite-level table -----
H2("Composite-Level Results")

t = doc.add_table(rows=1, cols=3)
t.style = "Light Grid Accent 1"
headers = ["Component", "2020", "2023"]
for i, h in enumerate(headers):
    cell = t.rows[0].cells[i]; cell.text = ""
    rr = cell.paragraphs[0].add_run(h); rr.bold = True; rr.font.size = Pt(9)


def add_row(label, v20, v23, fmt="{:.4f}"):
    cells = t.add_row().cells
    cells[0].text = ""; cells[0].paragraphs[0].add_run(label).font.size = Pt(9)
    cells[1].text = ""; cells[1].paragraphs[0].add_run(fmt.format(v20)).font.size = Pt(9)
    cells[2].text = ""; cells[2].paragraphs[0].add_run(fmt.format(v23)).font.size = Pt(9)


add_row("N (combined)",            result_2020["N"], result_2023["N"], "{:d}")
add_row("Cronbach's α",            result_2020["alpha_used"], result_2023["alpha_used"])
add_row("σ²_Total",                result_2020["var_total"], result_2023["var_total"])
add_row("σ²_Dissensual (between)", result_2020["var_dissensual"], result_2023["var_dissensual"])
add_row("σ²_Consensual (α × within)", result_2020["var_consensual"], result_2023["var_consensual"])
add_row("σ²_Error ((1−α) × within)",  result_2020["var_error"], result_2023["var_error"])
add_row("ICC (consensual)",        result_2020["ICC"], result_2023["ICC"])

doc.add_paragraph()


# ----- Substantive interpretation -----
def interpret_icc(icc):
    if icc >= 0.85:
        return "highly consensual"
    if icc >= 0.65:
        return "moderately consensual"
    if icc >= 0.45:
        return "mixed"
    if icc >= 0.25:
        return "moderately dissensual"
    return "highly dissensual"


body(
    f"Substantive reading: the composite-level ICC is "
    f"{result_2020['ICC']:.3f} in 2020 and {result_2023['ICC']:.3f} in 2023, "
    f"placing the construct in the '{interpret_icc(result_2020['ICC'])}' "
    f"region in 2020 and '{interpret_icc(result_2023['ICC'])}' in 2023. "
    f"In Sidanius & Pratto's terms, an ICC near 1 indicates that almost all "
    f"reliable variance in perceived comparative opportunity is consensual "
    f"(shared across the two ethnic groups), characteristic of a legitimizing "
    f"myth. An ICC near 0 indicates the two groups systematically disagree, "
    f"characteristic of a contested or dissensual ideology."
)


# ----- Item-level table -----
H2("Item-Level Raw ICCs (Upper Bound, No α Adjustment)")

body(
    "Item-level ICCs are computed without the α correction (single items have "
    "no internal-consistency reliability). They therefore treat all within-group "
    "variance as consensual and represent an UPPER BOUND on the consensual ICC "
    "per item. Useful for comparing items relative to each other.",
    italic=True
)

t = doc.add_table(rows=1, cols=4)
t.style = "Light Grid Accent 1"
headers = ["Item", "ICC 2020", "ICC 2023", "Δ (2023 − 2020)"]
for i, h in enumerate(headers):
    cell = t.rows[0].cells[i]; cell.text = ""
    rr = cell.paragraphs[0].add_run(h); rr.bold = True; rr.font.size = Pt(9)

for r in item_rows:
    cells = t.add_row().cells
    cells[0].text = ""
    p = cells[0].paragraphs[0]
    rr = p.add_run(f"Q44_{r['idx']}  "); rr.bold = True; rr.font.size = Pt(9)
    rr = p.add_run(r["label"]); rr.font.size = Pt(9)
    cells[1].text = ""; cells[1].paragraphs[0].add_run(f"{r['icc20']:.3f}").font.size = Pt(9)
    cells[2].text = ""; cells[2].paragraphs[0].add_run(f"{r['icc23']:.3f}").font.size = Pt(9)
    delta = r['icc23'] - r['icc20']
    cells[3].text = ""; cells[3].paragraphs[0].add_run(f"{delta:+.3f}").font.size = Pt(9)


# ----- Per-group within-group variances (descriptive) -----
H2("Per-Group Within-Group Variance (Descriptive)")

body(
    "Within-group variance reflects how much disagreement exists WITHIN each "
    "ethnic group on the composite. Larger within-group variance means the "
    "group is internally divided; smaller variance means the group is "
    "internally united in its perception. Useful complement to the ICC because "
    "it surfaces whether ideological consensus / dissensus is more on one side.",
    italic=True
)


def per_group_var(df, items):
    composite = compute_composite(df, items)
    g = pd.DataFrame({"x": composite, "g": df["ethnicity_binary"]}).dropna()
    out = {}
    for grp_val, name in [(0, "Estonian"), (1, "Russian")]:
        sub = g[g["g"] == grp_val]["x"]
        out[name] = {"N": len(sub), "M": sub.mean(), "SD": sub.std(ddof=1), "Var": sub.var(ddof=1)}
    return out


pg_2020 = per_group_var(df20, items_2020)
pg_2023 = per_group_var(df23, items_2023)

t = doc.add_table(rows=1, cols=5)
t.style = "Light Grid Accent 1"
headers = ["Group / Year", "N", "M", "SD", "Variance"]
for i, h in enumerate(headers):
    cell = t.rows[0].cells[i]; cell.text = ""
    rr = cell.paragraphs[0].add_run(h); rr.bold = True; rr.font.size = Pt(9)

for year, pg in [("2020", pg_2020), ("2023", pg_2023)]:
    for grp in ["Estonian", "Russian"]:
        s = pg[grp]
        cells = t.add_row().cells
        cells[0].text = ""; cells[0].paragraphs[0].add_run(f"{grp} {year}").font.size = Pt(9)
        cells[1].text = ""; cells[1].paragraphs[0].add_run(f"{s['N']}").font.size = Pt(9)
        cells[2].text = ""; cells[2].paragraphs[0].add_run(f"{s['M']:.3f}").font.size = Pt(9)
        cells[3].text = ""; cells[3].paragraphs[0].add_run(f"{s['SD']:.3f}").font.size = Pt(9)
        cells[4].text = ""; cells[4].paragraphs[0].add_run(f"{s['Var']:.4f}").font.size = Pt(9)


# ----- Methodological notes -----
H2("Methodological Notes")
body(
    "The ICC computation here follows Sidanius & Pratto's published "
    "operationalization. Two implementation choices worth noting: "
    "(1) Cronbach's α was computed pooled across both ethnic groups, treating "
    "the combined sample as one population. An alternative is per-group α "
    "averaged. (2) Item-level raw ICCs treat all within-group variance as "
    "consensual; the true item-level ICC accounting for measurement error "
    "would be lower. The composite-level ICC is the more rigorous estimate. "
    "(3) DK responses (code 9) were recoded to NaN before all computations, "
    "consistent with the rest of the project's analytical pipeline.",
    italic=True
)
body(
    "The framework was developed for cross-status-group comparisons in stable "
    "societies (Sidanius & Pratto's example uses U.S. and post-Soviet data). "
    "Whether the Estonian–Russian comparison fits 'stable society' assumptions "
    "in the post-2022 period is itself a substantive question the analysis can "
    "raise.",
    italic=True
)

out_path = ROOT / "reports" / "Comparative_Opportunity_Consensual_ICC.docx"
doc.save(out_path)
print(f"\nSaved: {out_path}")
