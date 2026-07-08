"""
Bivariate OLS: out-group language ability -> SD Primary Out-group, by ethnic group.

Estonians: Russian-language ability (Q71_2)  -> SD toward Russian-speakers (Q57/58/59_1)
Russians:  Estonian-language ability (Q71_1) -> SD toward Estonian-speakers (Q57/58/59_2)

Q71 scale: 1=Native ... 6=No knowledge at all (9=DK).
Reverse-coded to lang_ability = 7 - Q71 so higher = better proficiency.

SD Primary: mean of three context items (1=very close ... 5=very distant); higher = more distance.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

CSV = "../data/EIM23.csv"
OUT_DIR = "../viz"
TSV = "_language_sd_regression.tsv"


def to_num(s):
    return pd.to_numeric(s, errors="coerce")


def recode_lang(col):
    x = to_num(col).replace(9, np.nan)
    return 7 - x


def sd_composite(df, suffix):
    items = [f"Q57_{suffix}", f"Q58_{suffix}", f"Q59_{suffix}"]
    raw = df[items].apply(to_num)
    raw = raw.where((raw >= 1) & (raw <= 5))
    return raw.mean(axis=1, skipna=True), items


def run_ols(y, x, label):
    d = pd.concat([y, x], axis=1).dropna()
    d.columns = ["y", "x"]
    X = sm.add_constant(d["x"])
    m = sm.OLS(d["y"], X).fit()
    ci = m.conf_int().loc["x"].tolist()
    return {
        "label": label,
        "n": int(m.nobs),
        "intercept": float(m.params["const"]),
        "slope": float(m.params["x"]),
        "se": float(m.bse["x"]),
        "ci_lo": float(ci[0]),
        "ci_hi": float(ci[1]),
        "t": float(m.tvalues["x"]),
        "p": float(m.pvalues["x"]),
        "r2": float(m.rsquared),
        "data": d,
        "model": m,
    }


def main():
    df = pd.read_csv(CSV, low_memory=False)
    df = df[df["ethnicity_binary"].isin([0, 1])].copy()

    df["lang_estonian"] = recode_lang(df["Q71_1"])  # how well speak Estonian
    df["lang_russian"] = recode_lang(df["Q71_2"])   # how well speak Russian

    est = df[df["ethnicity_binary"] == 0].copy()
    rus = df[df["ethnicity_binary"] == 1].copy()

    est["sd_primary"], _ = sd_composite(est, "1")  # Russian-speakers as out-group
    rus["sd_primary"], _ = sd_composite(rus, "2")  # Estonian-speakers as out-group

    res_est = run_ols(est["sd_primary"], est["lang_russian"],
                      "Estonians: Russian-language ability -> SD: Russian-speakers")
    res_rus = run_ols(rus["sd_primary"], rus["lang_estonian"],
                      "Russians: Estonian-language ability -> SD: Estonian-speakers")

    # ---- summary table to TSV + console ----
    rows = []
    for r in (res_est, res_rus):
        rows.append({k: r[k] for k in ("label","n","intercept","slope","se","ci_lo","ci_hi","t","p","r2")})
    tbl = pd.DataFrame(rows)
    tbl.to_csv(TSV, sep="\t", index=False)
    pd.set_option("display.float_format", lambda v: f"{v:.4f}")
    print(tbl.to_string(index=False))
    print()
    for r in (res_est, res_rus):
        print(r["label"])
        print(r["model"].summary().tables[1])
        print()

    # ---- regression scatter + fit ----
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    panels = [
        (axes[0], res_est, "Estonians", "Russian-language ability (1=none → 6=native)",
         "Social Distance: Russian-speakers", "#1f77b4"),
        (axes[1], res_rus, "Russians", "Estonian-language ability (1=none → 6=native)",
         "Social Distance: Estonian-speakers", "#d62728"),
    ]
    for ax, r, title, xlab, ylab, color in panels:
        d = r["data"]
        # jitter only x because it is integer-valued
        rng = np.random.default_rng(0)
        jx = d["x"] + rng.uniform(-0.15, 0.15, size=len(d))
        ax.scatter(jx, d["y"], s=12, alpha=0.30, color=color, edgecolor="none")
        xs = np.linspace(d["x"].min(), d["x"].max(), 100)
        ys = r["intercept"] + r["slope"] * xs
        ax.plot(xs, ys, color="black", lw=2)
        # 95% CI band for the mean line
        Xnew = sm.add_constant(xs)
        pred = r["model"].get_prediction(Xnew).summary_frame(alpha=0.05)
        ax.fill_between(xs, pred["mean_ci_lower"], pred["mean_ci_upper"],
                        color=color, alpha=0.18, linewidth=0)
        sig = "***" if r["p"] < .001 else "**" if r["p"] < .01 else "*" if r["p"] < .05 else "ns"
        ax.set_title(f"{title} (N={r['n']})\nβ={r['slope']:.3f}, SE={r['se']:.3f}, "
                     f"p={r['p']:.3g} {sig}, R²={r['r2']:.3f}", fontsize=10)
        ax.set_xlabel(xlab); ax.set_ylabel(ylab)
        ax.set_xlim(0.5, 6.5); ax.set_ylim(0.8, 5.2)
        ax.grid(alpha=0.25)
    fig.suptitle("Out-group language ability vs. Social Distance from primary out-group (2023)",
                 fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/fig_language_sd_regression.jpg", dpi=300, bbox_inches="tight")

    # ---- coefficient (forest) plot ----
    fig2, ax2 = plt.subplots(figsize=(8, 3.2))
    labels = ["Estonians:\nRussian-language ability", "Russians:\nEstonian-language ability"]
    slopes = [res_est["slope"], res_rus["slope"]]
    errs_lo = [res_est["slope"] - res_est["ci_lo"], res_rus["slope"] - res_rus["ci_lo"]]
    errs_hi = [res_est["ci_hi"] - res_est["slope"], res_rus["ci_hi"] - res_rus["slope"]]
    colors = ["#1f77b4", "#d62728"]
    ys = np.arange(len(labels))[::-1]
    for y, s, lo, hi, c in zip(ys, slopes, errs_lo, errs_hi, colors):
        ax2.errorbar(s, y, xerr=[[lo],[hi]], fmt="o", color=c, ecolor=c,
                     markersize=9, capsize=5, lw=2)
    ax2.axvline(0, color="black", lw=1, alpha=0.6)
    ax2.set_yticks(ys); ax2.set_yticklabels(labels)
    ax2.set_xlabel("OLS slope (β) — change in SD Primary per 1-step gain in language ability")
    ax2.set_title("Coefficient plot: out-group language ability → SD Primary (2023)", fontsize=11)
    ax2.grid(axis="x", alpha=0.25)
    for y, s, p in zip(ys, slopes, (res_est["p"], res_rus["p"])):
        sig = "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "ns"
        ax2.annotate(f"β={s:.3f}  {sig}", xy=(s, y), xytext=(8, 8),
                     textcoords="offset points", fontsize=9)
    fig2.tight_layout()
    fig2.savefig(f"{OUT_DIR}/fig_language_sd_coefficients.jpg", dpi=300, bbox_inches="tight")

    print(f"\nSaved: {OUT_DIR}/fig_language_sd_regression.jpg")
    print(f"Saved: {OUT_DIR}/fig_language_sd_coefficients.jpg")
    print(f"Saved: code/{TSV}")


if __name__ == "__main__":
    main()
