"""
2x2 Factorial ANOVA — Ethnicity × Year — for each non-contact composite.
Modeled directly on Bilali, Çelik & Ok (2014) Table 1.

Design:
  Both factors are between-subjects (ethnicity is unchangeable; year is repeated
  cross-section with different respondents at each wave).

Specification:
  - Type III sums of squares (cell Ns unbalanced).
  - Effect sizes: partial eta-squared (η²p) = SS_effect / (SS_effect + SS_error).
  - Cohen's f for reference (sqrt(η²p / (1 - η²p))).
  - All composites use the same scale-inversion as _effect_sizes.tsv so that
    positive cell means = more of the construct.
  - Levene's tests within each group across years (matching Bilali's variance-
    comparison paragraph; the §25 / §28 polarization framing in this project).

Outputs:
  reports/ANOVA_2x2_Composites.docx — Bilali-style Table 1 + Levene's section
  code/_anova_2x2_composites.tsv     — machine-readable

Caveats flagged in the doc:
  - SD: Primary Out-group between-group main effect uses different items per
    group (Estonians: Q57/58/59_1; Russians: Q57/58/59_2). The ethnicity main
    effect and ethnicity × year interaction are not on a uniform indicator.
  - SD: General Out-group year main effect and interaction confound year with
    item-set change (3 items in 2020, 6 items in 2023).
"""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = Path(__file__).parent.parent


# ---------- Load both waves ------------------------------------------------
df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy().reset_index(drop=True)
df23["__year__"] = 2023

df20, _ = pyreadstat.read_sav(
    str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"), encoding="latin1"
)
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy().reset_index(drop=True)
df20["__year__"] = 2020


# ---------- Composite builders --------------------------------------------
def composite(df, items, reverse_items=None, scale_max=None, dk_code=9):
    sub = df[items].apply(pd.to_numeric, errors="coerce").copy()
    sub = sub.where(sub != dk_code)
    if reverse_items:
        for it in reverse_items:
            sub[it] = (scale_max + 1) - sub[it]
    return sub.mean(axis=1, skipna=True)


def build_composite_long(name, items_23, items_20, *, reverse_items_23=None,
                          reverse_items_20=None, scale_max=None, inverted=False):
    """Returns long-format DataFrame with columns [group, year, value]
    for one composite. `inverted=True` applies (scale_max+1 - x) for display
    direction matching _effect_sizes.tsv (positive d = more of construct).
    Handles per-group items via the items_23 / items_20 specs that may
    differ across groups — pass dicts keyed 'E' / 'R' when needed."""
    pieces = []
    for df, year, item_spec, rev_spec in [
        (df23, 2023, items_23, reverse_items_23),
        (df20, 2020, items_20, reverse_items_20),
    ]:
        if isinstance(item_spec, dict):
            # Different items per group
            for grp_key, grp_code in (("E", 0), ("R", 1)):
                sub_df = df[df["ethnicity_binary"] == grp_code]
                grp_items = item_spec[grp_key]
                grp_rev = rev_spec[grp_key] if rev_spec else None
                vals = composite(sub_df, grp_items, grp_rev, scale_max)
                if inverted:
                    vals = (scale_max + 1) - vals
                pieces.append(pd.DataFrame({
                    "group": "Estonian" if grp_code == 0 else "Russian",
                    "year": year, "value": vals.values
                }))
        else:
            vals_full = composite(df, item_spec, rev_spec, scale_max)
            if inverted:
                vals_full = (scale_max + 1) - vals_full
            df_year = df[["ethnicity_binary"]].copy()
            df_year["value"] = vals_full.values
            df_year["group"] = df_year["ethnicity_binary"].map({0: "Estonian", 1: "Russian"})
            df_year["year"] = year
            pieces.append(df_year[["group", "year", "value"]])
    return pd.concat(pieces, ignore_index=True).dropna(subset=["value"]).reset_index(drop=True)


# ---------- Composite specs -----------------------------------------------
SPECS = []

SPECS.append({
    "name": "Superordinate Identity",
    "scale_max": 4, "inverted": True,
    "items_23": ["Q67_2", "Q67_4", "Q67_5"], "reverse_items_23": ["Q67_4"],
    "items_20": ["K6X5_2", "K6X5_3", "K6X5_4"], "reverse_items_20": ["K6X5_3"],
    "note": "Higher = stronger belonging (raw composite scale-inverted for display).",
})

