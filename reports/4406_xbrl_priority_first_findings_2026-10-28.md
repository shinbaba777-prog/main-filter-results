# 4406 XBRL priority queue — first artifact inspection (2026-10-28)

Source: GitHub Actions run [40582953435](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40582953435), artifact `4406-xbrl-priority-review` (ID 12770013568).

- 680 XBRL candidate rows grouped into **50 filing-by-metric groups**, five annual filing ZIPs.
- **0 rows approved**; this is a prioritization output, not a scoring authorization.
- Five ROE groups (one per filing) each have 10 candidate rows, all 10 marked `CONSOLIDATION_SCOPE_UNCLEAR` and `UNIT_UNCLEAR`.
- FY2022 filing groups: EPS 10 candidate rows, ordinary profit 14, sales 14, each flagged for unclear consolidated scope. Similar EPS groups occur in subsequent filing ZIPs.
- Important: review priority is heuristic, and includes historical contexts; do not assume every candidate represents its ZIP's current fiscal year.
- For ROE, determine whether `unit_id` and raw value represent percentage or decimal ratio before conversion. Also distinguish consolidated from nonconsolidated management-indicator tables.
- For sales/ordinary profit, identify current-year consolidated contexts and compare numeric values against five-year issuer-PDF reference; source-row flags must not be cleared merely because a value matches.
- For FY2023, use corrected operating/investing CF values (104m / -659m) and preserve amendment provenance.

## Next manual review gate
For each target fiscal year, record `source_zip`, `source_csv`, `row_number`, `element_id`, `context_id`, `consolidation_scope`, `unit_id`, original value, normalized value, issuer PDF reference, and explicit reviewer approval. Only then consider a separate approval mechanism with tests. Do not alter `financial_metric_audit.csv` or promote all 680 rows.

Status: REVIEW_REQUIRED; scoring_eligible=false.
