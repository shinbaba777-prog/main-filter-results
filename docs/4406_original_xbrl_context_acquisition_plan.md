# 4406 EDINET original XBRL context acquisition — review-only plan

## Verified prerequisite
Integrated regression [#40585508247](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40585508247): 53/53 tests passed. 65 current-year XBRL comparisons and five ROE ratios matched issuer references. 35 management-indicator facts have unresolved consolidation scope, but all 35 trace to original EDINET XBRL-to-CSV ZIP source paths.

## Source gap
The five currently committed ZIPs are `*_xbrl_csv.zip` (EDINET **CSV conversion** payloads), not proof of the original XBRL instance. Source ZIP inspection found no matching XBRL/XML context definition files. The `その他` extraction label cannot be converted to `連結` merely because numeric values agree.

## Required acquisition (without modifying the existing collector)
For each docID `S100OK43`, `S100R83V`, `S100TUAP`, `S100W17N`, `S100YGXD`, retrieve the EDINET **original filing** document through the official documents API (type=1 ZIP, not type=5 CSV conversion). Use the existing GitHub EDINET API secret; never print or interpolate it into logs. Use retry/backoff for HTTP 429, rate-limit JSON, and transient errors. Validate ZIP signature and XBRL instance presence; reject non-ZIP error bodies.

For every unresolved concept and document, extract:
- `contextRef`, `unitRef`, the XBRL namespace-qualified concept and numeric value;
- the `xbrli:context` entity, period, explicit/typed dimensions, and `ConsolidatedMember` / `NonConsolidatedMember` evidence;
- the presentation/table role if dimensions alone do not disambiguate;
- original document ID and immutable source ZIP checksum.

The context `CurrentYearDuration` is **not** itself proof of consolidated scope. Prefer exact context IDs and source context definitions over heuristic labels.

## Decision gate
Emit a separate machine-readable report with `scope_status=CONFIRMED_CONSOLIDATED` only where primary XBRL context and presentation evidence agree; otherwise `REVIEW_REQUIRED`. No automatic scoring approval: `scoring_eligible=false`, `publish_to_index=false`, and `approved_rows=0` for this entire research phase. Never rewrite the verified financials, existing audit CSV, `main`, Claude configuration, or `index.csv`.

## Operational guardrails
Use an isolated manual-dispatch review workflow and a five-minute timeout. Do not trigger repeated full historical rescans or store raw ZIP binaries in Git. Persist compact context evidence as a short-lived Actions artifact, without API keys or private metadata. The existing data-refresh workflow may trigger on feature-branch commits independently; it is not part of this review.
