# Market-data verification gate

Before Main Filter 2.3.1 scoring, record each non-EDINET input with its as-of date, unit, source URL, retrieval timestamp, and verification status.

Required groups:
- Price/valuation: close, shares outstanding, market cap, actual/forecast PER, same-market and JPX33 industry PER, next earnings date.
- Capital/financial: ROIC, WACC, net debt excluding IFRS 16 lease liabilities where required, EBITDA, dilution, forecast growth.
- Short positions: dated JPX institutional short balance history. Missing data is not zero.
- IR reaction: event date, close on event date, close after five business days, matching benchmark return, excess return.
- Classification: exchange market and JPX33 industry.

Prefer EDINET, TDnet, JPX, exchange data and official company IR. Secondary sources are cross-checks, not silent replacements. If a value cannot be reconciled, mark it unavailable and apply the active filter's missing-data rules; do not estimate it from adjacent values.

This gate does not assign scores. Formal scoring and index.csv updates remain blocked until source periods, amendments, definitions, units and calculations have been reviewed.