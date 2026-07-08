"""
Slope-graph visualizations for the age-controlled MLR models from script 111.
Produces two figures, parallel to scripts 100 and 101 but using the
demographic-controlled coefficients:

  fig_mlr_with_age_slope_graphs.jpg
    — Additive MLR: standardized slopes of contact, language, and age per cell

  fig_mlr_with_age_interaction_simple_slopes.jpg
    — Interactive MLR with age control: contact slopes at three language
      levels per cell (simple-slopes visualization of the moderation)

8 outcomes × 4 cells = 32 panels each.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

# ---------- Load + helpers (same as script 111) ---------------------------
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
df23["age"] = pd.to_numeric(df23["T3"], errors="coerce")
df20["age"] = pd.to_numeric(df20["vanus"], errors="coerce")


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
    age = sub_df["age"].values
    return pd.DataFrame({
        "value": outcome.values, "contact": contact.values,
        "language": lang.values, "age": age,
    }).dropna()


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


# ---------- Refit both models (additive + interactive with age) ----------
fits = {}
for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        for year in (2020, 2023):
            data = build_cell(spec, year, grp_code)
            if len(data) < 10: continue
            data["contact_c"]  = data["contact"]  - data["contact"].mean()
            data["language_c"] = data["language"] - data["language"].mean()
            data["age_c"]      = data["age"]      - data["age"].mean()
            data["cxl"] = data["contact_c"] * data["language_c"]
            sd_y = data["value"].std(ddof=1)
            sd_c = data["contact_c"].std(ddof=1)
            sd_l = data["language_c"].std(ddof=1)
            sd_a = data["age_c"].std(ddof=1)

            # Additive
            X_a = sm.add_constant(data[["contact_c", "language_c", "age_c"]])
            m_a = sm.OLS(data["value"], X_a).fit(cov_type="HC3")
            # Interactive
            X_i = sm.add_constant(data[["contact_c", "language_c", "age_c", "cxl"]])
            m_i = sm.OLS(data["value"], X_i).fit(cov_type="HC3")

            fits[(spec["name"], grp_name, year)] = {
                # Additive
                "beta1_a": m_a.params["contact_c"]  * sd_c / sd_y,
                "beta2_a": m_a.params["language_c"] * sd_l / sd_y,
                "beta3_a": m_a.params["age_c"]      * sd_a / sd_y,
                "p1_a": m_a.pvalues["contact_c"],
                "p2_a": m_a.pvalues["language_c"],
                "p3_a": m_a.pvalues["age_c"],
                # Interactive (standardized)
                "beta1_i": m_i.params["contact_c"]  * sd_c / sd_y,
                "beta2_i": m_i.params["language_c"] * sd_l / sd_y,
                "beta3_i": m_i.params["age_c"]      * sd_a / sd_y,
                "beta4_i": m_i.params["cxl"] * sd_c * sd_l / sd_y,
                "p4_i": m_i.pvalues["cxl"],
            }


# ============================================================================
#                              FIGURE 1 — Additive slopes
# ============================================================================
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.5,
})

OUTCOMES = [s["name"] for s in SPECS]
PRETTY = {
    "Superordinate Identity":             "Superordinate Identity",
    "SD: Primary Out-group":              "SD: Primary Out-group",
    "SD: General Out-group":              "SD: General Out-group",
    "Comparative Opportunity Assessment": "Comparative Opportunity",
    "Belief in Inevitable Conflict":      "Belief in Inevitable Conflict",
    "Minority Inclusion Support":         "Minority Inclusion Support",
    "Group ID Patterns":                  "Group ID Patterns",
    "Territorial Attachment":             "Territorial Attachment",
}
CELLS = [("Estonian", 2020), ("Estonian", 2023), ("Russian", 2020), ("Russian", 2023)]

CONTACT_COLOR  = "#2563eb"   # blue
LANGUAGE_COLOR = "#15803d"   # green
AGE_COLOR      = "#9333ea"   # purple

# Compute global y-axis range across all betas
all_betas = []
for f in fits.values():
    all_betas.extend([f["beta1_a"], f["beta2_a"], f["beta3_a"]])
y_max = max(abs(b) for b in all_betas) * 1.25
y_lim = (-y_max, y_max)

fig, axes = plt.subplots(8, 4, figsize=(15.0, 22.0), dpi=300, sharex=True, sharey=True)

for i, outcome in enumerate(OUTCOMES):
    for j, (group, year) in enumerate(CELLS):
        ax = axes[i, j]
        key = (outcome, group, year)
        if key not in fits:
            ax.set_visible(False); continue
        f = fits[key]

        # Contact slope (blue)
        ax.plot([-1, 1], [-f["beta1_a"], f["beta1_a"]],
                color=CONTACT_COLOR, linewidth=2.2, solid_capstyle="round",
                marker="o", markersize=6, markerfacecolor=CONTACT_COLOR,
                markeredgecolor="white", markeredgewidth=0.8, zorder=3)
        # Language slope (green)
        ax.plot([-1, 1], [-f["beta2_a"], f["beta2_a"]],
                color=LANGUAGE_COLOR, linewidth=2.2, solid_capstyle="round",
                marker="s", markersize=6, markerfacecolor=LANGUAGE_COLOR,
                markeredgecolor="white", markeredgewidth=0.8, zorder=3)
        # Age slope (purple)
        ax.plot([-1, 1], [-f["beta3_a"], f["beta3_a"]],
                color=AGE_COLOR, linewidth=2.2, solid_capstyle="round",
                marker="^", markersize=6, markerfacecolor=AGE_COLOR,
                markeredgecolor="white", markeredgewidth=0.8, zorder=3)

        # Reference lines
        ax.axhline(0, color="#999", linewidth=0.5, linestyle="--", zorder=1)
        ax.axvline(0, color="#999", linewidth=0.5, linestyle="--", zorder=1)

        # Endpoint annotations
        ax.text(1.05, f["beta1_a"],
                f"β={f['beta1_a']:+.2f}{stars(f['p1_a'])}",
                color=CONTACT_COLOR, fontsize=6.5, va="center", ha="left",
                family="monospace", fontweight="bold")
        ax.text(1.05, f["beta2_a"],
                f"β={f['beta2_a']:+.2f}{stars(f['p2_a'])}",
                color=LANGUAGE_COLOR, fontsize=6.5, va="center", ha="left",
                family="monospace", fontweight="bold")
        ax.text(1.05, f["beta3_a"],
                f"β={f['beta3_a']:+.2f}{stars(f['p3_a'])}",
                color=AGE_COLOR, fontsize=6.5, va="center", ha="left",
                family="monospace", fontweight="bold")

        ax.set_xlim(-1.4, 2.0)
        ax.set_ylim(y_lim)
        ax.set_xticks([-1, 0, 1])
        ax.set_xticklabels(["−1 SD", "0", "+1 SD"], fontsize=7)
        ax.tick_params(axis="both", labelsize=7, color="#888")
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        ax.grid(True, axis="y", linestyle=":", linewidth=0.3, color="#eee", zorder=0)
        if i == 0:
            ax.set_title(f"{group} {year}", fontsize=10, fontweight="bold",
                         pad=6, color="#333")

# Row labels
for i, outcome in enumerate(OUTCOMES):
    axes[i, 0].set_ylabel(PRETTY[outcome], fontsize=9, fontweight="bold",
                          color="#222", labelpad=8)
for j in range(4):
    axes[7, j].set_xlabel("Standardized predictor (SD)", fontsize=8, color="#555")

# Title
fig.text(0.04, 0.985,
         "Age-Controlled Additive MLR — Standardized Slopes of Contact, Language, and Age",
         fontsize=15, fontweight="bold", ha="left")
fig.text(0.04, 0.973,
         "Three slope lines per panel: contact (blue circle), language (green square), age (purple triangle). All standardized; slope = β coefficient.",
         fontsize=9, color="#444", ha="left")
fig.text(0.04, 0.963,
         "Compare with fig_mlr_slope_graphs.jpg (no-age version). Larger separation in contact/language slopes between figures = age absorbed variance from that predictor.",
         fontsize=9, color="#444", ha="left")

handles = [
    mlines.Line2D([], [], marker="o", color=CONTACT_COLOR, markerfacecolor=CONTACT_COLOR,
                  markeredgecolor="white", markersize=8, linewidth=2.2,
                  label="Out-group Contact"),
    mlines.Line2D([], [], marker="s", color=LANGUAGE_COLOR, markerfacecolor=LANGUAGE_COLOR,
                  markeredgecolor="white", markersize=8, linewidth=2.2,
                  label="Out-group Language"),
    mlines.Line2D([], [], marker="^", color=AGE_COLOR, markerfacecolor=AGE_COLOR,
                  markeredgecolor="white", markersize=8, linewidth=2.2,
                  label="Age (years)"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.99, 0.972),
           frameon=False, fontsize=9, ncol=1, handlelength=2.0)

fig.text(0.04, 0.015,
         "All predictors mean-centered within cell. HC3 robust standard errors. Significance: *** p<.001, ** p<.01, * p<.05, ⁺ p<.10.",
         fontsize=7.5, color="#555", ha="left")
fig.text(0.04, 0.005,
         "Slope formula: y_z = β × predictor_z. Each line plots from (−1 SD, −β) to (+1 SD, +β) on the standardized outcome scale.",
         fontsize=7.5, color="#555", ha="left")

plt.subplots_adjust(left=0.13, right=0.985, top=0.95, bottom=0.025,
                    wspace=0.15, hspace=0.30)
out1 = ROOT / "viz" / "fig_mlr_with_age_slope_graphs.jpg"
plt.savefig(out1, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out1}")
plt.close(fig)


# ============================================================================
#                       FIGURE 2 — Interactive simple-slopes (age-controlled)
# ============================================================================
LOW_LANG_COLOR  = "#86efac"
MID_LANG_COLOR  = "#15803d"
HIGH_LANG_COLOR = "#052e16"

# Y range from predicted values across the three language levels
y_vals = []
for f in fits.values():
    for c in (-1, 1):
        for l in (-1, 0, 1):
            y_pred = f["beta1_i"]*c + f["beta2_i"]*l + f["beta4_i"]*c*l
            y_vals.append(y_pred)
y_max2 = max(abs(v) for v in y_vals) * 1.25
y_lim2 = (-y_max2, y_max2)

fig, axes = plt.subplots(8, 4, figsize=(15.0, 22.0), dpi=300,
                          sharex=True, sharey=True)

for i, outcome in enumerate(OUTCOMES):
    for j, (group, year) in enumerate(CELLS):
        ax = axes[i, j]
        key = (outcome, group, year)
        if key not in fits:
            ax.set_visible(False); continue
        f = fits[key]

        contact_range = np.linspace(-1, 1, 30)
        for language_z, color, label_lvl, lw in [
            (-1, LOW_LANG_COLOR,  "Low Lang.",  1.6),
            ( 0, MID_LANG_COLOR,  "Mean Lang.", 2.0),
            ( 1, HIGH_LANG_COLOR, "High Lang.", 2.4),
        ]:
            y_pred = (f["beta1_i"] * contact_range
                      + f["beta2_i"] * language_z
                      + f["beta4_i"] * contact_range * language_z)
            ax.plot(contact_range, y_pred, color=color, linewidth=lw,
                    solid_capstyle="round", zorder=3)

        ax.axhline(0, color="#999", linewidth=0.5, linestyle="--", zorder=1)
        ax.axvline(0, color="#999", linewidth=0.5, linestyle="--", zorder=1)

        p_val = f["p4_i"]
        if p_val < .001:
            p_str = "p < .001"
        else:
            p_str = f"p = {p_val:.3f}".replace("0.", ".")
        ax.text(0.98, 0.97,
                f"β₄ = {f['beta4_i']:+.3f}\n{stars(p_val)} ({p_str})",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=7, color="#222", family="monospace",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor="#aaa", linewidth=0.4, alpha=0.92))

        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(y_lim2)
        ax.set_xticks([-1, 0, 1])
        ax.set_xticklabels(["−1 SD", "0", "+1 SD"], fontsize=7)
        ax.tick_params(axis="both", labelsize=7, color="#888")
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        ax.grid(True, axis="y", linestyle=":", linewidth=0.3, color="#eee", zorder=0)
        if i == 0:
            ax.set_title(f"{group} {year}", fontsize=10, fontweight="bold",
                         pad=6, color="#333")

for i, outcome in enumerate(OUTCOMES):
    axes[i, 0].set_ylabel(PRETTY[outcome], fontsize=9, fontweight="bold",
                          color="#222", labelpad=8)
for j in range(4):
    axes[7, j].set_xlabel("Standardized Contact (SD)", fontsize=8, color="#555")

fig.text(0.04, 0.985,
         "Age-Controlled MLR with Contact × Language Interaction — Simple Slopes by Cell",
         fontsize=15, fontweight="bold", ha="left")
fig.text(0.04, 0.973,
         "Each panel shows contact's predicted standardized effect on the outcome at three language levels: low (−1 SD), mean, and high (+1 SD). Age controlled in the model.",
         fontsize=9, color="#444", ha="left")
fig.text(0.04, 0.963,
         "Parallel lines = no Contact × Language moderation (B₄ ≈ 0). Fan-out / convergence pattern = moderation, even after age control.",
         fontsize=9, color="#444", ha="left")

handles = [
    mlines.Line2D([], [], color=LOW_LANG_COLOR,  linewidth=1.6, label="Low Language (−1 SD)"),
    mlines.Line2D([], [], color=MID_LANG_COLOR,  linewidth=2.0, label="Mean Language"),
    mlines.Line2D([], [], color=HIGH_LANG_COLOR, linewidth=2.4, label="High Language (+1 SD)"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.99, 0.973),
           frameon=False, fontsize=9, ncol=1, handlelength=2.0)

fig.text(0.04, 0.015,
         "Predicted outcome in standardized (β) units. y = β₁ × Contact_z + β₂ × Language_z + β₄ × (Contact_z × Language_z). Age included in model but suppressed from plot.",
         fontsize=7.5, color="#555", ha="left")
fig.text(0.04, 0.005,
         "Significance for B₄ Contact × Language: *** p<.001, ** p<.01, * p<.05, ⁺ p<.10. HC3 robust SEs.",
         fontsize=7.5, color="#555", ha="left")

plt.subplots_adjust(left=0.13, right=0.985, top=0.95, bottom=0.025,
                    wspace=0.15, hspace=0.30)
out2 = ROOT / "viz" / "fig_mlr_with_age_interaction_simple_slopes.jpg"
plt.savefig(out2, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out2}")
