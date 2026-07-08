"""
Russian Respondents — Superordinate Identity Items Scatter (2020 vs 2023)
==========================================================================
Per-respondent scatter (jittered strip plot) for each of the 3 Superordinate
Identity items, restricted to Russian respondents, comparing 2020 to 2023
side-by-side within each panel.

The 3 items (after the 2026-03-19 decision to drop Q67_1):

  - Q67_2 / K6X5_2: "You feel proud when you see the Estonian flag flying"
  - Q67_4 / K6X5_3: "You feel like a second-class citizen in Estonian society"
                    (REVERSED so higher = NOT feeling second-class = belonging)
  - Q67_5 / K6X5_4: "You feel that you are part of Estonian society"

All three items are displayed on the SAME inverted convention as the composite:
higher = stronger belonging on a 1–4 visualization scale (where 1 = weak,
4 = strong belonging). Q67_4 is reverse-coded; Q67_2 and Q67_5 are inverted
visually so the upward direction means "more belonging" consistently.

Each Russian respondent is shown as a single jittered dot. Means and 95%
CIs are overlaid in black. Sample sizes per panel are annotated.

Outputs:
  viz/fig_si_scatter_russian.jpg  (300 DPI, paper-style)
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyreadstat
from scipy import stats

ROOT = Path(__file__).parent.parent
RNG = np.random.default_rng(seed=42)

# ---------- Load both waves -------------------------------------------------
df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"] == 1].copy()    # Russian only

df20, _ = pyreadstat.read_sav(str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"),
                              encoding="latin1")
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"] == 1].copy()


# ---------- Item series ------------------------------------------------------
def to_num(s, dk=9):
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s != dk).dropna().astype(float)

def invert(s, scale_max=4):
    return (scale_max + 1) - s

# Direction handling:
#   - Q67_2 ("flag pride") and Q67_5 ("part of society") are POSITIVELY worded:
#     raw 1 = strongly agree = strong belonging. Invert (5 - raw) so that
#     higher displayed value = stronger belonging.
#   - Q67_4 ("feel second-class") is NEGATIVELY worded: raw 4 = strongly
#     DISAGREE = strong belonging. Raw direction already matches "higher =
#     more belonging" so we use raw values directly (no inversion).

# 2023 (Q67_*)
q67_2_23  = invert(to_num(df23["Q67_2"]))      # raw 1 → 4 (strong belonging)
q67_4_23  = to_num(df23["Q67_4"])              # raw 4 = strongly disagree = strong belonging (no inversion)
q67_5_23  = invert(to_num(df23["Q67_5"]))      # raw 1 → 4 (strong belonging)

# 2020 (K6X5_*)
k6x5_2_20 = invert(to_num(df20["K6X5_2"]))
k6x5_3_20 = to_num(df20["K6X5_3"])             # no inversion
k6x5_4_20 = invert(to_num(df20["K6X5_4"]))

ITEMS = [
    {
        "label": "Pride in Estonian flag",
        "code23": "Q67_2", "code20": "K6X5_2",
        "wording": '"I feel proud when I see the Estonian flag flying"',
        "s2020": k6x5_2_20, "s2023": q67_2_23,
    },
    {
        "label": "Not feeling second-class",
        "code23": "Q67_4", "code20": "K6X5_3",
        "wording": '"I feel like a second-class citizen in Estonian society"\n(higher = strongly DISAGREE = NOT feeling second-class)',
        "s2020": k6x5_3_20, "s2023": q67_4_23,
    },
    {
        "label": "Part of Estonian society",
        "code23": "Q67_5", "code20": "K6X5_4",
        "wording": '"I feel that I am part of Estonian society"',
        "s2020": k6x5_4_20, "s2023": q67_5_23,
    },
]


# ---------- Diagnostics -----------------------------------------------------
def diag(s):
    return {"M": s.mean(), "SD": s.std(ddof=1), "N": len(s),
            "CI_lo": s.mean() - 1.96 * s.std(ddof=1) / np.sqrt(len(s)),
            "CI_hi": s.mean() + 1.96 * s.std(ddof=1) / np.sqrt(len(s))}

print("="*92)
print("RUSSIAN RESPONDENTS — Superordinate Identity items (inverted; higher = more belonging)")
print("="*92)
for it in ITEMS:
    a = diag(it["s2020"]); b = diag(it["s2023"])
    p = stats.ttest_ind(it["s2023"], it["s2020"], equal_var=False).pvalue
    s_pool = np.sqrt((a["SD"]**2 + b["SD"]**2) / 2)
    d = (b["M"] - a["M"]) / s_pool
    print(f"\n  {it['code20']} / {it['code23']} — {it['label']}")
    print(f"    2020: N={a['N']:4d}  M={a['M']:.3f} (95% CI [{a['CI_lo']:.3f}, {a['CI_hi']:.3f}])  SD={a['SD']:.3f}")
    print(f"    2023: N={b['N']:4d}  M={b['M']:.3f} (95% CI [{b['CI_lo']:.3f}, {b['CI_hi']:.3f}])  SD={b['SD']:.3f}")
    print(f"    Welch's t-test: p = {p:.4f};  d = {d:+.3f}")


# ---------- Plot ------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

C2020 = "#9ca3af"   # gray for 2020
C2023 = "#d97706"   # amber for Russians 2023

fig, axes = plt.subplots(1, 3, figsize=(11.0, 6.5), dpi=300, sharey=True)

JITTER_W = 0.13
SLOT_OFFSET = 0.18    # horizontal offset between 2020 and 2023 within a panel

for ax, it in zip(axes, ITEMS):
    s20 = it["s2020"]; s23 = it["s2023"]

    # X positions: jittered around the slot center
    x_2020 = -SLOT_OFFSET + RNG.normal(0, JITTER_W, size=len(s20))
    x_2023 = +SLOT_OFFSET + RNG.normal(0, JITTER_W, size=len(s23))
    # Y positions: actual response with small jitter so dots don't overlap
    y_2020 = s20.values + RNG.normal(0, 0.05, size=len(s20))
    y_2023 = s23.values + RNG.normal(0, 0.05, size=len(s23))

    ax.scatter(x_2020, y_2020, s=10, color=C2020, alpha=0.30,
               edgecolors="none", zorder=2, label=f"2020 (n = {len(s20)})")
    ax.scatter(x_2023, y_2023, s=10, color=C2023, alpha=0.50,
               edgecolors="none", zorder=2, label=f"2023 (n = {len(s23)})")

    # Mean and 95% CI overlay
    for x_center, s, color in [(-SLOT_OFFSET, s20, C2020),
                                (+SLOT_OFFSET, s23, C2023)]:
        m = s.mean()
        ci = 1.96 * s.std(ddof=1) / np.sqrt(len(s))
        # Mean as a wide black dash
        ax.plot([x_center - 0.16, x_center + 0.16], [m, m],
                color="#111", linewidth=2.2, zorder=4)
        # 95% CI as a vertical line
        ax.plot([x_center, x_center], [m - ci, m + ci],
                color="#111", linewidth=1.4, zorder=4)
        # Cap the CI line
        for y in (m - ci, m + ci):
            ax.plot([x_center - 0.06, x_center + 0.06], [y, y],
                    color="#111", linewidth=1.2, zorder=4)
        # Mean numeric label
        ax.text(x_center, m + 0.18, f"{m:.2f}", ha="center", va="bottom",
                fontsize=8, fontweight="bold", color="#111", zorder=5)

    # Significance annotation between the two columns (placed BELOW the data,
    # in the unused axis space at y < 1, so it doesn't crowd the panel title).
    p = stats.ttest_ind(s23, s20, equal_var=False).pvalue
    s_pool = np.sqrt((s20.std(ddof=1)**2 + s23.std(ddof=1)**2) / 2)
    d = (s23.mean() - s20.mean()) / s_pool
    star = "***" if p<.001 else "**" if p<.01 else "*" if p<.05 else "ns"

    ax.text(0, 0.20, f"d = {d:+.2f} {star}   p = {p:.3f}", ha="center", fontsize=9,
            fontweight="bold", color="#111")

    # Cosmetics
    ax.set_xticks([-SLOT_OFFSET, +SLOT_OFFSET])
    ax.set_xticklabels(["2020", "2023"], fontsize=10, fontweight="bold")
    ax.set_xlim(-0.55, 0.55)
    ax.set_ylim(0.0, 4.5)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels(["1\n(weak)", "2", "3", "4\n(strong)"], fontsize=8)
    ax.tick_params(axis="x", length=0)
    ax.tick_params(axis="y", length=2.5, color="#888")
    ax.axhline(2.5, color="#e5e7eb", linewidth=0.6, linestyle="--", zorder=0)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.spines["left"].set_color("#888")
    ax.spines["bottom"].set_color("#888")

    # Panel header
    ax.set_title(it["label"], fontsize=10.5, fontweight="bold", loc="left", pad=18)
    # Item code subtitle
    ax.text(0, 4.65, f"{it['code20']}  →  {it['code23']}",
            ha="center", fontsize=8, color="#555", style="italic")

axes[0].set_ylabel("Response (inverted; higher = stronger belonging)",
                   fontsize=9.5, color="#444")

# Title and footnote (sized so panel headers don't collide with subtitle)
fig.text(0.04, 0.970,
         "Russian Respondents — Superordinate Identity Items, 2020 vs 2023",
         fontsize=13, fontweight="bold", ha="left")
fig.text(0.04, 0.948,
         "Each dot = one Russian respondent's response, with horizontal jitter to separate overlapping points. Black bar = mean; vertical line + caps = 95% CI.",
         fontsize=9, color="#444")

fig.text(0.04, 0.040,
         "All items shown on a 1–4 scale where 4 = strongest belonging. Q67_2/Q67_5 inverted (raw 1 = strongly agree → display 4); Q67_4 shown in raw form (raw 4 = strongly disagree feeling second-class = strong belonging).",
         fontsize=7, color="#555")
fig.text(0.04, 0.020,
         "Independent-samples Welch's t-test. Cohen's d uses RMS-SD denominator. Significance: *** p<.001, ** p<.01, * p<.05, ns = not significant.",
         fontsize=7, color="#555")

plt.subplots_adjust(left=0.07, right=0.98, top=0.84, bottom=0.10, wspace=0.10)

out = ROOT / "viz" / "fig_si_scatter_russian.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
