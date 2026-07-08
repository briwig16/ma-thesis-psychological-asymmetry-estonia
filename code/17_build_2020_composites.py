"""
Build All 2020 Composites
==========================
Constructs all 8 composite variables from the 2020 EIM SPSS file and saves
them to data/EIM2020_composites.csv for downstream analysis.

Ethnicity: T9_1/T9_2 (self-identified nationality) — T9_1=1 → Estonian, T9_2=1 → Russian
  (consistent with 2023's T8 nationality variable; neither selected → excluded)

All composites use pairwise mean of available items after recoding 9 → NaN.
"""

import pandas as pd
import numpy as np
import pyreadstat

# ─── Load 2020 data ──────────────────────────────────────────────────────────
df, meta = pyreadstat.read_sav(
    "../data/EIM 2020_20.10.25.sav copy",
    encoding='latin1'
)
print(f"2020 raw rows: {len(df)}")

# Ethnicity via T9_1/T9_2 (self-identified nationality)
# T9_1=1 → Estonian (0), T9_2=1 → Russian (1), neither → NaN
# Consistent with 2023's T8 (self-identified nationality)
df["ethnicity_binary"] = np.where(
    df["T9_1"] == 1, 0,
    np.where(df["T9_2"] == 1, 1, np.nan)
)
df = df[df["ethnicity_binary"].isin([0, 1])].copy()
est = df[df["ethnicity_binary"] == 0]
rus = df[df["ethnicity_binary"] == 1]
print(f"After filtering: {len(df)} total — {len(est)} Estonian, {len(rus)} Russian")


def recode_9(data, cols):
    """Coerce to numeric and recode 9 (Don't know) → NaN."""
    for col in cols:
        data[col] = pd.to_numeric(data[col], errors='coerce').replace(9, np.nan)
    return data


def cohens_d_rms(g1, g2):
    """Cohen's d with root-mean-square SD denominator."""
    s1, s2 = g1.std(ddof=1), g2.std(ddof=1)
    return (g1.mean() - g2.mean()) / np.sqrt((s1**2 + s2**2) / 2)


def report(label, comp_e, comp_r):
    """Print group comparison for a composite."""
    e, r = comp_e.dropna(), comp_r.dropna()
    d = cohens_d_rms(e, r)
    print(f"  {label}:")
    print(f"    Est: M={e.mean():.2f}, SD={e.std(ddof=1):.2f}, N={len(e)}")
    print(f"    Rus: M={r.mean():.2f}, SD={r.std(ddof=1):.2f}, N={len(r)}")
    print(f"    d={d:+.2f}")


# ══════════════════════════════════════════════════════════════════════════════
# 1. Superordinate Identity (K6X5_2, K6X5_3_inv, K6X5_4)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print("1. SUPERORDINATE IDENTITY")
si_items_raw = ["K6X5_2", "K6X5_3", "K6X5_4"]
df = recode_9(df, si_items_raw)
df["K6X5_3_inv"] = 5 - df["K6X5_3"]  # "second-class citizen" reversed
si_items = ["K6X5_2", "K6X5_3_inv", "K6X5_4"]
df["composite_superordinate_id"] = df[si_items].mean(axis=1)
report("Superordinate Identity",
       df.loc[est.index, "composite_superordinate_id"],
       df.loc[rus.index, "composite_superordinate_id"])

# ══════════════════════════════════════════════════════════════════════════════
# 2. SD: Primary Out-group (K4X7/K4X8/K4X9 — group-specific items)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print("2. SD: PRIMARY OUT-GROUP")
# Estonians rate Russian-speakers: _1 items
# Russians rate Estonian-speakers: _2 items
sd_pri_est_raw = ["K4X7_1", "K4X8_1", "K4X9_1"]
sd_pri_rus_raw = ["K4X7_2", "K4X8_2", "K4X9_2"]
df = recode_9(df, sd_pri_est_raw + sd_pri_rus_raw)

# Compute per-group and combine into one column
df["composite_sd_primary"] = np.nan
est_mask = df["ethnicity_binary"] == 0
rus_mask = df["ethnicity_binary"] == 1
df.loc[est_mask, "composite_sd_primary"] = df.loc[est_mask, sd_pri_est_raw].mean(axis=1)
df.loc[rus_mask, "composite_sd_primary"] = df.loc[rus_mask, sd_pri_rus_raw].mean(axis=1)
report("SD Primary Out-group",
       df.loc[est.index, "composite_sd_primary"],
       df.loc[rus.index, "composite_sd_primary"])

