# 4406 original XBRL contexts vs unresolved scope (2026-10-28)

Evidence from existing successful GitHub Actions runs:
- [Original XBRL fetch #40575714021](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40575714021), artifact `edinet-4406-original-contexts-40575714021`, five original XBRL filings, 1,106 contexts across PublicDoc and AuditDoc.
- [Integrated safety #40585857970](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40585857970), artifact `4406-integrated-review-artifacts`, 57 tests passed, 35 unresolved scope rows.

Cross-checked all 35 unresolved rows against the original **PublicDoc** instance context map. Every unresolved row uses `context_id=CurrentYearDuration`, with 7 rows per document. All five original context definitions exist and have **no explicit or typed dimensions**:

| Doc ID | Context period | Unresolved rows | Dimensions |
|---|---|---:|---|
| S100OK43 | 2021-04-01 – 2022-03-31 | 7 | none |
| S100R83V | 2022-04-01 – 2023-03-31 | 7 | none |
| S100TUAP | 2023-04-01 – 2024-03-31 | 7 | none |
| S100W17N | 2024-04-01 – 2025-03-31 | 7 | none |
| S100YGXD | 2025-04-01 – 2026-03-31 | 7 | none |

Seven concepts per filing: `NetSalesSummaryOfBusinessResults`, `OrdinaryIncomeLossSummaryOfBusinessResults`, `ProfitLossAttributableToOwnersOfParentSummaryOfBusinessResults`, `BasicEarningsLossPerShareSummaryOfBusinessResults`, `NetCashProvidedByUsedInOperatingActivitiesSummaryOfBusinessResults`, `NetCashProvidedByUsedInInvestingActivitiesSummaryOfBusinessResults`, `RateOfReturnOnEquitySummaryOfBusinessResults` (all `jpcrp_cor:`).

**Finding:** Original context IDs and periods are confirmed, but the empty dimension set alone cannot establish consolidated scope. Next inspect original XBRL fact occurrences and the consolidated/non-consolidated presentation or definition linkbase relationships; do not infer from a numeric match or the word `CurrentYear`.

**Fail-closed:** `status=REVIEW_REQUIRED`, `scoring_eligible=false`, `publish_to_index=false`, `approved_rows=0`. No existing collector, Claude settings, `main`, or `index.csv` changes.
