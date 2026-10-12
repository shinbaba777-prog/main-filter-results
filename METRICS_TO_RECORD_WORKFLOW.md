# Source-verified score preparation and recording

## Required order

1. Copy `examples/metrics_payload.template.json` to a working JSON file.
2. Populate metrics only from source-verified data. Keep unknown metrics as `null`; do not turn unknowns into zero.
3. Set every `buy_block_inputs` boolean to explicit `true` or `false` only after checking the condition. The template intentionally uses `null` so unreviewed conditions cannot silently become false.
4. Calculate and set `base_upside_pct` to the Base scenario upside percentage. If the scenario has not been assessed, stop: scoring/recording must not proceed because the +20% BUY-block condition is unresolved.
5. Prepare the rubric items:
   ```sh
   python3 scripts/prepare_analysis.py metrics.json payload.json
   ```
   This rejects absent/unverified BUY-block booleans.
6. Review the resulting payload and scoring before any write:
   ```sh
   python3 scripts/record_verified_analysis.py payload.json --dry-run
   ```
7. Only after verifying the output, record it:
   ```sh
   python3 scripts/record_verified_analysis.py payload.json
   ```

## Important limitations

- The validator checks that the mandatory BUY-block decisions were explicitly supplied. It does **not** independently determine whether the booleans are true; that still requires source review and calculation.
- The verified entry point rejects a missing, null, non-numeric, or non-finite Base scenario upside. It will not treat an unassessed scenario as passing the +20% BUY-block condition.
- This workflow is deterministic scoring from normalized inputs, not fully autonomous equity research. It does not yet automatically gather, reconcile, and verify every EDINET/XBRL, stock-price, sector-PER, short-position, IR-reaction, or scenario input.
- Use `record_verified_analysis.py` for both dry-run and actual recording; it validates mandatory block inputs and the assessed Base scenario before delegating to the recorder.
- Review the 2.3.1 specification as the authority for all scoring thresholds and BUY-block definitions.
