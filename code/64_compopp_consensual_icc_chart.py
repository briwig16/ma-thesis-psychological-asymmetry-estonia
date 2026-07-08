"""
Visualisation — Consensual ICC analysis of Comparative Opportunity Assessment
==============================================================================
Two-panel figure paired with code/63's numeric output:

  Top panel:    Composite-level variance decomposition (proportional stacked
                bar per year) — Dissensual / Consensual / Error. Headline
                ICC printed at the right edge of each bar.

  Bottom panel: Item-level raw ICC ranking. 12 items as horizontal dot pairs,
                2020 (open) → 2023 (filled). Sorted by 2023 ICC ascending so
                the most-contested items sit at the top and the most-
                consensual at the bottom. Reference lines mark common
                thresholds (>0.85 highly consensual, <0.50 dissensual).

Output: viz/fig_compopp_consensual_icc.jpg  (300 DPI)
"""

from pathlib import Path
import pandas as pd
import numpy as np
import pyreadstat
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

ITEM_LABELS = [
    "Material well-being",
    "Cultural participation",
    "Education",
    "Social / political rights",
    "Entrepreneurship",
    "Career & jobs",
    "Medical care",
    "Housing",
    "Leisure & holidays",
    "Children & youth opportunities",
    "Sports & exercise",
    "State benefits / services",
]


# ---------- Load data -------------------------------------------------------
df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy()

df20, _ = pyreadstat.read_sav(str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"),
                              encoding="latin1")
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy()


def cronbach_alpha(item_matrix):
    M = item_matrix.dropna()
    k = M.shape[1]
    item_vars = M.var(axis=0, ddof=1).sum()
    total_var = M.sum(axis=1).var(ddof=1)
    return (k / (k - 1)) * (1 - item_vars / total_var)


def variance_decomposition(scores, group_labels):
    df = pd.DataFrame({"x": scores, "g": group_labels}).dropna()
    N = len(df)
    overall_M = df["x"].mean()
    grouped = df.groupby("g")["x"]
    n_g = grouped.count()
    M_g = grouped.mean()
    var_g = grouped.var(ddof=1)
    var_between = (n_g * (M_g - overall_M) ** 2).sum() / (N - 1)
    var_within = (n_g * var_g).sum() / (N - 1)
    return float(var_between), float(var_within), int(N)


def composite_decomp(df, items):
    raw = df[items].apply(pd.to_numeric, errors="coerce").where(lambda x: x != 9)
    composite = raw.mean(axis=1, skipna=True)
    alpha = cronbach_alpha(raw)
    var_b, var_w, N = variance_decomposition(composite, df["ethnicity_binary"])
    var_c = alpha * var_w
    var_e = (1 - alpha) * var_w
    icc = var_c / (var_b + var_c) if (var_b + var_c) > 0 else float("nan")
    return {"alpha": alpha, "N": N,
            "var_dissensual": var_b, "var_consensual": var_c, "var_error": var_e,
            "icc": icc}


def item_decomp_raw(s, group_labels):
    s_num = pd.to_numeric(s, errors="coerce").where(lambda x: x != 9)
    var_b, var_w, _ = variance_decomposition(s_num, group_labels)
    if var_b + var_w == 0:
        return float("nan")
    return var_w / (var_b + var_w)


items_2020 = [f"K3X1_{i}" for i in range(1, 13)]
items_2023 = [f"Q44_{i}"  for i in range(1, 13)]

c20 = composite_decomp(df20, items_2020)
c23 = composite_decomp(df23, items_2023)

item_data = []
for i, label in enumerate(ITEM_LABELS, start=1):
    icc20 = item_decomp_raw(df20[f"K3X1_{i}"], df20["ethnicity_binary"])
    icc23 = item_decomp_raw(df23[f"Q44_{i}"],  df23["ethnicity_binary"])
    item_data.append({"idx": i, "label": label, "icc20": icc20, "icc23": icc23})

# Sort items by 2023 ICC ascending (most contested at top of plot)
item_data.sort(key=lambda r: r["icc23"])


# ---------- Style ----------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.6,
})

C_DISSENSUAL = "#b45309"   # warm amber — between-group disagreement
C_CONSENSUAL = "#155e75"   # deep teal  — shared / consensual
C_ERROR      = "#cbd5e1"   # light gray — random
LINE_2020    = "#9ca3af"
LINE_2023    = "#1f2937"

fig = plt.figure(figsize=(11.5, 9.5), dpi=300)
gs = gridspec.GridSpec(
    2, 1,
    height_ratios=[0.9, 2.2],
    hspace=0.35,
    left=0.30, right=0.96, top=0.86, bottom=0.07
)


# =========================================================================
# Top panel — composite-level variance decomposition (stacked, proportional)
# =========================================================================
ax_top = fig.add_subplot(gs[0, 0])

