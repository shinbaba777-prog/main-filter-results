# Source-verified score preparation and recording

## Required order

1. Copy `examples/metrics_payload.template.json` to a working JSON file.
2. Populate metrics only from source-verified data. Keep unknown metrics as `null`; do not turn unknowns into zero.
3. Set every `buy_block_inputs` boolean to explicit `true` or `false` only after checking the condition. The template intentionally uses `null` so unreviewed conditions cannot silently become false.
4. Set `base_upside_pct` to the calculated Base scenario upside percentage, or keep `null` if the scenario has not been assessed.
5. Prepare the rubric items:
   ```sh
   python3 scripts/prepare_analysis.py metrics.json payload.json
   ```
   This rejects absent/unverified BUY-block booleans.
6. Review the resulting payload and scoring before any write:
   ```sh
   python3 scripts/record_analysis.py payload.json --dry-run
   ```
7. Only after verifying the output, record it:
   ```sh
   python3 scripts/record_analysis.py payload.json
   ```

## Important limitations

- The validator checks that the mandatory BUY-block decisions were explicitly supplied. It does **not** independently determine whether the booleans are true; that still requires source review and calculation.
- A `null` Base scenario upside means the block condition is unassessed. Do not interpret it as proof that the +20% requirement passes.
- This workflow is deterministic scoring from normalized inputs, not fully autonomous equity research. It does not yet automatically gather, reconcile, and verify every EDINET/XBRL, stock-price, sector-PER, short-position, IR-reaction, or scenario input.
- Do not directly run `record_analysis.py` on a manually assembled payload that has bypassed `prepare_analysis.py` validation.
- Review the 2.3.1 specification as the authority for all scoring thresholds and BUY-block definitions.