SPECS.append({
    "name": "SD: Primary Out-group",
    "scale_max": 5, "inverted": False,
    "items_23": {"E": ["Q57_1","Q58_1","Q59_1"], "R": ["Q57_2","Q58_2","Q59_2"]},
    "items_20": {"E": ["K4X7_1","K4X8_1","K4X9_1"], "R": ["K4X7_2","K4X8_2","K4X9_2"]},
    "reverse_items_23": None, "reverse_items_20": None,
    "note": "CAVEAT: Items differ by group (Estonians rate Russian-speakers; "
            "Russians rate Estonian-speakers). The ethnicity main effect and "
            "ethnicity × year interaction are on a mixed metric.",
})

SPECS.append({
    "name": "SD: General Out-group",
    "scale_max": 5, "inverted": False,
    "items_23": ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"],
    "items_20": ["K4X7_3","K4X8_3","K4X9_3"],
    "note": "CAVEAT: Item set differs across waves (3 items in 2020, 6 in 2023). "
            "Year main effect and interaction confound year with item-set change.",
})

SPECS.append({
    "name": "Comparative Opportunity Assessment",
    "scale_max": 5, "inverted": True,
    "items_23": [f"Q44_{i}" for i in range(1, 13)],
    "items_20": [f"K3X1_{i}" for i in range(1, 13)],
})

SPECS.append({
    "name": "Belief in Inevitable Conflict",
    "scale_max": 4, "inverted": False,
    "items_23": ["Q63_1","Q63_2","Q63_3","Q63_4"], "reverse_items_23": ["Q63_1","Q63_2"],
    "items_20": ["K6X1_1","K6X1_2","K6X1_3","K6X1_4"], "reverse_items_20": ["K6X1_1","K6X1_2"],
})

SPECS.append({
    "name": "Minority Inclusion Support",
    "scale_max": 4, "inverted": True,
    "items_23": ["Q68_1","Q68_2","Q68_3"],
    "items_20": ["K6X6_1","K6X6_2","K6X6_3"],
})


# ---------- Run ANOVA per composite ---------------------------------------
def run_anova(df_long):
    df_long = df_long.copy()
    # Sum-contrast coding so Type III main effects are well-identified
    df_long["group_c"] = df_long["group"].astype("category")
    df_long["year_c"]  = df_long["year"].astype("category")
    model = smf.ols(
        "value ~ C(group_c, Sum) * C(year_c, Sum)",
        data=df_long,
    ).fit()
    tbl = sm.stats.anova_lm(model, typ=3)
    # Compute partial eta-squared per effect
    ss_resid = tbl.loc["Residual", "sum_sq"]
    rows = {}
    for label, term in [
        ("Ethnicity",      "C(group_c, Sum)"),
        ("Year",           "C(year_c, Sum)"),
        ("Ethnicity × Year","C(group_c, Sum):C(year_c, Sum)"),
    ]:
        ss_eff = tbl.loc[term, "sum_sq"]
        df_eff = tbl.loc[term, "df"]
        F_eff  = tbl.loc[term, "F"]
        p_eff  = tbl.loc[term, "PR(>F)"]
        eta2p  = ss_eff / (ss_eff + ss_resid)
        rows[label] = {"SS": ss_eff, "df": int(df_eff), "F": F_eff,
                       "p": p_eff, "eta2p": eta2p}
    rows["__residual__"] = {"SS": ss_resid, "df": int(tbl.loc["Residual","df"])}
    rows["__N__"] = int(model.nobs)
    return rows


def cell_stats(df_long):
    """Return dict keyed (group, year) -> (M, SD, N)."""
    out = {}
    for g in ("Estonian", "Russian"):
        for y in (2020, 2023):
            s = df_long[(df_long["group"] == g) & (df_long["year"] == y)]["value"]
            s = s.dropna()
            out[(g, y)] = (s.mean(), s.std(ddof=1), len(s))
    return out


def levene_within_group(df_long, group):
    """Levene's test comparing 2020 vs 2023 variance within one group."""
    s20 = df_long[(df_long["group"] == group) & (df_long["year"] == 2020)]["value"].dropna()
    s23 = df_long[(df_long["group"] == group) & (df_long["year"] == 2023)]["value"].dropna()
    F, p = stats.levene(s20, s23, center="median")
    return F, p, len(s20), len(s23), s20.var(ddof=1), s23.var(ddof=1)


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "ns"


