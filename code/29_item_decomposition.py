"""
Item-Level Decomposition of Composite Effect Sizes
====================================================
For every multi-item composite in the analysis, computes a Cohen's d for
each constituent item (with 95% CI and p-value), under the same four
comparisons used in the canonical effect-size pipeline:

  - Between-group, 2020 (Estonian vs Russian)
  - Between-group, 2023 (Estonian vs Russian)
  - Within-group, Estonian (2020 vs 2023)
  - Within-group, Russian  (2020 vs 2023)

This answers the question "which constituent item is driving the
composite-level effect?" — the natural follow-up to the canonical
composite-level d's reported in code/_effect_sizes.tsv.

Methodological caveats:
  - SD: Primary Out-group uses group-specific items (Q57_1/Q58_1/Q59_1 for
    Estonians toward Russian-speakers; Q57_2/Q58_2/Q59_2 for Russians toward
    Estonian-speakers). For the between-group comparison the items are paired
    by social context (neighbors / work / marriage) since they are functional
    analogs.
  - SD: General Out-group uses 3 items in 2020 (K4X7_3, K4X8_3, K4X9_3 —
    "new immigrants") and 6 items in 2023 (Q57_4, Q57_5, Q58_4, Q58_5,
    Q59_4, Q59_5 — Europeans + non-Europeans). Within-group decomposition
    is skipped because the item sets are not comparable across waves.
  - Single-item variables (Group ID Patterns, Territorial Attachment) and
    Contact: Out-group (a derived combination) are excluded.

Outputs:
  code/_item_decomposition.tsv               (machine-readable)
  reports/Item_Level_Decomposition.docx      (formatted tables, one per composite)
  viz/fig_item_decomp_<composite>.jpg        (one figure per composite, ×8)
"""

import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import pyreadstat
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from scipy import stats

ROOT = Path(__file__).parent.parent

# ---------- Load both waves --------------------------------------------------
df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy()

df20, _ = pyreadstat.read_sav(str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"),
                              encoding="latin1")
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy()


# ---------- Helpers ---------------------------------------------------------
def get_item(df, var, dk=9, reverse_max=None):
    s = pd.to_numeric(df[var], errors="coerce")
    s = s.where(s != dk)
    if reverse_max is not None:
        s = (reverse_max + 1) - s
    return s.astype(float)

def m_sd_n(s):
    s = s.dropna()
    return s.mean(), s.std(ddof=1), len(s)

def cohens_d_ci(m1, sd1, n1, m2, sd2, n2):
    """RMS-SD Cohen's d + 95% CI (Hedges & Olkin asymptotic SE)."""
    if any(pd.isna(x) for x in (m1, sd1, m2, sd2)) or n1 < 2 or n2 < 2:
        return np.nan, np.nan, np.nan
    s = math.sqrt((sd1**2 + sd2**2) / 2)
    if s == 0:
        return np.nan, np.nan, np.nan
    d = (m1 - m2) / s
    se = math.sqrt((n1 + n2) / (n1 * n2) + d**2 / (2 * (n1 + n2 - 2)))
    return d, d - 1.96 * se, d + 1.96 * se

def welch_p(a, b):
    a = a.dropna(); b = b.dropna()
    if len(a) < 2 or len(b) < 2:
        return np.nan
    return float(stats.ttest_ind(a, b, equal_var=False).pvalue)

def stars(p):
    if pd.isna(p): return ""
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"


# ---------- Composite specifications ----------------------------------------
# Each spec defines, per group and year, the items + reverse-coding rules.
# `pair_label` gives a human-readable label per item (the social context, etc.)
# used in tables and figures. For SD: Primary Out-group, est_items and
# rus_items differ but are paired by context.

