# 4406 ROIC 2.3.1 arithmetic cross-check — 2026-10-28

This is **review-only**. Original 2021–2026 balance candidates are from the existing reconciliation work. The figures below were independently recalculated from the published *rounded million-yen inputs*.

Formula: excess cash = max(cash and deposits − annual sales / 12, 0); invested capital candidate = parent equity candidate + consolidated borrowing schedule total − excess cash.

| FY | Parent equity candidate (JPY m) | Borrowing schedule (JPY m) | Cash (JPY m) | Sales (JPY m) | Excess cash (JPY m) | Invested capital (JPY m) |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | 15,208 | 8,925 | 3,148 | 24,437 | 1,111.6 | 23,021.4 |
| 2022 | 15,937 | 9,962 | 3,495 | 32,358 | 798.5 | 25,100.5 |
| 2023 | 15,866 | 10,166 | 2,956 | 33,105 | 197.3 | 25,834.8 |
| 2024 | 17,285 | 7,589 | 3,816 | 32,863 | 1,077.4 | 23,796.6 |
| 2025 | 17,786 | 7,295 | 2,942 | 32,703 | 216.8 | 24,864.3 |
| 2026 | 19,743 | 7,402 | 5,685 | 32,105 | 3,009.6 | 24,135.4 |

Arithmetic agrees with the prior provisional table to 0.1 million JPY except tie-rounding display choices (2023 25,834.75; 2025 24,864.25). **This check does not independently verify the upstream accounting inputs.**

Prior provisional ROIC series, **not formally approved**: FY2022 4.73%; FY2023 −1.20%; FY2024 0.95%; FY2025 2.68%; FY2026 2.24%.

Remaining blockers: independently verify annual pretax income and total income taxes for all years, effective-tax-rate fallback rules, debt and equity schedule line-level rounding, and final 2.3.1 gating. Do not infer zero for an absent XBRL tag. No scoring or index publishing.

`scoring_eligible=false`, `publish_to_index=false`, `approved_rows=0`.

Protected: main, index.csv, existing EDINET collectors, Claude-related settings.
