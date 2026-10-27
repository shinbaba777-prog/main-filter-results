# 4406 FY2021 and ROIC source availability — inventory result

[GitHub Actions #40602820322](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40602820322) succeeded. Artifact `4406-fy2021-roic-source-inventory` (ID 12779490996).

- Existing checked-in `data/edinet` files inspected: **23**.
- FY2021 fiscal-year-end keyword/path candidates: **0**.
- Files containing ROIC-related *keywords*: **6**.
- Of these, the meaningful potential XBRL data files are `extracted/financial_metric_audit.csv` and `extracted/financial_metric_candidates.csv` (TotalAssets), and `extracted/xbrl_numeric_rows.csv` (TotalAssets, CashAndCashEquivalents). The other three are verified financial summaries that contain the label `roic` but have blank ROIC values.

This inventory is deliberately a **keyword search, not financial-fact validation**. No source-confirmed ROIC numerator/denominator or FY2021 values have been obtained by this job. A five-year annualized growth rate from FY2021 to FY2026 requires an FY2021 baseline; the current five filing years FY2022–FY2026 only cover four year-over-year intervals.

## Next required acquisition
1. Retrieve issuer original FY2021 EDINET filing or a later official comparative XBRL fact with matching period and consolidation scope. Validate the document ID, period, unit, and concept; never fill from estimates.
2. Inspect original XBRL values and accounting definitions for NOPAT, invested capital and capital-cost inputs; ROIC methodology must be explicitly fixed before computation.
3. Re-run source provenance, dimensional default, unit, numeric and scoring gates before changing approval.

**Safety unchanged:** scoring_eligible=false; publish_to_index=false; approved_rows=0. No index, main, Claude or existing collector modifications.
