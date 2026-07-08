"""
Item-Level Decomposition — Belief in Inevitable Conflict (Corrected Direction)
==================================================================================
Replacement for the BiC panel of code/29_item_decomposition.py. Uses the
corrected per-item direction handling so every item is oriented
"higher d = more conflict belief".

The "Differences divide society" item is highlighted because it is the only
item where Estonian and Russian within-group changes are BOTH significant
and go in OPPOSITE directions (Estonians +0.26 ***, Russians −0.21 ***) —
the cross-group divergence pattern surfaced by the Round 3 Blindspot report.
Same visual scheme as code/40_minority_item_decomp.py "Understand opinions".

  - Q63_1 / K6X1_1 ("Conflicts inevitable"):       INVERT (5 - raw)
  - Q63_2 / K6X1_2 ("Differences divide society"): INVERT (5 - raw)
  - Q63_3 / K6X1_3 ("Groups can cooperate"):       RAW (high disagreement = more conflict belief)
  - Q63_4 / K6X1_4 ("Immigration enriches life"):  RAW (same logic)

The composite-level reference line (red dashed) uses the canonical d from
code/_effect_sizes.tsv with sign flipped to match the corrected direction
(canonical composite has direction "higher composite = LESS conflict belief"
due to the historical reverse-coding choice; we flip the d sign so the
chart's positive direction means "more conflict belief" consistently).

Output: viz/fig_item_decomp_BiC_corrected.jpg  (300 DPI)
"""

import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import pyreadstat
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


def to_num(s, dk=9):
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s != dk).astype(float)

def m_sd_n(s):
    s = s.dropna()
    return s.mean(), s.std(ddof=1), len(s)

def cohens_d_ci(m1, sd1, n1, m2, sd2, n2):
    if any(pd.isna(x) for x in (m1, sd1, m2, sd2)) or n1 < 2 or n2 < 2:
        return np.nan, np.nan, np.nan
    s = math.sqrt((sd1**2 + sd2**2) / 2)
    if s == 0: return np.nan, np.nan, np.nan
    d = (m1 - m2) / s
    se = math.sqrt((n1 + n2) / (n1 * n2) + d**2 / (2 * (n1 + n2 - 2)))
    return d, d - 1.96 * se, d + 1.96 * se

def welch_p(a, b):
    a = a.dropna(); b = b.dropna()
    if len(a) < 2 or len(b) < 2: return np.nan
    return float(stats.ttest_ind(a, b, equal_var=False).pvalue)

def stars(p):
    if pd.isna(p): return ""
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"


# ---------- Item series with corrected direction --------------------------
# Higher = more conflict belief on every item.
ITEMS = [
    {"label": "Conflicts inevitable",
     "code23": "Q63_1", "code20": "K6X1_1", "invert": True},
    {"label": "Differences divide society",
     "code23": "Q63_2", "code20": "K6X1_2", "invert": True},
    {"label": "Groups can cooperate",
     "code23": "Q63_3", "code20": "K6X1_3", "invert": False},
    {"label": "Immigration enriches life",
     "code23": "Q63_4", "code20": "K6X1_4", "invert": False},
]

def fetch(df, ethval, code, do_invert):
    sub = df[df["ethnicity_binary"] == ethval]
    s = to_num(sub[code])
    if do_invert:
        s = 5 - s
    return s

series = {}
for it in ITEMS:
    series[(it["label"], "est20")] = fetch(df20, 0, it["code20"], it["invert"])
    series[(it["label"], "rus20")] = fetch(df20, 1, it["code20"], it["invert"])
    series[(it["label"], "est23")] = fetch(df23, 0, it["code23"], it["invert"])
    series[(it["label"], "rus23")] = fetch(df23, 1, it["code23"], it["invert"])


# ---------- Compute item-level d's per comparison --------------------------
results = []   # rows of (label, comparison, d, lo, hi, p)

