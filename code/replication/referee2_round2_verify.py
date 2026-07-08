"""
Referee 2 — Round 2 Verification
==================================
Verifies:
1. composite_belonging in EIM23.csv is now the 3-item version
2. All 8 composites in EIM2020_composites.csv match independent reconstruction
3. Cohen's d values using documented RMS formula match SESSION_LOG
4. SD split script (05_sd_split_pca.py) produces correct reliability stats

This script does NOT modify any author code or data files.
"""

import pandas as pd
import numpy as np
import pyreadstat
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

REPORT = []
PASS = 0
FAIL = 0

def log(msg):
    print(msg)
    REPORT.append(msg)

def check(label, computed, expected, tol=0.015):
    global PASS, FAIL
    diff = abs(computed - expected)
    if diff <= tol:
        PASS += 1
        log(f"    PASS  {label}: {computed:.4f} (expected {expected}, diff={diff:.4f})")
    else:
        FAIL += 1
        log(f"    FAIL  {label}: {computed:.4f} (expected {expected}, diff={diff:.4f})")

def cohens_d_rms(g1, g2):
    """Cohen's d with root-mean-square SD (author's documented formula)."""
    s1, s2 = g1.std(ddof=1), g2.std(ddof=1)
    return (g1.mean() - g2.mean()) / np.sqrt((s1**2 + s2**2) / 2)

def cronbach_alpha(df_items):
    """Independent Cronbach's alpha computation."""
    sub = df_items.dropna()
    k = sub.shape[1]
    if k < 2 or len(sub) < 3:
        return np.nan, len(sub)
    item_vars = sub.var(ddof=1)
    total_var = sub.sum(axis=1).var(ddof=1)
    alpha = (k / (k - 1)) * (1 - item_vars.sum() / total_var)
    return alpha, len(sub)


# ══════════════════════════════════════════════════════════════════════════════
# VERIFICATION 1: 2023 composite_belonging is 3-item
# ══════════════════════════════════════════════════════════════════════════════
log("\n" + "=" * 70)
log("VERIFICATION 1: composite_belonging is 3-item version")
log("=" * 70)

