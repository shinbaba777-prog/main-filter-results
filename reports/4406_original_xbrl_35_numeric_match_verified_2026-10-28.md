# 4406 original XBRL 35-row exact numeric reconciliation — completed

## Confirmed result
[GitHub Actions #40602534713](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40602534713) completed **success**. Artifact: `4406-original-xbrl-35-numeric-evidence` (ID 12779038733).

The review-only job regenerated the 35 unresolved-row references from the checked-in audit CSV and the existing reconciliation scripts, downloaded the actual five-filing original XBRL evidence from [successful extraction #40601946647](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40601946647), and performed exact per-row checks:

- Document ID resolved from source ZIP and original filing;
- exact element local name and context ID;
- unique original fact occurrence per source row;
- exact raw numeric equality using `Decimal` (no rounding tolerance);
- exact XBRL `unitRef` versus CSV `unit_id`.

**Result: 35/35 numeric matches, 0 mismatches; 35/35 unit matches.** This is in addition to the issuer-origin consolidated dimension-default and group-summary presentation evidence for the same 35 facts, established in [the scope report](4406_original_xbrl_dimension_default_scope_resolution_2026-10-28.md).

### Remaining gate before scoring
The above proves **original-fact lineage and exact raw values** for these 35 rows; it does not yet prove that all 35 are valid *Main Filter 2.3.1 scoring inputs*. Separate metric mapping, fiscal-period selection, year-over-year completeness, cash-flow and EPS accounting semantics, missing-data handling, and Stage 1 / Stage 2 gates remain to be verified. No new investment decision should be issued from this evidence alone.

**Safeguards remain:** `scoring_eligible=false`, `publish_to_index=false`, `approved_rows=0`. Existing EDINET collector, Claude configuration, main branch and index.csv were not modified.
