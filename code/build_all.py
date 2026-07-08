"""
Master Build Script — EIM2 Project
====================================
Runs the full pipeline from raw data to final composites, diagnostics,
publication figures, and Referee 2 replication audits.

Execute from the code/ directory:  python3 build_all.py

Stage 1: Data preparation (adds derived columns to EIM23.csv)
Stage 2: Composite construction (builds DV + 2020 composites)
Stage 3: PCA/reliability diagnostics (print-only validation)
Stage 3b: Comparison tables
Stage 4: PCA/reliability diagnostics (2020)
Stage 5: Effect sizes + publication figures (TSV + JPEGs + Word doc)
Stage 7: Blindspot Round 2 follow-up artifacts (polarization, item decomp, etc.)
Stage 7b: Measurement invariance (R lavaan + Python docx report)
Stage 8: Round 3 distribution & item-decomposition charts (single-construct)
Stage 9: Round 3 Primary-vs-General comparison + paired test + focused chart
Stage 10: Round 3 reports & publication-ready tables
Stage 6: Round 3 replication audit (Python + R) — runs LAST
"""

import os
import re
import shutil
import subprocess
import sys
import time

STAGES = [
    ("Stage 1: Data Preparation", [
        ("01_create_ethnicity_binary.py", "Creating ethnicity_binary"),
        ("02_create_parents_birthplace.py", "Creating parents_birthplace"),
        ("03_create_edu_language.py", "Creating edu_language"),
    ]),
    ("Stage 2: Composite Construction", [
        ("04_composite_and_pca.py", "Building composite_belonging (3-item DV)"),
        ("17_build_2020_composites.py", "Building all 2020 composites"),
    ]),
    ("Stage 3: PCA/Reliability Diagnostics (2023)", [
        ("05_sd_split_pca.py", "SD Primary/General split (varimax)"),
        ("07_q44_composite_pca.py", "Comparative Opportunity PCA"),
        ("08_q63_composite_pca.py", "Belief in Conflict PCA"),
        ("09_q68_composite_pca.py", "Minority Support PCA"),
        ("10_pca_by_ethnicity.py", "Superordinate Identity by group"),
    ]),
    ("Stage 3b: Comparison Tables", [
        ("19_comparison_tables.py", "Between-group and within-group comparisons"),
    ]),
    ("Stage 4: PCA/Reliability Diagnostics (2020)", [
        ("11_pca_2020_by_ethnicity.py", "Superordinate Identity by group (2020)"),
        ("12_outgroup_2020_pca.py", "SD out-group PCA (2020)"),
        ("14_q44_2020_pca.py", "Comparative Opportunity PCA (2020)"),
        ("15_q63_2020_pca.py", "Belief in Conflict PCA (2020)"),
        ("16_q68_2020_pca.py", "Minority Support PCA (2020)"),
    ]),
    ("Stage 5: Effect Sizes + Publication Figures", [
        ("24_effect_sizes_with_ci.py",       "Canonical TSV + Effect_Sizes_with_CI.docx"),
        ("19_diverging_bars_within_group.py", "fig_within_group_change.jpg"),
        ("20_diverging_bars_between_group.py","fig_between_group_gap.jpg"),
        ("21_dumbbell_between_group.py",     "fig_between_group_dumbbell.jpg"),
        ("22_dumbbell_cohens_d.py",          "fig_between_group_dumbbell_d.jpg (normalized)"),
        ("23_contact_breakdown.py",          "fig_contact_breakdown.jpg"),
    ]),
    ("Stage 7: Blindspot Follow-Up Artifacts", [
        ("25_polarization_density.py",       "fig_polarization_density.jpg + Levene's tests"),
        ("26_russian_edu_subgroups.py",      "Russian_Edu_Subgroup_Robustness.docx"),
        ("27_blindspot_report_docx.py",      "Blindspot_Report_2026-04-29.docx"),
        ("28_bic_density.py",                "fig_bic_density.jpg (Belief in Conflict)"),
        ("29_item_decomposition.py",         "Item-level d for all 8 composites + 8 figures"),
        ("30_compopp_item_distributions.py", "12 Q44 distribution charts + bundled Word doc"),
    ]),
]

