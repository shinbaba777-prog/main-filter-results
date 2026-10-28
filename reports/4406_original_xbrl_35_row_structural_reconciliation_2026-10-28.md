# 4406: 35-row original XBRL structural reconciliation (2026-10-28)

## Source artifacts
- [Original XBRL fact + linkbase extraction #40601946647](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40601946647), artifact `4406-original-xbrl-fact-evidence`.
- [Integrated review #40585857970](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40585857970), artifact `4406-integrated-review-artifacts`, file `4406_consolidation_scope_review.json`.

## Independent local crosscheck
Joined all 35 previously unresolved source-CSV row references against the 5 original XBRL document IDs using exact concept local-name and `CurrentYearDuration` context. Checked each fact occurs exactly once; has a unit; has no explicit dimension; the original issuer definition linkbase `rol_BusinessResultsOfGroup` declares `BusinessResultsOfGroupTable -> ConsolidatedOrNonConsolidatedAxis` and `ConsolidatedOrNonConsolidatedAxis -> ConsolidatedMember` via `dimension-default`; and the group-summary presentation network includes each target concept.

| Test | Result |
|---|---|
| Source CSV row references reconciled | 35 / 35 |
| Unique original XBRL fact per row | 35 / 35 |
| Group-summary concept network membership | 35 / 35 |
| Consolidated dimension-default | 35 / 35 |
| Structural check failures | **0** |
| Unit distribution | JPY 25, JPYPerShares 5, pure 5 |

**Scope result:** the 35 facts have issuer-origin structural evidence for consolidated scope; they are no longer ambiguous on the dimension-default criterion. The five original filings contain seven candidate facts each.

**Not yet done:** compare the *actual numeric content and unit/decimals normalization* of each of the 35 referenced original source CSV rows against the original XBRL fact values; verify periods and fiscal-year accounting semantics. The downloaded review artifact includes source CSV paths and row numbers, **not the CSV row contents**. Do not claim that numeric source-CSV reconciliation has passed.

**Safety:** `scoring_eligible=false`, `publish_to_index=false`, `approved_rows=0` pending independent numeric and accounting-definition checks. Existing EDINET collector, Claude settings, main and index.csv unchanged.
