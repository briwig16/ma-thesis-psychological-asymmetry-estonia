"""
Multivariate OLS: out-group language ability + age -> SD Primary Out-group, by group.

Predictors:
  lang_ability — reverse-coded Q71_x (1=none ... 6=native), out-group language
  age          — T3 (years)

Outcome:
  SD Primary — mean of Q57/58/59_{1 for Estonians, 2 for Russians}; higher = more distance.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

CSV = "../data/EIM23.csv"
OUT_DIR = "../viz"
TSV = "_language_age_sd_regression.tsv"


def to_num(s):
    return pd.to_numeric(s, errors="coerce")


def recode_lang(col):
    x = to_num(col).replace(9, np.nan)
    return 7 - x


def sd_composite(df, suffix):
    items = [f"Q57_{suffix}", f"Q58_{suffix}", f"Q59_{suffix}"]
    raw = df[items].apply(to_num)
    raw = raw.where((raw >= 1) & (raw <= 5))
    return raw.mean(axis=1, skipna=True)


def run_ols(y, X_df, label):
    d = pd.concat([y, X_df], axis=1).dropna()
    y_ = d.iloc[:, 0]
    X_ = sm.add_constant(d.iloc[:, 1:])
    m = sm.OLS(y_, X_).fit()
    out = {"label": label, "n": int(m.nobs), "r2": float(m.rsquared),
           "r2_adj": float(m.rsquared_adj), "model": m, "data": d}
    for name in X_.columns:
        ci = m.conf_int().loc[name].tolist()
        out[name] = {
            "coef": float(m.params[name]),
            "se": float(m.bse[name]),
            "ci_lo": float(ci[0]),
            "ci_hi": float(ci[1]),
            "t": float(m.tvalues[name]),
            "p": float(m.pvalues[name]),
        }
    return out


def main():
    df = pd.read_csv(CSV, low_memory=False)
    df = df[df["ethnicity_binary"].isin([0, 1])].copy()
    df["lang_estonian"] = recode_lang(df["Q71_1"])
    df["lang_russian"]  = recode_lang(df["Q71_2"])
    df["age"] = to_num(df["T3"])

    est = df[df["ethnicity_binary"] == 0].copy()
    rus = df[df["ethnicity_binary"] == 1].copy()
    est["sd_primary"] = sd_composite(est, "1")
    rus["sd_primary"] = sd_composite(rus, "2")

    res_est = run_ols(est["sd_primary"], est[["lang_russian", "age"]],
                      "Estonians: Russian-language ability + age -> SD: Russian-speakers")
    res_rus = run_ols(rus["sd_primary"], rus[["lang_estonian", "age"]],
                      "Russians: Estonian-language ability + age -> SD: Estonian-speakers")

    # ---- summary table ----
    rows = []
    for r, lang_key in ((res_est, "lang_russian"), (res_rus, "lang_estonian")):
        rows.append({
            "label": r["label"], "N": r["n"], "R2": r["r2"], "R2_adj": r["r2_adj"],
            "intercept": r["const"]["coef"],
            "b_lang": r[lang_key]["coef"], "se_lang": r[lang_key]["se"],
            "lang_ci_lo": r[lang_key]["ci_lo"], "lang_ci_hi": r[lang_key]["ci_hi"],
            "p_lang": r[lang_key]["p"],
            "b_age": r["age"]["coef"], "se_age": r["age"]["se"],
            "age_ci_lo": r["age"]["ci_lo"], "age_ci_hi": r["age"]["ci_hi"],
            "p_age": r["age"]["p"],
        })
    tbl = pd.DataFrame(rows)
    tbl.to_csv(TSV, sep="\t", index=False)
    pd.set_option("display.float_format", lambda v: f"{v:.4f}")
    print(tbl.to_string(index=False))
    print()
    for r in (res_est, res_rus):
        print(r["label"])
        print(r["model"].summary().tables[1])
        print()

    # ---- partial-regression scatter: language slope, holding age constant ----
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    panels = [
        (axes[0], res_est, "lang_russian", "Estonians",
         "Russian-language ability (1=none → 6=native)",
         "Social Distance: Russian-speakers (partial)", "#1f77b4"),
        (axes[1], res_rus, "lang_estonian", "Russians",
         "Estonian-language ability (1=none → 6=native)",
         "Social Distance: Estonian-speakers (partial)", "#d62728"),
    ]
    for ax, r, key, title, xlab, ylab, color in panels:
        d = r["data"].copy()
        # Partial-regression (added-variable) plot for language: residualize y and lang on age
        m_y = sm.OLS(d["sd_primary"], sm.add_constant(d["age"])).fit()
        m_x = sm.OLS(d[key],          sm.add_constant(d["age"])).fit()
        ry = d["sd_primary"] - m_y.predict(sm.add_constant(d["age"]))
        rx = d[key]          - m_x.predict(sm.add_constant(d["age"]))
        rng = np.random.default_rng(0)
        jx = rx + rng.uniform(-0.08, 0.08, size=len(rx))
        ax.scatter(jx, ry, s=12, alpha=0.30, color=color, edgecolor="none")
        b = r[key]["coef"]
        xs = np.linspace(rx.min(), rx.max(), 100)
        ax.plot(xs, b * xs, color="black", lw=2)
        ax.axhline(0, color="grey", lw=0.7, alpha=0.5)
        ax.axvline(0, color="grey", lw=0.7, alpha=0.5)
        p = r[key]["p"]
        sig = "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "ns"
        ax.set_title(f"{title} (N={r['n']}, R²={r['r2']:.3f})\n"
                     f"β_lang|age={b:.3f}, SE={r[key]['se']:.3f}, p={p:.3g} {sig}",
                     fontsize=10)
        ax.set_xlabel(f"{xlab}  (residualized on age)")
        ax.set_ylabel(ylab)
        ax.grid(alpha=0.25)
    fig.suptitle("Language ability → SD Primary, controlling for age (added-variable plot, 2023)",
                 fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/fig_language_age_sd_regression.jpg", dpi=300, bbox_inches="tight")

    # ---- coefficient plot: 4 standardized coefficients ----
    # Standardize so language (6-pt) and age (years) live on a comparable axis.
    def standardize_betas(res, key):
        d = res["data"]
        sx_lang = d[key].std()
        sx_age  = d["age"].std()
        sy      = d["sd_primary"].std()
        return {
            "lang": (res[key]["coef"] * sx_lang / sy,
                     res[key]["ci_lo"] * sx_lang / sy,
                     res[key]["ci_hi"] * sx_lang / sy,
                     res[key]["p"]),
            "age":  (res["age"]["coef"] * sx_age / sy,
                     res["age"]["ci_lo"] * sx_age / sy,
                     res["age"]["ci_hi"] * sx_age / sy,
                     res["age"]["p"]),
        }
    sb_est = standardize_betas(res_est, "lang_russian")
    sb_rus = standardize_betas(res_rus, "lang_estonian")

    fig2, ax2 = plt.subplots(figsize=(9, 4.2))
    rows = [
        ("Estonians: Russian lang. (out-group)", sb_est["lang"], "#1f77b4"),
        ("Estonians: age",                       sb_est["age"],  "#1f77b4"),
        ("Russians: Estonian lang. (out-group)", sb_rus["lang"], "#d62728"),
        ("Russians: age",                        sb_rus["age"],  "#d62728"),
    ]
    ys = np.arange(len(rows))[::-1]
    for y, (lab, vals, c) in zip(ys, rows):
        b, lo, hi, p = vals
        ax2.errorbar(b, y, xerr=[[b - lo], [hi - b]], fmt="o", color=c, ecolor=c,
                     markersize=9, capsize=5, lw=2)
        sig = "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "ns"
        ax2.annotate(f"β*={b:+.3f}  {sig}", xy=(b, y), xytext=(8, 8),
                     textcoords="offset points", fontsize=9)
    ax2.axvline(0, color="black", lw=1, alpha=0.6)
    ax2.set_yticks(ys); ax2.set_yticklabels([r[0] for r in rows])
    ax2.set_xlabel("Standardized OLS coefficient (β*) — SD Primary as outcome")
    ax2.set_title("Coefficient plot: out-group language ability + age → SD Primary (2023, std.)",
                  fontsize=11)
    ax2.grid(axis="x", alpha=0.25)
    fig2.tight_layout()
    fig2.savefig(f"{OUT_DIR}/fig_language_age_sd_coefficients.jpg", dpi=300, bbox_inches="tight")

    print(f"\nSaved: {OUT_DIR}/fig_language_age_sd_regression.jpg")
    print(f"Saved: {OUT_DIR}/fig_language_age_sd_coefficients.jpg")
    print(f"Saved: code/{TSV}")


if __name__ == "__main__":
    main()