# --------------------------------------------------------------------------
# Stage 8 — Round 3 single-construct distribution & item-decomp charts
# Distribution shapes and item-level decomposition for the three constructs
# that became central in the May 2026 Round 3 wave: Belief in Inevitable
# Conflict, Minority Inclusion Support, SD: Primary Out-group, SD: General
# Out-group. Each script reads raw data + canonical TSV; no inter-script
# dependencies within Stage 8.
# --------------------------------------------------------------------------
STAGE_8_SCRIPTS = [
    ("34_bic_item_density.py",           "fig_bic_item_density.jpg (4 BiC items × 2 groups)"),
    ("35_bic_item_decomp_corrected.py",  "fig_item_decomp_BiC_corrected.jpg (with amber highlight)"),
    ("39_minority_item_density.py",      "fig_minority_item_density.jpg"),
    ("40_minority_item_decomp.py",       "fig_item_decomp_Minority_Support_inverted.jpg (with amber highlight)"),
    ("41_minority_density.py",           "fig_minority_density.jpg (composite distribution)"),
    ("42_sd_primary_density.py",         "fig_sd_primary_density.jpg (composite distribution)"),
    ("43_sd_primary_item_decomp.py",     "fig_item_decomp_SD_Primary_Outgroup.jpg"),
    ("44_sd_primary_item_density.py",    "fig_sd_primary_item_density.jpg"),
    ("48_sd_general_density.py",         "fig_sd_general_density.jpg (composite distribution)"),
    ("49_sd_general_item_decomp.py",     "fig_item_decomp_SD_General_Outgroup.jpg"),
    ("50_sd_general_item_density.py",    "fig_sd_general_item_density.jpg (4 rows × 3 contexts)"),
]

# --------------------------------------------------------------------------
# Stage 9 — Round 3 Primary-vs-General comparisons + paired test
# Tests + visualizations underpinning the §51 Estonian sign-reversal finding.
# Script 51 emits text only (paired t + Wilcoxon); 52-55 produce comparison
# JPEGs; 58 produces the focused thesis bar chart.
# --------------------------------------------------------------------------
STAGE_9_SCRIPTS = [
    ("51_estonian_sd_primary_vs_general.py",  "§51 paired test (text output: t, p, d_z)"),
    ("52_sd_primary_vs_general_2020.py",      "fig_sd_primary_vs_general_2020.jpg"),
    ("53_sd_primary_vs_general_2023.py",      "fig_sd_primary_vs_general_2023.jpg"),
    ("54_sd_primary_vs_general_estonian.py",  "fig_sd_primary_vs_general_estonian.jpg"),
    ("55_sd_primary_vs_general_russian.py",   "fig_sd_primary_vs_general_russian.jpg"),
    ("58_between_group_gap_focused.py",       "fig_between_group_gap_focused.jpg (contact removed; bold/italic labels)"),
]

# --------------------------------------------------------------------------
# Stage 10 — Round 3 reports & tables
# Word-doc generators that read from canonical TSV + produced figures.
# --------------------------------------------------------------------------
STAGE_10_SCRIPTS = [
    ("56_blindspot_round3_report_docx.py",    "Blindspot_Report_2026-05-02.docx"),
    ("57_test3_paired_table_docx.py",         "Table_Test3_Paired_Estonian_Primary_vs_General.docx"),
]

# Stage 7b: R-side invariance testing, then Python docx report (one R then one Py).
# Runs after the main STAGES loop, before Stage 6 audit.
R_STAGE_SCRIPTS = [
    ("36_measurement_invariance.R",
     "Multi-group + longitudinal CFA invariance testing (8 composites)"),
]
PY_STAGE_7B_FOLLOWUP = [
    ("37_invariance_report_docx.py", "Measurement_Invariance.docx"),
    ("38_invariance_per_composite_docx.py",
     "Measurement_Invariance_Per_Composite_Interpretation.docx"),
]

# Stage 6 has its own runner because we want to parse PASS/FAIL totals.
VERIFICATION_SCRIPTS = [
    # (script path relative to code/, language, description)
    ("replication/referee2_round3_verify_ci.py", "python", "Python independent verification of canonical TSV"),
    ("replication/referee2_round3_R_ci.R",       "R",      "R cross-language replication"),
]

def run_script(script, description):
    """Run a Python script and return success/failure."""
    print(f"  Running {script} — {description}...", end=" ", flush=True)
    start = time.time()
    result = subprocess.run(
        [sys.executable, script],
        capture_output=True, text=True, timeout=180
    )
    elapsed = time.time() - start
    if result.returncode == 0:
        print(f"OK ({elapsed:.1f}s)")
        return True
    else:
        print(f"FAILED ({elapsed:.1f}s)")
        print(f"    stderr: {result.stderr[:200]}")
        return False