years = ["2020", "2023"]
results = [c20, c23]
y_pos_top = np.array([1.0, 0.0])
bar_h = 0.45

for y, year, r in zip(y_pos_top, years, results):
    total = r["var_dissensual"] + r["var_consensual"] + r["var_error"]
    p_d = r["var_dissensual"] / total
    p_c = r["var_consensual"] / total
    p_e = r["var_error"] / total

    ax_top.barh(y, p_d, left=0,             height=bar_h,
                color=C_DISSENSUAL, edgecolor="white", linewidth=1.0, zorder=2)
    ax_top.barh(y, p_c, left=p_d,           height=bar_h,
                color=C_CONSENSUAL, edgecolor="white", linewidth=1.0, zorder=2)
    ax_top.barh(y, p_e, left=p_d + p_c,     height=bar_h,
                color=C_ERROR,      edgecolor="white", linewidth=1.0, zorder=2)

    # In-bar percentage labels (only show if segment is wide enough)
    def lbl(center, pct, color):
        if pct >= 0.06:
            ax_top.text(center, y, f"{pct*100:.0f}%",
                        ha="center", va="center", fontsize=9,
                        color=color, fontweight="bold")
    lbl(p_d / 2,             p_d, "white")
    lbl(p_d + p_c / 2,       p_c, "white")
    lbl(p_d + p_c + p_e / 2, p_e, "#444")

    # Year label on the left, ICC on the right
    ax_top.text(-0.012, y, year, ha="right", va="center",
                fontsize=11, fontweight="bold", color="#111")
    ax_top.text(1.008, y, f"ICC = {r['icc']:.3f}", ha="left", va="center",
                fontsize=10, color="#111", fontweight="bold")
    ax_top.text(1.008, y - 0.18, f"α = {r['alpha']:.3f}", ha="left", va="center",
                fontsize=8, color="#666")

ax_top.set_xlim(-0.04, 1.18)
ax_top.set_ylim(-0.6, 1.6)
ax_top.set_yticks([])
ax_top.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
ax_top.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=8, color="#666")
ax_top.set_xlabel("Proportion of total variance", fontsize=9, labelpad=6, color="#444")
for s_ in ("top", "right", "left"):
    ax_top.spines[s_].set_visible(False)
ax_top.spines["bottom"].set_color("#888")
ax_top.tick_params(axis="x", length=2.5, color="#888")
ax_top.tick_params(axis="y", length=0)

ax_top.set_title("Composite-level variance decomposition",
                 fontsize=11, fontweight="bold", loc="left", pad=8, color="#111")


# =========================================================================
# Bottom panel — item-level ICC ranking
# =========================================================================
ax_bot = fig.add_subplot(gs[1, 0])

n_items = len(item_data)
y_pos = np.arange(n_items)[::-1]   # most contested at top

# Reference shading: <0.50 dissensual zone, >0.85 highly consensual zone
ax_bot.axvspan(0.0,  0.50, color="#fef3c7", alpha=0.45, zorder=0)
ax_bot.axvspan(0.85, 1.00, color="#cffafe", alpha=0.40, zorder=0)
ax_bot.axvline(0.50, color="#b45309", linestyle=(0, (3, 3)), linewidth=0.7, alpha=0.6, zorder=1)
ax_bot.axvline(0.85, color="#155e75", linestyle=(0, (3, 3)), linewidth=0.7, alpha=0.6, zorder=1)

# Zone labels at top
ax_bot.text(0.25, n_items - 0.4, "Dissensual zone\n(<0.50)",
            ha="center", va="bottom", fontsize=7.5, color="#92400e",
            style="italic", linespacing=1.2)
ax_bot.text(0.93, n_items - 0.4, "Highly consensual\n(≥0.85)",
            ha="center", va="bottom", fontsize=7.5, color="#155e75",
            style="italic", linespacing=1.2)

for i, r in enumerate(item_data):
    y = y_pos[i]
    icc20, icc23 = r["icc20"], r["icc23"]

    # Connector
    ax_bot.plot([icc20, icc23], [y, y],
                color="#666", linewidth=1.1, alpha=0.85, zorder=2)
    # 2020 dot (open)
    ax_bot.scatter([icc20], [y], s=70, facecolors="white",
                   edgecolors=LINE_2020, linewidths=1.5, zorder=3)
    # 2023 dot (filled)
    ax_bot.scatter([icc23], [y], s=78, color=LINE_2023, edgecolors="white",
                   linewidths=0.8, zorder=3)
    # Inline labels: 2020 to the left of its dot, 2023 to the right of its dot
    if icc20 < icc23:
        ax_bot.text(icc20 - 0.012, y, f"{icc20:.2f}",
                    ha="right", va="center", fontsize=7.4,
                    color="#666")
        ax_bot.text(icc23 + 0.012, y, f"{icc23:.2f}",
                    ha="left", va="center", fontsize=7.6,
                    color="#111", fontweight="bold")
    else:
        ax_bot.text(icc20 + 0.012, y, f"{icc20:.2f}",
                    ha="left", va="center", fontsize=7.4, color="#666")
        ax_bot.text(icc23 - 0.012, y, f"{icc23:.2f}",
                    ha="right", va="center", fontsize=7.6,
                    color="#111", fontweight="bold")

