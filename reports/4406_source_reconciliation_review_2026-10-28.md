# 4406 source reconciliation — review only

Checked 2026-10-28. Comparison: existing EDINET verified CSV versus official earnings PDFs. This does not approve the separate 680 extracted candidate rows.

Source CSV: data/edinet/verified/4406_five_year_financials.csv

| FY Mar | Sales | OP | Ordinary | Net income | EPS | OCF | ICF | FCF | ROE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2022 | 32358 | 1202 | 1589 | 811 | 21.76 | 1078 | -1602 | -524 | 5.2 |
| 2023 | 33105 | -439 | 105 | -444 | -11.92 | 104 | -659 | -555 | -2.8 |
| 2024 | 32863 | 361 | 780 | 220 | 5.92 | 3578 | -60 | 3518 | 1.3 |
| 2025 | 32703 | 829 | 1195 | 522 | 14.00 | -224 | -174 | -398 | 3.0 |
| 2026 | 32105 | 576 | 547 | 597 | 16.03 | 1643 | 501 | 2144 | 3.2 |

Units: million JPY except EPS (JPY) and ROE (%). FCF = OCF + ICF. 45/45 cells match the official earnings summary PDF figures reviewed in this session. FY2023 OCF/ICF use corrected disclosure (2023-05-18), not original filing.

Official PDF links:
- FY2022 https://www.nj-chem.co.jp/app/upload/ir/pdf/7886c91d07b578a9668c7f24ad043e7b.pdf
- FY2023 correction https://www.nj-chem.co.jp/app/upload/ir/pdf/902fa1a42a70865c4acb65e800cd039c.pdf
- FY2024 https://www.nj-chem.co.jp/app/upload/ir/pdf/9a99425afa1448d2ba95ca002fa93b69.pdf
- FY2025 https://www.nj-chem.co.jp/app/upload/ir/pdf/6c2c396ea2b7e6780721715f90b83c3a.pdf
- FY2026 https://www.nj-chem.co.jp/app/upload/ir/pdf/36433ee666c2c24d3f13cbb481af6901.pdf

Validation limits: did not reparse the original EDINET ZIPs here. data/edinet/extracted/financial_metric_audit_summary.json still reports zero approved scoring rows among 680 candidates. ROIC, WACC, leverage, shorts, sector PER and event alpha remain unverified. No scoring or dashboard update authorized.
