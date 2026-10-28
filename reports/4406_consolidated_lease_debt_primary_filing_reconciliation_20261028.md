# 4406 consolidated lease obligations — primary-filing reconciliation (2026-10-28)

**Correction of prior gap:** The consolidated `借入金等明細表` in the original annual securities report explicitly provides lease-obligation balances. The previous inability to find consolidated `LeaseObligationsCL`/`LeaseObligationsNCL` as core instant XBRL facts was a **tagging/context discovery limitation**, not a missing reported balance.

## Original filing figures (million JPY)

| FY | Short-term borrowings | Current long-term loans | Long-term loans | Current lease obligations | Noncurrent lease obligations | Total schedule |
|---|---:|---:|---:|---:|---:|---:|
| 2024 | 1,265 | 1,515 | 4,802 | 2 | 4 | 7,589 |
| 2025 | 270 | 2,100 | 4,760 | 38 | 126 | 7,295 |
| 2026 | 260 | 2,063 | 4,946 | 41 | 91 | 7,402 |

Sources:
- FY2026 original S100YGXD, EDINET-sourced PDF https://info.gbiz.go.jp/hojin/edinetDownload?docId=S100YGXD , page 78/99 (`連結附属明細表／借入金等明細表`).
- FY2025 original S100W17N https://info.gbiz.go.jp/hojin/edinetDownload?docId=S100W17N , consolidated borrowing schedule.
- FY2024 original S100TUAP, consolidated borrowing schedule (also comparative FY2023 opening balances).

The schedule totals differ by 1–2 million from adding rounded display lines in some years. **Use original reported total**, not a forced balancing adjustment. FY2026 260+2063+4946+41+91=7401 while displayed total=7402, due to underlying rounding.

FY2026 **confirmed consolidated lease balance = 132 million JPY** (41+91). FY2025 = 164 million. FY2024 = 6 million. These are **not** the nonconsolidated lease balances (FY2026 127 million; FY2025 160 million).

## Remaining checks before ROIC approval

1. Read the FY2022 and FY2023 original consolidated borrowing schedules to establish their lease balances and FY2021 comparative opening lease balance. **Do not infer zero**.
2. Validate year-by-year net assets, NCI, subscription rights, cash and sales against original filings; check FY2021 beginning invested capital.
3. Calculate excess cash, effective tax rate, invested capital and average beginning/end invested capital using exact filter 2.3.1 rules.
4. Do not publish or score yet: `scoring_eligible=false`, `publish_to_index=false`, `approved_rows=0`.

**No changes** to existing EDINET collectors, Claude settings, main or index.csv.