def run_verification(script, lang, description):
    """Run a verification script and parse its PASS/FAIL summary line.

    Returns a tuple (ok: bool, passed: int, failed: int, elapsed: float).
    Looks for a line matching 'NN/NN PASS, NN/NN FAIL' in stdout.
    """
    print(f"  Running {script} — {description}...", end=" ", flush=True)
    start = time.time()
    if lang == "python":
        cmd = [sys.executable, script]
    elif lang == "R":
        rscript = shutil.which("Rscript") or "/usr/local/bin/Rscript"
        if not os.path.exists(rscript):
            print(f"SKIP (Rscript not found at {rscript})")
            return (False, 0, 0, 0.0)
        cmd = [rscript, script]
    else:
        print(f"SKIP (unknown language: {lang})")
        return (False, 0, 0, 0.0)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    elapsed = time.time() - start

    # Parse "NNN/NNN PASS, NN/NNN FAIL" anywhere in stdout
    m = re.search(r"(\d+)\s*/\s*(\d+)\s*PASS\s*,\s*(\d+)\s*/\s*\d+\s*FAIL",
                  result.stdout)
    if m:
        passed, total, failed = int(m.group(1)), int(m.group(2)), int(m.group(3))
        ok = (result.returncode == 0) and (failed == 0)
        status = "OK" if ok else "FAILED"
        print(f"{status} {passed}/{total} PASS  ({elapsed:.1f}s)")
        if not ok:
            # Print a few of the FAIL lines so the user can see what diverged
            fail_lines = [ln for ln in result.stdout.splitlines() if "FAIL " in ln][:5]
            for ln in fail_lines:
                print(f"      {ln.strip()}")
        return (ok, passed, failed, elapsed)
    else:
        ok = (result.returncode == 0)
        status = "OK (no PASS/FAIL summary parsed)" if ok else "FAILED"
        print(f"{status} ({elapsed:.1f}s)")
        if not ok:
            print(f"    stderr: {result.stderr[:200]}")
        return (ok, 0, 0, elapsed)