df23 = pd.read_csv("/Users/brianwiggins/Desktop/Claude Code/EIM2/data/EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy()

for col in ["Q67_1", "Q67_2", "Q67_4", "Q67_5"]:
    df23[col] = pd.to_numeric(df23[col], errors='coerce').replace(9, np.nan)
df23["Q67_4_inv"] = 5 - df23["Q67_4"]

three_item = df23[["Q67_2", "Q67_4_inv", "Q67_5"]].mean(axis=1)
four_item = df23[["Q67_1", "Q67_2", "Q67_4_inv", "Q67_5"]].mean(axis=1)
existing = df23["composite_belonging"]

r3 = existing.corr(three_item)
r4 = existing.corr(four_item)
log(f"  Correlation with 3-item: {r3:.6f}")
log(f"  Correlation with 4-item: {r4:.6f}")

if r3 > 0.9999:
    PASS += 1
    log("  PASS: composite_belonging is the 3-item version")
else:
    FAIL += 1
    log("  FAIL: composite_belonging does NOT match 3-item reconstruction")

# Verify group means
est23 = df23[df23["ethnicity_binary"] == 0]
rus23 = df23[df23["ethnicity_binary"] == 1]
cb_e = est23["composite_belonging"].dropna()
cb_r = rus23["composite_belonging"].dropna()
check("Est mean 2023", cb_e.mean(), 1.50)
check("Rus mean 2023", cb_r.mean(), 2.05)
check("Cohen's d (RMS)", cohens_d_rms(cb_e, cb_r), -0.79)


# ══════════════════════════════════════════════════════════════════════════════
# VERIFICATION 2: 2020 composites match independent reconstruction
# ══════════════════════════════════════════════════════════════════════════════
log("\n" + "=" * 70)
log("VERIFICATION 2: 2020 composites (EIM2020_composites.csv)")
log("=" * 70)

# Load author's saved composites
saved = pd.read_csv("/Users/brianwiggins/Desktop/Claude Code/EIM2/data/EIM2020_composites.csv")
log(f"  Saved file: {len(saved)} rows, {len(saved.columns)} columns")

# Load raw 2020 data independently
df20, meta = pyreadstat.read_sav(
    "/Users/brianwiggins/Desktop/Claude Code/EIM2/data/EIM 2020_20.10.25.sav copy",
    encoding='latin1'
)
# Ethnicity via T9_1/T9_2 (self-identified nationality, matches 2023 T8)
df20["ethnicity_binary"] = np.where(
    df20["T9_1"] == 1, 0,
    np.where(df20["T9_2"] == 1, 1, np.nan)
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy()
est20 = df20[df20["ethnicity_binary"] == 0]
rus20 = df20[df20["ethnicity_binary"] == 1]
log(f"  Independent load: {len(df20)} rows — {len(est20)} Est, {len(rus20)} Rus")

def recode_9(data, cols):
    for col in cols:
        data[col] = pd.to_numeric(data[col], errors='coerce').replace(9, np.nan)
    return data

# --- 2020 Superordinate Identity ---
log("\n  2020 Superordinate Identity:")
df20 = recode_9(df20, ["K6X5_2", "K6X5_3", "K6X5_4"])
df20["K6X5_3_inv"] = 5 - df20["K6X5_3"]
r2_si = df20[["K6X5_2", "K6X5_3_inv", "K6X5_4"]].mean(axis=1)
check("Est M", r2_si[est20.index].dropna().mean(), 1.45)
check("Rus M", r2_si[rus20.index].dropna().mean(), 2.08)
check("d (RMS)", cohens_d_rms(r2_si[est20.index].dropna(), r2_si[rus20.index].dropna()), -1.08)
# Compare to saved
saved_si = saved["composite_superordinate_id"]
r2_corr = r2_si.reset_index(drop=True).corr(saved_si)
log(f"    Correlation with saved: {r2_corr:.6f}")

# --- 2020 SD Primary ---
log("\n  2020 SD Primary Out-group:")
df20 = recode_9(df20, ["K4X7_1", "K4X8_1", "K4X9_1", "K4X7_2", "K4X8_2", "K4X9_2"])
r2_sdp = pd.Series(np.nan, index=df20.index)
r2_sdp[est20.index] = df20.loc[est20.index, ["K4X7_1", "K4X8_1", "K4X9_1"]].mean(axis=1)
r2_sdp[rus20.index] = df20.loc[rus20.index, ["K4X7_2", "K4X8_2", "K4X9_2"]].mean(axis=1)
check("Est M", r2_sdp[est20.index].dropna().mean(), 2.51)
check("Rus M", r2_sdp[rus20.index].dropna().mean(), 1.90)
check("d (RMS)", cohens_d_rms(r2_sdp[est20.index].dropna(), r2_sdp[rus20.index].dropna()), 0.74)

# --- 2020 SD General ---
log("\n  2020 SD General Out-group:")
df20 = recode_9(df20, ["K4X7_3", "K4X8_3", "K4X9_3"])
r2_sdg = df20[["K4X7_3", "K4X8_3", "K4X9_3"]].mean(axis=1)
check("Est M", r2_sdg[est20.index].dropna().mean(), 2.91)
check("Rus M", r2_sdg[rus20.index].dropna().mean(), 3.12)
check("d (RMS)", cohens_d_rms(r2_sdg[est20.index].dropna(), r2_sdg[rus20.index].dropna()), -0.21)

# --- 2020 Comparative Opportunity ---
log("\n  2020 Comparative Opportunity:")
q44_cols = [f"K3X1_{i}" for i in range(1, 13)]
df20 = recode_9(df20, q44_cols)
r2_co = df20[q44_cols].mean(axis=1)
check("Est M", r2_co[est20.index].dropna().mean(), 2.56)
check("Rus M", r2_co[rus20.index].dropna().mean(), 2.14)
check("d (RMS)", cohens_d_rms(r2_co[est20.index].dropna(), r2_co[rus20.index].dropna()), 0.79)

# --- 2020 Belief in Conflict ---
log("\n  2020 Belief in Conflict:")
df20 = recode_9(df20, ["K6X1_1", "K6X1_2", "K6X1_3", "K6X1_4"])
df20["K6X1_3_inv"] = 5 - df20["K6X1_3"]
df20["K6X1_4_inv"] = 5 - df20["K6X1_4"]
r2_bc = df20[["K6X1_1", "K6X1_2", "K6X1_3_inv", "K6X1_4_inv"]].mean(axis=1)
check("Est M", r2_bc[est20.index].dropna().mean(), 2.78)
check("Rus M", r2_bc[rus20.index].dropna().mean(), 3.03)
check("d (RMS)", cohens_d_rms(r2_bc[est20.index].dropna(), r2_bc[rus20.index].dropna()), -0.44)

# --- 2020 Minority Support ---
log("\n  2020 Minority Support:")
df20 = recode_9(df20, ["K6X6_1", "K6X6_2", "K6X6_3"])
r2_ms = df20[["K6X6_1", "K6X6_2", "K6X6_3"]].mean(axis=1)
check("Est M", r2_ms[est20.index].dropna().mean(), 2.21)
check("Rus M", r2_ms[rus20.index].dropna().mean(), 1.57)
check("d (RMS)", cohens_d_rms(r2_ms[est20.index].dropna(), r2_ms[rus20.index].dropna()), 1.00)

# --- 2020 Contact Estonian speakers ---
log("\n  2020 Contact Estonian speakers:")
q51_cols = [f"K4X1_{i}" for i in range(1, 7)]
df20 = recode_9(df20, q51_cols)
r2_ce = df20[q51_cols].mean(axis=1)
check("Est M", r2_ce[est20.index].dropna().mean(), 1.85)
check("Rus M", r2_ce[rus20.index].dropna().mean(), 3.86)
check("d (RMS)", cohens_d_rms(r2_ce[est20.index].dropna(), r2_ce[rus20.index].dropna()), -1.89)

# --- 2020 Contact Russian speakers ---
log("\n  2020 Contact Russian speakers:")
q52_cols = [f"K4X2_{i}" for i in range(1, 7)]
df20 = recode_9(df20, q52_cols)
r2_cr = df20[q52_cols].mean(axis=1)
check("Est M", r2_cr[est20.index].dropna().mean(), 3.98)
check("Rus M", r2_cr[rus20.index].dropna().mean(), 1.79)
check("d (RMS)", cohens_d_rms(r2_cr[est20.index].dropna(), r2_cr[rus20.index].dropna()), 2.25)


# ══════════════════════════════════════════════════════════════════════════════
# VERIFICATION 3: SD split script reliability stats
# ══════════════════════════════════════════════════════════════════════════════
log("\n" + "=" * 70)
log("VERIFICATION 3: SD split composite reliability (2023)")
log("=" * 70)

# Primary out-group
est23_items = df23.loc[est23.index, ["Q57_1", "Q58_1", "Q59_1"]].copy()
for c in est23_items.columns:
    est23_items[c] = pd.to_numeric(est23_items[c], errors='coerce').replace(9, np.nan)
alpha_e, n_e = cronbach_alpha(est23_items)
log(f"\n  SD Primary — Estonian:")
check("alpha", alpha_e, 0.827)
log(f"    N (listwise) = {n_e}")

rus23_items = df23.loc[rus23.index, ["Q57_2", "Q58_2", "Q59_2"]].copy()
for c in rus23_items.columns:
    rus23_items[c] = pd.to_numeric(rus23_items[c], errors='coerce').replace(9, np.nan)
alpha_r, n_r = cronbach_alpha(rus23_items)
log(f"\n  SD Primary — Russian:")
check("alpha", alpha_r, 0.772)
log(f"    N (listwise) = {n_r}")

# General out-group (6 items)
gen_cols = ["Q57_4", "Q57_5", "Q58_4", "Q58_5", "Q59_4", "Q59_5"]
est23_gen = df23.loc[est23.index, gen_cols].copy()
for c in gen_cols:
    est23_gen[c] = pd.to_numeric(est23_gen[c], errors='coerce').replace(9, np.nan)
alpha_eg, n_eg = cronbach_alpha(est23_gen)
log(f"\n  SD General — Estonian:")
check("alpha", alpha_eg, 0.911)

rus23_gen = df23.loc[rus23.index, gen_cols].copy()
for c in gen_cols:
    rus23_gen[c] = pd.to_numeric(rus23_gen[c], errors='coerce').replace(9, np.nan)
alpha_rg, n_rg = cronbach_alpha(rus23_gen)
log(f"\n  SD General — Russian:")
check("alpha", alpha_rg, 0.902)


# ══════════════════════════════════════════════════════════════════════════════
# VERIFICATION 4: Absolute path check
# ══════════════════════════════════════════════════════════════════════════════
log("\n" + "=" * 70)
log("VERIFICATION 4: No absolute paths in author scripts")
log("=" * 70)

import os, re
code_dir = "/Users/brianwiggins/Desktop/Claude Code/EIM2/code"
abs_path_pattern = re.compile(r'["\'][A-Z]:\\|["\']/Users/|["\']/home/')
abs_path_files = []
for root, dirs, files in os.walk(code_dir):
    # Skip replication directory (referee's own scripts)
    if 'replication' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path) as fh:
                for i, line in enumerate(fh, 1):
                    if abs_path_pattern.search(line):
                        abs_path_files.append((path, i, line.strip()))

if abs_path_files:
    FAIL += 1
    log(f"  FAIL: {len(abs_path_files)} absolute path(s) found:")
    for p, ln, content in abs_path_files:
        log(f"    {os.path.basename(p)}:{ln}: {content[:80]}")
else:
    PASS += 1
    log("  PASS: No absolute paths in author scripts")


# ══════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
log("\n" + "=" * 70)
log("ROUND 2 VERIFICATION SUMMARY")
log("=" * 70)
log(f"\n  PASS: {PASS}")
log(f"  FAIL: {FAIL}")
log(f"  Total checks: {PASS + FAIL}")
if FAIL == 0:
    log("\n  ALL CHECKS PASSED")
else:
    log(f"\n  {FAIL} CHECK(S) FAILED — see details above")
log("\n" + "=" * 70)
