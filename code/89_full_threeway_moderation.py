"""
Full three-way interaction model: Year × Contact × Language.

For each composite × ethnic group, fits the full model with all main effects,
all two-way interactions, and the three-way interaction:

composite = B0 + B1*year + B2*contact_c + B3*language_c
          + B4*(year × contact_c)
          + B5*(year × language_c)
          + B6*(contact_c × language_c)
          + B7*(year × contact_c × language_c)
          + ε

Each coefficient's interpretation (centered variables):

  B1 — year main effect at AVERAGE contact AND AVERAGE language
  B2 — contact main effect at year=2020 AND average language
  B3 — language main effect at year=2020 AND average contact
  B4 — does the year effect change per unit of contact (at avg language)?
  B5 — does the year effect change per unit of language (at avg contact)?
  B6 — does contact's slope depend on language level (at year=2020)?
       This is the test of "does language affect the impact of contact?"
  B7 — does the Year × Contact moderation itself depend on language?

Outputs:
  code/_full_threeway_moderation.tsv
  reports/Full_Threeway_Moderation.docx
  viz/fig_full_threeway_moderation_forest.jpg
"""

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = Path(__file__).parent.parent

# ---------- Load + prep ---------------------------------------------------
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

COEF_KEYS = [
    ("B1_year",            "year_2023"),
    ("B2_contact",         "contact_c"),
    ("B3_language",        "language_c"),
    ("B4_year_x_contact",  "yearXcontact"),
    ("B5_year_x_language", "yearXlanguage"),
    ("B6_contact_x_lang",  "contactXlanguage"),
    ("B7_threeway",        "yearXcontactXlanguage"),
]

rows = []
for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        s20 = build_cell(spec, df20, 2020, grp_code)
        s23 = build_cell(spec, df23, 2023, grp_code)
        long = pd.concat([s20, s23], ignore_index=True).dropna()

        long["contact_c"]            = long["contact"]  - long["contact"].mean()
        long["language_c"]           = long["language"] - long["language"].mean()
        long["yearXcontact"]         = long["year_2023"] * long["contact_c"]
        long["yearXlanguage"]        = long["year_2023"] * long["language_c"]
        long["contactXlanguage"]     = long["contact_c"] * long["language_c"]
        long["yearXcontactXlanguage"] = long["year_2023"] * long["contact_c"] * long["language_c"]

        predictors = [k for _, k in COEF_KEYS]
        X = sm.add_constant(long[predictors])
        m = sm.OLS(long["value"], X).fit(cov_type="HC3")

        row = {"variable": spec["name"], "group": grp_name,
               "N": int(m.nobs), "R2": m.rsquared}
        for label, key in COEF_KEYS:
            row[label]        = m.params[key]
            row[f"{label}_SE"] = m.bse[key]
            row[f"{label}_p"]  = m.pvalues[key]
            row[f"{label}_CI_low"]  = m.conf_int().loc[key][0]
            row[f"{label}_CI_high"] = m.conf_int().loc[key][1]
        rows.append(row)

out = pd.DataFrame(rows)
tsv = ROOT / "code" / "_full_threeway_moderation.tsv"
out.to_csv(tsv, sep="\t", index=False, float_format="%.4f")
print(f"Saved TSV: {tsv}\n")


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ("⁺" if p < .10 else "ns")


def fmt_p(p):
    if pd.isna(p): return "—"
    if p < .001:   return "< .001"
    return f"{p:.3f}".lstrip("0")


# Console summary focused on B6 and B7
print(f"{'Composite':<37}{'Group':<10}{'B6 (CxL)':>11}{'p B6':>9}{'B7 (3-way)':>13}{'p B7':>9}")
print("=" * 91)
for r in rows:
    print(f"{r['variable']:<37}{r['group']:<10}"
          f"{r['B6_contact_x_lang']:>+11.4f}{fmt_p(r['B6_contact_x_lang_p']):>9} {stars(r['B6_contact_x_lang_p'])}"
          f"{r['B7_threeway']:>+13.4f}{fmt_p(r['B7_threeway_p']):>9} {stars(r['B7_threeway_p'])}")


# ============================================================================
#                               WORD DOC
# ============================================================================
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


def body(text, italic=False, size=10):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.size = Pt(size); r.italic = italic


H("Full Three-way Moderation: Year × Out-group Contact × Out-group Language",
  size=14, color=RGBColor(0x1f, 0x29, 0x37))

body(
    "For each composite × ethnic group, fits the full regression with year, "
    "out-group contact, out-group language ability, all three pairwise "
    "interactions, and the three-way interaction. This is the saturated "
    "linear-additive moderation model for these three predictors.",
    italic=True
)

