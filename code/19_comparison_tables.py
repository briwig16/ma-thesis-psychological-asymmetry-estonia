"""
Cross-Year Comparison Tables
==============================
Produces the between-group (Estonian vs Russian) and within-group (2020 → 2023)
comparison tables for all 8 composite variables.

Uses Cohen's d with root-mean-square SD: d = (M1 - M2) / sqrt((SD1² + SD2²) / 2)
Uses Welch's t-test (unequal variances).

Reads:
  - ../data/EIM23.csv (2023 composites, built by scripts 01-04)
  - ../data/EIM2020_composites.csv (2020 composites, built by script 17)
"""

import pandas as pd
import numpy as np
from scipy import stats

# ─── Load data ───────────────────────────────────────────────────────────────
df23 = pd.read_csv("../data/EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy()

df20 = pd.read_csv("../data/EIM2020_composites.csv")
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy()

# ─── Build 2023 composites inline (matching script logic) ────────────────────
# We need all 8 composites for 2023. composite_belonging is already in the CSV.
# The others were computed inline in prior sessions. Reconstruct here.

def recode_9(data, cols):
    for col in cols:
        data[col] = pd.to_numeric(data[col], errors='coerce').replace(9, np.nan)

# Superordinate Identity — already in CSV as composite_belonging
# SD Primary Out-group — group-specific items
recode_9(df23, ["Q57_1", "Q58_1", "Q59_1", "Q57_2", "Q58_2", "Q59_2"])
df23["composite_sd_primary"] = np.nan
df23.loc[df23["ethnicity_binary"] == 0, "composite_sd_primary"] = \
    df23.loc[df23["ethnicity_binary"] == 0, ["Q57_1", "Q58_1", "Q59_1"]].mean(axis=1)
df23.loc[df23["ethnicity_binary"] == 1, "composite_sd_primary"] = \
    df23.loc[df23["ethnicity_binary"] == 1, ["Q57_2", "Q58_2", "Q59_2"]].mean(axis=1)

# SD General Out-group (6 items, no Ukrainian)
sd_gen = ["Q57_4", "Q57_5", "Q58_4", "Q58_5", "Q59_4", "Q59_5"]
recode_9(df23, sd_gen)
df23["composite_sd_general"] = df23[sd_gen].mean(axis=1)

# Comparative Opportunity
q44 = [f"Q44_{i}" for i in range(1, 13)]
recode_9(df23, q44)
df23["composite_comp_opp"] = df23[q44].mean(axis=1)

# Belief in Conflict
recode_9(df23, ["Q63_1", "Q63_2", "Q63_3", "Q63_4"])
df23["Q63_3_inv"] = 5 - df23["Q63_3"]
df23["Q63_4_inv"] = 5 - df23["Q63_4"]
df23["composite_conflict"] = df23[["Q63_1", "Q63_2", "Q63_3_inv", "Q63_4_inv"]].mean(axis=1)

# Minority Support
recode_9(df23, ["Q68_1", "Q68_2", "Q68_3"])
df23["composite_minority_support"] = df23[["Q68_1", "Q68_2", "Q68_3"]].mean(axis=1)

# Contact Estonian speakers
q51 = [f"Q51_{i}" for i in range(1, 7)]
recode_9(df23, q51)
df23["composite_contact_est"] = df23[q51].mean(axis=1)

# Contact Russian speakers
q52 = [f"Q52_{i}" for i in range(1, 7)]
recode_9(df23, q52)
df23["composite_contact_rus"] = df23[q52].mean(axis=1)


# ─── Statistics functions ─────────────────────────────────────────────────────
def cohens_d_rms(g1, g2):
    """Cohen's d with root-mean-square SD denominator."""
    s1, s2 = g1.std(ddof=1), g2.std(ddof=1)
    denom = np.sqrt((s1**2 + s2**2) / 2)
    return (g1.mean() - g2.mean()) / denom if denom > 0 else np.nan

def fmt_p(p):
    """Format p-value with significance stars."""
    if p < 0.0001:
        return "<.0001***"
    elif p < 0.001:
        return f"{p:.4f}***"
    elif p < 0.01:
        return f"{p:.3f}**"
    elif p < 0.05:
        return f"{p:.3f}*"
    else:
        return f"{p:.3f} ns"

def compare(g1, g2):
    """Return M, SD, N for each group plus d and p."""
    g1, g2 = g1.dropna(), g2.dropna()
    t, p = stats.ttest_ind(g1, g2, equal_var=False)
    d = cohens_d_rms(g1, g2)
    return g1.mean(), g1.std(ddof=1), len(g1), g2.mean(), g2.std(ddof=1), len(g2), d, p


# ─── Define composite mapping ────────────────────────────────────────────────
# (label, 2023_column, 2020_column)
COMPOSITES = [
    ("Superordinate Identity",        "composite_belonging",        "composite_superordinate_id"),
    ("SD: Primary Out-group",         "composite_sd_primary",       "composite_sd_primary"),
    ("SD: General Out-group",         "composite_sd_general",       "composite_sd_general"),
    ("Comparative Opp. Assessment",   "composite_comp_opp",         "composite_comp_opp"),
    ("Belief in Inevitable Conflict", "composite_conflict",         "composite_conflict"),
    ("Minority Support Inclusion",    "composite_minority_support", "composite_minority_support"),
    ("Contact w/ Estonian spkrs",     "composite_contact_est",      "composite_contact_est"),
    ("Contact w/ Russian spkrs",      "composite_contact_rus",      "composite_contact_rus"),
]


# ─── Table 1: Between-Group (Estonian vs Russian) ────────────────────────────
print("=" * 95)
print("  TABLE 1: BETWEEN-GROUP COMPARISON (Estonian vs Russian)")
print("=" * 95)
print(f"{'Variable':<35} {'Year':>4}  {'Est M (SD)':<14} {'Rus M (SD)':<14} {'d':>6}  {'p':<12}")
print("-" * 95)

for label, col23, col20 in COMPOSITES:
    for year, df, col in [(2020, df20, col20), (2023, df23, col23)]:
        est = df[df["ethnicity_binary"] == 0][col]
        rus = df[df["ethnicity_binary"] == 1][col]
        m1, s1, n1, m2, s2, n2, d, p = compare(est, rus)
        print(f"{label:<35} {year:>4}  {m1:.2f} ({s1:.2f})     {m2:.2f} ({s2:.2f})     {d:>+6.2f}  {fmt_p(p)}")

# Gap change summary
print(f"\n{'─' * 95}")
print("  Gap changes (2020 → 2023 d):")
for label, col23, col20 in COMPOSITES:
    est20 = df20[df20["ethnicity_binary"] == 0][col20].dropna()
    rus20 = df20[df20["ethnicity_binary"] == 1][col20].dropna()
    est23 = df23[df23["ethnicity_binary"] == 0][col23].dropna()
    rus23 = df23[df23["ethnicity_binary"] == 1][col23].dropna()
    d20 = cohens_d_rms(est20, rus20)
    d23 = cohens_d_rms(est23, rus23)
    direction = "widened" if abs(d23) > abs(d20) else "narrowed" if abs(d23) < abs(d20) else "unchanged"
    if np.sign(d20) != np.sign(d23):
        direction = "FLIPPED"
    print(f"    {label:<35} {d20:>+.2f} → {d23:>+.2f}  ({direction})")


# ─── Table 2: Within-Group Change (2020 → 2023) ─────────────────────────────
print(f"\n\n{'=' * 95}")
print("  TABLE 2: WITHIN-GROUP CHANGE (2020 → 2023)")
print("=" * 95)
print(f"{'Variable':<35} {'Group':<10} {'2020 M (SD)':<14} {'2023 M (SD)':<14} {'d':>6}  {'p':<12}")
print("-" * 95)

for label, col23, col20 in COMPOSITES:
    for eth, eth_label in [(0, "Estonian"), (1, "Russian")]:
        g20 = df20[df20["ethnicity_binary"] == eth][col20].dropna()
        g23 = df23[df23["ethnicity_binary"] == eth][col23].dropna()
        # d = (2023 - 2020) direction
        m1, s1, n1, m2, s2, n2, d, p = compare(g23, g20)
        # Flip sign so positive d = increase from 2020 to 2023
        print(f"{label:<35} {eth_label:<10} {m2:.2f} ({s2:.2f})     {m1:.2f} ({s1:.2f})     {d:>+6.2f}  {fmt_p(p)}")

print(f"\n{'─' * 95}")
print("  Note: d is computed as (2023 M - 2020 M) / RMS_SD. Positive d = increase from 2020 to 2023.")
print("  SD General Out-group uses different items across years (6 items in 2023, 3 items in 2020).")
print(f"{'─' * 95}")