def fmt_p(p):
    if p < .0001: return "< .0001"
    if p < .001:  return f"{p:.4f}"
    return f"{p:.3f}"


# ---------- Run all -------------------------------------------------------
results = []
for spec in SPECS:
    long = build_composite_long(
        spec["name"], spec["items_23"], spec["items_20"],
        reverse_items_23=spec.get("reverse_items_23"),
        reverse_items_20=spec.get("reverse_items_20"),
        scale_max=spec["scale_max"],
        inverted=spec.get("inverted", False),
    )
    anova = run_anova(long)
    cells = cell_stats(long)
    lev_E = levene_within_group(long, "Estonian")
    lev_R = levene_within_group(long, "Russian")
    results.append({
        "spec": spec, "anova": anova, "cells": cells,
        "lev_E": lev_E, "lev_R": lev_R, "N_total": anova["__N__"],
    })

# ---------- TSV output ----------------------------------------------------
tsv_rows = []
for r in results:
    name = r["spec"]["name"]
    cE20 = r["cells"][("Estonian", 2020)]; cE23 = r["cells"][("Estonian", 2023)]
    cR20 = r["cells"][("Russian", 2020)];  cR23 = r["cells"][("Russian", 2023)]
    eth = r["anova"]["Ethnicity"]; yr = r["anova"]["Year"]; ix = r["anova"]["Ethnicity × Year"]
    tsv_rows.append({
        "variable": name,
        "N_total": r["N_total"],
        "Est_2020_M": cE20[0], "Est_2020_SD": cE20[1], "Est_2020_N": cE20[2],
        "Est_2023_M": cE23[0], "Est_2023_SD": cE23[1], "Est_2023_N": cE23[2],
        "Rus_2020_M": cR20[0], "Rus_2020_SD": cR20[1], "Rus_2020_N": cR20[2],
        "Rus_2023_M": cR23[0], "Rus_2023_SD": cR23[1], "Rus_2023_N": cR23[2],
        "F_ethnicity": eth["F"], "p_ethnicity": eth["p"], "eta2p_ethnicity": eth["eta2p"],
        "F_year": yr["F"], "p_year": yr["p"], "eta2p_year": yr["eta2p"],
        "F_interaction": ix["F"], "p_interaction": ix["p"], "eta2p_interaction": ix["eta2p"],
        "Levene_Est_F": r["lev_E"][0], "Levene_Est_p": r["lev_E"][1],
        "Levene_Est_var_2020": r["lev_E"][4], "Levene_Est_var_2023": r["lev_E"][5],
        "Levene_Rus_F": r["lev_R"][0], "Levene_Rus_p": r["lev_R"][1],
        "Levene_Rus_var_2020": r["lev_R"][4], "Levene_Rus_var_2023": r["lev_R"][5],
    })
tsv_path = ROOT / "code" / "_anova_2x2_composites.tsv"
pd.DataFrame(tsv_rows).to_csv(tsv_path, sep="\t", index=False, float_format="%.4f")
print(f"Saved TSV: {tsv_path}\n")

# ---------- Print summary -------------------------------------------------
for r in results:
    name = r["spec"]["name"]
    print(f"\n=== {name}  (N = {r['N_total']}) ===")
    for g in ("Estonian", "Russian"):
        for y in (2020, 2023):
            M, SD, N = r["cells"][(g, y)]
            print(f"  {g:<9} {y}: M = {M:.3f}, SD = {SD:.3f}, n = {N}")
    for effect in ("Ethnicity", "Year", "Ethnicity × Year"):
        e = r["anova"][effect]
        print(f"  {effect:<18}: F({e['df']}, {r['anova']['__residual__']['df']}) = {e['F']:.2f}, "
              f"p = {fmt_p(e['p'])} {stars(e['p'])},  η²p = {e['eta2p']:.4f}")
    fE, pE, _, _, vE20, vE23 = r["lev_E"]
    fR, pR, _, _, vR20, vR23 = r["lev_R"]
    print(f"  Levene Estonian: F = {fE:.2f}, p = {fmt_p(pE)} {stars(pE)}  "
          f"(var 2020 = {vE20:.3f}, var 2023 = {vE23:.3f})")
    print(f"  Levene Russian:  F = {fR:.2f}, p = {fmt_p(pR)} {stars(pR)}  "
          f"(var 2020 = {vR20:.3f}, var 2023 = {vR23:.3f})")


