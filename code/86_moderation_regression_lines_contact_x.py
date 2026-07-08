"""
Visualization of the Year × Contact moderation regressions from script 84,
with CONTACT on the x-axis (instead of year). Each panel shows four
regression lines per composite:

  Estonian 2020 — blue dashed
  Estonian 2023 — blue solid
  Russian  2020 — orange dashed
  Russian  2023 — orange solid

The slope of each line is:
  Year = 0 (2020): slope = B2
  Year = 1 (2023): slope = B2 + B3

When B3 ≠ 0, the 2020 and 2023 lines for a group diverge in slope — that
divergence IS the year × contact interaction. The plot makes the moderation
directly visible as a difference in slopes between waves within each group.

Output: viz/fig_moderation_regression_lines_contact_x.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

# ---------- Re-fit moderation regressions to get B0, B1, B2, B3 + contact range
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


CONTACT_2023 = {0: [f"Q52_{i}" for i in range(1, 7)], 1: [f"Q51_{i}" for i in range(1, 7)]}
CONTACT_2020 = {0: [f"K4X2_{i}" for i in range(1, 7)], 1: [f"K4X1_{i}" for i in range(1, 7)]}


def build_cell(spec, df, year, grp_code):
    if isinstance(spec[f"items_{year}"], dict):
        grp_key = "E" if grp_code == 0 else "R"
        items = spec[f"items_{year}"][grp_key]
        rev = (spec[f"rev_{year}"][grp_key] if spec.get(f"rev_{year}") else None)
    else:
        items = spec[f"items_{year}"]
        rev = spec.get(f"rev_{year}")
    sub_df = df[df["ethnicity_binary"] == grp_code]
    composite_vals = clean(sub_df, items, rev, spec["smax"])
    if spec["inv"]:
        composite_vals = (spec["smax"] + 1) - composite_vals
    contact_items = (CONTACT_2023[grp_code] if year == 2023 else CONTACT_2020[grp_code])
    contact_vals = 6 - clean(sub_df, contact_items)
    return pd.DataFrame({
        "value": composite_vals.values, "contact": contact_vals.values,
        "year_2023": 1 if year == 2023 else 0,
    })


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
]

fits = {}
for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        s20 = build_cell(spec, df20, 2020, grp_code)
        s23 = build_cell(spec, df23, 2023, grp_code)
        long = pd.concat([s20, s23], ignore_index=True).dropna()
        contact_mean = long["contact"].mean()
        long["contact_c"]   = long["contact"] - contact_mean
        long["yearXcontact"] = long["year_2023"] * long["contact_c"]
        X = sm.add_constant(long[["year_2023", "contact_c", "yearXcontact"]])
        m = sm.OLS(long["value"], X).fit(cov_type="HC3")
        # Get observed contact range for this group (5–95 percentile to avoid extreme tails)
        contact_lo = long["contact"].quantile(0.05)
        contact_hi = long["contact"].quantile(0.95)
        fits[(spec["name"], grp_name)] = {
            "B0": m.params["const"], "B1": m.params["year_2023"],
            "B2": m.params["contact_c"], "B3": m.params["yearXcontact"],
            "p3": m.pvalues["yearXcontact"],
            "contact_mean": contact_mean,
            "contact_lo": contact_lo, "contact_hi": contact_hi,
        }


# ---- Plot setup -----------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.7,
})

RUS = "#d97706"
EST = "#2563eb"

PRETTY = {
    "Superordinate Identity":             "Superordinate Identity",
    "SD: Primary Out-group":              "SD: Primary Out-group",
    "SD: General Out-group":              "SD: General Out-group ⁱ",
    "Comparative Opportunity Assessment": "Comparative Opportunity",
    "Belief in Inevitable Conflict":      "Belief in Inevitable Conflict",
    "Minority Inclusion Support":         "Minority Inclusion Support",
}


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ("⁺" if p < .10 else "ns")


def fmt_p(p):
    if p < .001: return "< .001"
    return f"{p:.3f}".lstrip("0")


def predict(fit, year, contact_raw):
    contact_c = contact_raw - fit["contact_mean"]
    return fit["B0"] + fit["B1"] * year + fit["B2"] * contact_c + fit["B3"] * year * contact_c


fig, axes = plt.subplots(2, 3, figsize=(16.0, 10.0), dpi=300)
axes = axes.flatten()

for ax, spec in zip(axes, SPECS):
    name = spec["name"]
    fE = fits[(name, "Estonian")]
    fR = fits[(name, "Russian")]

    # Plot regression lines across the observed contact range, per group × year
    for fit, color, group in [(fE, EST, "Estonian"), (fR, RUS, "Russian")]:
        x_grid = np.linspace(fit["contact_lo"], fit["contact_hi"], 50)

        # 2020 line (dashed)
        y_2020 = predict(fit, 0, x_grid)
        ax.plot(x_grid, y_2020, color=color, linewidth=1.8,
                linestyle=(0, (4, 2)), alpha=0.9, zorder=2,
                label=f"{group} 2020")

        # 2023 line (solid)
        y_2023 = predict(fit, 1, x_grid)
        ax.plot(x_grid, y_2023, color=color, linewidth=2.4,
                alpha=1.0, zorder=3, label=f"{group} 2023")

        # Mark group mean contact with a thin vertical tick
        ax.axvline(fit["contact_mean"], color=color, linewidth=0.6,
                   linestyle=":", alpha=0.4, zorder=1)

    # Annotation
    p_E = fE["p3"]; p_R = fR["p3"]
    ax.text(0.02, 0.97,
            f"Est. B₃ = {fE['B3']:+.4f}  p = {fmt_p(p_E)} {stars(p_E)}\n"
            f"Rus. B₃ = {fR['B3']:+.4f}  p = {fmt_p(p_R)} {stars(p_R)}",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=8.0, color="#222", family="monospace",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      edgecolor="#aaa", linewidth=0.5, alpha=0.93))

    ax.set_title(PRETTY[name], fontsize=11, fontweight="bold", loc="left", pad=8)
    ax.set_xlabel("Out-group contact  (1 = no communication … 5 = almost every day)",
                  fontsize=8.5, color="#444")
    ax.set_ylabel("Predicted composite", fontsize=9, color="#444")
    ax.set_xlim(1, 5)
    ax.set_xticks([1, 2, 3, 4, 5])
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")
    ax.grid(True, axis="y", linestyle="--", linewidth=0.4, color="#ddd", zorder=0)

# Title block
fig.text(0.04, 0.965,
         "Year × Out-group Contact Moderation — Regression Lines",
         fontsize=14, fontweight="bold", ha="left")
fig.text(0.04, 0.940,
         "Predicted composite values as a function of out-group contact, separately by year (2020 dashed, 2023 solid) and ethnic group (Estonian = blue, Russian = orange).",
         fontsize=9, color="#444", ha="left")
fig.text(0.04, 0.918,
         "Slope of each line = B₂ at 2020, or B₂ + B₃ at 2023. Slope differences within a group ARE the moderation effect. Dotted vertical lines mark within-group mean contact.",
         fontsize=9, color="#444", ha="left")

# Legend
handles = [
    mlines.Line2D([], [], color=EST, linewidth=1.8,
                  linestyle=(0,(4,2)), label="Estonian 2020"),
    mlines.Line2D([], [], color=EST, linewidth=2.4,
                  label="Estonian 2023"),
    mlines.Line2D([], [], color=RUS, linewidth=1.8,
                  linestyle=(0,(4,2)), label="Russian 2020"),
    mlines.Line2D([], [], color=RUS, linewidth=2.4,
                  label="Russian 2023"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.985, 0.940),
           frameon=False, fontsize=9, ncol=4,
           handlelength=3.0, columnspacing=1.5)

fig.text(0.04, 0.015,
         "ⁱ SD: General Out-group uses different items in 2020 (3 items) vs 2023 (6 items); shifts partially confound year with item-set change.",
         fontsize=7.0, color="#555", ha="left")
fig.text(0.04, 0.003,
         "Lines plotted across each group's 5th–95th percentile of contact. Contact scale: 1 = no communication, 5 = almost every day (inverted from raw Likert). Significance: *** p<.001, ** p<.01, * p<.05, ⁺ p<.10.",
         fontsize=7.0, color="#555", ha="left")

plt.subplots_adjust(left=0.05, right=0.985, top=0.88, bottom=0.07,
                    wspace=0.22, hspace=0.40)

out = ROOT / "viz" / "fig_moderation_regression_lines_contact_x.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
