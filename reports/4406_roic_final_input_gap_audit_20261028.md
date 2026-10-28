# 4406 ROIC final input audit: unresolved source and scope checks (2026-10-28)

## Verified execution
GitHub Actions [40624341237](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40624341237) passed the five safety regression tests, review-only arithmetic and artifact upload. This **does not approve the inputs**.

## Specific remaining issues (not merely generic rounding)
1. **FY2021 sales = 24,437 million JPY** is used to compute opening-year excess cash (3,148 − 24,437/12). The previously extracted FY2022 original inventory covered **instant balance-sheet contexts**, not duration sales. The FY2021 comparative sales figure needs a direct `Prior1YearDuration` original-filing provenance check.
2. **FY2021 borrowing schedule total = 8,925 million JPY** in the arithmetic input; independently confirmed FY2021 loan subtotal from original FY2022 `Prior1YearInstant` is **8,914 million JPY**. The difference is **11 million JPY**, plausibly lease obligations plus display rounding. The consolidated borrowing schedule is the required authority; verify its comparative figure and period before accepting 8,925.
3. **Parent equity**: FY2026 arithmetic uses 19,743 million JPY from net assets minus NCI; the earnings-per-share note reports 19,742 million JPY. Determine rounding policy from source facts rather than silently overriding.
4. **FY2022–2026 borrowing schedule totals** should be checked against original schedules and their underlying unrounded XBRL values; don't force sums of rounded line items to equal schedule totals.
5. **Tax gate**: five years of total income taxes and pretax profits have been cross-checked in earlier reports. Retain 30.6% fallback for FY2023 negative pretax.

## Effect of the FY2021 opening uncertainty
The FY2022 ROIC denominator includes FY2021 invested capital; incorrect FY2021 sales or borrowing total changes FY2022 ROIC. Other fiscal-year denominators also need period-accurate parent equity and debt.

## Required resolution
Use the original EDINET FY2022 document `S100OK43` to extract comparative `Prior1YearDuration` sales and the FY2021 borrowing schedule; cross-compare XBRL fact values to published notes. Keep evidence in an artifact with document ID, context ID, source instance and numeric units. Do not accept undocumented rounded numbers.

**Gates unchanged:** `scoring_eligible=false`, `publish_to_index=false`, `approved_rows=0`. No change to main, index.csv, EDINET collectors or Claude settings.
