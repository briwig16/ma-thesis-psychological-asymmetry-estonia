"""
Distribution Plot — Social Distance: General Out-group
==================================================
Same visual grammar as fig_sd_primary_density.jpg (script 42).

Important caveat — items DIFFER across years:
  - 2020: 3 items, all about "new immigrants in last 5 years"
          (K4X7_3, K4X8_3, K4X9_3 — Neighbors, Work, Marriage)
  - 2023: 6 items, split into "other Europeans" + "non-Europeans"
          (Q57_4/Q57_5, Q58_4/Q58_5, Q59_4/Q59_5 — same 3 contexts × 2 targets)

Both groups use the SAME items in each year (no group-specific items).
The 2020 → 2023 within-group comparison is not measuring exactly the same
construct — note this limitation in the methods chapter.

Direction: scale 1–5, no reverse coding. Higher = more general out-group distance.

Outputs: viz/fig_sd_general_density.jpg  (300 DPI)
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


def composite(df, items):
    sub = df[items].apply(pd.to_numeric, errors="coerce").where(lambda x: x != 9)
    return sub.mean(axis=1, skipna=True)

ITEMS_2023 = ["Q57_4", "Q57_5", "Q58_4", "Q58_5", "Q59_4", "Q59_5"]
ITEMS_2020 = ["K4X7_3", "K4X8_3", "K4X9_3"]

est23 = composite(df23[df23["ethnicity_binary"] == 0], ITEMS_2023).dropna()
rus23 = composite(df23[df23["ethnicity_binary"] == 1], ITEMS_2023).dropna()
est20 = composite(df20[df20["ethnicity_binary"] == 0], ITEMS_2020).dropna()
rus20 = composite(df20[df20["ethnicity_binary"] == 1], ITEMS_2020).dropna()


def diag(s):
    return {
        "M": s.mean(), "SD": s.std(ddof=1),
        "IQR": s.quantile(.75) - s.quantile(.25),
        "skew": stats.skew(s, bias=False),
        "kurt": stats.kurtosis(s, bias=False, fisher=True),
        "N": len(s),
    }

print("="*92)
print("SD: GENERAL OUT-GROUP — distribution diagnostics")
print("(Higher = more general-out-group social distance; scale 1-5)")
print("(2020 = 3 items re: 'new immigrants'; 2023 = 6 items re: 'other Europeans' + 'non-Europeans')")
print("="*92)
for label, s in [("Rus 2020", rus20), ("Rus 2023", rus23),
                 ("Est 2020", est20), ("Est 2023", est23)]:
    d = diag(s)
    print(f"  {label}: N={d['N']:4d}  M={d['M']:.3f}  SD={d['SD']:.3f}  "
          f"IQR={d['IQR']:.3f}  skew={d['skew']:+.3f}  kurt={d['kurt']:+.3f}")

lev_rus = stats.levene(rus20, rus23, center="median").pvalue
lev_est = stats.levene(est20, est23, center="median").pvalue
print(f"\nLevene's test for equal variance (2020 vs 2023):")
print(f"  Russian respondents:  p = {lev_rus:.4f}")
print(f"  Estonian respondents: p = {lev_est:.4f}")


# ---------- Plot ------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

EST = "#2563eb"; RUS = "#d97706"; LINE_2020 = "#9ca3af"

fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), dpi=300, sharey=True)


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


xg = np.linspace(0.8, 5.2, 400)

kde_overlay(axes[0], rus20, rus23, RUS, xg, "Russian 2020", "Russian 2023")
axes[0].set_title("Russian respondents",
                  fontsize=10.5, fontweight="bold", loc="left")
axes[0].set_xlim(0.8, 5.2)
axes[0].legend(frameon=False, fontsize=8, loc="upper right")

kde_overlay(axes[1], est20, est23, EST, xg, "Estonian 2020", "Estonian 2023")
axes[1].set_title("Estonian respondents",
                  fontsize=10.5, fontweight="bold", loc="left")
axes[1].set_xlim(0.8, 5.2)
axes[1].legend(frameon=False, fontsize=8, loc="upper right")

for ax in axes:
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=7.5, color="#888")
    ax.set_xlabel("Score (1–5: 1 = no distance / would accept, 5 = maximal distance)",
                  fontsize=8.5, color="#444")
axes[0].set_ylabel("Density", fontsize=9, color="#444")

fig.text(0.04, 0.955,
         "Social Distance: General Out-group — Distribution Shapes 2020 → 2023",
         fontsize=12.5, fontweight="bold", ha="left")
fig.text(0.04, 0.918,
         "Higher scores = more reluctance to accept members of general (non-Russian / non-Estonian) out-groups in everyday social roles.",
         fontsize=8.5, color="#444")
fig.text(0.04, 0.890,
         "CAVEAT: 2020 = 3 items (\"new immigrants\"). 2023 = 6 items (\"other Europeans\" + \"non-Europeans\").",
         fontsize=8, color="#a0522d", style="italic")
fig.text(0.04, 0.866,
         "Within-year comparison meaningful; cross-year measures different construct.",
         fontsize=8, color="#a0522d", style="italic")

fig.text(0.04, 0.050,
         f"Levene's test for equal variance (2020 vs 2023): "
         f"Russian respondents p = {lev_rus:.3f}; Estonian respondents p = {lev_est:.3f}.",
         fontsize=7, color="#555")
fig.text(0.04, 0.022,
         "Dotted vertical lines = group means. Faint bars = histograms (probability density). Curves = Gaussian KDE.",
         fontsize=7, color="#555")

plt.subplots_adjust(left=0.06, right=0.985, top=0.76, bottom=0.20, wspace=0.18)

out = ROOT / "viz" / "fig_sd_general_density.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
