# 4406 full original XBRL instant-context audit — 2026-10-28

Evidence: GitHub Actions run [40612904461](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40612904461), artifact ID **12784130139** (`4406_full_balance_context_inventory.json`). Five original EDINET document IDs: S100OK43, S100R83V, S100TUAP, S100W17N, S100YGXD.

The extractor inventories **722** numeric facts in `CurrentYearInstant` and `Prior1YearInstant` contexts without explicit dimensions (138/144/145/147/148 facts respectively). This is a **context-limited inventory**, not a complete financial-statement/notes audit.

## Consolidated balance-sheet candidate balances (million JPY)

| Fiscal year | Lease assets net, PPE | Short-term borrowings | Current portion of long-term borrowings | Long-term borrowings | Lease liabilities | Bonds / CP | Subscription rights |
|---|---:|---:|---:|---:|---|---|---|
| FY2022 | 6 | 2,226 | 1,629 | 6,100 | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| FY2023 | 3 | 2,696 | 2,021 | 5,443 | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| FY2024 | 6 | 1,265 | 1,515 | 4,802 | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| FY2025 | 152 | 270 | 2,100 | 4,760 | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| FY2026 | 122 | 260 | 2,063 | 4,946 | UNVERIFIED | UNVERIFIED | UNVERIFIED |

Lease **assets** must not be substituted for lease **liabilities**. No fact named `LeaseObligationsCL`, `LeaseObligationsNCL`, `BondsPayable`, or `SubscriptionRightsToShares` was found in these exact two core contexts. **This is not evidence of a zero balance**: liabilities may be in `OtherCL`/`OtherNCL`, dimensioned contexts, note text blocks, issuer extensions, or separate financial statements.

## Additional FY2026 balance-sheet candidates

- `AssetRetirementObligationsCL`: **1,039 million JPY** (current).
- `AssetRetirementObligationsNCL`: **43 million JPY** (noncurrent).
- FY2025 `AssetRetirementObligationsNCL`: **827 million JPY**.
- These asset-retirement obligations must not automatically be added to interest-bearing debt. They warrant classification review separately.

## Audit conclusions

1. Borrowing subtotal for FY2026 is 7,269 million JPY, **not proven complete interest-bearing debt**.
2. Investigate `OtherCL` and `OtherNCL` with note disclosures and presentation/calculation linkbases, plus extension taxonomy labels.
3. Review the FY2026 change in asset-retirement obligation classification independently; it is **not** a proxy for lease debt.
4. Verify FY2021 opening invested capital from the FY2022 original prior-year context before attempting FY2022 ROIC.
5. Keep all ROIC values **unapproved** and all Main Filter 2.3.1 gates fail-closed: `scoring_eligible=false`, `publish_to_index=false`, `approved_rows=0`.

This review does not change existing collectors, Claude settings, the main branch, or index.csv.
