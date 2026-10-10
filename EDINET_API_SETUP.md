# EDINET API v2 setup

This repository uses the Financial Services Agency's official EDINET API v2. The API key is never committed to the repository and must not be pasted into chat, source code, or public files.

## One-time setup

1. Register/sign in and issue an API key at https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1 .
2. Open this repository on GitHub: https://github.com/shinbaba777-prog/main-filter-results
3. Go to **Settings → Secrets and variables → Actions → New repository secret**.
4. Set the secret name to exactly `EDINET_API_KEY` and paste the key into the secret's value field. Save it. Do not add the key as a repository variable.
5. Go to **Actions → EDINET API data refresh** and select **Run workflow**.
6. For a metadata-only check, leave both inputs empty/default. To try a specific company, enter its securities code (e.g. `4406`) and check **Download the latest annual-report XBRL CSV ZIP for the code**. Run workflow.

## Automation

- Scheduled run: daily at 01:35 Japan time (16:35 UTC).
- The workflow refreshes filing metadata for the most recent 14 calendar days and commits it under `data/edinet/documents.csv` and `data/edinet/documents.json`.
- A manual run can optionally download the latest matching annual-report CSV ZIP when EDINET marks CSV as available. Files are stored under `data/edinet/`.
- The workflow does not modify `index.csv` or automatically score companies. This is intentional: EDINET disclosures are raw primary-source evidence, not a substitute for the Main Filter 2.3.1 calculations, cross-checks, short-interest data, price data, or missing-data rules.
- The 4-digit Japanese securities code is normalized to the 5-digit EDINET securities code form when matching (e.g. 4406 → 44060).

## Security and troubleshooting

- Never paste the API key into a chat or commit it to any file.
- The key is passed only as the GitHub Actions secret `EDINET_API_KEY`.
- If the workflow says the key is missing, check that the secret is named exactly `EDINET_API_KEY`.
- If no CSV ZIP is found, the annual report may be older than the 14-day metadata window or a CSV may not be available. Increase `--days` in `scripts/fetch_edinet.py` and rerun; do not assume no filing exists.
- EDINET may temporarily return errors or restrict excessive access. The script uses a low request rate and does not repeatedly retry failed dates.
- The API is provided under the EDINET API terms. Respect those terms and cite EDINET as the source when using retrieved data.