# ============================================================================
#                              WORD DOCUMENT
# ============================================================================

doc = Document()

# Page setup
section = doc.sections[0]
section.left_margin = section.right_margin = Cm(1.8)
section.top_margin = section.bottom_margin = Cm(2.0)
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(10)


def H(text, size=14, color=None):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = True; r.font.size = Pt(size)
    if color: r.font.color.rgb = color


def body(text, italic=False, size=10):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.size = Pt(size); r.italic = italic
    return p


# ----- Title + intro -------------------------------------------------------
H("2 × 2 Factorial ANOVA — Ethnicity × Year — for Non-Contact Composites",
  size=15, color=RGBColor(0x1f, 0x29, 0x37))

body(
    "Each composite was regressed on ethnicity (Estonian / Russian), year (2020 / 2023), "
    "and their interaction in a between-subjects 2 × 2 factorial ANOVA. Type III sums of "
    "squares are used because cell Ns are unbalanced. Partial eta-squared (η²p) is "
    "reported alongside F and p; conventional benchmarks are .01 = small, .06 = medium, "
    ".14 = large. The interaction effect tests directly whether the between-group gap "
    "changed from 2020 to 2023 — the asymmetric-divergence claim. Levene's tests of "
    "variance homogeneity, comparing within-group response variance across years, are "
    "reported separately, parallel to the variance findings reported in Bilali, Çelik, "
    "& Ok (2014).",
    italic=True
)

body(
    "Design note. Both ethnicity and year are between-subjects factors: the Estonian "
    "Integration Monitor is a repeated cross-section, with different respondents drawn "
    "at each wave from the same target population. No paired or repeated-measures "
    "machinery applies.",
    italic=True, size=9,
)

doc.add_paragraph()


# ----- Table 1: cell means + ANOVA -----------------------------------------
H("Table 1. Cell means, standard deviations, and 2 × 2 ANOVA results", size=12)

# Column structure mimics Bilali et al. (2014) Table 1.
header = [
    "Variable", "Cell",
    "Est. M (SD), n", "Rus. M (SD), n",
    "Ethnicity\nF, p, η²p", "Year\nF, p, η²p", "Eth. × Year\nF, p, η²p"
]
table = doc.add_table(rows=1, cols=len(header))
table.style = "Light Grid Accent 1"
for i, h in enumerate(header):
    c = table.rows[0].cells[i]; c.text = ""
    rr = c.paragraphs[0].add_run(h); rr.bold = True; rr.font.size = Pt(9)


def fmt_F(F, p, eta):
    s = stars(p)
    return f"{F:.2f}, {fmt_p(p)} {s}, .{int(round(eta*1000)):03d}"


for r in results:
    name = r["spec"]["name"]
    cells = r["cells"]; a = r["anova"]
    inv = r["spec"].get("inverted", False)
    label = name + (" (inv.)" if inv else "")

    # Row 1 of each variable: 2020 cell means + ANOVA results (spanning rows)
    row = table.add_row().cells
    row[0].text = ""; row[0].paragraphs[0].add_run(label).font.size = Pt(9)
    row[1].text = "LIC (2020)"
    row[1].paragraphs[0].runs[0].font.size = Pt(9)
    eM, eSD, eN = cells[("Estonian", 2020)]; rM, rSD, rN = cells[("Russian", 2020)]
    row[2].text = f"{eM:.2f} ({eSD:.2f}), n = {eN}"
    row[3].text = f"{rM:.2f} ({rSD:.2f}), n = {rN}"
    row[4].text = fmt_F(a["Ethnicity"]["F"], a["Ethnicity"]["p"], a["Ethnicity"]["eta2p"])
    row[5].text = fmt_F(a["Year"]["F"],      a["Year"]["p"],      a["Year"]["eta2p"])
    row[6].text = fmt_F(a["Ethnicity × Year"]["F"], a["Ethnicity × Year"]["p"], a["Ethnicity × Year"]["eta2p"])
    for c in row:
        for para in c.paragraphs:
            for run in para.runs:
                run.font.size = Pt(9)

    # Row 2: 2023 cells, ANOVA columns blank (since they apply to the whole 2x2)
    row = table.add_row().cells
    row[0].text = ""; row[1].text = "HIC (2023)"; row[1].paragraphs[0].runs[0].font.size = Pt(9)
    eM, eSD, eN = cells[("Estonian", 2023)]; rM, rSD, rN = cells[("Russian", 2023)]
    row[2].text = f"{eM:.2f} ({eSD:.2f}), n = {eN}"
    row[3].text = f"{rM:.2f} ({rSD:.2f}), n = {rN}"
    row[4].text = row[5].text = row[6].text = ""
    for c in row:
        for para in c.paragraphs:
            for run in para.runs:
                run.font.size = Pt(9)


