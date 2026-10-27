# 4406 original XBRL fact-pair evidence (2026-10-28)

**Source:** successful [original-XBRL fact extraction #40589527987](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40589527987), artifact `4406-original-xbrl-fact-evidence` (275 fact occurrences, 10 definition/presentation linkbase filenames). The previous [integrated safety run #40587833759](https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40587833759) passed 61 tests.

All five original PublicDoc instances contain seven target facts with context `CurrentYearDuration`, plus **four same-concept facts** with explicitly nonconsolidated context `CurrentYearDuration_NonConsolidatedMember` (sales, ordinary profit, EPS and ROE). The values differ in all five periods. This is strong direct evidence that the dimensionless and explicitly standalone contexts are different reporting series, but it is not an automatic consolidated-scope approval.

| FY ending March | Sales current-year (JPY million) | Sales explicitly nonconsolidated (JPY million) | Ordinary income current-year (JPY million) | Ordinary income explicitly nonconsolidated (JPY million) |
|---|---:|---:|---:|---:|
| 2022 | 32,358 | 28,449 | 1,589 | 1,253 |
| 2023 | 33,105 | 28,859 | 105 | -168 |
| 2024 | 32,863 | 28,122 | 780 | 455 |
| 2025 | 32,703 | 28,085 | 1,195 | 945 |
| 2026 | 32,105 | 26,819 | 547 | 511 |

**Still pending:** inspect the ten `*_def.xml` and `*_pre.xml` files (the extraction artifact contains their *filenames*, not XML contents) to prove the target fact placement in consolidated/standalone tables. The 35 unresolved facts should remain `REVIEW_REQUIRED`; `scoring_eligible=false`, `publish_to_index=false`, `approved_rows=0`. The four explicitly nonconsolidated same-concept pairs per year must not be substituted for the consolidated series.

No edits to the existing EDINET collector, Claude configuration, main branch or index.csv.
