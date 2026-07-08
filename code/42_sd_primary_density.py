"""
Distribution Plot — Social Distance: Primary Out-group
==================================================
Same visual grammar as fig_bic_density.jpg (script 28) and
fig_minority_density.jpg (script 41), focused on the SD: Primary
Out-group composite.

Important:
  - SD: Primary Out-group uses GROUP-SPECIFIC items.
    * Estonian respondents rate Russian-speakers (Q57_1, Q58_1, Q59_1)
    * Russian respondents rate Estonian-speakers (Q57_2, Q58_2, Q59_2)
    2020 equivalents: K4X7_1/K4X8_1/K4X9_1 (Est) and K4X7_2/K4X8_2/K4X9_2 (Rus).
  - Q57_1, Q57_2, Q58_1, Q58_2, Q59_1, Q59_2 are stored as STRINGS in EIM23.csv
    (' ' for missing); coerced via pd.to_numeric(errors='coerce').
  - Scale 1–5: 1 = no distance (would accept), 5 = maximal distance. No
    reverse coding — higher = more distance directly.

Two panels, one per ethnic group, each overlaying 2020 (open/dashed) and
2023 (solid). Each group's panel reflects their own primary out-group items.

Outputs: viz/fig_sd_primary_density.jpg  (300 DPI, paper-style)
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


# ---------- SD Primary composite (group-specific items, no reverse coding) -
def sd_primary(df, items):
    sub = df[items].apply(pd.to_numeric, errors="coerce")
    sub = sub.where(sub != 9)
    return sub.mean(axis=1, skipna=True)

est23_sd = sd_primary(df23[df23["ethnicity_binary"] == 0],
                      ["Q57_1", "Q58_1", "Q59_1"]).dropna()
rus23_sd = sd_primary(df23[df23["ethnicity_binary"] == 1],
                      ["Q57_2", "Q58_2", "Q59_2"]).dropna()
est20_sd = sd_primary(df20[df20["ethnicity_binary"] == 0],
                      ["K4X7_1", "K4X8_1", "K4X9_1"]).dropna()
rus20_sd = sd_primary(df20[df20["ethnicity_binary"] == 1],
                      ["K4X7_2", "K4X8_2", "K4X9_2"]).dropna()


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
print("SD: PRIMARY OUT-GROUP — distribution diagnostics")
print("(Higher = more social distance from primary out-group; scale 1-5)")
print("(Estonians rate Russian-speakers; Russians rate Estonian-speakers)")
print("="*92)
for label, s in [("Rus 2020", rus20_sd), ("Rus 2023", rus23_sd),
                 ("Est 2020", est20_sd), ("Est 2023", est23_sd)]:
    d = diag(s)
    print(f"  {label}: N={d['N']:4d}  M={d['M']:.3f}  SD={d['SD']:.3f}  "
          f"IQR={d['IQR']:.3f}  skew={d['skew']:+.3f}  kurt(excess)={d['kurt']:+.3f}")

lev_rus = stats.levene(rus20_sd, rus23_sd, center="median").pvalue
lev_est = stats.levene(est20_sd, est23_sd, center="median").pvalue
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

fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6), dpi=300, sharey=True)


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

# Russian panel — rate Estonian-speakers
kde_overlay(axes[0], rus20_sd, rus23_sd, RUS, xg,
            "Russian 2020", "Russian 2023")
axes[0].set_title("Russian respondents (rating Estonian-speakers)",
                  fontsize=10.5, fontweight="bold", loc="left")
axes[0].set_xlim(0.8, 5.2)
axes[0].legend(frameon=False, fontsize=8, loc="upper right")

# Estonian panel — rate Russian-speakers
kde_overlay(axes[1], est20_sd, est23_sd, EST, xg,
            "Estonian 2020", "Estonian 2023")
axes[1].set_title("Estonian respondents (rating Russian-speakers)",
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

# Title and subtitle
fig.text(0.04, 0.955,
         "Social Distance: Primary Out-group — Distribution Shapes 2020 → 2023",
         fontsize=12.5, fontweight="bold", ha="left")
fig.text(0.04, 0.918,
         "Higher scores = more reluctance to accept the primary out-group as neighbor, coworker / classmate, or family member.",
         fontsize=8.5, color="#444")
fig.text(0.04, 0.890,
         "Each group's panel uses their OWN primary-out-group items "
         "(Est rate Russian-speakers; Rus rate Estonian-speakers).",
         fontsize=8.5, color="#444")

fig.text(0.04, 0.050,
         f"Levene's test for equal variance (2020 vs 2023): "
         f"Russian respondents p = {lev_rus:.3f}; Estonian respondents p = {lev_est:.3f}.",
         fontsize=7, color="#555")
fig.text(0.04, 0.022,
         "Dotted vertical lines = group means. Faint bars = histograms (probability density). "
         "Curves = Gaussian KDE.",
         fontsize=7, color="#555")

plt.subplots_adjust(left=0.06, right=0.985, top=0.80, bottom=0.20, wspace=0.18)

out = ROOT / "viz" / "fig_sd_primary_density.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
