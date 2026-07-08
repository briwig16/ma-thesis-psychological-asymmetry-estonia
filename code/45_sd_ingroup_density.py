"""
Distribution Plot — Social Distance: Primary IN-GROUP (exploratory)
==================================================
Mirror of script 42 (SD: Primary Out-group), but with the item assignment
FLIPPED so each group rates THEIR OWN linguistic group instead of the
out-group:

  - Estonian respondents rate Estonian-speakers: Q57_2, Q58_2, Q59_2
                                                 (2020: K4X7_2, K4X8_2, K4X9_2)
  - Russian respondents rate Russian-speakers:   Q57_1, Q58_1, Q59_1
                                                 (2020: K4X7_1, K4X8_1, K4X9_1)

This is a new, exploratory composite — NOT in the canonical effect-size TSV.
Built to gauge whether in-group social distance is worth a deeper look.

Direction: scale 1–5, no reverse coding. Higher = more reluctance to accept
in-group members in everyday social roles.

Outputs: viz/fig_sd_ingroup_density.jpg  (300 DPI)
"""

from pathlib import Path

import math
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


# ---------- SD In-group composite ------------------------------------------
def sd_composite(df, items):
    sub = df[items].apply(pd.to_numeric, errors="coerce")
    sub = sub.where(sub != 9)
    return sub.mean(axis=1, skipna=True)

# Estonian respondents rate Estonian-speakers (their in-group)
est23 = sd_composite(df23[df23["ethnicity_binary"] == 0],
                     ["Q57_2", "Q58_2", "Q59_2"]).dropna()
est20 = sd_composite(df20[df20["ethnicity_binary"] == 0],
                     ["K4X7_2", "K4X8_2", "K4X9_2"]).dropna()

# Russian respondents rate Russian-speakers (their in-group)
rus23 = sd_composite(df23[df23["ethnicity_binary"] == 1],
                     ["Q57_1", "Q58_1", "Q59_1"]).dropna()
rus20 = sd_composite(df20[df20["ethnicity_binary"] == 1],
                     ["K4X7_1", "K4X8_1", "K4X9_1"]).dropna()


# ---------- Diagnostics + composite-level d's ------------------------------
def diag(s):
    return {
        "M": s.mean(), "SD": s.std(ddof=1),
        "IQR": s.quantile(.75) - s.quantile(.25),
        "skew": stats.skew(s, bias=False),
        "kurt": stats.kurtosis(s, bias=False, fisher=True),
        "N": len(s),
    }

def cohens_d_ci(m1, sd1, n1, m2, sd2, n2):
    s = math.sqrt((sd1**2 + sd2**2) / 2)
    if s == 0: return np.nan, np.nan, np.nan
    d = (m1 - m2) / s
    se = math.sqrt((n1 + n2) / (n1 * n2) + d**2 / (2 * (n1 + n2 - 2)))
    return d, d - 1.96 * se, d + 1.96 * se

def welch_p(a, b):
    return float(stats.ttest_ind(a, b, equal_var=False).pvalue)


print("="*92)
print("SD: PRIMARY IN-GROUP (exploratory) — distribution diagnostics")
print("(Higher = more social distance from one's OWN linguistic group; scale 1-5)")
print("(Estonians rate Estonian-speakers; Russians rate Russian-speakers)")
print("="*92)
for label, s in [("Rus 2020", rus20), ("Rus 2023", rus23),
                 ("Est 2020", est20), ("Est 2023", est23)]:
    d = diag(s)
    print(f"  {label}: N={d['N']:4d}  M={d['M']:.3f}  SD={d['SD']:.3f}  "
          f"IQR={d['IQR']:.3f}  skew={d['skew']:+.3f}  kurt={d['kurt']:+.3f}")

# Composite-level d's
def line(label, m1, sd1, n1, m2, sd2, n2, p):
    d, lo, hi = cohens_d_ci(m1, sd1, n1, m2, sd2, n2)
    star = "***" if p<.001 else "**" if p<.01 else "*" if p<.05 else "ns"
    return f"  {label:<28s}  d = {d:+.3f}  [{lo:+.3f}, {hi:+.3f}]   p = {p:.4f}  {star}"

print("\nComposite-level Cohen's d (root-mean-square SD), 95% CI, Welch's p:")
print(line("Between-group, 2020 (Est−Rus)",
           diag(est20)["M"], diag(est20)["SD"], diag(est20)["N"],
           diag(rus20)["M"], diag(rus20)["SD"], diag(rus20)["N"],
           welch_p(est20, rus20)))
print(line("Between-group, 2023 (Est−Rus)",
           diag(est23)["M"], diag(est23)["SD"], diag(est23)["N"],
           diag(rus23)["M"], diag(rus23)["SD"], diag(rus23)["N"],
           welch_p(est23, rus23)))
print(line("Within Estonian (2023−2020)",
           diag(est23)["M"], diag(est23)["SD"], diag(est23)["N"],
           diag(est20)["M"], diag(est20)["SD"], diag(est20)["N"],
           welch_p(est23, est20)))
print(line("Within Russian  (2023−2020)",
           diag(rus23)["M"], diag(rus23)["SD"], diag(rus23)["N"],
           diag(rus20)["M"], diag(rus20)["SD"], diag(rus20)["N"],
           welch_p(rus23, rus20)))

lev_rus = stats.levene(rus20, rus23, center="median").pvalue
lev_est = stats.levene(est20, est23, center="median").pvalue
print(f"\nLevene's test for equal variance (2020 vs 2023):")
print(f"  Russian:  p = {lev_rus:.4f}  "
      f"({'sig variance change' if lev_rus < .05 else 'no sig variance change'})")
print(f"  Estonian: p = {lev_est:.4f}  "
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


xg = np.linspace(0.8, 5.2, 400)

# Russian panel — rate Russian-speakers (in-group)
kde_overlay(axes[0], rus20, rus23, RUS, xg,
            "Russian 2020", "Russian 2023")
axes[0].set_title("Russian respondents (rating Russian-speakers)",
                  fontsize=10.5, fontweight="bold", loc="left")
axes[0].set_xlim(0.8, 5.2)
axes[0].legend(frameon=False, fontsize=8, loc="upper right")

# Estonian panel — rate Estonian-speakers (in-group)
kde_overlay(axes[1], est20, est23, EST, xg,
            "Estonian 2020", "Estonian 2023")
axes[1].set_title("Estonian respondents (rating Estonian-speakers)",
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
fig.text(0.05, 0.955,
         "Social Distance: Primary IN-Group — Distribution Shapes 2020 → 2023",
         fontsize=12.5, fontweight="bold", ha="left")
fig.text(0.05, 0.928,
         "Higher scores = more reluctance to accept members of one's OWN linguistic group as neighbor, coworker / classmate, or family member.",
         fontsize=8.5, color="#444")
fig.text(0.05, 0.908,
         "Exploratory variable — items mirror SD: Primary Out-group with the in/out group flipped.",
         fontsize=8.5, color="#444")

fig.text(0.05, 0.045,
         f"Levene's test for equal variance (2020 vs 2023): "
         f"Russian p = {lev_rus:.3f}; Estonian p = {lev_est:.3f}.",
         fontsize=7, color="#555")
fig.text(0.05, 0.020,
         "Dotted vertical lines = group means. Faint bars = histograms (probability density). Curves = Gaussian KDE.",
         fontsize=7, color="#555")

plt.subplots_adjust(left=0.08, right=0.97, top=0.80, bottom=0.18, wspace=0.12)

out = ROOT / "viz" / "fig_sd_ingroup_density.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