for it in ITEMS:
    lbl = it["label"]
    e20 = series[(lbl, "est20")]; r20 = series[(lbl, "rus20")]
    e23 = series[(lbl, "est23")]; r23 = series[(lbl, "rus23")]

    # between-group 2020 (Est - Rus)
    me, sde, ne = m_sd_n(e20); mr, sdr, nr = m_sd_n(r20)
    d, lo, hi = cohens_d_ci(me, sde, ne, mr, sdr, nr)
    p = welch_p(e20, r20)
    results.append((lbl, "between 2020", d, lo, hi, p))

    # between-group 2023
    me, sde, ne = m_sd_n(e23); mr, sdr, nr = m_sd_n(r23)
    d, lo, hi = cohens_d_ci(me, sde, ne, mr, sdr, nr)
    p = welch_p(e23, r23)
    results.append((lbl, "between 2023", d, lo, hi, p))

    # within-group, Estonian (2023 - 2020)
    m20, s20, n20 = m_sd_n(e20); m23, s23, n23 = m_sd_n(e23)
    d, lo, hi = cohens_d_ci(m23, s23, n23, m20, s20, n20)
    p = welch_p(e20, e23)
    results.append((lbl, "within Estonian", d, lo, hi, p))

    # within-group, Russian
    m20, s20, n20 = m_sd_n(r20); m23, s23, n23 = m_sd_n(r23)
    d, lo, hi = cohens_d_ci(m23, s23, n23, m20, s20, n20)
    p = welch_p(r20, r23)
    results.append((lbl, "within Russian", d, lo, hi, p))


df_results = pd.DataFrame(results,
    columns=["item", "comparison", "d", "CI_lo", "CI_hi", "p"])
df_results["sig"] = df_results["p"].apply(stars)
print("="*92)
print("BELIEF IN INEVITABLE CONFLICT — item-level d's (CORRECTED DIRECTION)")
print("(Higher d means more conflict belief on that item)")
print("="*92)
print(df_results.to_string(index=False))


# ---------- Composite-level d under corrected direction -------------------
# Pull from canonical TSV and flip sign (corrected composite = 5 - canonical).
canon = pd.read_csv(ROOT / "code" / "_effect_sizes.tsv", sep="\t")
def canon_d(comparison):
    if comparison.startswith("between"):
        year = comparison.split()[1]
        sub = canon[(canon["table"]=="between") &
                    (canon["variable"]=="Belief in Inevitable Conflict") &
                    (canon["comparison"]==year)]
    else:
        grp = comparison.split()[1]
        sub = canon[(canon["table"]=="within") &
                    (canon["variable"]=="Belief in Inevitable Conflict") &
                    (canon["comparison"]==grp)]
    row = sub.iloc[0]
    # 2026-04-30: under Option B recode, the canonical TSV already has the
    # corrected direction (higher = more conflict belief) — no sign flip needed.
    return row["d"], row["p"]


# ---------- Plot ------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

EST = "#2563eb"; RUS = "#d97706"
LINE_2020 = "#9ca3af"; LINE_2023 = "#1f2937"

PANEL_ORDER = [
    ("between 2020", "Between-group, 2020", LINE_2020),
    ("between 2023", "Between-group, 2023", LINE_2023),
    ("within Estonian", "Within Estonian, 2020 → 2023", EST),
    ("within Russian",  "Within Russian, 2020 → 2023", RUS),
]

fig = plt.figure(figsize=(13.0, 7.4), dpi=300)
gs = gridspec.GridSpec(2, 2, hspace=0.65, wspace=0.50,
                       left=0.15, right=0.985, top=0.82, bottom=0.13)

# Common x-range
finite = df_results[["d", "CI_lo", "CI_hi"]].abs().max().max()
d_max = max(finite, 1.0)
xmin, xmax = -d_max - 0.45, d_max + 0.45     # extra padding so labels don't run off

HIGHLIGHT_ITEM = "Differences divide society"  # diverging-direction item
HIGHLIGHT_BG = "#fef3c7"                        # soft amber band