eq = doc.add_paragraph()
eq.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = eq.add_run("composite = B₀ + B₁·Year + B₂·Contact_c + B₃·Language_c "
                "+ B₄·(Year×Contact) + B₅·(Year×Language) + B₆·(Contact×Language) "
                "+ B₇·(Year×Contact×Language) + ε")
r.italic = True; r.font.size = Pt(10)

body(
    "Contact and language are mean-centered within each group. Year is binary "
    "(0 = 2020, 1 = 2023). HC3 robust standard errors. Key coefficients for the "
    "substantive questions:",
    italic=True, size=9,
)

body(
    "B₆ (Contact × Language). Does the contact–attitude slope DEPEND on language "
    "level? A positive B₆ on a 'positive-attitude' composite means contact's "
    "protective effect strengthens at higher language levels. B₆ ≈ 0 means "
    "contact's effect is uniform regardless of language proficiency.",
    italic=True, size=9,
)

body(
    "B₇ (Year × Contact × Language). Does the Year × Contact moderation ITSELF "
    "depend on language level? A non-zero B₇ means the asymmetric shifts "
    "documented in Tables 6/7 differ between high-language and low-language "
    "respondents — language qualifies the contact-moderation story.",
    italic=True, size=9,
)

doc.add_paragraph()


# Table 8 — interaction coefficients only (the substantive focus)
H("Table 8. Two-way and three-way interaction coefficients", size=12)
header8 = ["Variable", "Group", "N",
           "B₄ Year×Contact", "B₅ Year×Lang", "B₆ Contact×Lang", "B₇ 3-way",
           "p (B₆)", "p (B₇)"]
table8 = doc.add_table(rows=1, cols=len(header8))
table8.style = "Light Grid Accent 1"
for i, h in enumerate(header8):
    c = table8.rows[0].cells[i]; c.text = ""
    rr = c.paragraphs[0].add_run(h); rr.bold = True; rr.font.size = Pt(8.5)

for r in rows:
    row = table8.add_row().cells
    cells = [
        r["variable"], r["group"], str(r["N"]),
        f"{r['B4_year_x_contact']:+.4f} {stars(r['B4_year_x_contact_p'])}",
        f"{r['B5_year_x_language']:+.4f} {stars(r['B5_year_x_language_p'])}",
        f"{r['B6_contact_x_lang']:+.4f} {stars(r['B6_contact_x_lang_p'])}",
        f"{r['B7_threeway']:+.4f} {stars(r['B7_threeway_p'])}",
        fmt_p(r["B6_contact_x_lang_p"]),
        fmt_p(r["B7_threeway_p"]),
    ]
    for i, val in enumerate(cells):
        c = row[i]; c.text = ""
        rr = c.paragraphs[0].add_run(val); rr.font.size = Pt(8.5)
        if i >= 3:
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph()


# Table 9 — full coefficients (main + interactions)
H("Table 9. Full coefficients (main effects + interactions)", size=12)
header9 = ["Variable", "Group",
           "B₁ Year", "B₂ Contact", "B₃ Language",
           "B₄ Y×C", "B₅ Y×L", "B₆ C×L", "B₇ Y×C×L", "R²"]
table9 = doc.add_table(rows=1, cols=len(header9))
table9.style = "Light Grid Accent 1"
for i, h in enumerate(header9):
    c = table9.rows[0].cells[i]; c.text = ""
    rr = c.paragraphs[0].add_run(h); rr.bold = True; rr.font.size = Pt(8.5)

for r in rows:
    row = table9.add_row().cells
    coef_strs = []
    for k in ["B1_year", "B2_contact", "B3_language",
              "B4_year_x_contact", "B5_year_x_language",
              "B6_contact_x_lang", "B7_threeway"]:
        coef_strs.append(f"{r[k]:+.3f} {stars(r[f'{k}_p'])}")
    cells = [r["variable"], r["group"]] + coef_strs + [f"{r['R2']:.3f}"]
    for i, val in enumerate(cells):
        c = row[i]; c.text = ""
        rr = c.paragraphs[0].add_run(val); rr.font.size = Pt(8.5)
        if i >= 2:
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph()
body(
    "Note. All centered predictors. *** p < .001, ** p < .01, * p < .05, ⁺ p < .10, "
    "ns = not significant. Cross-reference Tables 1–3 for the omnibus ANOVA and d-based "
    "effect sizes, Table 6 for the Year × Contact moderation without language control, "
    "Table 7 for the same with language as an additive covariate (no B₆ or B₇).",
    italic=True, size=8,
)


