# 4406 ROIC unresolved liabilities audit (2026-10-28)

Source: GitHub Actions run 40604100300, artifact 12779532335, original EDINET XBRL candidate inventory. The inventory is a **keyword-filtered subset**, not a complete financial-statement extract. Absence from it **does not prove zero balances**.

## FY2026 (S100YGXD) verified candidate facts

- Consolidated CurrentYearInstant: NetAssets 20,987,000,000 JPY; NonControllingInterests 1,244,000,000 JPY; CashAndDeposits 5,685,000,000 JPY; ShortTermLoansPayable 260,000,000 JPY; CurrentPortionOfLongTermLoansPayable 2,063,000,000 JPY; LongTermLoansPayable 4,946,000,000 JPY.
- Consolidated CurrentYearDuration: OperatingIncome 576,000,000 JPY; IncomeBeforeIncomeTaxes 679,000,000 JPY; IncomeTaxes 32,000,000 JPY.
- **Nonconsolidated** CurrentYearInstant: LeaseObligationsCL 38,000,000 JPY; LeaseObligationsNCL 89,000,000 JPY. **Do not add these to consolidated invested capital.**
- Consolidated CurrentYearDuration: RepaymentsOfFinanceLeaseObligationsFinCF -39,000,000 JPY; cash flow is **not** period-end lease liability.
- No matching consolidated lease liability, bonds payable or subscription-rights balance candidate was found in this *limited inventory*. Mark **UNVERIFIED**, not zero.

## Required gate before formal ROIC

1. Examine **full original consolidated BS presentation/calculation linkbase and relevant note disclosures** for lease liabilities, bonds, other interest-bearing financing, subscription rights and potential custom extension tags. The keyword-filtered XBRL extract cannot establish completeness.
2. Cross-check CurrentYearInstant and Prior1YearInstant for the same reporting perimeter and unit, including FY2021 opening capital for FY2022 ROIC.
3. Resolve whether noncontrolling interests and subscription rights are separately identified; document subtraction and any nil or omitted line with evidence.
4. Recalculate 2022-2026 ROIC from the 2.3.1 definition only when all inputs are verified; compare against prior provisional values, which are **not approved**.

Fail-closed: scoring_eligible=false; publish_to_index=false; approved_rows=0. No modifications to main, Claude configuration, or index.csv.