for ax_i, (cmp_key, cmp_label, color) in enumerate(PANEL_ORDER):
    ax = fig.add_subplot(gs[ax_i // 2, ax_i % 2])
    sub = df_results[df_results["comparison"] == cmp_key].copy().reset_index(drop=True)
    ys = np.arange(len(sub))[::-1]

    # Background highlight band for the diverging-direction item — drawn first
    # so bars and CIs render on top.
    for i, row in sub.iterrows():
        if row["item"] == HIGHLIGHT_ITEM:
            ax.axhspan(ys[i] - 0.45, ys[i] + 0.45,
                       color=HIGHLIGHT_BG, alpha=0.85, zorder=0)

    for i, row in sub.iterrows():
        d = row["d"]; lo = row["CI_lo"]; hi = row["CI_hi"]
        sig = row["p"] < 0.05 if pd.notna(row["p"]) else False
        y = ys[i]
        ax.barh(y, d, height=0.55, color=color,
                alpha=0.92 if sig else 0.32,
                edgecolor=color, linewidth=0, zorder=2)
        if pd.notna(lo) and pd.notna(hi):
            ax.plot([lo, hi], [y, y], color="#333", linewidth=0.9,
                    alpha=0.6, zorder=3)
            for xx in (lo, hi):
                ax.plot([xx, xx], [y - 0.12, y + 0.12], color="#333",
                        linewidth=0.9, alpha=0.6, zorder=3)

        # Place labels OUTSIDE the CI bracket end (not the bar tip), so labels
        # never visually merge with bar/CI even when d is large.
        end = hi if (d >= 0 and pd.notna(hi)) else \
              lo if (d < 0 and pd.notna(lo)) else d
        offset = 0.08 if d >= 0 else -0.08
        ha = "left" if d >= 0 else "right"
        col = "#111" if sig else "#777"
        weight = "bold" if sig else "normal"
        ax.text(end + offset, y, f"{d:+.2f} {row['sig']}",
                ha=ha, va="center", fontsize=7.4,
                color=col, fontweight=weight)

    # Composite reference line — label pinned to top-right of axes (axes coords)
    # so it never collides with bar value labels.
    cd, cp = canon_d(cmp_key)
    ax.axvline(cd, color="#dc2626", linewidth=1.0,
               linestyle=(0, (4, 3)), zorder=1, alpha=0.85)
    ax.text(0.985, 1.02, f"composite d = {cd:+.2f}",
            transform=ax.transAxes,
            ha="right", va="bottom",
            fontsize=7.2, color="#dc2626", fontweight="bold")

    ax.axvline(0, color="#333", linewidth=0.8, zorder=1)
    ax.set_yticks(ys)
    ax.set_yticklabels(sub["item"].tolist(), fontsize=8.5)
    # Bold the highlighted item's y-tick label.
    for tl, item_name in zip(ax.get_yticklabels(), sub["item"].tolist()):
        if item_name == HIGHLIGHT_ITEM:
            tl.set_fontweight("bold")
            tl.set_color("#92400e")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(-0.7, len(sub) - 0.2)
    ax.tick_params(axis="x", length=2.5, color="#888", labelsize=7)
    ax.tick_params(axis="y", length=0)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.spines["left"].set_color("#888")
    ax.spines["bottom"].set_color("#888")
    ax.set_title(cmp_label, fontsize=10, fontweight="bold", loc="left")

# Title and footer
fig.text(0.03, 0.952,
         "Item-Level Decomposition — Belief in Inevitable Conflict",
         fontsize=13, fontweight="bold", ha="left")
fig.text(0.03, 0.928,
         "Each bar = item-level Cohen's d. All items oriented so higher d = MORE belief in conflict.",
         fontsize=8.5, color="#444")
fig.text(0.03, 0.910,
         "Black brackets = 95% CI. Red dashed line (top-right of each panel) = composite d (corrected direction).",
         fontsize=8.5, color="#444")
fig.text(0.03, 0.892,
         "Amber-highlighted row (\"Differences divide society\") is the only item where Estonian and Russian within-group changes are BOTH significant and OPPOSITE in direction.",
         fontsize=8, color="#92400e", style="italic")

fig.text(0.03, 0.060,
         "Direction handling per item: Q63_1 / Q63_2 inverted via 5−raw (so display 4 = strongly agree to conflict-positive statement);",
         fontsize=7, color="#555")
fig.text(0.03, 0.040,
         "Q63_3 / Q63_4 shown raw (raw 4 = strongly disagree with conflict-negative statement = high conflict belief).",
         fontsize=7, color="#555")
fig.text(0.03, 0.020,
         "Composite d shown with sign flipped from canonical TSV to align with corrected direction. Significance: *** p<.001, ** p<.01, * p<.05.",
         fontsize=7, color="#555")

out = ROOT / "viz" / "fig_item_decomp_BiC_corrected.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
