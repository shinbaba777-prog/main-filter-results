# 4406 ROIC nine-input scope gate execution — 2026-10-28

Input: original EDINET XBRL candidate artifact 12779532335, GitHub Actions run 40604100300. Independent local inspection of its five document inventories.

| Fiscal year | Document ID | Required current-year consolidated candidate concepts |
|---|---|---|
| 2022 | S100OK43 | 9 / 9 |
| 2023 | S100R83V | 9 / 9 |
| 2024 | S100TUAP | 9 / 9 |
| 2025 | S100W17N | 9 / 9 |
| 2026 | S100YGXD | 9 / 9 |

Nine concepts: OperatingIncome, IncomeBeforeIncomeTaxes, IncomeTaxes (CurrentYearDuration), NetAssets, NonControllingInterests, CashAndDeposits, ShortTermLoansPayable, CurrentPortionOfLongTermLoansPayable, LongTermLoansPayable (CurrentYearInstant). All matched candidate rows without explicit dimensions. Consolidated interpretation depends on the previously corroborated original XBRL dimension-default, not absence of an explicit dimension alone.

**Scope warning:** Nine present concepts do not establish complete invested capital. Bonds, consolidated lease obligations, subscription rights, issuer-specific financing tags and beginning invested capital remain to be checked in original statements and notes. Missing candidate tags are not zero balances. Candidate data is not a finalized ROIC.

Gate remains: scoring_eligible=false; publish_to_index=false; approved_rows=0. No changes to main, index.csv, existing collector or Claude configuration.