# Narrative for significant B6 / B7
sig_b6 = [r for r in rows if r["B6_contact_x_lang_p"] < .10]
sig_b7 = [r for r in rows if r["B7_threeway_p"] < .10]

doc.add_paragraph()
H("Interpretation", size=12)

p = doc.add_paragraph()
run = p.add_run("Contact × Language (B₆) — does language affect the impact of contact? ")
run.bold = True; run.font.size = Pt(11)

if sig_b6:
    descs = []
    for r in sig_b6:
        direction = "amplifies" if r["B6_contact_x_lang"] > 0 else "buffers"
        descs.append(
            f"{r['variable']} ({r['group']}): B₆ = {r['B6_contact_x_lang']:+.4f}, "
            f"p = {fmt_p(r['B6_contact_x_lang_p'])} — language {direction} contact"
        )
    run = p.add_run(
        f"{len(sig_b6)} of 12 regressions show a Contact × Language interaction at "
        f"p < .10: " + "; ".join(descs) + "."
    )
    run.font.size = Pt(11)
else:
    run = p.add_run(
        "None of the 12 regressions show a significant Contact × Language interaction "
        "at p < .10. The contact–attitude slope does NOT depend on language proficiency "
        "in any cell — contact and language operate as independent (additive) predictors "
        "of the composite, not as multiplicative ones."
    )
    run.font.size = Pt(11)


p = doc.add_paragraph()
run = p.add_run("Year × Contact × Language (B₇) — does the contact-moderation pattern itself depend on language? ")
run.bold = True; run.font.size = Pt(11)

if sig_b7:
    descs = []
    for r in sig_b7:
        descs.append(
            f"{r['variable']} ({r['group']}): B₇ = {r['B7_threeway']:+.4f}, "
            f"p = {fmt_p(r['B7_threeway_p'])}"
        )
    run = p.add_run(
        f"{len(sig_b7)} of 12 regressions show a three-way interaction at p < .10: "
        + "; ".join(descs) + ". For these cells, the Year × Contact moderation pattern "
        "differs between high-language and low-language respondents; the substantive "
        "moderation story should be qualified by language level."
    )
    run.font.size = Pt(11)
else:
    run = p.add_run(
        "None of the 12 regressions show a three-way interaction at p < .10. The "
        "Year × Contact moderation pattern documented in Table 6 holds uniformly "
        "across high-language and low-language respondents. The contact-moderation "
        "story is robust to language qualifications."
    )
    run.font.size = Pt(11)

out_doc = ROOT / "reports" / "Full_Threeway_Moderation.docx"
doc.save(out_doc)
print(f"\nSaved Word doc: {out_doc}")


# ============================================================================
#                               FOREST PLOT
# ============================================================================
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.7,
})

RUS = "#d97706"
EST = "#2563eb"

COMPOSITES = [s["name"] for s in SPECS]
PRETTY = {
    "Superordinate Identity":             "Superordinate Identity",
    "SD: Primary Out-group":              "SD: Primary Out-group",
    "SD: General Out-group":              "SD: General Out-group ⁱ",
    "Comparative Opportunity Assessment": "Comparative Opportunity",
    "Belief in Inevitable Conflict":      "Belief in Inevitable Conflict",
    "Minority Inclusion Support":         "Minority Inclusion Support",
}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(17.0, 9.0), dpi=300, sharey=True)

y_positions = {}
y = 13.0
for comp in COMPOSITES:
    y_positions[(comp, "Estonian")] = y; y -= 1.0
    y_positions[(comp, "Russian")]  = y; y -= 1.7

y_min, y_max = min(y_positions.values()) - 0.6, max(y_positions.values()) + 0.7

