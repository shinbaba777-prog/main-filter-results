# 4406 original XBRL notes: bonds, share options and lease scope (2026-10-28)

Evidence: original five EDINET filings S100OK43 (FY2022), S100R83V (FY2023), S100TUAP (FY2024), S100W17N (FY2025), S100YGXD (FY2026). Actions [40618252933](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40618252933), artifact ID **12785912890**, `4406_original_xbrl_note_evidence.json`. 365 keyword-matched note/label/fact candidates total (60/55/59/93/98).

## Directly confirmed original-text evidence

All five filings have `AnnexedConsolidatedDetailedScheduleOfCorporateBondsTextBlock` in `CurrentYearDuration` with heading `【社債明細表】` and statement `該当事項はありません。` This directly supports **no applicable entries in the consolidated corporate-bonds schedule** for these fiscal years; it does not by itself resolve every conceivable commercial-paper or hybrid instrument classification.

All five filings have `NotesRegardingNewShareSubscriptionRightsEtcTextBlock` in `CurrentYearDuration` with `新株予約権等に関する事項` and `該当事項はありません。` This is direct original-note evidence for the stated scope, subject to final equity reconciliation.

## Lease facts: context must be preserved

`LeaseObligationsCL` and `LeaseObligationsNCL` were found with **`_NonConsolidatedMember`** context IDs, not consolidated current-year instant context. Examples:

- FY2024: individual current 0 million JPY; individual noncurrent 4 million JPY.
- FY2025: individual current 37 million JPY; individual noncurrent 123 million JPY; subtotal **160 million JPY**.
- FY2026: individual current 38 million JPY; individual noncurrent 89 million JPY; subtotal **127 million JPY**.

These values **must not be inserted into consolidated invested capital**.

`RepaymentsOfFinanceLeaseObligationsFinCF` in consolidated `CurrentYearDuration`: FY2022 -3m, FY2023 -3m, FY2024 -2m, FY2025 -31m, FY2026 -39m JPY. These are annual cash flows, **not year-end lease liabilities**.

## Remaining gates

- Confirm consolidated lease obligations from original financial-statement notes and whether any amount sits inside `OtherCL`/`OtherNCL`; don't set absent tag to zero.
- Independently verify year-end consolidated debt scope and equity reconciliation including subscription-rights.
- Keep `scoring_eligible=false`, `publish_to_index=false`, `approved_rows=0` until the original-filing evidence is complete.
- No change to main, index.csv, existing EDINET collectors or Claude settings.
