# Main Filter 2.3.1 production-readiness audit — 4406 (2026-10-28)

**No formal score is authorized. No production merge or index update.**

## Confirmed working automation
- EDINET five-year source CSV and official-PDF comparison: 45/45 matched, with 680 extracted candidate rows still unapproved for scoring.
- Evidence inventory: 45 provenance-tagged review entries, scoring_eligible=false.
- Scoring bridge dry-run: STAGE1 DATA-INSUFFICIENT, adjusted_score=null, publish_to_index=false.
- FCF sensitivity: reported 3y FCF 5,264m JPY vs 4,322m after excluding 2026 investment-security sale proceeds of 942m; neither is automatically normalized FCF.
- Separate CI test suites: primary gate 7, scoring bridge 5, FCF 4, inventory gate 4. Each has passed on its own run.

## Blocking tasks before formal scoring
| Category | Status | Next required evidence / decision |
|---|---|---|
| XBRL candidates | BLOCKED | Audit 680 extracted rows individually for consolidation, context, units, amended filings, then explicitly approve rubric inputs; 45 PDF matches do not constitute blanket approval |
| ROIC numerator | BLOCKED | Determine tax-adjusted operating profit/NOPAT per canonical filter definition; do not infer from ROE |
| ROIC denominator | BLOCKED | Confirm capital employed, minority interests, operating/non-operating investment securities, lease treatment, and FY2025/FY2026 averaging |
| WACC/H hurdle | BLOCKED | Document dated risk-free rate, equity risk premium, beta, cost of debt, capital weights, tax rate and official hurdle rule |
| Dilution | REVIEW | FY2023–FY2026 issued shares stable at 37,286,906; verify potential dilutive securities and later filings |
| Finance/CF | REVIEW | Verify complete debt and EBITDA definitions, FCF treatment of security sales, equity ratio, three-year ratios |
| JPX short positions | BLOCKED | Date-stamped 0.5% disclosure series and 90-day lookback, or explicit not-applicable determination |
| Industry PER | BLOCKED | Date-stamped JPX 33-sector reference and applicable company PER |
| IR event alpha | BLOCKED | Company announcement timestamp and 5-trading-day returns against correct index |
| Scoring rubric mapping | BLOCKED | Per-subitem evidence with source and explicit approval; no automatic promotion of review data |

## Code behavior requiring specification review
- `scripts/scoring_engine.py` requires both stage1 achievement >=65% **and raw stage1 points >=52**, even when `not_applicable` removes points from the denominator. This may be inconsistent with a denominator-adjusted threshold for non-applicable items; **do not change without comparing canonical spec**.
- `roic_unavailable` currently generates a notice, not a BUY block; confirm canonical behavior.
- `scripts/rubric_scoring.py` FCF stability accepts reported OCF+ICF, potentially including nonrecurring security sales.
- A numeric score must never be derived from the review-only inventory.

## Safeguards
Continue all edits on `feature/source-provenance-report-20261028`; preserve `main`, Claude files, existing EDINET workflows and `index.csv`. Merge only after explicit user approval and passing end-to-end tests.
