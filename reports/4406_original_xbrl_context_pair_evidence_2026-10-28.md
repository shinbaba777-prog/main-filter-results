# 4406 original XBRL: context-pair evidence and remaining scope gate

## Verified original XBRL evidence
Source: successful [EDINET original XBRL manual evidence #40575714021](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40575714021), artifact `edinet-4406-original-contexts-40575714021`. Cross-reference: [57-test integrated safety #40585857970](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40585857970).

Each original filing has a PublicDoc XBRL instance and two AuditDoc XBRL instances. The 35 unresolved management-indicator facts (7 per filing) use `CurrentYearDuration`. Its period matches the filing year and its `dimensions` array is empty. **In the same PublicDoc instance**, a separate `CurrentYearDuration_NonConsolidatedMember` context has the same period and an explicit dimension:

- dimension: `jppfs_cor:ConsolidatedOrNonConsolidatedAxis`
- member: `jppfs_cor:NonConsolidatedMember`

This exact pairing exists in all five filings, with 2022 through 2026 periods respectively. The explicit member **confirms the latter context is nonconsolidated**; it does not by itself prove that the dimensionless `CurrentYearDuration` context is consolidated.

| Document | PublicDoc context count | AuditDoc contexts | Unresolved `CurrentYearDuration` facts |
|---|---:|---:|---:|
| S100OK43 | 230 | 2 + 2 | 7 |
| S100R83V | 213 | 2 + 2 | 7 |
| S100TUAP | 221 | 2 + 2 | 7 |
| S100W17N | 211 | 2 + 2 | 7 |
| S100YGXD | 211 | 2 + 2 | 7 |

## Required final disambiguation
Compare the **actual XBRL fact occurrences** (concept QName, contextRef, value, unitRef) and the issuer's consolidated / nonconsolidated summary-table presentation and definition linkbases. Do not infer consolidated scope from context naming, absent dimensions, or numeric agreement alone. The existing context-only artifact does **not** contain fact occurrences or linkbases, so this final check remains pending.

## Strict gate
`status=REVIEW_REQUIRED`, `scoring_eligible=false`, `publish_to_index=false`, `approved_rows=0`. Keep existing collector, Claude configuration, main branch and index.csv unchanged. No fresh original XBRL API request is needed until the context-only evidence gap is explicitly addressed.
