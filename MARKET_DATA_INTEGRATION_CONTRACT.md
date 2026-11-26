# Main Filter 2.3.1 — Market-data integration contract

This contract defines the evidence required before formal scoring. It does not make any candidate fact verified merely because a row exists.

## Input file

Use `data/market_data/market_data_inputs.csv` with the exact columns in `market_data_inputs_template.csv`. One row per metric, security code, as-of date and source. Store source URLs and retrieval timestamps; never store API keys or credentials in CSVs.

Required metadata:
- `security_code`: Japanese security code, normalized consistently.
- `as_of_date`: market/session date in Japan time (YYYY-MM-DD).
- `metric`: one of the enumerated fields below.
- `value`, `unit`, `source_name`, `source_url`, `retrieved_at_utc`.
- `verification_status`: `UNVERIFIED`, `VERIFIED_PRIMARY`, `VERIFIED_SECONDARY`, or `UNAVAILABLE`.
- `verification_note`: basis for confirmation, context/period, calculation method, or why unavailable.

## Metrics that must be independently gathered

- Market/valuation: `close_price`, `shares_outstanding`, `market_cap`, `actual_per`, `forecast_per`, `sector_per`, `market_per`, `next_earnings_date`.
- Financial/capital: `roic`, `wacc`, `net_debt`, `ebitda`, `dilution_risk`, `forecast_sales_growth`, `forecast_profit_growth`.
- Shorts: `jpx_short_balance_pct`, `jpx_short_balance_date`, `short_balance_history`.
- IR/market reaction: `ir_event_date`, `event_close_price`, `close_price_plus_5_business_days`, `benchmark_return_5d`, `excess_return_5d`.
- Market classification: `exchange_market`, `jpx33_industry`.

## Source and calculation rules

1. Prefer official company disclosures, EDINET, TDnet, JPX and exchange data. Secondary providers can cross-check but do not silently override official disclosures.
2. Each value must include date/period, unit, scope and source. If it cannot be obtained or reconciled, record `UNAVAILABLE`; never infer it from an adjacent metric.
3. JPX short balances are dated observations. A missing report is not a zero balance; only classify as zero/non-applicable if the source and applicable disclosure rules support that conclusion.
4. Five-business-day IR excess return requires the actual event date, stock prices, matching benchmark prices, correct exchange calendar and a reproducible calculation. Do not use calendar-day offsets.
5. Compute net debt and ROIC using the definitions in the active Main Filter 2.3.1 prompt. Exclude IFRS 16 lease liabilities from net debt if that is the active rule. Do not compute ROIC/WACC from incompatible scopes or mixed accounting periods.
6. This contract is not a substitute for the active Main Filter 2.3.1 scoring specification. Do not assign points or BUY/HOLD based only on this file.

## Gate

Formal scoring remains blocked unless:
- all expected EDINET periods are present and reconciled, including amendments;
- each material financial metric has source verification;
- required market/valuation/short/IR/capital metrics are verified or explicitly classified under the filter's missing-data rules;
- all formula inputs and as-of dates are compatible;
- the official scoring implementation passes independent tests.

Never auto-write the performance index from unverified inputs.
