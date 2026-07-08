"""
Item-Level Decomposition — SD: General Out-group
==================================================================================
Companion to scripts 35 / 40 / 43, with one structural change: SD General has
DIFFERENT item sets in 2020 (3 items, "new immigrants") and 2023 (6 items,
"other Europeans" + "non-Europeans"). Item-level d's cannot be paired across
years, so the within-group panels are computed at the COMPOSITE level only.

Layout (2x2):
  Top-left:     Between-group 2020 (3 items, K4X7_3 / K4X8_3 / K4X9_3)
  Top-right:    Between-group 2023 (6 items, Q57_4..Q59_5)
  Bottom-left:  Within Estonian (2020 → 2023) — composite-level only
  Bottom-right: Within Russian  (2020 → 2023) — composite-level only

Direction: scale 1–5, no reverse coding. Higher = more general out-group distance.

Output: viz/fig_item_decomp_SD_General_Outgroup.jpg  (300 DPI)
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


# ---------- Item series -----------------------------------------------------
ITEMS_2020 = [
    ("Neighbors: new immigrants",  "K4X7_3"),
    ("Work: new immigrants",       "K4X8_3"),
    ("Marriage: new immigrants",   "K4X9_3"),
]

ITEMS_2023 = [
    ("Neighbors: other Europeans", "Q57_4"),
    ("Neighbors: non-Europeans",   "Q57_5"),
    ("Work: other Europeans",      "Q58_4"),
    ("Work: non-Europeans",        "Q58_5"),
    ("Marriage: other Europeans",  "Q59_4"),
    ("Marriage: non-Europeans",    "Q59_5"),
]

def fetch(df, ethval, code):
    sub = df[df["ethnicity_binary"] == ethval]
    return to_num(sub[code])

# Between-group d's per year
between_2020 = []
for label, code in ITEMS_2020:
    e = fetch(df20, 0, code); r = fetch(df20, 1, code)
    me, sde, ne = m_sd_n(e); mr, sdr, nr = m_sd_n(r)
    d, lo, hi = cohens_d_ci(me, sde, ne, mr, sdr, nr)
    p = welch_p(e, r)
    between_2020.append((label, d, lo, hi, p))

between_2023 = []
for label, code in ITEMS_2023:
    e = fetch(df23, 0, code); r = fetch(df23, 1, code)
    me, sde, ne = m_sd_n(e); mr, sdr, nr = m_sd_n(r)
    d, lo, hi = cohens_d_ci(me, sde, ne, mr, sdr, nr)
    p = welch_p(e, r)
    between_2023.append((label, d, lo, hi, p))

print("="*92)
print("SD: GENERAL OUT-GROUP — item-level d's (between-group only)")
print("(Higher d means more out-group social distance)")
print("="*92)
print("\nBetween-group 2020 (3 items):")
for label, d, lo, hi, p in between_2020:
    print(f"  {label:<32s}  d = {d:+.3f}  [{lo:+.3f}, {hi:+.3f}]   p = {p:.4f}  {stars(p)}")
print("\nBetween-group 2023 (6 items):")
for label, d, lo, hi, p in between_2023:
    print(f"  {label:<32s}  d = {d:+.3f}  [{lo:+.3f}, {hi:+.3f}]   p = {p:.4f}  {stars(p)}")


# ---------- Composite reference d (canonical TSV) --------------------------
canon = pd.read_csv(ROOT / "code" / "_effect_sizes.tsv", sep="\t")
def canon_d(comparison):
    if comparison.startswith("between"):
        year = comparison.split()[1]
        sub = canon[(canon["table"]=="between") &
                    (canon["variable"]=="SD: General Out-group") &
                    (canon["comparison"]==year)]
    else:
        grp = comparison.split()[1]
        sub = canon[(canon["table"]=="within") &
                    (canon["variable"]=="SD: General Out-group") &
                    (canon["comparison"]==grp)]
    row = sub.iloc[0]
    return row["d"], row["p"]

print("\nComposite-level d's (canonical TSV):")
for k in ["between 2020", "between 2023", "within Estonian", "within Russian"]:
    d, p = canon_d(k)
    print(f"  {k:<18s}  d = {d:+.3f}   p = {p:.4f}  {stars(p)}")


# ---------- Plot ------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

EST = "#2563eb"; RUS = "#d97706"
LINE_2020 = "#9ca3af"; LINE_2023 = "#1f2937"

fig = plt.figure(figsize=(14.0, 8.4), dpi=300)
gs = gridspec.GridSpec(2, 2, hspace=0.65, wspace=0.50,
                       left=0.20, right=0.985, top=0.78, bottom=0.13,
                       height_ratios=[1.6, 1.0])

# ---- common x-range -------------------------------------------------------
all_d = (
    [d for _, d, *_ in between_2020] +
    [d for _, d, *_ in between_2023] +
    [lo for _, _, lo, _, _ in between_2020] +
    [hi for _, _, _, hi, _ in between_2020] +
    [lo for _, _, lo, _, _ in between_2023] +
    [hi for _, _, _, hi, _ in between_2023] +
    [canon_d(k)[0] for k in ["between 2020", "between 2023",
                              "within Estonian", "within Russian"]]
)
d_max = max(max(abs(x) for x in all_d), 1.0)
xmin, xmax = -d_max - 0.45, d_max + 0.45

def draw_bars(ax, rows, color):
    """rows = [(label, d, lo, hi, p), ...]"""
    ys = np.arange(len(rows))[::-1]
    for i, (label, d, lo, hi, p) in enumerate(rows):
        sig = (p is not None) and pd.notna(p) and (p < 0.05)
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
        offset = 0.03 if d >= 0 else -0.03
        ha = "left" if d >= 0 else "right"
        col = "#111" if sig else "#777"
        weight = "bold" if sig else "normal"
        ax.text(d + offset, y, f"{d:+.2f} {stars(p)}",
                ha=ha, va="center", fontsize=7.4,
                color=col, fontweight=weight)
    ax.set_yticks(ys)
    ax.set_yticklabels([r[0] for r in rows], fontsize=8.2)
    ax.set_ylim(-0.7, len(rows) - 0.2)


# ----- Top-left: Between-group 2020 (3 items) -----
ax = fig.add_subplot(gs[0, 0])
draw_bars(ax, between_2020, LINE_2020)
cd, _ = canon_d("between 2020")
ax.axvline(cd, color="#dc2626", linewidth=1.0,
           linestyle=(0, (4, 3)), zorder=1, alpha=0.85)
ax.text(0.985, 1.02, f"composite d = {cd:+.2f}",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=7.2, color="#dc2626", fontweight="bold")
ax.axvline(0, color="#333", linewidth=0.8, zorder=1)
ax.set_xlim(xmin, xmax)
ax.tick_params(axis="x", length=2.5, color="#888", labelsize=7)
ax.tick_params(axis="y", length=0)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
ax.spines["left"].set_color("#888"); ax.spines["bottom"].set_color("#888")
ax.set_title("Between-group, 2020   (3 items)",
             fontsize=10, fontweight="bold", loc="left")

# ----- Top-right: Between-group 2023 (6 items) -----
ax = fig.add_subplot(gs[0, 1])
draw_bars(ax, between_2023, LINE_2023)
cd, _ = canon_d("between 2023")
ax.axvline(cd, color="#dc2626", linewidth=1.0,
           linestyle=(0, (4, 3)), zorder=1, alpha=0.85)
ax.text(0.985, 1.02, f"composite d = {cd:+.2f}",
        transform=ax.transAxes, ha="right", va="bottom",
        fontsize=7.2, color="#dc2626", fontweight="bold")
ax.axvline(0, color="#333", linewidth=0.8, zorder=1)
ax.set_xlim(xmin, xmax)
ax.tick_params(axis="x", length=2.5, color="#888", labelsize=7)
ax.tick_params(axis="y", length=0)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
ax.spines["left"].set_color("#888"); ax.spines["bottom"].set_color("#888")
ax.set_title("Between-group, 2023   (6 items)",
             fontsize=10, fontweight="bold", loc="left")

# ----- Bottom-left: Within Estonian (composite-only) -----
ax = fig.add_subplot(gs[1, 0])
cd, cp = canon_d("within Estonian")
draw_bars(ax, [("Composite (3-item 2020 vs. 6-item 2023)", cd, np.nan, np.nan, cp)], EST)
ax.axvline(0, color="#333", linewidth=0.8, zorder=1)
ax.set_xlim(xmin, xmax)
ax.tick_params(axis="x", length=2.5, color="#888", labelsize=7)
ax.tick_params(axis="y", length=0)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
ax.spines["left"].set_color("#888"); ax.spines["bottom"].set_color("#888")
ax.set_title("Within Estonian, 2020 → 2023   (composite-only)",
             fontsize=10, fontweight="bold", loc="left")

# ----- Bottom-right: Within Russian (composite-only) -----
ax = fig.add_subplot(gs[1, 1])
cd, cp = canon_d("within Russian")
draw_bars(ax, [("Composite (3-item 2020 vs. 6-item 2023)", cd, np.nan, np.nan, cp)], RUS)
ax.axvline(0, color="#333", linewidth=0.8, zorder=1)
ax.set_xlim(xmin, xmax)
ax.tick_params(axis="x", length=2.5, color="#888", labelsize=7)
ax.tick_params(axis="y", length=0)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
ax.spines["left"].set_color("#888"); ax.spines["bottom"].set_color("#888")
ax.set_title("Within Russian, 2020 → 2023   (composite-only)",
             fontsize=10, fontweight="bold", loc="left")

# Title and footer
fig.text(0.03, 0.952,
         "Item-Level Decomposition — Social Distance: General Out-group",
         fontsize=13, fontweight="bold", ha="left")
fig.text(0.03, 0.928,
         "Each bar = item-level Cohen's d. Higher d = MORE social distance from general out-group.",
         fontsize=8.5, color="#444")
fig.text(0.03, 0.910,
         "Black brackets = 95% CI. Red dashed line (top-right of each panel) = composite d from canonical TSV.",
         fontsize=8.5, color="#444")
fig.text(0.03, 0.886,
         "CAVEAT: WITHIN-GROUP item-level pairing not possible — 2020 used a single 'new immigrants' target; 2023 split into 'other Europeans' + 'non-Europeans'.",
         fontsize=8, color="#a0522d", style="italic")
fig.text(0.03, 0.866,
         "Composite-level within-group d shown as a single bar with its known limitation.",
         fontsize=8, color="#a0522d", style="italic")

fig.text(0.03, 0.060,
         "Both groups answered the same items in each year (no group-specific items). Scale 1–5, no reverse coding (higher = more distance).",
         fontsize=7, color="#555")
fig.text(0.03, 0.040,
         "Significance: *** p<.001, ** p<.01, * p<.05.",
         fontsize=7, color="#555")

out = ROOT / "viz" / "fig_item_decomp_SD_General_Outgroup.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