# ----- Notes ---------------------------------------------------------------
doc.add_paragraph()
body(
    "Note. M = mean composite score on the original Likert metric (after scale-inversion "
    "where indicated, so that higher = more of the construct). SD = standard deviation, "
    "n = pairwise-deletion cell N. F = Type III ANOVA F-statistic, p = exact p-value, "
    "η²p = partial eta-squared. Significance: *** p < .001, ** p < .01, * p < .05, "
    "ns = not significant. \"(inv.)\" marks composites whose raw scale was inverted for "
    "display direction; the inversion does not change effect sizes or p-values but flips "
    "the sign of the cell means relative to the raw scale.",
    italic=True, size=8,
)


# ----- Caveat sections per problematic composite ---------------------------
doc.add_paragraph()
H("Caveats on specific composites", size=12)
for r in results:
    note = r["spec"].get("note")
    if note and "CAVEAT" in note:
        p = doc.add_paragraph()
        run = p.add_run(f"{r['spec']['name']}. ")
        run.bold = True; run.font.size = Pt(10)
        run2 = p.add_run(note.replace("CAVEAT: ", ""))
        run2.font.size = Pt(10)


# ----- Levene's section ----------------------------------------------------
doc.add_paragraph()
H("Within-group variance comparisons (Levene's test, 2020 vs 2023)", size=12)
body(
    "Per Bilali, Çelik & Ok (2014), variance comparisons across waves within each group "
    "test whether the heightened intergroup context produced more homogeneous reactions "
    "(strong-situation hypothesis) or more heterogeneous reactions (within-group "
    "polarization). The Russian community shows the second pattern on Superordinate "
    "Identity and the Estonian community shows it on Belief in Inevitable Conflict — see "
    "Decision log §29, §33.",
    italic=True, size=9
)

header2 = ["Variable", "Estonian Levene\nF, p, var(2020) → var(2023)",
           "Russian Levene\nF, p, var(2020) → var(2023)"]
table2 = doc.add_table(rows=1, cols=len(header2))
table2.style = "Light Grid Accent 1"
for i, h in enumerate(header2):
    c = table2.rows[0].cells[i]; c.text = ""
    rr = c.paragraphs[0].add_run(h); rr.bold = True; rr.font.size = Pt(9)

for r in results:
    name = r["spec"]["name"]
    fE, pE, _, _, vE20, vE23 = r["lev_E"]
    fR, pR, _, _, vR20, vR23 = r["lev_R"]
    arrow_E = "↑" if vE23 > vE20 else "↓"
    arrow_R = "↑" if vR23 > vR20 else "↓"
    cells_r = table2.add_row().cells
    cells_r[0].text = name
    cells_r[1].text = (f"F = {fE:.2f}, p = {fmt_p(pE)} {stars(pE)}    "
                       f"{vE20:.3f} → {vE23:.3f} {arrow_E}")
    cells_r[2].text = (f"F = {fR:.2f}, p = {fmt_p(pR)} {stars(pR)}    "
                       f"{vR20:.3f} → {vR23:.3f} {arrow_R}")
    for c in cells_r:
        for para in c.paragraphs:
            for run in para.runs:
                run.font.size = Pt(9)


# ----- Footer note ---------------------------------------------------------
doc.add_paragraph()
body(
    "Notes. Levene's tests use the median-centered (Brown–Forsythe) version, which is "
    "more robust to non-normal distributions than the mean-centered original. var(2020) → "
    "var(2023) shows the within-group variance at each wave; ↑ = increased dispersion "
    "(community fragmenting on this attitude); ↓ = decreased dispersion (community "
    "converging). Same convention as Bilali et al. (2014).",
    italic=True, size=8,
)

# Save
out_doc = ROOT / "reports" / "ANOVA_2x2_Composites.docx"
doc.save(out_doc)
print(f"\nSaved Word doc: {out_doc}")