SPECS = [
    {
        "name": "Superordinate Identity",
        "scale_max": 4,
        "inverted_composite": True,
        "items_2023": ["Q67_2", "Q67_4", "Q67_5"],
        "items_2020": ["K6X5_2", "K6X5_3", "K6X5_4"],
        "labels": ["Pride in flag",
                   "Second-class citizen (rev.)",
                   "Part of society"],
        "reverse_2023": ["Q67_4"],
        "reverse_2020": ["K6X5_3"],
        # When inverting the composite, we also invert each item the same way
        # so the item-level direction matches the composite-level direction.
    },
    {
        "name": "SD: Primary Out-group",
        "scale_max": 5,
        "inverted_composite": False,
        "labels": ["Neighbors", "Work / study", "Marriage in family"],
        "est_items_2023": ["Q57_1", "Q58_1", "Q59_1"],   # Est rate Russian-speakers
        "rus_items_2023": ["Q57_2", "Q58_2", "Q59_2"],   # Rus rate Estonian-speakers
        "est_items_2020": ["K4X7_1", "K4X8_1", "K4X9_1"],
        "rus_items_2020": ["K4X7_2", "K4X8_2", "K4X9_2"],
        "group_specific": True,  # different items per group (for between-group)
    },
    {
        "name": "SD: General Out-group",
        "scale_max": 5,
        "inverted_composite": False,
        # 6 items in 2023, 3 items in 2020 — within-group skipped.
        "items_2023": ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"],
        "items_2020": ["K4X7_3","K4X8_3","K4X9_3"],
        "labels_2023": ["Neighbors: other Europeans","Neighbors: non-Europeans",
                        "Work: other Europeans","Work: non-Europeans",
                        "Marriage: other Europeans","Marriage: non-Europeans"],
        "labels_2020": ["Neighbors: new immigrants","Work: new immigrants",
                        "Marriage: new immigrants"],
        "skip_within": True,
    },
    {
        "name": "Comparative Opportunity Assessment",
        "scale_max": 5,
        "inverted_composite": True,
        "items_2023": [f"Q44_{i}" for i in range(1, 13)],
        "items_2020": [f"K3X1_{i}" for i in range(1, 13)],
        "labels": [
            "Material well-being", "Cultural participation", "Education",
            "Social/political rights", "Entrepreneurship", "Career & jobs",
            "Medical care", "Housing", "Leisure & holidays",
            "Children & youth", "Sports & exercise", "State benefits/services",
        ],
        "reverse_2023": [],
        "reverse_2020": [],
    },
    {
        # 2026-04-30: switched reverse-coding from Q63_3/Q63_4 to Q63_1/Q63_2.
        # Composite direction now correctly reads "higher = more conflict belief."
        # Per-item direction: Q63_1/Q63_2 inverted (so high = strongly agree to
        # conflict-positive statements); Q63_3/Q63_4 raw (so high = strongly
        # disagree with conflict-negative statements = more conflict belief).
        "name": "Belief in Inevitable Conflict",
        "highlight_item": "Differences divide society (rev.)",
        "scale_max": 4,
        "inverted_composite": False,
        "items_2023": ["Q63_1", "Q63_2", "Q63_3", "Q63_4"],
        "items_2020": ["K6X1_1", "K6X1_2", "K6X1_3", "K6X1_4"],
        "labels": [
            "Conflicts inevitable (rev.)",
            "Differences divide society (rev.)",
            "Groups can cooperate",
            "Immigration enriches life",
        ],
        "reverse_2023": ["Q63_1", "Q63_2"],
        "reverse_2020": ["K6X1_1", "K6X1_2"],
    },
    {
        "name": "Minority Support Inclusion",
        "chart_label": "Minority Inclusion Support",
        "highlight_item": "Understand opinions",
        "scale_max": 4,
        "inverted_composite": True,
        "items_2023": ["Q68_1", "Q68_2", "Q68_3"],
        "items_2020": ["K6X6_1", "K6X6_2", "K6X6_3"],
        "labels": ["Involve in economy", "Involve in governance",
                   "Understand opinions"],
        "reverse_2023": [],
        "reverse_2020": [],
    },
    {
        "name": "Contact: Estonian Speakers",
        "scale_max": 5,
        "inverted_composite": True,
        "items_2023": [f"Q51_{i}" for i in range(1, 7)],
        "items_2020": [f"K4X1_{i}" for i in range(1, 7)],
        "labels": ["Work / school", "Neighbors", "Internet / social media",
                   "Leisure", "Family", "Friends"],
        "reverse_2023": [],
        "reverse_2020": [],
    },
    {
        "name": "Contact: Russian Speakers",
        "scale_max": 5,
        "inverted_composite": True,
        "items_2023": [f"Q52_{i}" for i in range(1, 7)],
        "items_2020": [f"K4X2_{i}" for i in range(1, 7)],
        "labels": ["Work / school", "Neighbors", "Internet / social media",
                   "Leisure", "Family", "Friends"],
        "reverse_2023": [],
        "reverse_2020": [],
    },
]


