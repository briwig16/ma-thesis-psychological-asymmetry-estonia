"""
Distribution Plot — Belief in Inevitable Conflict
==================================================
Same visual grammar as fig_polarization_density.jpg (script 25), focused on
the Belief in Inevitable Conflict (BiC) composite.

Why this composite is interesting at the distribution level:

  - Russian respondents: mean shifted UP (3.03 → 3.21, d = +0.32 ***) but SD
    stayed essentially flat (0.57 → 0.58). This is a **uniform upward shift**
    in conflict belief — not polarization.

  - Estonian respondents: mean barely moved (2.78 → 2.72, d = −0.09, ns) but
    SD GREW (0.57 → 0.67). This is the **inverse of the polarization signal
    seen for Russians on Superordinate Identity** — Estonians' BiC beliefs
    dispersed even as the average held steady.

Two panels, one per ethnic group, each overlaying 2020 (open/dashed) and
2023 (solid). Levene's test for variance equality reported in the footnote.

Outputs: viz/fig_bic_density.jpg  (300 DPI, paper-style)
"""

from pathlib import Path

import matplotlib.pyplot as plt
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


# ---------- BiC composite (4 items, 2 reverse-coded) -----------------------
def bic(df, items, reverse_items, scale_max=4):
    sub = df[items].apply(pd.to_numeric, errors="coerce")
    sub = sub.where(sub != 9)
    for it in reverse_items:
        sub[it] = (scale_max + 1) - sub[it]
    return sub.mean(axis=1, skipna=True)

# 2026-04-30: BiC reverse-coding flipped (Option B) so that higher composite
# value = more conflict belief, matching documentation.
est23_bic = bic(df23[df23["ethnicity_binary"] == 0],
                ["Q63_1","Q63_2","Q63_3","Q63_4"], ["Q63_1","Q63_2"], scale_max=4).dropna()
rus23_bic = bic(df23[df23["ethnicity_binary"] == 1],
                ["Q63_1","Q63_2","Q63_3","Q63_4"], ["Q63_1","Q63_2"], scale_max=4).dropna()
est20_bic = bic(df20[df20["ethnicity_binary"] == 0],
                ["K6X1_1","K6X1_2","K6X1_3","K6X1_4"], ["K6X1_1","K6X1_2"], scale_max=4).dropna()
rus20_bic = bic(df20[df20["ethnicity_binary"] == 1],
                ["K6X1_1","K6X1_2","K6X1_3","K6X1_4"], ["K6X1_1","K6X1_2"], scale_max=4).dropna()


# ---------- Diagnostics ----------------------------------------------------
def diag(s):
    return {
        "M": s.mean(), "SD": s.std(ddof=1),
        "IQR": s.quantile(.75) - s.quantile(.25),
        "skew": stats.skew(s, bias=False),
        "kurt": stats.kurtosis(s, bias=False, fisher=True),
        "N": len(s),
    }

print("="*92)
print("BELIEF IN INEVITABLE CONFLICT — distribution diagnostics")
print("(Higher = stronger belief in conflict; scale 1-4)")
print("="*92)
for label, s in [("Rus 2020", rus20_bic), ("Rus 2023", rus23_bic),
                 ("Est 2020", est20_bic), ("Est 2023", est23_bic)]:
    d = diag(s)
    print(f"  {label}: N={d['N']:4d}  M={d['M']:.3f}  SD={d['SD']:.3f}  "
          f"IQR={d['IQR']:.3f}  skew={d['skew']:+.3f}  kurt(excess)={d['kurt']:+.3f}")

lev_rus = stats.levene(rus20_bic, rus23_bic, center="median").pvalue
lev_est = stats.levene(est20_bic, est23_bic, center="median").pvalue
print(f"\nLevene's test for equal variance (2020 vs 2023):")
print(f"  Russian respondents:  p = {lev_rus:.4f}  "
      f"({'sig variance change' if lev_rus < .05 else 'no sig variance change'})")
