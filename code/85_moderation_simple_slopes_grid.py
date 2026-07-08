"""
Simple-slopes visualization of the Year × Contact moderation regressions
from script 84. For each composite, a 2 × 3 grid panel shows the predicted
composite value at 2020 vs 2023, separately for low-contact (mean − 1 SD)
and high-contact (mean + 1 SD) respondents, in each ethnic group.

Four lines per panel:
  Estonian, low contact   — blue, dashed
  Estonian, high contact  — blue, solid
  Russian,  low contact   — orange, dashed
  Russian,  high contact  — orange, solid

The vertical spread between the dashed and solid lines for a group reflects
the strength of the moderation: bigger spread = stronger moderation. Lines
crossing or fanning out across years signal the year × contact interaction.

Output: viz/fig_moderation_simple_slopes.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

# Load moderation regression coefficients
mod = pd.read_csv(ROOT / "code" / "_year_x_contact_moderation.tsv", sep="\t")

# Need each cell's B0, B1, B2, B3 + contact_sd to compute predicted values.
# Currently the TSV has B1, B2, B3 but NOT B0 (intercept). Re-fit minimally
# to get B0 for each cell.
import pyreadstat
import statsmodels.api as sm

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
        rev = (spec[f"rev_{year}"][grp_key]
               if spec.get(f"rev_{year}") else None)
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
        "value": composite_vals.values,
        "contact": contact_vals.values,
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

# Re-fit and store full coefficients including intercept + contact SD
fits = {}
for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        s20 = build_cell(spec, df20, 2020, grp_code)
        s23 = build_cell(spec, df23, 2023, grp_code)
        long = pd.concat([s20, s23], ignore_index=True).dropna()
        contact_mean = long["contact"].mean()
        contact_sd   = long["contact"].std(ddof=1)
        long["contact_c"]    = long["contact"] - contact_mean
        long["yearXcontact"] = long["year_2023"] * long["contact_c"]
        X = sm.add_constant(long[["year_2023", "contact_c", "yearXcontact"]])
        m = sm.OLS(long["value"], X).fit(cov_type="HC3")
        fits[(spec["name"], grp_name)] = {
            "B0": m.params["const"],
            "B1": m.params["year_2023"],
            "B2": m.params["contact_c"],
            "B3": m.params["yearXcontact"],
            "p3": m.pvalues["yearXcontact"],
            "contact_sd": contact_sd,
        }


# ---------- Plot setup -----------------------------------------------------
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


def predict(fit, year, contact_c):
    return fit["B0"] + fit["B1"] * year + fit["B2"] * contact_c + fit["B3"] * year * contact_c


fig, axes = plt.subplots(2, 3, figsize=(16.0, 10.0), dpi=300)
axes = axes.flatten()

for ax, spec in zip(axes, SPECS):
    name = spec["name"]
    fE = fits[(name, "Estonian")]
    fR = fits[(name, "Russian")]

    # Predicted values at low (-1 SD) and high (+1 SD) contact, at year = 0 and 1
    for fit, color, group in [(fE, EST, "Estonian"), (fR, RUS, "Russian")]:
        c_low  = -fit["contact_sd"]
        c_high = +fit["contact_sd"]

        # Low contact (dashed)
        y_low_2020  = predict(fit, 0, c_low)
        y_low_2023  = predict(fit, 1, c_low)
        ax.plot([0, 1], [y_low_2020, y_low_2023],
                color=color, linewidth=1.8, linestyle=(0, (4, 2)),
                marker="o", markersize=7, markerfacecolor="white",
                markeredgecolor=color, markeredgewidth=1.5,
                label=f"{group}, low contact", alpha=0.9, zorder=2)

        # High contact (solid)
        y_high_2020 = predict(fit, 0, c_high)
        y_high_2023 = predict(fit, 1, c_high)
        ax.plot([0, 1], [y_high_2020, y_high_2023],
                color=color, linewidth=2.4,
                marker="s", markersize=8, markerfacecolor=color,
                markeredgecolor="white", markeredgewidth=1.0,
                label=f"{group}, high contact", alpha=1.0, zorder=3)

    # Annotation with B3 interaction p-values for both groups
    p_E = fE["p3"]; p_R = fR["p3"]
    ax.text(0.02, 0.97,
            f"Est. B₃ = {fE['B3']:+.4f}  p = {fmt_p(p_E)} {stars(p_E)}\n"
            f"Rus. B₃ = {fR['B3']:+.4f}  p = {fmt_p(p_R)} {stars(p_R)}",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=8.0, color="#222", family="monospace",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      edgecolor="#aaa", linewidth=0.5, alpha=0.93))

    ax.set_title(PRETTY[name], fontsize=11, fontweight="bold", loc="left", pad=8)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["2020", "2023"], fontsize=10)
    ax.set_xlim(-0.20, 1.20)
    ax.set_xlabel("Year", fontsize=9, color="#444")
    ax.set_ylabel("Predicted composite", fontsize=9, color="#444")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")
    ax.grid(True, axis="y", linestyle="--", linewidth=0.4, color="#ddd", zorder=0)

# Title block
fig.text(0.04, 0.965,
         "Year × Out-group Contact Moderation — Simple Slopes by Composite",
         fontsize=14, fontweight="bold", ha="left")
fig.text(0.04, 0.940,
         "Predicted composite values at low (mean − 1 SD) and high (mean + 1 SD) out-group contact, separately for Estonian (blue) and Russian (orange) respondents.",
         fontsize=9, color="#444", ha="left")
fig.text(0.04, 0.918,
         "Dashed lines = low contact (open circles). Solid lines = high contact (filled squares). Diverging or converging line pairs within a group indicate moderation.",
         fontsize=9, color="#444", ha="left")

# Legend
handles = [
    mlines.Line2D([], [], marker="o", color=EST, markerfacecolor="white",
                  markeredgecolor=EST, markersize=8, linewidth=1.8,
                  linestyle=(0,(4,2)), label="Estonian, low contact"),
    mlines.Line2D([], [], marker="s", color=EST, markerfacecolor=EST,
                  markeredgecolor="white", markersize=8, linewidth=2.4,
                  label="Estonian, high contact"),
    mlines.Line2D([], [], marker="o", color=RUS, markerfacecolor="white",
                  markeredgecolor=RUS, markersize=8, linewidth=1.8,
                  linestyle=(0,(4,2)), label="Russian, low contact"),
    mlines.Line2D([], [], marker="s", color=RUS, markerfacecolor=RUS,
                  markeredgecolor="white", markersize=8, linewidth=2.4,
                  label="Russian, high contact"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.985, 0.940),
           frameon=False, fontsize=8.5, ncol=2,
           handlelength=2.5, columnspacing=1.5)

fig.text(0.04, 0.015,
         "ⁱ SD: General Out-group uses different items in 2020 (3 items) vs 2023 (6 items); within-group shifts partially confound year with item-set change.",
         fontsize=7.0, color="#555", ha="left")
fig.text(0.04, 0.003,
         "Out-group contact: Estonian respondents → Russian-speakers (Q52/K4X2); Russian respondents → Estonian-speakers (Q51/K4X1). Inverted: higher = more frequent contact. Mean-centered within group. Significance: *** p<.001, ** p<.01, * p<.05, ⁺ p<.10.",
         fontsize=7.0, color="#555", ha="left")

plt.subplots_adjust(left=0.05, right=0.985, top=0.88, bottom=0.07,
                    wspace=0.22, hspace=0.35)

out = ROOT / "viz" / "fig_moderation_simple_slopes.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