# ══════════════════════════════════════════════════════════════════════════════
# 3. SD: General Out-group (K4X7_3, K4X8_3, K4X9_3 — new immigrants)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print("3. SD: GENERAL OUT-GROUP")
# 2020 has 3 items (new immigrants in last 5 years), not 6 like 2023
sd_gen_raw = ["K4X7_3", "K4X8_3", "K4X9_3"]
df = recode_9(df, sd_gen_raw)
df["composite_sd_general"] = df[sd_gen_raw].mean(axis=1)
report("SD General Out-group",
       df.loc[est.index, "composite_sd_general"],
       df.loc[rus.index, "composite_sd_general"])

# ══════════════════════════════════════════════════════════════════════════════
# 4. Comparative Opportunity Assessment (K3X1_1 through K3X1_12)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print("4. COMPARATIVE OPPORTUNITY ASSESSMENT")
q44_raw = [f"K3X1_{i}" for i in range(1, 13)]
df = recode_9(df, q44_raw)
df["composite_comp_opp"] = df[q44_raw].mean(axis=1)
report("Comparative Opportunity",
       df.loc[est.index, "composite_comp_opp"],
       df.loc[rus.index, "composite_comp_opp"])

# ══════════════════════════════════════════════════════════════════════════════
# 5. Belief in Inevitable Conflict (K6X1_1, K6X1_2, K6X1_3_inv, K6X1_4_inv)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print("5. BELIEF IN INEVITABLE CONFLICT")
q63_raw = ["K6X1_1", "K6X1_2", "K6X1_3", "K6X1_4"]
df = recode_9(df, q63_raw)
df["K6X1_3_inv"] = 5 - df["K6X1_3"]  # "groups can cooperate" reversed
df["K6X1_4_inv"] = 5 - df["K6X1_4"]  # "immigration enriches" reversed
q63_items = ["K6X1_1", "K6X1_2", "K6X1_3_inv", "K6X1_4_inv"]
df["composite_conflict"] = df[q63_items].mean(axis=1)
report("Belief in Conflict",
       df.loc[est.index, "composite_conflict"],
       df.loc[rus.index, "composite_conflict"])

# ══════════════════════════════════════════════════════════════════════════════
# 6. Minority Support Inclusion (K6X6_1, K6X6_2, K6X6_3)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print("6. MINORITY SUPPORT INCLUSION")
q68_raw = ["K6X6_1", "K6X6_2", "K6X6_3"]
df = recode_9(df, q68_raw)
df["composite_minority_support"] = df[q68_raw].mean(axis=1)
report("Minority Support",
       df.loc[est.index, "composite_minority_support"],
       df.loc[rus.index, "composite_minority_support"])

# ══════════════════════════════════════════════════════════════════════════════
# 7. Contact with Estonian speakers (K4X1_1 through K4X1_6)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print("7. CONTACT WITH ESTONIAN SPEAKERS")
q51_raw = [f"K4X1_{i}" for i in range(1, 7)]
df = recode_9(df, q51_raw)
df["composite_contact_est"] = df[q51_raw].mean(axis=1)
report("Contact Estonian spkrs",
       df.loc[est.index, "composite_contact_est"],
       df.loc[rus.index, "composite_contact_est"])

# ══════════════════════════════════════════════════════════════════════════════
# 8. Contact with Russian speakers (K4X2_1 through K4X2_6)
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print("8. CONTACT WITH RUSSIAN SPEAKERS")
q52_raw = [f"K4X2_{i}" for i in range(1, 7)]
df = recode_9(df, q52_raw)
df["composite_contact_rus"] = df[q52_raw].mean(axis=1)
report("Contact Russian spkrs",
       df.loc[est.index, "composite_contact_rus"],
       df.loc[rus.index, "composite_contact_rus"])

# ══════════════════════════════════════════════════════════════════════════════
# Save
# ══════════════════════════════════════════════════════════════════════════════
composite_cols = [
    "ethnicity_binary",
    "composite_superordinate_id",
    "composite_sd_primary",
    "composite_sd_general",
    "composite_comp_opp",
    "composite_conflict",
    "composite_minority_support",
    "composite_contact_est",
    "composite_contact_rus",
]
out = df[composite_cols].copy()
out.to_csv("../data/EIM2020_composites.csv", index=False)
print(f"\n{'='*60}")
print(f"Saved {len(out)} rows to data/EIM2020_composites.csv")
print(f"Columns: {', '.join(composite_cols)}")