ax_bot.set_yticks(y_pos)
ax_bot.set_yticklabels(
    [f"Q44_{r['idx']}  {r['label']}" for r in item_data],
    fontsize=9
)
ax_bot.set_xlim(0.05, 1.07)
ax_bot.set_xticks([0.0, 0.25, 0.5, 0.75, 1.0])
ax_bot.set_ylim(-0.7, n_items + 0.2)
ax_bot.set_xlabel("Item-level raw ICC (within-group variance ÷ total non-error variance)",
                  fontsize=9, color="#444", labelpad=6)
for s_ in ("top", "right"):
    ax_bot.spines[s_].set_visible(False)
ax_bot.spines["left"].set_color("#888")
ax_bot.spines["bottom"].set_color("#888")
ax_bot.tick_params(axis="x", length=2.5, color="#888", labelsize=8)
ax_bot.tick_params(axis="y", length=0)

ax_bot.set_title("Item-level raw ICC ranking — most contested (top) → most consensual (bottom)",
                 fontsize=11, fontweight="bold", loc="left", pad=8, color="#111")


# =========================================================================
# Title, subtitle, legend, footer
# =========================================================================
fig.text(0.025, 0.965,
         "Comparative Opportunity Assessment — Consensual vs. Dissensual Variance",
         fontsize=13.5, fontweight="bold", ha="left")
fig.text(0.025, 0.943,
         "Sidanius & Pratto's variance decomposition: how much of the variance in perceived comparative opportunity reflects",
         fontsize=9, color="#444", ha="left")
fig.text(0.025, 0.928,
         "shared individual differences (consensual) vs. systematic disagreement between Estonian and Russian respondents (dissensual)?",
         fontsize=9, color="#444", ha="left")

# Legend
diss_patch = mlines.Line2D([], [], marker="s", color="white",
                           markerfacecolor=C_DISSENSUAL, markersize=10,
                           linestyle="None", label="Dissensual (between-group)")
cons_patch = mlines.Line2D([], [], marker="s", color="white",
                           markerfacecolor=C_CONSENSUAL, markersize=10,
                           linestyle="None", label="Consensual (α × within-group)")
err_patch  = mlines.Line2D([], [], marker="s", color="white",
                           markerfacecolor=C_ERROR, markersize=10, markeredgecolor="#888",
                           linestyle="None", label="Random error ((1−α) × within-group)")
y20_dot    = mlines.Line2D([], [], marker="o", color="white",
                           markerfacecolor="white", markeredgecolor=LINE_2020,
                           markersize=8, linestyle="None", label="2020 (open)")
y23_dot    = mlines.Line2D([], [], marker="o", color="white",
                           markerfacecolor=LINE_2023, markeredgecolor=LINE_2023,
                           markersize=8, linestyle="None", label="2023 (filled)")
fig.legend(handles=[diss_patch, cons_patch, err_patch, y20_dot, y23_dot],
           loc="upper center", bbox_to_anchor=(0.5, 0.910),
           frameon=False, fontsize=8, ncol=5,
           handlelength=1.4, columnspacing=1.6)

# Footer
fig.text(0.025, 0.025,
         "ICC = σ²_Consensual / (σ²_Dissensual + σ²_Consensual). Values near 1 indicate the construct functions as a consensual legitimizing belief shared across groups; values near 0 indicate ideological conflict.",
         fontsize=7, color="#555", ha="left")
fig.text(0.025, 0.012,
         "Item-level ICCs are 'raw' (no α adjustment, no error component subtracted) and so are upper bounds. Composite-level ICCs incorporate the α correction.",
         fontsize=7, color="#555", ha="left")

out_path = ROOT / "viz" / "fig_compopp_consensual_icc.jpg"
plt.savefig(out_path, dpi=300, format="jpg",
            facecolor="white", pil_kwargs={"quality": 95})
print(f"Saved: {out_path}")

# Also print the data shown in the chart for traceability
print()
print(f"Composite ICC: 2020 = {c20['icc']:.4f}, 2023 = {c23['icc']:.4f}")
print(f"Composite α:   2020 = {c20['alpha']:.4f}, 2023 = {c23['alpha']:.4f}")
print()
print("Item-level ICCs (sorted by 2023 ascending):")
for r in item_data:
    print(f"  Q44_{r['idx']:<2d}  {r['label']:<32s}  "
          f"2020 = {r['icc20']:.4f}   2023 = {r['icc23']:.4f}   "
          f"Δ = {r['icc23']-r['icc20']:+.4f}")
