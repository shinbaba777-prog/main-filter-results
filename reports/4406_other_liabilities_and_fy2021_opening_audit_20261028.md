# 4406: consolidated other liabilities and FY2021 opening balances (2026-10-28)

Evidence: original EDINET XBRL five-document full instant-context inventory, Actions [40612904461](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40612904461), artifact **12784130139**. Each figure is from `CurrentYearInstant` unless stated otherwise; unit million JPY. The source instance is `XBRL/PublicDoc/jpcrp030000-asr-001_E00882-000_YYYY-03-31_01_YYYY-06-DD.xbrl`.

| FY | Other current liabilities (`OtherCL`) | Other noncurrent liabilities (`OtherNCL`) | Total |
|---|---:|---:|---:|
| 2022 | 1,242 | 122 | 1,364 |
| 2023 | 2,089 | 154 | 2,243 |
| 2024 | 1,710 | 116 | 1,826 |
| 2025 | 1,150 | 144 | 1,294 |
| 2026 | 1,378 | 106 | 1,484 |

**These are aggregate other-liability line items, not confirmed lease liabilities.** Never add their entire balances to interest-bearing debt. Inspect the original notes, taxonomy extensions and presentation linkbases to establish any lease portion.

## FY2021 comparative opening balance from FY2022 original S100OK43

The original FY2022 XBRL includes `Prior1YearInstant` (2021-03-31) numeric facts:

| Concept | Million JPY |
|---|---:|
| `NetAssets` | 16,216 |
| `NonControllingInterests` | 1,008 |
| `CashAndDeposits` | 3,148 |
| `ShortTermLoansPayable` | 2,786 |
| `CurrentPortionOfLongTermLoansPayable` | 1,819 |
| `LongTermLoansPayable` | 4,309 |
| `OtherCL` | 1,769 |
| `OtherNCL` | 207 |

FY2021 parent-equity **candidate** = 16,216 − 1,008 = **15,208 million JPY** before subscription-rights adjustment; FY2021 borrowings **subtotal** = 2,786 + 1,819 + 4,309 = **8,914 million JPY**. Neither is final invested capital. Opening FY2021 data **exists**, so do not mark the entire FY2021 opening period as missing.

## Remaining review and fail-closed status

- Check notes and extension taxonomy for lease debt, bonds, commercial paper, subscription rights and balances hidden in other liabilities.
- Validate original FY2021 and FY2022 beginning/end invested-capital completeness before ROIC.
- No assumption that absent lease/bond tags mean zero.
- `scoring_eligible=false`, `publish_to_index=false`, `approved_rows=0`.
- No modifications to existing EDINET collector, Claude settings, main or index.csv.