# ---------- Build all item series upfront ---------------------------------
def get_series_for_spec(spec):
    """Return dict of {comparison_axis: {label: pd.Series}}.

    Keys at the top level are 'est20', 'rus20', 'est23', 'rus23'.
    Inner keys are item labels.
    Reverse-coding and composite-level inversion both applied.
    """
    inv = spec["inverted_composite"]
    smax = spec["scale_max"]

    def fetch(df, items_list, reverse_list, labels):
        series_by_label = {}
        for it, lbl in zip(items_list, labels):
            rmax = smax if it in reverse_list else None
            s = get_item(df, it, reverse_max=rmax)
            if inv:
                # invert items so positive = more of the construct,
                # matching composite-level convention
                s = (smax + 1) - s
            series_by_label[lbl] = s
        return series_by_label

    out = {}
    if spec.get("group_specific"):
        # SD: Primary — different items per group, paired by label
        labels = spec["labels"]
        out["est20"] = fetch(df20[df20["ethnicity_binary"]==0],
                             spec["est_items_2020"], [], labels)
        out["rus20"] = fetch(df20[df20["ethnicity_binary"]==1],
                             spec["rus_items_2020"], [], labels)
        out["est23"] = fetch(df23[df23["ethnicity_binary"]==0],
                             spec["est_items_2023"], [], labels)
        out["rus23"] = fetch(df23[df23["ethnicity_binary"]==1],
                             spec["rus_items_2023"], [], labels)
    elif spec.get("skip_within"):
        # SD: General — different item count per wave; build per-wave dicts
        out["est20"] = fetch(df20[df20["ethnicity_binary"]==0],
                             spec["items_2020"], [], spec["labels_2020"])
        out["rus20"] = fetch(df20[df20["ethnicity_binary"]==1],
                             spec["items_2020"], [], spec["labels_2020"])
        out["est23"] = fetch(df23[df23["ethnicity_binary"]==0],
                             spec["items_2023"], [], spec["labels_2023"])
        out["rus23"] = fetch(df23[df23["ethnicity_binary"]==1],
                             spec["items_2023"], [], spec["labels_2023"])
    else:
        # Standard case — same items both groups, same labels both waves
        labels = spec["labels"]
        out["est20"] = fetch(df20[df20["ethnicity_binary"]==0],
                             spec["items_2020"], spec["reverse_2020"], labels)
        out["rus20"] = fetch(df20[df20["ethnicity_binary"]==1],
                             spec["items_2020"], spec["reverse_2020"], labels)
        out["est23"] = fetch(df23[df23["ethnicity_binary"]==0],
                             spec["items_2023"], spec["reverse_2023"], labels)
        out["rus23"] = fetch(df23[df23["ethnicity_binary"]==1],
                             spec["items_2023"], spec["reverse_2023"], labels)
    return out


# ---------- Compute decomposition for one composite ----------------------
def decompose(spec):
    series = get_series_for_spec(spec)
    rows = []
    name = spec["name"]

    # Determine which comparisons to run
    do_within  = not spec.get("skip_within", False)

    # Comparisons
    comparisons = []
    # Between-group, both years (use this wave's labels)
    for yr_key, yr in [("20", "2020"), ("23", "2023")]:
        labels_for_year = list(series[f"est{yr_key}"].keys())
        for lbl in labels_for_year:
            sA = series[f"est{yr_key}"][lbl]
            sB = series[f"rus{yr_key}"][lbl]
            mA, sdA, nA = m_sd_n(sA)
            mB, sdB, nB = m_sd_n(sB)
            d, lo, hi = cohens_d_ci(mA, sdA, nA, mB, sdB, nB)
            p = welch_p(sA, sB)
            rows.append({
                "composite": name, "comparison": f"between {yr}",
                "item": lbl,
                "M1": mA, "SD1": sdA, "N1": nA,
                "M2": mB, "SD2": sdB, "N2": nB,
                "d": d, "CI_lo": lo, "CI_hi": hi,
                "p": p, "sig": stars(p),
            })

    # Within-group, both groups
    if do_within:
        labels_for_year = list(series["est20"].keys())
        for grp, k20, k23 in [("Estonian", "est20", "est23"),
                              ("Russian",  "rus20", "rus23")]:
            for lbl in labels_for_year:
                if lbl not in series[k23]:
                    continue
                sA = series[k20][lbl]   # 2020
                sB = series[k23][lbl]   # 2023
                mA, sdA, nA = m_sd_n(sA)
                mB, sdB, nB = m_sd_n(sB)
                d, lo, hi = cohens_d_ci(mB, sdB, nB, mA, sdA, nA)  # 2023 - 2020
                p = welch_p(sA, sB)
                rows.append({
                    "composite": name, "comparison": f"within {grp}",
                    "item": lbl,
                    "M1": mA, "SD1": sdA, "N1": nA,
                    "M2": mB, "SD2": sdB, "N2": nB,
                    "d": d, "CI_lo": lo, "CI_hi": hi,
                    "p": p, "sig": stars(p),
                })
    return rows