print(f"  Estonian respondents: p = {lev_est:.4f}  "
      f"({'sig variance change' if lev_est < .05 else 'no sig variance change'})")


# ---------- Plot ------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

EST = "#2563eb"
RUS = "#d97706"
LINE_2020 = "#9ca3af"

fig, axes = plt.subplots(1, 2, figsize=(8.5, 4.0), dpi=300, sharey=True)


def kde_overlay(ax, s2020, s2023, color2023, x_grid, label2020, label2023):
    bins = np.arange(min(x_grid)-0.05, max(x_grid)+0.05, 0.1)
    ax.hist(s2020, bins=bins, density=True, alpha=0.18, color=LINE_2020, zorder=1)
    ax.hist(s2023, bins=bins, density=True, alpha=0.18, color=color2023, zorder=1)
    if len(s2020) > 5:
        k20 = stats.gaussian_kde(s2020)
        ax.plot(x_grid, k20(x_grid), color=LINE_2020, linewidth=1.6,
                linestyle=(0, (3, 2)), label=label2020, zorder=3)
    if len(s2023) > 5:
        k23 = stats.gaussian_kde(s2023)
        ax.plot(x_grid, k23(x_grid), color=color2023, linewidth=1.8,
                linestyle="-", label=label2023, zorder=3)
    ax.axvline(s2020.mean(), color=LINE_2020, linewidth=0.9,
               linestyle=":", alpha=0.7, zorder=2)
    ax.axvline(s2023.mean(), color=color2023, linewidth=0.9,
               linestyle=":", alpha=0.9, zorder=2)


xg = np.linspace(0.8, 4.2, 400)

# Russian panel
kde_overlay(axes[0], rus20_bic, rus23_bic, RUS, xg,
            "Russian 2020", "Russian 2023")
axes[0].set_title("Russian respondents",
                  fontsize=10.5, fontweight="bold", loc="left")
axes[0].set_xlim(0.8, 4.2)
axes[0].legend(frameon=False, fontsize=8, loc="upper left")

# Estonian panel
kde_overlay(axes[1], est20_bic, est23_bic, EST, xg,
            "Estonian 2020", "Estonian 2023")
axes[1].set_title("Estonian respondents",
                  fontsize=10.5, fontweight="bold", loc="left")
axes[1].set_xlim(0.8, 4.2)
axes[1].legend(frameon=False, fontsize=8, loc="upper left")

for ax in axes:
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=7.5, color="#888")
    ax.set_xlabel("Score (1–4: 1 = weak, 4 = strong belief in conflict)",
                  fontsize=8.5, color="#444")
axes[0].set_ylabel("Density", fontsize=9, color="#444")

# Title and subtitle (split across two lines so they fit the figure width)
fig.text(0.05, 0.955, "Belief in Inevitable Conflict — Distribution Shapes 2020 → 2023",
         fontsize=12.5, fontweight="bold", ha="left")
fig.text(0.05, 0.928,
         "Higher scores = stronger belief that ethnic conflict is unavoidable.",
         fontsize=8.5, color="#444")
fig.text(0.05, 0.908,
         "Distribution SHAPES distinguish uniform shifts (mean moves, dispersion stable) from polarization (dispersion grows).",
         fontsize=8.5, color="#444")

fig.text(0.05, 0.045,
         f"Levene's test for equal variance (2020 vs 2023): "
         f"Russian respondents p = {lev_rus:.3f}; Estonian respondents p = {lev_est:.3f}.",
         fontsize=7, color="#555")
fig.text(0.05, 0.020,
         "Dotted vertical lines = group means. Faint bars = histograms (probability density). "
         "Curves = Gaussian KDE.",
         fontsize=7, color="#555")

plt.subplots_adjust(left=0.08, right=0.97, top=0.80, bottom=0.18, wspace=0.12)

out = ROOT / "viz" / "fig_bic_density.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
