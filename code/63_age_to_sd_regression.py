"""
Bivariate OLS: age (T3) -> SD Primary Out-group, by group.

Estonians: SD toward Russian-speakers   (Q57/58/59_1)
Russians:  SD toward Estonian-speakers  (Q57/58/59_2)
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

CSV = "../data/EIM23.csv"
OUT_DIR = "../viz"
TSV = "_age_to_sd_regression.tsv"


def to_num(s):
    return pd.to_numeric(s, errors="coerce")


def sd_composite(df, suffix):
    items = [f"Q57_{suffix}", f"Q58_{suffix}", f"Q59_{suffix}"]
    raw = df[items].apply(to_num)
    raw = raw.where((raw >= 1) & (raw <= 5))
    return raw.mean(axis=1, skipna=True)


def run_ols(y, x, label):
    d = pd.concat([y, x], axis=1).dropna()
    d.columns = ["y", "x"]
    X = sm.add_constant(d["x"])
    m = sm.OLS(d["y"], X).fit()
    ci = m.conf_int().loc["x"].tolist()
    return {
        "label": label, "n": int(m.nobs),
        "intercept": float(m.params["const"]),
        "slope": float(m.params["x"]), "se": float(m.bse["x"]),
        "ci_lo": float(ci[0]), "ci_hi": float(ci[1]),
        "t": float(m.tvalues["x"]), "p": float(m.pvalues["x"]),
        "r2": float(m.rsquared), "data": d, "model": m,
    }


def main():
    df = pd.read_csv(CSV, low_memory=False)
    df = df[df["ethnicity_binary"].isin([0, 1])].copy()
    df["age"] = to_num(df["T3"])

    est = df[df["ethnicity_binary"] == 0].copy()
    rus = df[df["ethnicity_binary"] == 1].copy()
    est["sd_primary"] = sd_composite(est, "1")
    rus["sd_primary"] = sd_composite(rus, "2")

    res_est = run_ols(est["sd_primary"], est["age"],
                      "Estonians: age -> SD: Russian-speakers")
    res_rus = run_ols(rus["sd_primary"], rus["age"],
                      "Russians: age -> SD: Estonian-speakers")

    rows = [{k: r[k] for k in
             ("label","n","intercept","slope","se","ci_lo","ci_hi","t","p","r2")}
            for r in (res_est, res_rus)]
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
        (axes[0], res_est, "Estonians", "Age (years)",
         "Social Distance: Russian-speakers", "#1f77b4"),
        (axes[1], res_rus, "Russians", "Age (years)",
         "Social Distance: Estonian-speakers", "#d62728"),
    ]
    for ax, r, title, xlab, ylab, color in panels:
        d = r["data"]
        rng = np.random.default_rng(0)
        # jitter the (composite) y to break ties from 1/3-step bins
        jy = d["y"] + rng.uniform(-0.06, 0.06, size=len(d))
        ax.scatter(d["x"], jy, s=12, alpha=0.30, color=color, edgecolor="none")
        xs = np.linspace(d["x"].min(), d["x"].max(), 100)
        ys = r["intercept"] + r["slope"] * xs
        ax.plot(xs, ys, color="black", lw=2)
        Xnew = sm.add_constant(xs)
        pred = r["model"].get_prediction(Xnew).summary_frame(alpha=0.05)
        ax.fill_between(xs, pred["mean_ci_lower"], pred["mean_ci_upper"],
                        color=color, alpha=0.18, linewidth=0)
        sig = "***" if r["p"] < .001 else "**" if r["p"] < .01 else "*" if r["p"] < .05 else "ns"
        ax.set_title(f"{title} (N={r['n']})\nβ={r['slope']:.4f}, SE={r['se']:.4f}, "
                     f"p={r['p']:.3g} {sig}, R²={r['r2']:.3f}", fontsize=10)
        ax.set_xlabel(xlab); ax.set_ylabel(ylab)
        ax.set_ylim(0.8, 5.2)
        ax.grid(alpha=0.25)
    fig.suptitle("Age vs. Social Distance from primary out-group (2023)", fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/fig_age_to_sd_regression.jpg", dpi=300, bbox_inches="tight")

    # ---- coefficient plot ----
    fig2, ax2 = plt.subplots(figsize=(8.5, 3.2))
    labels = ["Estonians:\nage → SD (Russian-speakers)",
              "Russians:\nage → SD (Estonian-speakers)"]
    slopes = [res_est["slope"], res_rus["slope"]]
    los = [res_est["ci_lo"], res_rus["ci_lo"]]
    his = [res_est["ci_hi"], res_rus["ci_hi"]]
    colors = ["#1f77b4", "#d62728"]
    ys = np.arange(len(labels))[::-1]
    for y, s, lo, hi, c in zip(ys, slopes, los, his, colors):
        ax2.errorbar(s, y, xerr=[[s - lo], [hi - s]], fmt="o", color=c, ecolor=c,
                     markersize=9, capsize=5, lw=2)
    ax2.axvline(0, color="black", lw=1, alpha=0.6)
    ax2.set_yticks(ys); ax2.set_yticklabels(labels)
    ax2.set_xlabel("OLS slope (β) — change in SD Primary per 1 year of age")
    ax2.set_title("Coefficient plot: age → SD Primary (2023)", fontsize=11)
    ax2.grid(axis="x", alpha=0.25)
    for y, s, p in zip(ys, slopes, (res_est["p"], res_rus["p"])):
        sig = "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "ns"
        ax2.annotate(f"β={s:+.4f}  {sig}", xy=(s, y), xytext=(8, 8),
                     textcoords="offset points", fontsize=9)
    fig2.tight_layout()
    fig2.savefig(f"{OUT_DIR}/fig_age_to_sd_coefficients.jpg", dpi=300, bbox_inches="tight")

    print(f"\nSaved: {OUT_DIR}/fig_age_to_sd_regression.jpg")
    print(f"Saved: {OUT_DIR}/fig_age_to_sd_coefficients.jpg")
    print(f"Saved: code/{TSV}")


if __name__ == "__main__":
    main()
