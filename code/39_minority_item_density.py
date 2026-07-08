"""
Minority Inclusion Support — Item-Level Distribution Shapes
================================================================
Two-row × 3-column figure: top row = Russian, bottom row = Estonian, each
column = one of the three Q68 / K6X6 items. Same visual grammar as the BiC
item-density figure: KDE + integer-centered overlapping bars.

Direction handling (so every panel reads "higher x = MORE support for
minority inclusion"):

  - Q68_1 / K6X6_1 ("Estonia should involve other nationalities in economic life")
        raw 1 = strongly agree (HIGH support).
        INVERT via 5 - raw so display 4 = strongly agree = HIGH support.
  - Q68_2 / K6X6_2 ("...involve in governance")           — INVERT.
  - Q68_3 / K6X6_3 ("...understand the opinions of other nationalities") — INVERT.

Output: viz/fig_minority_item_density.jpg  (300 DPI, both groups in one figure)
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyreadstat
from scipy import stats

ROOT = Path(__file__).parent.parent

# ---------- Load data --------------------------------------------------------
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
    return s.where(s != dk).dropna().astype(float)

def invert(s, scale_max=4):
    return (scale_max + 1) - s


# Item specifications: (label, code23, code20, invert?)
ITEMS = [
    ("Involve in economy",      "Q68_1", "K6X6_1", True),
    ("Involve in governance",   "Q68_2", "K6X6_2", True),
    ("Understand opinions",     "Q68_3", "K6X6_3", True),
]


def get_series(df, var, do_invert):
    s = to_num(df[var])
    return invert(s) if do_invert else s


def block(df, eth_val, code_field):
    sub = df[df["ethnicity_binary"] == eth_val]
    out = {}
    for label, c23, c20, do_inv in ITEMS:
        var = c23 if code_field == "23" else c20
        out[label] = get_series(sub, var, do_inv)
    return out

rus20 = block(df20, 1, "20")
rus23 = block(df23, 1, "23")
est20 = block(df20, 0, "20")
est23 = block(df23, 0, "23")


# ---------- Diagnostics -----------------------------------------------------
print("="*92)
print("MINORITY INCLUSION SUPPORT — item-level diagnostics")
print("(All items oriented so higher = MORE support for inclusion)")
print("="*92)
for label, c23, c20, do_inv in ITEMS:
    print(f"\n  {c20} / {c23} — {label} {'(inverted: 5-raw)' if do_inv else '(raw)'}")
    for tag, s in [("Rus 2020", rus20[label]), ("Rus 2023", rus23[label]),
                   ("Est 2020", est20[label]), ("Est 2023", est23[label])]:
        print(f"    {tag}: N={len(s):4d}  M={s.mean():.3f}  SD={s.std(ddof=1):.3f}")
    lev_r = stats.levene(rus20[label], rus23[label], center="median").pvalue
    lev_e = stats.levene(est20[label], est23[label], center="median").pvalue
    p_r = stats.ttest_ind(rus23[label], rus20[label], equal_var=False).pvalue
    p_e = stats.ttest_ind(est23[label], est20[label], equal_var=False).pvalue
    print(f"    Russian: p = {p_r:.4f},  Levene's p = {lev_r:.4f}")
    print(f"    Estonian: p = {p_e:.4f},  Levene's p = {lev_e:.4f}")


# ---------- Plot ------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

LINE_2020 = "#9ca3af"
RUS = "#d97706"
EST = "#2563eb"

fig, axes = plt.subplots(2, 3, figsize=(13.5, 8.0), dpi=300, sharey="row")

xg = np.linspace(0.5, 4.5, 400)
bin_edges = np.array([0.5, 1.5, 2.5, 3.5, 4.5])
centers = np.array([1, 2, 3, 4], dtype=float)
BAR_W = 0.33


def panel(ax, s2020, s2023, color2023, label2020, label2023):
    h20, _ = np.histogram(s2020, bins=bin_edges, density=True)
    h23, _ = np.histogram(s2023, bins=bin_edges, density=True)
    ax.bar(centers, h20, width=BAR_W, align="center",
           color=LINE_2020, alpha=0.55, edgecolor="none", zorder=1)
    ax.bar(centers, h23, width=BAR_W, align="center",
           color=color2023, alpha=0.50, edgecolor="none", zorder=2)
    if len(s2020) > 5:
        k = stats.gaussian_kde(s2020)
        ax.plot(xg, k(xg), color=LINE_2020, linewidth=1.4,
                linestyle=(0, (3, 2)), label=label2020, zorder=3)
    if len(s2023) > 5:
        k = stats.gaussian_kde(s2023)
        ax.plot(xg, k(xg), color=color2023, linewidth=1.6,
                linestyle="-", label=label2023, zorder=3)
    ax.axvline(s2020.mean(), color=LINE_2020, linewidth=0.9,
               linestyle=":", alpha=0.7, zorder=2)
    ax.axvline(s2023.mean(), color=color2023, linewidth=0.9,
               linestyle=":", alpha=0.9, zorder=2)


# Top row: Russian respondents
for col, (label, c23, c20, do_inv) in enumerate(ITEMS):
    ax = axes[0, col]
    panel(ax, rus20[label], rus23[label], RUS, "Russian 2020", "Russian 2023")
    ax.set_title(f"{label}\n{c20}  →  {c23}{' (inv.)' if do_inv else ''}",
                 fontsize=10, fontweight="bold", loc="left", pad=8,
                 linespacing=1.4)
    if col == 0:
        ax.set_ylabel("Density", fontsize=9, color="#444")
    ax.set_xlim(0.4, 4.6)
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xticklabels(["1", "2", "3", "4"])
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")

# Bottom row: Estonian respondents
for col, (label, c23, c20, do_inv) in enumerate(ITEMS):
    ax = axes[1, col]
    panel(ax, est20[label], est23[label], EST, "Estonian 2020", "Estonian 2023")
    ax.set_title(f"{label}\n{c20}  →  {c23}{' (inv.)' if do_inv else ''}",
                 fontsize=10, fontweight="bold", loc="left", pad=8,
                 linespacing=1.4)
    if col == 0:
        ax.set_ylabel("Density", fontsize=9, color="#444")
    ax.set_xlim(0.4, 4.6)
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xticklabels(["1", "2", "3", "4"])
    ax.set_xlabel("Score (1 = weak, 4 = strong support for inclusion)",
                  fontsize=8.5, color="#444")
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")

# Title and footer
fig.text(0.03, 0.968,
         "Minority Inclusion Support — Item-Level Distribution Shapes 2020 → 2023",
         fontsize=13, fontweight="bold", ha="left")
fig.text(0.03, 0.945,
         "Top row: Russian respondents (orange).  Bottom row: Estonian respondents (blue).",
         fontsize=9, color="#444")
fig.text(0.03, 0.927,
         "All items oriented so higher x = stronger endorsement of involving other nationalities.",
         fontsize=9, color="#444")

fig.text(0.03, 0.030,
         "All three items are inverted via 5 − raw so display 4 = 'strongly agree' with the inclusion-positive statement.",
         fontsize=7, color="#555")
fig.text(0.03, 0.015,
         "Bars are histogram density, curves are Gaussian KDE. Dotted vertical lines mark each year's mean.",
         fontsize=7, color="#555")

plt.subplots_adjust(left=0.06, right=0.985, top=0.86, bottom=0.10,
                    wspace=0.20, hspace=0.65)

out = ROOT / "viz" / "fig_minority_item_density.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
