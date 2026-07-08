# Archived Reports

These reports were produced before the **Round 3 effect-size re-computation**
(2026-04-28/29) that established `code/_effect_sizes.tsv` as the canonical
source of truth for all M, SD, N, Cohen's d, 95% CI, and p values under
**pairwise-deletion** methodology.

The values in these archived documents predate the listwise → pairwise
correction documented in SESSION_LOG §26. Some rows differ from the canonical
values; in particular, the four within-group comparisons that flipped
significance levels (Superordinate Identity Estonian, Contact: Estonian
Speakers Estonian, Contact: Russian Speakers Estonian) will not match.

**Do not cite these documents in the thesis.** Cite
`reports/Effect_Sizes_with_CI.docx` instead, which is regenerated from the
canonical TSV by `code/24_effect_sizes_with_ci.py` and verified by the Round 3
audit (444/444 Python + 440/440 R replication checks).

## Contents and provenance

| File | Original date | Provenance | Why archived |
|---|---|---|---|
| `AI_Assisted_Analysis_Methodology.docx` | 2026-04-21 | Methodology write-up | Predates Round 3; methodology-section text may need refresh against the canonical TSV |
| `Comparative_Opportunity_Assessment.docx` | 2026-03-28 | SESSION_LOG §9.3 standalone analysis | Pre-recomputation values |
| `Composite_Comparison_Tables.docx` | 2026-03-30 | SESSION_LOG §12 between/within tables | Superseded by `Effect_Sizes_with_CI.docx` (Round 3) |
| `Master_Composite_Summary.docx` | 2026-03-30 | SESSION_LOG §10 reliability + comparison summary | Reliability stats still valid; comparison stats superseded |
| `Social_Distance_Composite_Analysis.docx` | 2026-03-28 | SESSION_LOG §9.2 standalone analysis | Pre-recomputation values |
| `Superordinate_Identity_Patterns_Analysis.docx` | 2026-03-28 | SESSION_LOG §9.1 standalone analysis | Pre-recomputation values |

If you need any of these regenerated against the canonical TSV, the JS
generator scripts are still in `reports/generators/` and can be re-run after
sourcing fresh values from `code/_effect_sizes.tsv`.
