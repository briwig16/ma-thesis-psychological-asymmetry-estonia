"""
Density-overlay grid for ANOVA Table 3 — visualizes the Levene's variance
comparisons by showing the distribution shape of each outcome at 2020 vs 2023
within each group.

Each panel = one outcome × one group. Within each panel:
  - Filled translucent KDE for the 2020 distribution
  - Solid darker KDE outline for the 2023 distribution
  - Vertical lines marking the cell means
  - Annotation: Levene's F, p, var(2020) → var(2023), ↑ or ↓

Layout: 8 outcomes (rows) × 2 groups (columns) = 16 panels.

Visual interpretation:
  - A peaked 2020 KDE that spreads out in 2023 = POLARIZATION (variance ↑)
  - A wide 2020 KDE that concentrates in 2023 = CONVERGENCE (variance ↓)
  - Overlapping nearly-identical KDEs = stable variance (Levene's ns)

Output: viz/fig_levene_density_grid.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
from scipy.stats import gaussian_kde
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

# ---------- Load + compute composite values per cell ----------------------
df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy().reset_index(drop=True)
df20, _ = pyreadstat.read_sav(
    str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"), encoding="latin1"
)
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy().reset_index(drop=True)


def clean(df, items, reverse_items=None, scale_max=None, dk_code=9):
    sub = df[items].apply(pd.to_numeric, errors="coerce")
    sub = sub.where(sub != dk_code)
    if reverse_items:
        for it in reverse_items:
            sub[it] = (scale_max + 1) - sub[it]
    return sub.mean(axis=1, skipna=True)


def single_item(df, var, dk_code=9):
    s = pd.to_numeric(df[var], errors="coerce")
    return s.where(s != dk_code).astype(float)


def build_cell(spec, year, grp_code):
    df = df23 if year == 2023 else df20
    sub_df = df[df["ethnicity_binary"] == grp_code]
    if spec.get("single_item"):
        item = spec[f"items_{year}"]
        dk = spec.get(f"dk_{year}", 9)
        outcome = single_item(sub_df, item, dk_code=dk)
    elif isinstance(spec[f"items_{year}"], dict):
        grp_key = "E" if grp_code == 0 else "R"
        items = spec[f"items_{year}"][grp_key]
        rev = (spec[f"rev_{year}"][grp_key] if spec.get(f"rev_{year}") else None)
        outcome = clean(sub_df, items, rev, spec["smax"])
    else:
        items = spec[f"items_{year}"]
        rev = spec.get(f"rev_{year}")
        outcome = clean(sub_df, items, rev, spec["smax"])
    if spec["inv"]:
        outcome = (spec["smax"] + 1) - outcome
    return outcome.dropna().values


SPECS = [
    {"name": "Superordinate Identity", "smax": 4, "inv": True,
     "items_2023": ["Q67_2","Q67_4","Q67_5"], "rev_2023": ["Q67_4"],
     "items_2020": ["K6X5_2","K6X5_3","K6X5_4"], "rev_2020": ["K6X5_3"]},
    {"name": "SD: Primary Out-group", "smax": 5, "inv": False,
     "items_2023": {"E": ["Q57_1","Q58_1","Q59_1"], "R": ["Q57_2","Q58_2","Q59_2"]},
     "items_2020": {"E": ["K4X7_1","K4X8_1","K4X9_1"], "R": ["K4X7_2","K4X8_2","K4X9_2"]}},
    {"name": "SD: General Out-group", "smax": 5, "inv": False,
     "items_2023": ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"],
     "items_2020": ["K4X7_3","K4X8_3","K4X9_3"]},
    {"name": "Comparative Opportunity Assessment", "smax": 5, "inv": True,
     "items_2023": [f"Q44_{i}" for i in range(1,13)],
     "items_2020": [f"K3X1_{i}" for i in range(1,13)]},
    {"name": "Belief in Inevitable Conflict", "smax": 4, "inv": False,
     "items_2023": ["Q63_1","Q63_2","Q63_3","Q63_4"], "rev_2023": ["Q63_1","Q63_2"],
     "items_2020": ["K6X1_1","K6X1_2","K6X1_3","K6X1_4"], "rev_2020": ["K6X1_1","K6X1_2"]},
    {"name": "Minority Inclusion Support", "smax": 4, "inv": True,
     "items_2023": ["Q68_1","Q68_2","Q68_3"],
     "items_2020": ["K6X6_1","K6X6_2","K6X6_3"]},
    {"name": "Group ID Patterns", "smax": 5, "inv": False, "single_item": True,
     "items_2023": "Q66", "items_2020": "K6X4",
     "dk_2023": 9, "dk_2020": 6},
    {"name": "Territorial Attachment", "smax": 4, "inv": True, "single_item": True,
     "items_2023": "Q67_1", "items_2020": "K6X5_1"},
]

# Read Levene's results from the canonical TSV
levene = pd.read_csv(ROOT / "code" / "_anova_2x2_all_variables.tsv", sep="\t")


def stars(p):
    if pd.isna(p): return ""
    if p < .001: return "***"
    if p < .01:  return "**"
    if p < .05:  return "*"
    if p < .10:  return "⁺"
    return ""


def fmt_p(p):
    if p < .001: return "p < .001"
    return f"p = {p:.3f}".replace("0.", ".")


PRETTY = {s["name"]: s["name"] for s in SPECS}
PRETTY["Comparative Opportunity Assessment"] = "Comparative Opportunity"


# ---------- Plot ----------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.5,
})

EST_COLOR = "#2563eb"
RUS_COLOR = "#d97706"
COLOR_2020 = "#94a3b8"   # gray for 2020
COLOR_2023 = "#0f172a"   # darker outline for 2023

fig, axes = plt.subplots(8, 2, figsize=(13.0, 22.0), dpi=300, sharex=False)

for i, spec in enumerate(SPECS):
    smax = spec["smax"]
    levene_row = levene[levene["variable"] == spec["name"]].iloc[0]

    for j, (group, grp_code) in enumerate([("Estonian", 0), ("Russian", 1)]):
        ax = axes[i, j]
        # Pull 2020 and 2023 distributions for this cell
        vals_20 = build_cell(spec, 2020, grp_code)
        vals_23 = build_cell(spec, 2023, grp_code)
        if len(vals_20) < 5 or len(vals_23) < 5:
            ax.set_visible(False); continue

        # KDE smoothing
        x_grid = np.linspace(1, smax, 200)
        kde_20 = gaussian_kde(vals_20, bw_method=0.30)(x_grid)
        kde_23 = gaussian_kde(vals_23, bw_method=0.30)(x_grid)

        group_color = EST_COLOR if group == "Estonian" else RUS_COLOR

        # 2020 filled KDE (lighter)
        ax.fill_between(x_grid, kde_20, color=group_color, alpha=0.20,
                        zorder=2, linewidth=0)
        ax.plot(x_grid, kde_20, color=group_color, linewidth=1.0,
                alpha=0.45, linestyle="--", zorder=3, label="2020")

        # 2023 KDE outline (solid)
        ax.plot(x_grid, kde_23, color=group_color, linewidth=2.4,
                zorder=4, label="2023")
        ax.fill_between(x_grid, kde_23, color=group_color, alpha=0.10,
                        zorder=2.5, linewidth=0)

        # Mean lines
        ax.axvline(vals_20.mean(), color=group_color, linewidth=0.6,
                   linestyle=":", alpha=0.55, zorder=1)
        ax.axvline(vals_23.mean(), color=group_color, linewidth=0.6,
                   linestyle="-", alpha=0.8, zorder=1)

        # Levene's annotation
        if group == "Estonian":
            F = levene_row["Levene_Est_F"]; p_lv = levene_row["Levene_Est_p"]
            v20 = levene_row["Levene_Est_var_2020"]; v23 = levene_row["Levene_Est_var_2023"]
        else:
            F = levene_row["Levene_Rus_F"]; p_lv = levene_row["Levene_Rus_p"]
            v20 = levene_row["Levene_Rus_var_2020"]; v23 = levene_row["Levene_Rus_var_2023"]
        arrow = "↑" if v23 > v20 else "↓"

        # Compact one-line annotation at bottom-right
        ann = f"F={F:.1f}{stars(p_lv)}  var: {v20:.2f}→{v23:.2f}{arrow}"
        ax.text(0.98, 0.04, ann,
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=7.5, color="#222", family="monospace", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                          edgecolor="#bbb", linewidth=0.4, alpha=0.95))

        # Format
        ax.set_xlim(0.7, smax + 0.3)
        ax.set_xticks(list(range(1, smax + 1)))
        # Cap y at 1.25× the taller KDE peak so panels don't have huge whitespace
        max_y = max(kde_20.max(), kde_23.max()) * 1.25
        ax.set_ylim(0, max_y)
        ax.tick_params(axis="x", labelsize=8, color="#888")
        ax.tick_params(axis="y", labelsize=7, color="#888", labelleft=False)
        for s_ in ("top", "right", "left"):
            ax.spines[s_].set_visible(False)
        ax.spines["bottom"].set_color("#666")

        # Column titles (top row)
        if i == 0:
            ax.set_title(f"{group} respondents", fontsize=11, fontweight="bold",
                         color="#333", pad=8)

        # Bottom row x-axis label
        if i == len(SPECS) - 1:
            ax.set_xlabel(f"Composite scale (1–{smax})", fontsize=8, color="#555")

    # Row label (outcome name) on the leftmost panel
    axes[i, 0].set_ylabel(PRETTY[spec["name"]], fontsize=9.5,
                          fontweight="bold", color="#222", labelpad=6)

# Title (compact)
fig.text(0.04, 0.982,
         "Levene's Variance Comparison — Distribution Shape by Wave",
         fontsize=15, fontweight="bold", ha="left")
fig.text(0.04, 0.969,
         "2020 distribution (dashed, light fill) overlaid with 2023 distribution (solid, darker fill). Vertical lines mark cell means.",
         fontsize=9, color="#444", ha="left")

# Legend below title in a single row
handles = [
    mlines.Line2D([], [], color="#444", linewidth=1.0, alpha=0.6,
                  linestyle="--", label="2020 KDE"),
    mlines.Line2D([], [], color="#444", linewidth=2.4,
                  label="2023 KDE"),
    mlines.Line2D([], [], color="#666", linewidth=0.6, linestyle=":",
                  label="2020 mean"),
    mlines.Line2D([], [], color="#666", linewidth=0.6, linestyle="-",
                  label="2023 mean"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.99, 0.978),
           frameon=False, fontsize=8.5, ncol=4,
           handlelength=2.0, columnspacing=1.5)

fig.text(0.04, 0.010,
         "Each panel shows the Levene's F, p, and the within-group variance 2020→2023 with direction arrow (↑ polarization, ↓ convergence). Stars: *** p<.001, ** p<.01, * p<.05, ⁺ p<.10.",
         fontsize=7.5, color="#555", ha="left")

plt.subplots_adjust(left=0.10, right=0.985, top=0.945, bottom=0.025,
                    wspace=0.10, hspace=0.40)

out = ROOT / "viz" / "fig_levene_density_grid.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
