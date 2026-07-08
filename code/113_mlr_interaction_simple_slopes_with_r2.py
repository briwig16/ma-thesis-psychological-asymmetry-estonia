"""
Updated version of fig_mlr_interaction_simple_slopes.jpg (script 101) that
adds R² and ΔR² to each panel's annotation box, alongside the β₃ Contact ×
Language coefficient and p-value.

For each cell, the annotation now shows:
  β₃ = ... (standardized interaction coefficient)
  p = ...  (significance of B₃)
  R² = ... (R² of the full interactive model)
  ΔR² = ... (R²_interaction − R²_additive, the incremental variance from adding
              the Contact × Language interaction term)

ΔR² formally tests how much variance the interaction term adds over and above
the additive (main-effects-only) MLR. Values close to 0 confirm "the
interaction adds nothing"; larger positive values indicate the interaction is
doing real predictive work.

Output: viz/fig_mlr_interaction_simple_slopes_with_r2.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

# ---------- Load + helpers ------------------------------------------------
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


def to_num(s, dk=9):
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s != dk).astype(float)


CONTACT_2023 = {0: [f"Q52_{i}" for i in range(1, 7)], 1: [f"Q51_{i}" for i in range(1, 7)]}
CONTACT_2020 = {0: [f"K4X2_{i}" for i in range(1, 7)], 1: [f"K4X1_{i}" for i in range(1, 7)]}
LANG_2023 = {0: "Q71_2", 1: "Q71_1"}
LANG_2020 = {0: "K5_2",  1: "K5_1"}


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
    contact_items = CONTACT_2023[grp_code] if year == 2023 else CONTACT_2020[grp_code]
    contact = 6 - clean(sub_df, contact_items)
    lang_col = LANG_2023[grp_code] if year == 2023 else LANG_2020[grp_code]
    lang = 7 - to_num(sub_df[lang_col])
    return pd.DataFrame({"value": outcome.values, "contact": contact.values,
                          "language": lang.values}).dropna()


SPECS = [
    {"name": "SD: Primary Out-group", "smax": 5, "inv": False,
     "items_2023": {"E": ["Q57_1","Q58_1","Q59_1"], "R": ["Q57_2","Q58_2","Q59_2"]},
     "items_2020": {"E": ["K4X7_1","K4X8_1","K4X9_1"], "R": ["K4X7_2","K4X8_2","K4X9_2"]}},
    {"name": "SD: General Out-group", "smax": 5, "inv": False,
     "items_2023": ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"],
     "items_2020": ["K4X7_3","K4X8_3","K4X9_3"]},
    {"name": "Minority Inclusion Support", "smax": 4, "inv": True,
     "items_2023": ["Q68_1","Q68_2","Q68_3"],
     "items_2020": ["K6X6_1","K6X6_2","K6X6_3"]},
    {"name": "Belief in Inevitable Conflict", "smax": 4, "inv": False,
     "items_2023": ["Q63_1","Q63_2","Q63_3","Q63_4"], "rev_2023": ["Q63_1","Q63_2"],
     "items_2020": ["K6X1_1","K6X1_2","K6X1_3","K6X1_4"], "rev_2020": ["K6X1_1","K6X1_2"]},
    {"name": "Comparative Opportunity Assessment", "smax": 5, "inv": True,
     "items_2023": [f"Q44_{i}" for i in range(1,13)],
     "items_2020": [f"K3X1_{i}" for i in range(1,13)]},
    {"name": "Superordinate Identity", "smax": 4, "inv": True,
     "items_2023": ["Q67_2","Q67_4","Q67_5"], "rev_2023": ["Q67_4"],
     "items_2020": ["K6X5_2","K6X5_3","K6X5_4"], "rev_2020": ["K6X5_3"]},
    {"name": "Group ID Patterns", "smax": 5, "inv": False, "single_item": True,
     "items_2023": "Q66", "items_2020": "K6X4",
     "dk_2023": 9, "dk_2020": 6},
    {"name": "Territorial Attachment", "smax": 4, "inv": True, "single_item": True,
     "items_2023": "Q67_1", "items_2020": "K6X5_1"},
]

# ---------- Refit and store β + R² for each cell --------------------------
fits = {}
for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        for year in (2020, 2023):
            data = build_cell(spec, year, grp_code)
            if len(data) < 10: continue
            data["contact_c"]  = data["contact"]  - data["contact"].mean()
            data["language_c"] = data["language"] - data["language"].mean()
            data["cxl"] = data["contact_c"] * data["language_c"]
            sd_y = data["value"].std(ddof=1)
            sd_c = data["contact_c"].std(ddof=1)
            sd_l = data["language_c"].std(ddof=1)

            # Additive
            X_a = sm.add_constant(data[["contact_c", "language_c"]])
            m_a = sm.OLS(data["value"], X_a).fit(cov_type="HC3")
            # Interactive
            X_i = sm.add_constant(data[["contact_c", "language_c", "cxl"]])
            m_i = sm.OLS(data["value"], X_i).fit(cov_type="HC3")

            beta1 = m_i.params["contact_c"]  * sd_c / sd_y
            beta2 = m_i.params["language_c"] * sd_l / sd_y
            beta3 = m_i.params["cxl"] * sd_c * sd_l / sd_y
            fits[(spec["name"], grp_name, year)] = {
                "beta1": beta1, "beta2": beta2, "beta3": beta3,
                "p3": m_i.pvalues["cxl"],
                "R2_int": m_i.rsquared,
                "R2_add": m_a.rsquared,
                "delta_R2": m_i.rsquared - m_a.rsquared,
            }


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


# ---------- Plot setup ----------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.5,
})

LOW_LANG_COLOR  = "#86efac"
MID_LANG_COLOR  = "#15803d"
HIGH_LANG_COLOR = "#052e16"

OUTCOMES = [s["name"] for s in SPECS]
PRETTY = {
    "Superordinate Identity":             "Superordinate\nIdentity",
    "SD: Primary Out-group":              "SD: Primary\nOut-group",
    "SD: General Out-group":              "SD: General\nOut-group",
    "Comparative Opportunity Assessment": "Comparative\nOpportunity",
    "Belief in Inevitable Conflict":      "Belief in\nInevitable Conflict",
    "Minority Inclusion Support":         "Minority\nInclusion Support",
    "Group ID Patterns":                  "Group ID\nPatterns",
    "Territorial Attachment":             "Territorial\nAttachment",
}
CELLS = [("Estonian", 2020), ("Estonian", 2023), ("Russian", 2020), ("Russian", 2023)]

# Common y-axis
y_vals = []
for f in fits.values():
    for c in (-1, 1):
        for l in (-1, 0, 1):
            y_vals.append(f["beta1"]*c + f["beta2"]*l + f["beta3"]*c*l)
y_max = max(abs(v) for v in y_vals) * 1.25
y_lim = (-y_max, y_max)

# A4 portrait: 8.27" × 11.69"
fig, axes = plt.subplots(8, 4, figsize=(8.27, 11.69), dpi=300,
                          sharex=True, sharey=True)

for i, outcome in enumerate(OUTCOMES):
    for j, (group, year) in enumerate(CELLS):
        ax = axes[i, j]
        key = (outcome, group, year)
        if key not in fits:
            ax.set_visible(False); continue
        f = fits[key]

        contact_range = np.linspace(-1, 1, 30)
        for language_z, color, lw in [
            (-1, LOW_LANG_COLOR,  1.0),
            ( 0, MID_LANG_COLOR,  1.3),
            ( 1, HIGH_LANG_COLOR, 1.6),
        ]:
            y_pred = (f["beta1"] * contact_range
                      + f["beta2"] * language_z
                      + f["beta3"] * contact_range * language_z)
            ax.plot(contact_range, y_pred, color=color, linewidth=lw,
                    solid_capstyle="round", zorder=3)

        ax.axhline(0, color="#999", linewidth=0.5, linestyle="--", zorder=1)
        ax.axvline(0, color="#999", linewidth=0.5, linestyle="--", zorder=1)

        # Annotation: β₃, p, R², ΔR² — compact 2-line format for A4
        p_val = f["p3"]
        if p_val < .001:
            p_str = "p<.001"
        else:
            p_str = f"p={p_val:.3f}".replace("0.", ".")
        ann_text = (f"β₃={f['beta3']:+.2f}{stars(p_val)} {p_str}\n"
                    f"R²={f['R2_int']:.2f}  ΔR²={f['delta_R2']:+.3f}")
        ax.text(0.97, 0.96, ann_text,
                transform=ax.transAxes, ha="right", va="top",
                fontsize=5.2, color="#222", family="monospace",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                          edgecolor="#aaa", linewidth=0.35, alpha=0.92))

        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(y_lim)
        ax.set_xticks([-1, 0, 1])
        ax.set_xticklabels(["−1", "0", "+1"], fontsize=6)
        ax.tick_params(axis="both", labelsize=6, color="#888",
                       length=2, width=0.4, pad=1.5)
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        ax.grid(True, axis="y", linestyle=":", linewidth=0.25, color="#eee", zorder=0)
        if i == 0:
            ax.set_title(f"{group} {year}", fontsize=8, fontweight="bold",
                         pad=3, color="#333")

# Row labels (outcome names, left column only) — horizontal 2-line labels
for i, outcome in enumerate(OUTCOMES):
    axes[i, 0].set_ylabel(PRETTY[outcome], fontsize=6.5, fontweight="bold",
                          color="#222", labelpad=2, rotation=0,
                          ha="right", va="center", linespacing=1.0)

# Bottom x-axis label (compact, single placement under center)
for j in range(4):
    axes[7, j].set_xlabel("Standardized Contact (SD)",
                          fontsize=6.5, color="#555", labelpad=2)

# Title
fig.text(0.025, 0.982,
         "Figure 3 - MLR with Contact × Language Interaction",
         fontsize=10.5, fontweight="bold", ha="left")
fig.text(0.025, 0.968,
         "Simple Slopes with R² and ΔR²",
         fontsize=8.5, fontweight="bold", color="#333", ha="left")
fig.text(0.025, 0.956,
         "Each panel: contact's predicted standardized effect on the outcome at low (−1 SD), mean, and high (+1 SD) language.",
         fontsize=6.2, color="#444", ha="left")
fig.text(0.025, 0.947,
         "Annotation: β₃ Contact × Language (standardized), p-value, R² of interactive model, ΔR² = R²_int − R²_add.",
         fontsize=6.2, color="#444", ha="left")

# Legend (compact, top-right)
handles = [
    mlines.Line2D([], [], color=LOW_LANG_COLOR,  linewidth=1.2, label="Low Lang (−1 SD)"),
    mlines.Line2D([], [], color=MID_LANG_COLOR,  linewidth=1.5, label="Mean Lang"),
    mlines.Line2D([], [], color=HIGH_LANG_COLOR, linewidth=1.8, label="High Lang (+1 SD)"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.985, 0.978),
           frameon=False, fontsize=6.5, ncol=1, handlelength=1.8,
           labelspacing=0.3, borderaxespad=0.2)

# Footer notes
fig.text(0.025, 0.016,
         "y = β₁·Contact_z + β₂·Lang_z + β₃·(Contact_z × Lang_z). β₃ standardized. ΔR² = R²_interaction − R²_additive.",
         fontsize=5.8, color="#555", ha="left")
fig.text(0.025, 0.006,
         "ΔR² ≈ 0 → interaction adds nothing. ΔR² > .01 → meaningful. Significance: *** p<.001, ** p<.01, * p<.05, ⁺ p<.10.",
         fontsize=5.8, color="#555", ha="left")

plt.subplots_adjust(left=0.165, right=0.985, top=0.935, bottom=0.045,
                    wspace=0.13, hspace=0.28)

out = ROOT / "viz" / "fig_mlr_interaction_simple_slopes_with_r2.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
