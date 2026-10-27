# 4406 XBRL consolidated-scope triage (2026-10-28)

Source: GitHub Actions run [40584128296](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40584128296), artifact `4406-consolidation-scope-review` (ID `12770509217`).

The review-only output includes **70** numeric reference matches: **35 explicitly labeled 連結**, **35 labeled その他**. None is approved for scoring.

All 35 unresolved rows are **seven management-indicator-summary XBRL concepts in each of five annual filings**, with exactly 7 rows per EDINET document:

| XBRL concept | Rows |
| --- | ---: |
| `jpcrp_cor:NetSalesSummaryOfBusinessResults` | 5 |
| `jpcrp_cor:OrdinaryIncomeLossSummaryOfBusinessResults` | 5 |
| `jpcrp_cor:ProfitLossAttributableToOwnersOfParentSummaryOfBusinessResults` | 5 |
| `jpcrp_cor:BasicEarningsLossPerShareSummaryOfBusinessResults` | 5 |
| `jpcrp_cor:NetCashProvidedByUsedInOperatingActivitiesSummaryOfBusinessResults` | 5 |
| `jpcrp_cor:NetCashProvidedByUsedInInvestingActivitiesSummaryOfBusinessResults` | 5 |
| `jpcrp_cor:RateOfReturnOnEquitySummaryOfBusinessResults` | 5 |

Source documents: `S100OK43`, `S100R83V`, `S100TUAP`, `S100W17N`, `S100YGXD`, 7 rows each.

**Root-cause hypothesis (not yet proven):** the existing extraction labels generic management-indicator contexts `その他` instead of resolving the consolidated-vs-standalone table where the fact is presented. Exact numeric matches to consolidated issuer references are corroborating evidence, **not proof of consolidated scope**.

Next step: inspect the original annual-report XBRL context definitions and table presentation (including dimensions) and compare consolidated and standalone indicator blocks; then create explicit per-concept evidence of the correct scope. Do not relabel source audit rows or auto-approve them.

Safety: `scoring_eligible=false`, `publish_to_index=false`, 0 approved, no changes to existing EDINET collector, Claude settings, `main`, or `index.csv`.