# ---------- Run all composites and assemble the master TSV ------------------
all_rows = []
for spec in SPECS:
    print(f"Decomposing: {spec['name']}")
    all_rows.extend(decompose(spec))

df_out = pd.DataFrame(all_rows)
tsv_path = ROOT / "code" / "_item_decomposition.tsv"
df_out.to_csv(tsv_path, sep="\t", index=False, float_format="%.4f")
print(f"\nSaved: {tsv_path}  ({len(df_out)} rows)")


# ---------- Load canonical composite-level d's for reference -------------
canon = pd.read_csv(ROOT / "code" / "_effect_sizes.tsv", sep="\t")

def canonical_d(composite, comparison_label):
    """Return composite-level d for a comparison label like 'between 2020' or 'within Estonian'."""
    if comparison_label.startswith("between"):
        year = comparison_label.split()[1]
        sub = canon[(canon["table"]=="between") &
                    (canon["variable"]==composite) &
                    (canon["comparison"]==year)]
    else:
        grp = comparison_label.split()[1]
        sub = canon[(canon["table"]=="within") &
                    (canon["variable"]==composite) &
                    (canon["comparison"]==grp)]
    if len(sub) == 0:
        return None
    return sub.iloc[0]["d"], sub.iloc[0]["p"]


# ---------- Per-composite figure (4 panels) ------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

EST = "#2563eb"
RUS = "#d97706"
LINE_2020 = "#9ca3af"
LINE_2023 = "#64748b"   # slate-500 — light enough that black numeric labels stay readable inside the bar

PANEL_ORDER = [
    ("between 2020", "Between-group, 2020", LINE_2020),
    ("between 2023", "Between-group, 2023", LINE_2023),
    ("within Estonian", "Within Estonian, 2020 → 2023", EST),
    ("within Russian",  "Within Russian, 2020 → 2023", RUS),
]

