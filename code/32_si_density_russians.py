"""
Russian Respondents — Superordinate Identity Items Distribution Shapes
========================================================================
Three-panel KDE + histogram density plot, one panel per Superordinate
Identity item, restricted to Russian respondents. Same visual grammar as
fig_polarization_density.jpg / fig_bic_density.jpg.

Items (inverted to 1–4 scale where 4 = stronger belonging):

  - Q67_2 / K6X5_2: "Pride in Estonian flag"
  - Q67_4 / K6X5_3: "Not feeling second-class" (reverse-coded)
  - Q67_5 / K6X5_4: "Part of Estonian society"

Each panel shows the 2020 distribution (light gray dashed KDE) overlaid
with 2023 (solid orange KDE), with histograms in faint shading. Mean
lines and Levene's test p-values reported per panel.

Output: viz/fig_si_density_russian.jpg  (300 DPI)
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyreadstat
from scipy import stats

ROOT = Path(__file__).parent.parent

# ---------- Load data and item series --------------------------------------
df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"] == 1].copy()    # Russian only

df20, _ = pyreadstat.read_sav(str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"),
                              encoding="latin1")
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"] == 1].copy()


def to_num(s, dk=9):
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s != dk).dropna().astype(float)

def invert(s, scale_max=4):
    return (scale_max + 1) - s

ITEMS = [
    # NOTE on direction handling:
    # - Q67_2 ("flag pride") and Q67_5 ("part of society") are POSITIVELY worded:
    #   raw 1 = strongly agree (= strong belonging). To make "higher = more
    #   belonging" on the chart we invert via 5 - raw.
    # - Q67_4 ("feel second-class") is NEGATIVELY worded: raw 4 = strongly
    #   DISAGREE feeling second-class (= strong belonging). The raw direction
    #   already aligns with the chart's "higher = more belonging" convention,
    #   so we DO NOT invert. (Equivalently: this matches the double-inversion
    #   of reverse-coding for the composite plus inverting the composite for
    #   visualization, which nets out to "use raw value.")
    {
        "label": "Pride in Estonian flag",
        "code23": "Q67_2", "code20": "K6X5_2",
        "s2020": invert(to_num(df20["K6X5_2"])),
        "s2023": invert(to_num(df23["Q67_2"])),
    },
    {
        "label": "Not feeling second-class",
        "code23": "Q67_4", "code20": "K6X5_3",
        "s2020": to_num(df20["K6X5_3"]),    # raw — direction already aligns
        "s2023": to_num(df23["Q67_4"]),
    },
    {
        "label": "Part of Estonian society",
        "code23": "Q67_5", "code20": "K6X5_4",
        "s2020": invert(to_num(df20["K6X5_4"])),
        "s2023": invert(to_num(df23["Q67_5"])),
    },
]


# ---------- Diagnostics ----------------------------------------------------
def diag(s):
    return {"M": s.mean(), "SD": s.std(ddof=1),
            "IQR": s.quantile(.75) - s.quantile(.25),
            "skew": stats.skew(s, bias=False),
            "kurt": stats.kurtosis(s, bias=False, fisher=True),
            "N": len(s)}

print("="*92)
print("RUSSIAN RESPONDENTS — Superordinate Identity items, distribution diagnostics")
print("(All items inverted; higher = more belonging on a 1–4 scale)")
print("="*92)
for it in ITEMS:
    print(f"\n  {it['code20']} / {it['code23']} — {it['label']}")
    for tag, s in [("2020", it["s2020"]), ("2023", it["s2023"])]:
        d = diag(s)
        print(f"    Russian {tag}: N={d['N']:4d}  M={d['M']:.3f}  SD={d['SD']:.3f}  "
              f"IQR={d['IQR']:.3f}  skew={d['skew']:+.3f}  kurt={d['kurt']:+.3f}")
    lev = stats.levene(it["s2020"], it["s2023"], center="median").pvalue
    p   = stats.ttest_ind(it["s2023"], it["s2020"], equal_var=False).pvalue
    s_pool = np.sqrt((it["s2020"].std(ddof=1)**2 + it["s2023"].std(ddof=1)**2)/2)
    d   = (it["s2023"].mean() - it["s2020"].mean()) / s_pool
    it["lev"] = lev; it["p"] = p; it["d"] = d
    print(f"    Levene's p = {lev:.4f};  Welch's t-test p = {p:.4f};  d = {d:+.3f}")


# ---------- Plot ------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

LINE_2020 = "#9ca3af"
RUS       = "#d97706"

fig, axes = plt.subplots(1, 3, figsize=(11.0, 5.4), dpi=300, sharey=True)

xg = np.linspace(0.5, 4.5, 400)


def kde_overlay(ax, s2020, s2023, label2020, label2023):
    # Likert items take integer values 1-4 only. Both years' bars are
    # centered on the same integer position (overlapping), with semi-
    # transparency so both remain visible regardless of which is taller.
    bin_edges = np.array([0.5, 1.5, 2.5, 3.5, 4.5])
    centers = np.array([1, 2, 3, 4], dtype=float)
    BAR_W = 0.33

    h2020, _ = np.histogram(s2020, bins=bin_edges, density=True)
    h2023, _ = np.histogram(s2023, bins=bin_edges, density=True)

    # 2020 first (behind), 2023 second (front) — both at same x, semi-transparent
    ax.bar(centers, h2020, width=BAR_W, align="center",
           color=LINE_2020, alpha=0.55, edgecolor="none", zorder=1)
    ax.bar(centers, h2023, width=BAR_W, align="center",
           color=RUS, alpha=0.50, edgecolor="none", zorder=2)
    if len(s2020) > 5:
        k = stats.gaussian_kde(s2020)
        ax.plot(xg, k(xg), color=LINE_2020, linewidth=1.6,
                linestyle=(0, (3, 2)), label=label2020, zorder=3)
    if len(s2023) > 5:
        k = stats.gaussian_kde(s2023)
        ax.plot(xg, k(xg), color=RUS, linewidth=1.8,
                linestyle="-", label=label2023, zorder=3)
    ax.axvline(s2020.mean(), color=LINE_2020, linewidth=0.9,
               linestyle=":", alpha=0.7, zorder=2)
    ax.axvline(s2023.mean(), color=RUS, linewidth=0.9,
               linestyle=":", alpha=0.9, zorder=2)


for ax, it in zip(axes, ITEMS):
    kde_overlay(ax, it["s2020"], it["s2023"], "Russian 2020", "Russian 2023")
    # Two-line panel title (label on top, item codes underneath, both via set_title
    # so matplotlib reserves correct space and they never collide with the figure
    # suptitle above or the legend below).
    ax.set_title(f"{it['label']}\n{it['code20']}  →  {it['code23']}",
                 fontsize=10.5, fontweight="bold", loc="left", pad=10,
                 linespacing=1.4)
    ax.set_xlim(0.4, 4.6)
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xticklabels(["1", "2", "3", "4"])
    ax.set_xlabel("Score (1–4: 1 = weak, 4 = strong belonging)",
                  fontsize=8.5, color="#444")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=8.5, color="#888")

axes[0].set_ylabel("Density", fontsize=9, color="#444")

fig.text(0.04, 0.970,
         "Russian Respondents — Superordinate Identity Items, Distribution Shapes 2020 → 2023",
         fontsize=12.5, fontweight="bold", ha="left")
fig.text(0.04, 0.945,
         "Higher scores = stronger belonging. Comparing distribution SHAPES (not just means) reveals uniform shifts vs. polarization.",
         fontsize=8.5, color="#444")

fig.text(0.04, 0.045,
         f"Levene's tests for equal variance (2020 vs 2023):  "
         f"Pride in flag p = {ITEMS[0]['lev']:.3f};  Not second-class p = {ITEMS[1]['lev']:.3f};  Part of society p = {ITEMS[2]['lev']:.3f}.",
         fontsize=7, color="#555")
fig.text(0.04, 0.020,
         "Dotted vertical lines = group means. Bars = histogram density. Curves = Gaussian KDE. Q67_4/K6X5_3 shown in raw direction (raw 4 = strongly disagree feeling second-class = strong belonging).",
         fontsize=7, color="#555")

plt.subplots_adjust(left=0.06, right=0.98, top=0.83, bottom=0.16, wspace=0.18)

out = ROOT / "viz" / "fig_si_density_russian.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
