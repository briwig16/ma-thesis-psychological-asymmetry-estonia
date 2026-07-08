"""
Superordinate Identity — Distribution Shapes 2020 → 2023
=========================================================
Variant of fig_polarization_density.jpg that shows ONLY the Superordinate
Identity panels (Russian and Estonian respondents). Group ID Patterns row
removed.

Outputs:
  viz/fig_superordinate_density.jpg  (300 DPI)
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


def superord(df, items, reverse_item, scale_max=4):
    sub = df[items].apply(pd.to_numeric, errors="coerce")
    sub = sub.where(sub != 9)
    sub[reverse_item] = (scale_max + 1) - sub[reverse_item]
    raw = sub.mean(axis=1, skipna=True)
    return (scale_max + 1) - raw


def get_superord(group_code, year):
    if year == 2023:
        d = df23[df23["ethnicity_binary"] == group_code]
        return superord(d, ["Q67_2", "Q67_4", "Q67_5"], "Q67_4", 4).dropna()
    d = df20[df20["ethnicity_binary"] == group_code]
    return superord(d, ["K6X5_2", "K6X5_3", "K6X5_4"], "K6X5_3", 4).dropna()


est20_s = get_superord(0, 2020)
est23_s = get_superord(0, 2023)
rus20_s = get_superord(1, 2020)
rus23_s = get_superord(1, 2023)

lev_rus = stats.levene(rus20_s, rus23_s, center="median").pvalue
lev_est = stats.levene(est20_s, est23_s, center="median").pvalue


plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

EST = "#2563eb"
RUS = "#d97706"
LINE_2020 = "#9ca3af"

fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.6), dpi=300, sharey=True)


def kde_overlay(ax, s2020, s2023, color2020, color2023, x_grid,
                label2020, label2023):
    bins = np.arange(min(x_grid) - 0.05, max(x_grid) + 0.05, 0.1)
    ax.hist(s2020, bins=bins, density=True, alpha=0.18, color=color2020,
            zorder=1)
    ax.hist(s2023, bins=bins, density=True, alpha=0.18, color=color2023,
            zorder=1)
    if len(s2020) > 5:
        k20 = stats.gaussian_kde(s2020)
        ax.plot(x_grid, k20(x_grid), color=color2020, linewidth=1.6,
                linestyle=(0, (3, 2)), label=label2020, zorder=3)
    if len(s2023) > 5:
        k23 = stats.gaussian_kde(s2023)
        ax.plot(x_grid, k23(x_grid), color=color2023, linewidth=1.8,
                linestyle="-", label=label2023, zorder=3)
    ax.axvline(s2020.mean(), color=color2020, linewidth=0.9,
               linestyle=":", alpha=0.7, zorder=2)
    ax.axvline(s2023.mean(), color=color2023, linewidth=0.9,
               linestyle=":", alpha=0.9, zorder=2)


xg_s = np.linspace(0.8, 4.2, 400)

kde_overlay(axes[0], rus20_s, rus23_s, LINE_2020, RUS, xg_s,
            "Russian 2020", "Russian 2023")
axes[0].set_title("Russian respondents", fontsize=10, fontweight="bold",
                  loc="left")
axes[0].set_xlim(0.8, 4.2)
axes[0].legend(frameon=False, fontsize=8, loc="upper left")

kde_overlay(axes[1], est20_s, est23_s, LINE_2020, EST, xg_s,
            "Estonian 2020", "Estonian 2023")
axes[1].set_title("Estonian respondents", fontsize=10, fontweight="bold",
                  loc="left")
axes[1].set_xlim(0.8, 4.2)
axes[1].legend(frameon=False, fontsize=8, loc="upper left")

for ax in axes:
    ax.set_xlabel("Score (1–4 inverted: 1 = weak, 4 = strong belonging)",
                  fontsize=8.5, color="#444")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=7.5, color="#888")

axes[0].set_ylabel("Density", fontsize=8.5, color="#444")

fig.text(0.05, 0.955,
         "Superordinate Identity — Distribution Shapes 2020 → 2023",
         fontsize=12.5, fontweight="bold", ha="left")

fig.text(0.05, 0.030,
         f"Levene's test for equality of variance, 2020 vs 2023: "
         f"Russians p = {lev_rus:.3f}; Estonians p = {lev_est:.3f}.",
         fontsize=7, color="#555")
fig.text(0.05, 0.010,
         "Dotted vertical lines = group means. Faint bars = histograms "
         "(probability density). Curves = Gaussian KDE.",
         fontsize=7, color="#555")

plt.subplots_adjust(left=0.08, right=0.97, top=0.84, bottom=0.20,
                    wspace=0.12)

out = ROOT / "viz" / "fig_superordinate_density.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