for ax, coef_key, title_label, axis_label in [
    (ax1, "B6_contact_x_lang", "B₆ — Contact × Language",
     "B₆ — Contact × Language slope"),
    (ax2, "B7_threeway", "B₇ — Year × Contact × Language (three-way)",
     "B₇ — Three-way interaction"),
]:
    # Banding
    for i, comp in enumerate(COMPOSITES):
        if i % 2 == 0:
            y_top = y_positions[(comp, "Estonian")] + 0.6
            y_bot = y_positions[(comp, "Russian")]  - 0.6
            ax.axhspan(y_bot, y_top, facecolor="#f7f7f7", zorder=0)

    for r in rows:
        y = y_positions[(r["variable"], r["group"])]
        color = EST if r["group"] == "Estonian" else RUS
        b = r[coef_key]
        ll = r[f"{coef_key}_CI_low"]; ul = r[f"{coef_key}_CI_high"]
        p_val = r[f"{coef_key}_p"]
        sig = p_val < .10

        # CI bracket
        ax.plot([ll, ul], [y, y], color=color, linewidth=2.2, alpha=0.85,
                solid_capstyle="round", zorder=2)
        for xx in (ll, ul):
            ax.plot([xx, xx], [y - 0.10, y + 0.10],
                    color=color, linewidth=1.6, alpha=0.9, zorder=2)
        # Dot
        if sig:
            ax.scatter([b], [y], s=160, color=color,
                       edgecolor="white", linewidth=1.0, zorder=3)
        else:
            ax.scatter([b], [y], s=150, facecolor="white",
                       edgecolor=color, linewidth=1.8, zorder=3)

        # Annotation
        ax.text(ul + 0.005, y,
                f"{r['group'][0]} {b:+.4f} {stars(p_val)}",
                ha="left", va="center", fontsize=7.8,
                color="#222", family="monospace")

    ax.axvline(0, color="#666", linewidth=1.0, linestyle="-", zorder=1)
    ax.set_xlabel(axis_label, fontsize=10, color="#444", labelpad=8)
    ax.set_title(title_label, fontsize=12, fontweight="bold", loc="left", pad=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#ccc")
    ax.spines["bottom"].set_color("#666")
    ax.tick_params(axis="x", length=2.5, color="#666", labelsize=8)
    ax.tick_params(axis="y", length=0)

    # Pad x-range
    all_lo = min(r[f"{coef_key}_CI_low"] for r in rows)
    all_hi = max(r[f"{coef_key}_CI_high"] for r in rows)
    ax.set_xlim(all_lo - 0.005, all_hi + 0.07)

# Shared y-axis labels
yticks, yticklabels = [], []
for comp in COMPOSITES:
    y_E = y_positions[(comp, "Estonian")]
    y_R = y_positions[(comp, "Russian")]
    yticks.append((y_E + y_R) / 2)
    yticklabels.append(PRETTY[comp])
ax1.set_yticks(yticks)
ax1.set_yticklabels(yticklabels, fontsize=10, fontweight="bold")
ax1.set_ylim(y_min, y_max)
ax1.invert_yaxis()

# Title block
fig.text(0.04, 0.965,
         "Contact × Language and Year × Contact × Language — Forest Plot",
         fontsize=14, fontweight="bold", ha="left")
fig.text(0.04, 0.940,
         "Left: does the contact–attitude slope depend on language proficiency? Right: does the Year × Contact moderation itself differ between high- and low-language respondents?",
         fontsize=9, color="#444", ha="left")
fig.text(0.04, 0.918,
         "Filled dot = p < .10. Open dot = ns. Letters next to dots: E = Estonian, R = Russian. Reference lines at 0 = no interaction.",
         fontsize=9, color="#444", ha="left")

handles = [
    mlines.Line2D([], [], marker="o", color=EST, markerfacecolor=EST,
                  markeredgecolor="white", markersize=10, linestyle="None",
                  label="Estonian (sig.)"),
    mlines.Line2D([], [], marker="o", color=EST, markerfacecolor="white",
                  markeredgecolor=EST, markersize=10, markeredgewidth=1.8,
                  linestyle="None", label="Estonian (ns)"),
    mlines.Line2D([], [], marker="o", color=RUS, markerfacecolor=RUS,
                  markeredgecolor="white", markersize=10, linestyle="None",
                  label="Russian (sig.)"),
    mlines.Line2D([], [], marker="o", color=RUS, markerfacecolor="white",
                  markeredgecolor=RUS, markersize=10, markeredgewidth=1.8,
                  linestyle="None", label="Russian (ns)"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.985, 0.940),
           frameon=False, fontsize=8.5, ncol=2,
           handlelength=1.4, columnspacing=1.5)

fig.text(0.04, 0.022,
         "All centered predictors. HC3 robust standard errors. Contact composite inverted: higher = more frequent contact. Language ability reverse-coded: higher = more proficient.",
         fontsize=7.5, color="#555", ha="left")
fig.text(0.04, 0.008,
         "ⁱ SD: General Out-group uses different items in 2020 (3) vs 2023 (6). Significance: *** p<.001, ** p<.01, * p<.05, ⁺ p<.10.",
         fontsize=7.5, color="#555", ha="left")

plt.subplots_adjust(left=0.13, right=0.985, top=0.88, bottom=0.08, wspace=0.10)

out = ROOT / "viz" / "fig_full_threeway_moderation_forest.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved chart: {out}")
