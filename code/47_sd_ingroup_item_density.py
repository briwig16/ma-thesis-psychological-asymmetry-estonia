"""
Social Distance: Primary IN-GROUP — Item-Level Distribution Shapes (exploratory)
=====================================================================
Mirror of script 44 (out-group), with the item assignment FLIPPED:

  - Estonians rate Estonian-speakers (in-group): Q57_2 / Q58_2 / Q59_2
                                                 (2020: K4X7_2 / K4X8_2 / K4X9_2)
  - Russians  rate Russian-speakers  (in-group): Q57_1 / Q58_1 / Q59_1
                                                 (2020: K4X7_1 / K4X8_1 / K4X9_1)

Direction: scale 1–5, NO reverse coding. Higher = more in-group social distance.

Output: viz/fig_sd_ingroup_item_density.jpg  (300 DPI)
"""

from pathlib import Path

import matplotlib.pyplot as plt
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
    return s.where(s != dk).dropna().astype(float)


# (label, est23, rus23, est20, rus20)  — note FLIPPED suffix vs out-group script
ITEMS = [
    ("Neighbors",          "Q57_2", "Q57_1", "K4X7_2", "K4X7_1"),
    ("Work / study",       "Q58_2", "Q58_1", "K4X8_2", "K4X8_1"),
    ("Marriage in family", "Q59_2", "Q59_1", "K4X9_2", "K4X9_1"),
]


def block(df, eth_val, year):
    sub = df[df["ethnicity_binary"] == eth_val]
    out = {}
    for label, e23, r23, e20, r20 in ITEMS:
        if eth_val == 0:
            var = e23 if year == "23" else e20
        else:
            var = r23 if year == "23" else r20
        out[label] = to_num(sub[var])
    return out

rus20 = block(df20, 1, "20")
rus23 = block(df23, 1, "23")
est20 = block(df20, 0, "20")
est23 = block(df23, 0, "23")


# ---------- Diagnostics -----------------------------------------------------
print("="*92)
print("SD: PRIMARY IN-GROUP (exploratory) — item-level diagnostics")
print("(All items: higher = more in-group social distance, scale 1-5)")
print("(Estonians rate Estonian-speakers; Russians rate Russian-speakers)")
print("="*92)
for label, e23c, r23c, e20c, r20c in ITEMS:
    print(f"\n  {label}")
    print(f"    Est items: {e20c} (2020) / {e23c} (2023)   "
          f"Rus items: {r20c} (2020) / {r23c} (2023)")
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

fig, axes = plt.subplots(2, 3, figsize=(11.0, 7.5), dpi=300, sharey="row")

xg = np.linspace(0.5, 5.5, 500)
bin_edges = np.array([0.5, 1.5, 2.5, 3.5, 4.5, 5.5])
centers = np.array([1, 2, 3, 4, 5], dtype=float)
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


# Top row: Russian respondents — rate Russian-speakers (in-group)
for col, (label, e23, r23, e20, r20) in enumerate(ITEMS):
    ax = axes[0, col]
    panel(ax, rus20[label], rus23[label], RUS, "Russian 2020", "Russian 2023")
    ax.set_title(f"{label}\n{r20}  →  {r23}",
                 fontsize=10, fontweight="bold", loc="left", pad=8,
                 linespacing=1.4)
    if col == 0:
        ax.set_ylabel("Density", fontsize=9, color="#444")
    ax.set_xlim(0.4, 5.6)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xticklabels(["1", "2", "3", "4", "5"])
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")

# Bottom row: Estonian respondents — rate Estonian-speakers (in-group)
for col, (label, e23, r23, e20, r20) in enumerate(ITEMS):
    ax = axes[1, col]
    panel(ax, est20[label], est23[label], EST, "Estonian 2020", "Estonian 2023")
    ax.set_title(f"{label}\n{e20}  →  {e23}",
                 fontsize=10, fontweight="bold", loc="left", pad=8,
                 linespacing=1.4)
    if col == 0:
        ax.set_ylabel("Density", fontsize=9, color="#444")
    ax.set_xlim(0.4, 5.6)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xticklabels(["1", "2", "3", "4", "5"])
    ax.set_xlabel("Score (1 = no distance, 5 = maximal distance)",
                  fontsize=8.5, color="#444")
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")

# Title and footer
fig.text(0.03, 0.965,
         "SD: Primary IN-Group — Item-Level Distribution Shapes 2020 → 2023 (exploratory)",
         fontsize=13, fontweight="bold", ha="left")
fig.text(0.03, 0.940,
         "Top row: Russian respondents rating Russian-speakers (orange).  "
         "Bottom row: Estonian respondents rating Estonian-speakers (blue).  "
         "Higher x = more reluctance to accept own-group members in that role.",
         fontsize=9, color="#444")

fig.text(0.03, 0.030,
         "Group-specific item codes shown above each panel. Scale 1–5, no reverse coding.",
         fontsize=7, color="#555")
fig.text(0.03, 0.015,
         "Bars are histogram density, curves are Gaussian KDE. Dotted vertical lines mark each year's mean.",
         fontsize=7, color="#555")

plt.subplots_adjust(left=0.06, right=0.985, top=0.88, bottom=0.10,
                    wspace=0.20, hspace=0.55)

out = ROOT / "viz" / "fig_sd_ingroup_item_density.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