def main():
    print("=" * 60)
    print("  EIM2 — Master Build Script")
    print("=" * 60)

    total = sum(len(scripts) for _, scripts in STAGES)
    passed = 0
    failed = 0
    failed_scripts = []

    for stage_name, scripts in STAGES:
        print(f"\n{stage_name}")
        print("-" * 40)
        for script, desc in scripts:
            ok = run_script(script, desc)
            if ok:
                passed += 1
            else:
                failed += 1
                failed_scripts.append(script)
                # Stage 1 and 2 failures are fatal — later scripts depend on them
                if "Stage 1" in stage_name or "Stage 2" in stage_name:
                    print(f"\n  FATAL: {script} failed. Cannot continue.")
                    print(f"  Fix this script and re-run build_all.py.")
                    sys.exit(1)

    # ---- Stage 7b: Measurement invariance (R lavaan + Python docx report) ----
    print("\nStage 7b: Measurement Invariance (R lavaan → Python docx)")
    print("-" * 40)
    rscript = shutil.which("Rscript") or "/usr/local/bin/Rscript"
    for script, desc in R_STAGE_SCRIPTS:
        print(f"  Running {script} — {desc}...", end=" ", flush=True)
        if not os.path.exists(rscript):
            print("SKIP (Rscript not found)")
            failed += 1; failed_scripts.append(script)
            continue
        start = time.time()
        result = subprocess.run([rscript, script], capture_output=True,
                                text=True, timeout=600)
        elapsed = time.time() - start
        if result.returncode == 0:
            print(f"OK ({elapsed:.1f}s)")
            passed += 1
        else:
            print(f"FAILED ({elapsed:.1f}s)")
            print(f"    stderr: {result.stderr[:200]}")
            failed += 1
            failed_scripts.append(script)
    for script, desc in PY_STAGE_7B_FOLLOWUP:
        ok = run_script(script, desc)
        if ok: passed += 1
        else: failed += 1; failed_scripts.append(script)

    # ---- Stage 8: Round 3 distribution & item-decomp charts -----------------
    print("\nStage 8: Round 3 Distribution & Item-Decomp Charts")
    print("-" * 40)
    for script, desc in STAGE_8_SCRIPTS:
        ok = run_script(script, desc)
        if ok: passed += 1
        else: failed += 1; failed_scripts.append(script)

    # ---- Stage 9: Round 3 Primary-vs-General comparison + focused chart -----
    print("\nStage 9: Round 3 Primary-vs-General Comparison + Focused Chart")
    print("-" * 40)
    for script, desc in STAGE_9_SCRIPTS:
        ok = run_script(script, desc)
        if ok: passed += 1
        else: failed += 1; failed_scripts.append(script)

    # ---- Stage 10: Round 3 reports & publication-ready tables ---------------
    print("\nStage 10: Round 3 Reports & Tables")
    print("-" * 40)
    for script, desc in STAGE_10_SCRIPTS:
        ok = run_script(script, desc)
        if ok: passed += 1
        else: failed += 1; failed_scripts.append(script)

    # ---- Stage 6: Round 3 replication audit ---------------------------------
    print("\nStage 6: Round 3 Replication Audit")
    print("-" * 40)
    audit_total = 0
    audit_passed = 0
    audit_failed = 0
    audit_failed_scripts = []
    for script, lang, desc in VERIFICATION_SCRIPTS:
        ok, p_count, f_count, _ = run_verification(script, lang, desc)
        audit_total += (p_count + f_count)
        audit_passed += p_count
        audit_failed += f_count
        if ok:
            passed += 1
        else:
            failed += 1
            audit_failed_scripts.append(script)
            failed_scripts.append(script)
        # Each verification script counts as one "script" in the overall total
    # ----------------------------------------------------------------------------

    print(f"\n{'=' * 60}")
    pipeline_total = (total + len(VERIFICATION_SCRIPTS)
                      + len(R_STAGE_SCRIPTS) + len(PY_STAGE_7B_FOLLOWUP)
                      + len(STAGE_8_SCRIPTS) + len(STAGE_9_SCRIPTS)
                      + len(STAGE_10_SCRIPTS))
    print(f"  BUILD COMPLETE: {passed}/{pipeline_total} scripts succeeded")
    if failed > 0:
        print(f"  {failed} script(s) failed:")
        for s in failed_scripts:
            print(f"    - {s}")
    else:
        print(f"  All pipeline scripts passed.")
    if audit_total > 0:
        print(f"  Audit: {audit_passed}/{audit_total} replication checks passed"
              f"{', ' + str(audit_failed) + ' FAIL' if audit_failed else ''}")
    print(f"{'=' * 60}")

    # Summary of outputs
    print(f"\n  Outputs:")
    print(f"    ../data/EIM23.csv                  — derived columns + composite_belonging")
    print(f"    ../data/EIM2020_composites.csv     — all 8 composites for 2020")
    print(f"    ./_effect_sizes.tsv                — canonical M/SD/N/d/CI/p")
    print(f"    ../reports/Effect_Sizes_with_CI.docx — formatted tables")
    print(f"    ../viz/fig_within_group_change.jpg")
    print(f"    ../viz/fig_between_group_gap.jpg")
    print(f"    ../viz/fig_between_group_dumbbell.jpg")
    print(f"    ../viz/fig_between_group_dumbbell_d.jpg")
    print(f"    ../viz/fig_contact_breakdown.jpg")
    print(f"    ../viz/fig_polarization_density.jpg              — Blindspot polarization check")
    print(f"    ../viz/fig_bic_density.jpg                       — Belief in Conflict distribution")
    print(f"    ../viz/fig_item_decomp_*.jpg                     — Item-level decomposition (×8)")
    print(f"    ../viz/fig_compopp_item_*.jpg                    — Q44 item distributions (×12)")
    print(f"    ./_item_decomposition.tsv                        — Canonical item-level d table")
    print(f"    ../reports/Russian_Edu_Subgroup_Robustness.docx  — Blindspot edu_language robustness")
    print(f"    ../reports/Item_Level_Decomposition.docx         — Item-level d tables (8 composites)")
    print(f"    ../reports/Comparative_Opportunity_Item_Distributions.docx — 12 Q44 distribution charts")
    print(f"    ../reports/Blindspot_Report_2026-04-29.docx       — Blindspot report")
    print(f"    ../reports/Measurement_Invariance.docx           — Multi-group / longitudinal CFA")
    print(f"    ../reports/Measurement_Invariance_Per_Composite_Interpretation.docx — Per-composite write-up")
    print(f"    ./_invariance_results.tsv                        — Raw invariance fit indices")
    print(f"    --- Round 3 (May 2026) outputs ---")
    print(f"    ../viz/fig_bic_item_density.jpg                  — BiC item-level distributions")
    print(f"    ../viz/fig_item_decomp_BiC_corrected.jpg         — BiC item decomp (amber-highlighted divergent item)")
    print(f"    ../viz/fig_minority_*.jpg                        — Minority Inclusion Support distributions + item decomp")
    print(f"    ../viz/fig_sd_primary_*.jpg                      — SD: Primary Out-group distributions + item decomp")
    print(f"    ../viz/fig_sd_general_*.jpg                      — SD: General Out-group distributions + item decomp")
    print(f"    ../viz/fig_sd_primary_vs_general_*.jpg           — Primary vs. General comparison (year & group views)")
    print(f"    ../viz/fig_between_group_gap_focused.jpg         — Focused thesis bar chart (contact removed)")
    print(f"    ../reports/Blindspot_Report_2026-05-02.docx       — Round 3 Blindspot")
    print(f"    ../reports/Table_Test3_Paired_Estonian_Primary_vs_General.docx — §51 paired test table")
    print(f"\n  PCA/reliability diagnostics printed above for manual review.")

    # Exit non-zero if anything failed, so this is usable as a CI gate.
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
