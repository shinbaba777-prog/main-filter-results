# 4406 — 25 XBRL numeric mismatches: root-cause triage (2026-10-28)

Evidence: GitHub Actions [40583537486](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40583537486), artifact `4406-xbrl-current-year-review` ID `12771000309`. The original machine-generated JSON was downloaded and grouped by `candidate_metric` and `element_id`.

## Exact result
- **90** current-year numeric comparisons; **65** match issuer-PDF references, **25** do not.
- **All 25 mismatches are in the broad candidate category `profit`**, not in sales, operating profit, ordinary profit, EPS, operating CF, or investing CF.
- Of the 40 `profit` comparisons, **15 match** the reference parent-attributable net income and **25 mismatch** because the candidate mapper also included *different accounting concepts*:
  - `jppfs_cor:IncomeBeforeIncomeTaxes`: 10 mismatches (pre-tax income, not parent net income).
  - `jppfs_cor:ProfitLoss`: 10 mismatches (consolidated total profit, not parent net income).
  - `jppfs_cor:ProfitLossAttributableToNonControllingInterests`: 5 mismatches (minority-attributable profit, not parent net income).
- Exact target tags matching parent-attributable net income: `jpcrp_cor:ProfitLossAttributableToOwnersOfParentSummaryOfBusinessResults` (5 matches) and `jppfs_cor:ProfitLossAttributableToOwnersOfParent` (10 matches).
- Other comparisons: EPS 5/5, investing CF 10/10, operating CF 10/10, operating profit 5/5, ordinary profit 10/10, sales 10/10. These are **numeric matches only**; 0 rows are approved for scoring.

## Concrete examples
- FY2022 parent-attributable profit reference **811m JPY**; candidate pre-tax profit **930m**, total profit **881m**, and noncontrolling profit **69m**. These values should not be forced to equal 811m.
- FY2023 parent-attributable profit reference **-444m JPY**; candidate pre-tax profit **-230m**, total profit **-397m**, and noncontrolling profit **47m**.

## Fix before any scoring
Replace the broad `profit`-to-parent-net-income assumption with a concept-aware classifier. Different concepts must be classified as **NOT_COMPARABLE**, not **NUMERIC_MISMATCH**. Preserve raw rows and their original audit status; do not change original extraction/audit files. Still verify consolidated context, units, amendment provenance, and source row before granting approval.

Status: REVIEW_REQUIRED. Scoring eligibility: false. Publication: forbidden.