for spec in SPECS:
    name = spec["name"]
    chart_label = spec.get("chart_label", name)
    highlight_item = spec.get("highlight_item")
    safe = name.replace(":", "").replace(" ", "_").replace("/", "_")
    rows = df_out[df_out["composite"] == name].copy()
    if len(rows) == 0:
        continue

    fig = plt.figure(figsize=(12.5, 7.2), dpi=300)
    gs = gridspec.GridSpec(2, 2, hspace=0.55, wspace=0.75,
                           left=0.21, right=0.96, top=0.86, bottom=0.10)

    # Determine common x-range with generous padding. The padding has to hold
    # both the value label (≈0.5 data units wide at fontsize 8.8) AND a visual
    # gap between that label and the y-tick label sitting at the y-axis line.
    finite_d = rows["d"].dropna()
    if finite_d.empty:
        plt.close(fig); continue
    d_max = max(abs(rows[["d","CI_lo","CI_hi"]].min().min()),
                abs(rows[["d","CI_lo","CI_hi"]].max().max()))
    x_pad = max(1.05, d_max * 0.55)
    xmin, xmax = -d_max - x_pad, d_max + x_pad

    for ax_i, (cmp_key, cmp_label, color) in enumerate(PANEL_ORDER):
        ax = fig.add_subplot(gs[ax_i // 2, ax_i % 2])
        sub = rows[rows["comparison"] == cmp_key].copy()
        if len(sub) == 0:
            ax.text(0.5, 0.5, "(not applicable for this composite)",
                    ha="center", va="center", transform=ax.transAxes,
                    color="#888", style="italic", fontsize=9)
            ax.set_title(cmp_label, fontsize=10, fontweight="bold", loc="left")
            ax.axis("off")
            continue

        # Order items in original spec order
        sub = sub.reset_index(drop=True)
        ys = np.arange(len(sub))[::-1]

        # Background highlight band for the spec's highlight item — drawn first
        # so bars and CIs render on top.
        if highlight_item is not None:
            for i, row in sub.iterrows():
                if row["item"] == highlight_item:
                    ax.axhspan(ys[i] - 0.45, ys[i] + 0.45,
                               color="#fef3c7", alpha=0.85, zorder=0)

        # Item-level d bars with error bars (95% CI)
        for i, row in sub.iterrows():
            d = row["d"]; lo = row["CI_lo"]; hi = row["CI_hi"]
            sig = (row["p"] < 0.05) if pd.notna(row["p"]) else False
            y = ys[i]
            ax.barh(y, d, height=0.55, color=color,
                    alpha=0.92 if sig else 0.32,
                    edgecolor=color, linewidth=0,
                    zorder=2)
            # CI error bar
            if pd.notna(lo) and pd.notna(hi):
                ax.plot([lo, hi], [y, y], color="#333",
                        linewidth=0.9, alpha=0.6, zorder=3)
                ax.plot([lo, lo], [y - 0.12, y + 0.12], color="#333",
                        linewidth=0.9, alpha=0.6, zorder=3)
                ax.plot([hi, hi], [y - 0.12, y + 0.12], color="#333",
                        linewidth=0.9, alpha=0.6, zorder=3)
            # Numeric label placed outside the END of the 95% CI bracket so
            # the text never overlaps the CI cap or the bar tip. Falls back
            # to the bar tip if the CI is missing.
            label_text = f"{d:+.2f} {row['sig']}"
            label_color = "#111" if sig else "#777"
            label_weight = "bold" if sig else "normal"
            if d >= 0:
                end = hi if pd.notna(hi) else d
                label_x = end + 0.08
                ha = "left"
            else:
                end = lo if pd.notna(lo) else d
                label_x = end - 0.08
                ha = "right"
            ax.text(label_x, y, label_text,
                    ha=ha, va="center", fontsize=8.8,
                    color=label_color, fontweight=label_weight,
                    zorder=4)

        # Composite-level d as a vertical reference line
        canon_result = canonical_d(name, cmp_key)
        if canon_result is not None:
            cd, cp = canon_result
            ax.axvline(cd, color="#dc2626", linewidth=1.0,
                       linestyle=(0, (4, 3)), zorder=1, alpha=0.85)
            ax.text(cd, len(sub) - 0.35, f"composite d = {cd:+.2f}",
                    ha="left" if cd >= 0 else "right", va="bottom",
                    fontsize=8.2, color="#dc2626", fontweight="bold")

        # Zero line
        ax.axvline(0, color="#333", linewidth=0.8, zorder=1)

        # Cosmetics
        ax.set_yticks(ys)
        ax.set_yticklabels(sub["item"].tolist(), fontsize=9.2)
        # Bold + amber the highlighted item's y-tick label
        if highlight_item is not None:
            for tl, item_name in zip(ax.get_yticklabels(), sub["item"].tolist()):
                if item_name == highlight_item:
                    tl.set_fontweight("bold")
                    tl.set_color("#92400e")
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(-0.7, len(sub) - 0.2)
        ax.tick_params(axis="x", length=2.5, color="#888", labelsize=8.5)
        ax.tick_params(axis="y", length=0)
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        ax.spines["left"].set_color("#888")
        ax.spines["bottom"].set_color("#888")
        ax.set_title(cmp_label, fontsize=10.5, fontweight="bold", loc="left")

    # Title and footer
    fig.text(0.05, 0.955, f"Item-Level Decomposition — {chart_label}",
             fontsize=12.5, fontweight="bold", ha="left")
    fig.text(0.05, 0.928,
             "Each bar = Cohen's d on a single constituent item. "
             "Black brackets = 95% CI. Red dashed line = composite-level d for that comparison.",
             fontsize=8.5, color="#444")
    fig.text(0.05, 0.025,
             "d uses RMS-SD denominator: d = (M₁ − M₂) / √[(SD₁² + SD₂²)/2]. "
             "Significance: *** p<.001, ** p<.01, * p<.05, ns = not significant. "
             "Faded bars = not significant at α=.05.",
             fontsize=7, color="#555")

    out_path = ROOT / "viz" / f"fig_item_decomp_{safe}.jpg"
    plt.savefig(out_path, dpi=300, format="jpg", facecolor="white",
                pil_kwargs={"quality": 95})
    plt.close(fig)
    print(f"  Figure: {out_path.name}")


# ---------- Word doc with all decomposition tables -----------------------
doc = Document()
section = doc.sections[0]
section.left_margin = section.right_margin = Cm(1.7)
section.top_margin = section.bottom_margin = Cm(1.8)
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(10)

p = doc.add_paragraph()
r = p.add_run("Item-Level Decomposition of Composite Effect Sizes")
r.bold = True; r.font.size = Pt(15)

p = doc.add_paragraph()
r = p.add_run(
    "For each multi-item composite, this report lists the Cohen's d (with 95% CI and Welch's t-test p) "
    "for every constituent item under each of the four canonical comparisons. The composite-level d "
    "is shown for reference at the start of each section. Items where |d| is largest contribute most "
    "to the composite-level effect. Items with d near zero contribute little."
); r.font.size = Pt(9); r.italic = True

doc.add_paragraph()

for spec in SPECS:
    name = spec["name"]
    rows = df_out[df_out["composite"] == name]
    if len(rows) == 0:
        continue

    p = doc.add_paragraph()
    r = p.add_run(name); r.bold = True; r.font.size = Pt(13)
    r.font.color.rgb = RGBColor(0x1f, 0x29, 0x37)

    for cmp_key, cmp_label, _ in PANEL_ORDER:
        sub = rows[rows["comparison"] == cmp_key]
        if len(sub) == 0:
            continue

        p = doc.add_paragraph()
        # Show composite-level d for context
        cr = canonical_d(name, cmp_key)
        if cr is not None:
            cd, cp = cr
            cp_label = f"d = {cd:+.2f}, p = {cp:.4f}" if cp >= .001 else f"d = {cd:+.2f}, p < .001"
            r = p.add_run(f"{cmp_label}  —  composite {cp_label}")
        else:
            r = p.add_run(cmp_label)
        r.bold = True; r.font.size = Pt(10.5)

        cols = ["Item", "M₁ (SD), n", "M₂ (SD), n",
                "Item d", "95% CI", "p", "Sig"]
        t = doc.add_table(rows=1, cols=len(cols))
        t.style = "Light Grid Accent 1"
        for i, c in enumerate(cols):
            cell = t.rows[0].cells[i]; cell.text = ""
            pp = cell.paragraphs[0]
            rr = pp.add_run(c); rr.bold = True; rr.font.size = Pt(8.5)
        for _, row in sub.iterrows():
            cells = t.add_row().cells
            row_vals = [
                row["item"],
                f"{row['M1']:.2f} ({row['SD1']:.2f}), n = {int(row['N1'])}",
                f"{row['M2']:.2f} ({row['SD2']:.2f}), n = {int(row['N2'])}",
                f"{row['d']:+.2f}",
                f"[{row['CI_lo']:+.2f}, {row['CI_hi']:+.2f}]",
                f"{row['p']:.3f}" if row['p'] >= .001 else "<.001",
                row["sig"],
            ]
            for i, txt in enumerate(row_vals):
                cells[i].text = ""
                pp = cells[i].paragraphs[0]
                rr = pp.add_run(txt); rr.font.size = Pt(8.5)
                if i in (3, 4, 5, 6):
                    pp.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        doc.add_paragraph()

# Footer note
p = doc.add_paragraph()
r = p.add_run(
    "Notes. Cohen's d uses root-mean-square SD: d = (M₁ − M₂) / √[(SD₁² + SD₂²)/2]. "
    "95% CIs use the asymptotic SE: SE(d) = √[(n₁ + n₂)/(n₁n₂) + d² / (2(n₁ + n₂ − 2))]. "
    "All comparisons are independent-samples Welch's t-tests. "
    "For inverted composites (Superordinate Identity, Comparative Opportunity Assessment, "
    "Minority Support Inclusion, both Contact composites), each item's scale was inverted before "
    "computing d so that positive d indicates more of the construct, matching the composite-level "
    "convention. SD: General Out-group within-group decomposition is omitted because the item set "
    "differs across waves (3 items in 2020, 6 in 2023)."
)
r.font.size = Pt(8); r.italic = True

doc_path = ROOT / "reports" / "Item_Level_Decomposition.docx"
doc.save(doc_path)
print(f"\nSaved: {doc_path}")
