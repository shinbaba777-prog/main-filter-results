# 4406: Finance/CF rubric mapping — review only (2026-10-28)

Source data: EDINET five-year reconciled table `data/edinet/verified/4406_five_year_financials.csv`, company FY2026 earnings PDF https://www.nj-chem.co.jp/app/upload/ir/pdf/36433ee666c2c24d3f13cbb481af6901.pdf. Rubric code: `scripts/rubric_scoring.py` function `finance_cf_score`. **Not a formal score; candidate rubric mapping only.**

| Finance/CF subitem | Evidence | Rubric candidate | Verification state |
|---|---|---|---|
| 3y OCF / 3y parent NI | FY2024–26 OCF = 3578 - 224 + 1643 = 4997m; parent NI = 220 + 522 + 597 = 1339m; ratio 3.73; FY2025 OCF negative but not two consecutive years | 2/2 | REVIEW_REQUIRED: confirm rubric period/definitions and source approval |
| Net debt / EBITDA | FY2026 loans 7269m less cash/deposits 5685m = 1584m; simplified EBITDA 576 + 755 = 1331m; provisional ratio 1.19 | 1/2 **if definitions approved** | UNVERIFIED: full debt and EBITDA scope |
| 3y dilution | Shares outstanding and 3y history not audited | —/2 | UNVERIFIED |
| Equity ratio | FY2026 reported 48.9% | 1/2 | REVIEW_REQUIRED: source confirmed, rubric mapping not approved |
| 3y FCF stability | FY2024 3518m, FY2025 -398m, FY2026 2144m; 3y sum 5264m and latest positive | 2/2 | REVIEW_REQUIRED: FY2026 includes investment security disposals; verify FCF policy |

Candidate points for independently source-supported OCF/NI, equity ratio, FCF stability: 2 + 1 + 2 = **5 out of 6 considered**, NOT 5/10 final score; the remaining 4 points cannot be formally determined. Even these candidate points remain unapproved for formal scoring.

Cautions: `fcf_stability` code uses OCF+ICF without excluding securities sale proceeds, so it may reward nonrecurring divestments. This should be reviewed against the controlling Main Filter 2.3.1 specification before production use. Do not alter scoring_engine, index.csv, Claude settings, or main branch. ROIC/WACC, 3y dilution, short positions, JPX industry PER, and IR alpha remain incomplete.
