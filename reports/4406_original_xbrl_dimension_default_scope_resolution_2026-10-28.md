# 4406: original XBRL dimensional default resolves group-summary scope

## Evidence
Original EDINET ZIPs fetched in [GitHub Actions #40601946647](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40601946647), artifact `4406-original-xbrl-fact-evidence`, 5 documents (S100OK43, S100R83V, S100TUAP, S100W17N, S100YGXD), 275 fact occurrences and 3,741 relevant presentation/definition arcs.

For **each** of the five annual reports, the issuer's PublicDoc definition linkbase in role `http://disclosure.edinet-fsa.go.jp/role/jpcrp/rol_BusinessResultsOfGroup` contains:
1. `BusinessResultsOfGroupTable -> ConsolidatedOrNonConsolidatedAxis` (`hypercube-dimension`);
2. `ConsolidatedOrNonConsolidatedAxis -> ConsolidatedMember` (`dimension-domain`);
3. `ConsolidatedOrNonConsolidatedAxis -> ConsolidatedMember` (**`dimension-default`**);
4. `BusinessResultsOfGroupLineItems ->` all seven `*SummaryOfBusinessResults` target concepts (presentation arcs).

Each of the 35 target original facts uses `CurrentYearDuration`, which omits an explicit consolidation member. Under XBRL Dimensions default-member semantics, the issuer's definition linkbase explicitly declares `ConsolidatedMember` as the default for this axis. The same instance also has explicitly `NonConsolidatedMember` facts for sales, ordinary profit, EPS and ROE, providing independent fact-pair corroboration.

| Fiscal year | EDINET document | Default consolidated axis | Seven target group-summary concepts | Candidate scope |
|---|---|---|---|---|
| FY2022 | S100OK43 | confirmed | confirmed | consolidated |
| FY2023 | S100R83V | confirmed | confirmed | consolidated |
| FY2024 | S100TUAP | confirmed | confirmed | consolidated |
| FY2025 | S100W17N | confirmed | confirmed | consolidated |
| FY2026 | S100YGXD | confirmed | confirmed | consolidated |

**Scope finding:** 35/35 facts now have **positive issuer-origin dimensional-default evidence** for consolidated reporting. This is stronger than earlier numerical comparisons or missing-dimension inference. This finding applies to the seven specified `SummaryOfBusinessResults` concepts in the **BusinessResultsOfGroup** reporting network; do not generalize it to all XBRL contexts or concepts.

**Remaining independent gate:** map each fact back to the exact 35 source CSV rows and validate the source-document/context/period/unit/value lineage, including accounting-definition distinctions (profit attributable to owners of parent, cash flow, EPS, ROE). Until a separately tested approval gate is implemented, leave `scoring_eligible=false`, `publish_to_index=false`, `approved_rows=0`. The scope finding is **not** a Main Filter 2.3.1 BUY decision.

No modifications to existing EDINET collector, Claude settings, main branch, or index.csv.
