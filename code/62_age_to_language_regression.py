"""
Bivariate OLS: age -> out-group language ability, by group.

Russians:  age (T3) -> Estonian-language ability (Q71_1, reverse-coded)
Estonians: age (T3) -> Russian-language ability  (Q71_2, reverse-coded)

Q71 reverse-coded as 7 - x: 1 = no knowledge, 6 = native.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

CSV = "../data/EIM23.csv"
OUT_DIR = "../viz"
TSV = "_age_to_language_regression.tsv"


def to_num(s):
    return pd.to_numeric(s, errors="coerce")


def recode_lang(col):
    x = to_num(col).replace(9, np.nan)
    return 7 - x


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
    df["lang_estonian"] = recode_lang(df["Q71_1"])
    df["lang_russian"]  = recode_lang(df["Q71_2"])
    df["age"] = to_num(df["T3"])

    rus = df[df["ethnicity_binary"] == 1]
    est = df[df["ethnicity_binary"] == 0]

    res_rus = run_ols(rus["lang_estonian"], rus["age"],
                      "Russians: age -> Estonian-language ability")
    res_est = run_ols(est["lang_russian"],  est["age"],
                      "Estonians: age -> Russian-language ability")

    rows = [{k: r[k] for k in
             ("label","n","intercept","slope","se","ci_lo","ci_hi","t","p","r2")}
            for r in (res_rus, res_est)]
    tbl = pd.DataFrame(rows)
    tbl.to_csv(TSV, sep="\t", index=False)
    pd.set_option("display.float_format", lambda v: f"{v:.4f}")
    print(tbl.to_string(index=False))
    print()
    for r in (res_rus, res_est):
        print(r["label"])
        print(r["model"].summary().tables[1])
        print()

    # ---- regression scatter + fit ----
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    panels = [
        (axes[0], res_rus, "Russians", "Age (years)",
         "Estonian-language ability (1=none → 6=native)", "#d62728"),
        (axes[1], res_est, "Estonians", "Age (years)",
         "Russian-language ability (1=none → 6=native)", "#1f77b4"),
    ]
    for ax, r, title, xlab, ylab, color in panels:
        d = r["data"]
        rng = np.random.default_rng(0)
        # jitter only the integer-valued y; age is already continuous
        jy = d["y"] + rng.uniform(-0.18, 0.18, size=len(d))
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
        ax.set_ylim(0.5, 6.5)
        ax.grid(alpha=0.25)
    fig.suptitle("Age vs. out-group language ability (2023)", fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/fig_age_to_language_regression.jpg", dpi=300, bbox_inches="tight")

    # ---- coefficient plot ----
    fig2, ax2 = plt.subplots(figsize=(8.5, 3.2))
    labels = ["Russians:\nage → Estonian ability", "Estonians:\nage → Russian ability"]
    slopes = [res_rus["slope"], res_est["slope"]]
    los = [res_rus["ci_lo"], res_est["ci_lo"]]
    his = [res_rus["ci_hi"], res_est["ci_hi"]]
    colors = ["#d62728", "#1f77b4"]
    ys = np.arange(len(labels))[::-1]
    for y, s, lo, hi, c in zip(ys, slopes, los, his, colors):
        ax2.errorbar(s, y, xerr=[[s - lo], [hi - s]], fmt="o", color=c, ecolor=c,
                     markersize=9, capsize=5, lw=2)
    ax2.axvline(0, color="black", lw=1, alpha=0.6)
    ax2.set_yticks(ys); ax2.set_yticklabels(labels)
    ax2.set_xlabel("OLS slope (β) — change in language ability per 1 year of age")
    ax2.set_title("Coefficient plot: age → out-group language ability (2023)", fontsize=11)
    ax2.grid(axis="x", alpha=0.25)
    for y, s, p in zip(ys, slopes, (res_rus["p"], res_est["p"])):
        sig = "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "ns"
        ax2.annotate(f"β={s:+.4f}  {sig}", xy=(s, y), xytext=(8, 8),
                     textcoords="offset points", fontsize=9)
    fig2.tight_layout()
    fig2.savefig(f"{OUT_DIR}/fig_age_to_language_coefficients.jpg", dpi=300, bbox_inches="tight")

    print(f"\nSaved: {OUT_DIR}/fig_age_to_language_regression.jpg")
    print(f"Saved: {OUT_DIR}/fig_age_to_language_coefficients.jpg")
    print(f"Saved: code/{TSV}")


if __name__ == "__main__":
    main()
