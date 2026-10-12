# EDINET → Main Filter 2.3.1 metrics draft bridge

## Purpose

`scripts/build_edinet_metrics_draft.py` connects the existing EDINET extraction/review queue to the Main Filter metrics shape. It is intentionally **draft-only**. EDINET rows start as `MANUAL_REVIEW_REQUIRED`; the script consumes only rows that a reviewer explicitly changes to `APPROVED`.

It does not fetch stock prices, industry PER, institutional short positions, IR event returns, forecasts, ROIC inputs, or Base/Bear scenarios. It must not be described as full autonomous scoring.

## Procedure

1. Run the EDINET workflow manually for a known securities code and download annual-report CSVs. For a five-year series, enable the history option.
2. Inspect `data/edinet/extracted/core_metric_review_queue.csv`. Confirm filing, fiscal period, consolidated scope, context, unit/scale, sign, and duplicate handling from the official filing.
3. Change `review_status` to `APPROVED` only for facts verified against the source. Set `review_reason` to `APPROVED_SOURCE_VERIFIED` after all checks are complete. Do not approve ambiguous scope or period rows.
4. Generate a draft:
   ```sh
   python scripts/build_edinet_metrics_draft.py \
     --code 1234 --company "会社名" --analysis-date 2026-10-12 \
     --out data/edinet/metrics_draft_1234.json
   ```
   Replace the sample security code, company, and date.
5. Review every generated fact and its `edinet_fact_provenance`. The JSON keeps non-EDINET facts and BUY-block inputs null by design. It is not yet accepted by `prepare_analysis.py`; this is a safety barrier until those missing inputs are independently sourced and reviewed.

## Current scope and known limits

- Draft derivations include sales and operating-profit growth, operating margin, and EPS growth where the approved 5-year facts are complete.
- Financial statements can contain multiple facts for one concept/period. Conflicting approved values fail closed rather than choosing one silently.
- This is a bridge from a human-reviewed queue, not an automatic approval of XBRL concepts. The existing parser's heuristic candidates are not sufficient evidence by themselves.
- Main Filter 2.3.1 still needs source-verified market/valuation/short/IR/scenario inputs before complete scoring and recording.
