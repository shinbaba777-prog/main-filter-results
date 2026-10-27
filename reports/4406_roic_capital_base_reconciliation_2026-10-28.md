# 4406 ROIC capital-base reconciliation — review only (2026-10-28)

**Status: REVIEW_REQUIRED; scoring_eligible=false. No formal ROIC or WACC.**

Primary source: [2026 FY annual securities report on issuer IR library](https://www.nj-chem.co.jp/app/ir_library/securities), 2026-06-23; company consolidated financial statements. Cross-check: https://openfiling.app/companies/4406/disclosure (secondary transcription, not primary approval).

## FY2025 and FY2026 consolidated balance sheet (JPY millions)

| Field | FY2025 | FY2026 |
|---|---:|---:|
| Total equity including noncontrolling interests | 18,995 | 20,987 |
| Parent equity | 17,786 | 19,742 |
| Noncontrolling interests | 1,209 | 1,244 |
| Short-term borrowings | 270 | 260 |
| Current portion long-term borrowings | 2,100 | 2,063 |
| Noncurrent long-term borrowings | 4,760 | 4,946 |
| Current lease liabilities | 38 | 41 |
| Noncurrent lease liabilities | 126 | 91 |
| Cash and deposits | 2,942 | 5,685 |
| Noncurrent investment securities | 9,950 | 10,503 |

### Alternative capital-employed conventions (illustrations, NOT ROIC)

- Total equity + borrowings and lease liabilities - cash and deposits: FY2025 **23,347m** (18,995+7,294-2,942), FY2026 **22,703m** (20,987+7,401-5,685). Two-year average **23,025m**.
- Parent equity + borrowings and lease liabilities - cash and deposits: FY2025 **22,138m**, FY2026 **21,458m**; two-year average **21,798m**.
- Neither automatically equals operating invested capital. The FY2026 balance sheet holds 10,503m of investment securities and significant affiliate interests; blindly treating all invested assets as operating would materially distort ROIC. Investment securities include both operational/strategic and non-operating holdings, and subtraction requires defensible classification.

### Required before score

1. Confirm the controlling Main Filter 2.3.1 ROIC definition and how minority interest, cash, non-operating securities, goodwill, leases, and associates are handled.
2. Reconcile FY2025 and FY2026 invested capital using that definition and underlying notes.
3. Verify FY2026 NOPAT numerator (operating profit 576m, tax rate and adjustments), rather than assuming an arbitrary statutory rate.
4. Define WACC reference date, cost of equity, cost of debt, debt/equity weights and tax treatment; confirm the required threshold H.
5. Review how `scoring_engine.py` currently treats `roic_unavailable` as a **notice rather than a BUY block**; do not silently change its behavior without specification approval.

All figures are rounded to millions. Borrowings schedule aggregate totals may differ by 1m from the sum of displayed components due to rounding. This report is for audit only; no modification to `main`, `index.csv`, Claude files, or scoring engine.
