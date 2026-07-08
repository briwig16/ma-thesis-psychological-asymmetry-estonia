"""
Paired comparison — Estonian SD: Primary vs. SD: General Out-group
==================================================================
Tests whether Estonians' average social distance from their PRIMARY out-group
(Russian-speakers) differs from their social distance from GENERAL out-groups
(2020: 'new immigrants'; 2023: 'other Europeans' + 'non-Europeans').

This is the falsification test flagged in SESSION_LOG §29: did Estonians get
selectively more reluctant toward Russian-speakers (war-shock signature), or
toward out-groups in general?

Method: paired sample restricted to Estonians with BOTH composites available.
  - Welch's paired t-test (scipy.stats.ttest_rel)
  - Wilcoxon signed-rank (non-parametric alternative)
  - Cohen's d_z for paired samples = mean(diff) / sd(diff)

Run for 2020 AND 2023, plus Russian respondents as a symmetric comparison.

Direction reminder: scale 1–5, no reverse coding, higher = more distance.
A POSITIVE d_z means the respondent rates their PRIMARY out-group as more
socially distant than general out-groups.
"""

import math
from pathlib import Path
import pandas as pd
import pyreadstat
from scipy import stats

ROOT = Path(__file__).parent.parent

df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy()

df20, _ = pyreadstat.read_sav(str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"),
                              encoding="latin1")
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy()


def composite(df, items):
    sub = df[items].apply(pd.to_numeric, errors="coerce").where(lambda x: x != 9)
    return sub.mean(axis=1, skipna=True)


def paired_test(primary, general, label):
    paired = pd.concat([primary.rename("primary"),
                        general.rename("general")], axis=1).dropna()
    n = len(paired)
    if n < 2:
        print(f"\n  {label}: insufficient paired data (N={n})")
        return
    diff = paired["primary"] - paired["general"]
    m_diff, sd_diff = diff.mean(), diff.std(ddof=1)
    d_z = m_diff / sd_diff if sd_diff > 0 else float("nan")
    se_dz = math.sqrt(1/n + d_z**2 / (2*n))
    ci_lo, ci_hi = d_z - 1.96 * se_dz, d_z + 1.96 * se_dz
    t_stat, p_t = stats.ttest_rel(paired["primary"], paired["general"])
    w_stat, p_w = stats.wilcoxon(paired["primary"], paired["general"],
                                  zero_method="wilcox", alternative="two-sided")

    star = "***" if p_t < .001 else "**" if p_t < .01 else "*" if p_t < .05 else "ns"
    print(f"\n  {label}")
    print(f"    Paired N           = {n}")
    print(f"    M(Primary)         = {paired['primary'].mean():.3f}  "
          f"SD = {paired['primary'].std(ddof=1):.3f}")
    print(f"    M(General)         = {paired['general'].mean():.3f}  "
          f"SD = {paired['general'].std(ddof=1):.3f}")
    print(f"    Mean diff (P − G)  = {m_diff:+.3f}   SD(diff) = {sd_diff:.3f}")
    print(f"    Cohen's d_z        = {d_z:+.3f}   95% CI [{ci_lo:+.3f}, {ci_hi:+.3f}]")
    print(f"    Paired t({n-1})        = {t_stat:+.3f}   p = {p_t:.6f}  {star}")
    print(f"    Wilcoxon W         = {w_stat:.1f}     p = {p_w:.6f}")


print("="*92)
print("PAIRED COMPARISON — SD: Primary Out-group  vs.  SD: General Out-group")
print("="*92)
print("Direction: scale 1–5, higher = more distance.")
print("Positive d_z means respondent rates their PRIMARY out-group as more distant than general out-groups.")

# ---------- Estonian ------------------------------------------------------
print("\n" + "-"*92)
print("ESTONIAN respondents")
print("-"*92)

est_pri_2023 = composite(df23[df23["ethnicity_binary"]==0],
                         ["Q57_1", "Q58_1", "Q59_1"])
est_gen_2023 = composite(df23[df23["ethnicity_binary"]==0],
                         ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"])
paired_test(est_pri_2023, est_gen_2023,
            "2023 — Estonian Primary (Russian-speakers) vs. General (Eur+nonEur)")

est_pri_2020 = composite(df20[df20["ethnicity_binary"]==0],
                         ["K4X7_1", "K4X8_1", "K4X9_1"])
est_gen_2020 = composite(df20[df20["ethnicity_binary"]==0],
                         ["K4X7_3", "K4X8_3", "K4X9_3"])
paired_test(est_pri_2020, est_gen_2020,
            "2020 — Estonian Primary (Russian-speakers) vs. General (new immigrants)")

# ---------- Russian (symmetric comparison) --------------------------------
print("\n" + "-"*92)
print("RUSSIAN respondents (symmetric comparison)")
print("-"*92)

rus_pri_2023 = composite(df23[df23["ethnicity_binary"]==1],
                         ["Q57_2", "Q58_2", "Q59_2"])
rus_gen_2023 = composite(df23[df23["ethnicity_binary"]==1],
                         ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"])
paired_test(rus_pri_2023, rus_gen_2023,
            "2023 — Russian Primary (Estonian-speakers) vs. General (Eur+nonEur)")

rus_pri_2020 = composite(df20[df20["ethnicity_binary"]==1],
                         ["K4X7_2", "K4X8_2", "K4X9_2"])
rus_gen_2020 = composite(df20[df20["ethnicity_binary"]==1],
                         ["K4X7_3", "K4X8_3", "K4X9_3"])
paired_test(rus_pri_2020, rus_gen_2020,
            "2020 — Russian Primary (Estonian-speakers) vs. General (new immigrants)")
