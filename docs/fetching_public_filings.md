# Optional public filing fetch

The default workflow remains entirely offline. Public filings never overwrite the synthetic snapshot.

1. Use [SEC EDGAR search](https://www.sec.gov/edgar/search/) to locate a fund's public NPORT-P filing and select the XML holdings document. Record its fund/series, accession and reporting date separately. The script does not discover a filing or choose a fund.
2. Set a descriptive `SEC_USER_AGENT` containing a project or organization name and a real contact email. The script reads it from the environment and does not persist it.
3. Run the standalone fetch script with the exact document URL. A filing index or HTML rendering will fail XML/holdings checks.

```powershell
$Python = 'python'
$env:SEC_USER_AGENT = 'Project name contact@example.org'
# Replace the example contact and supply an actual selected SEC XML URL.
& $Python scripts/fetch_nport.py $SelectedSecXmlUrl
```

The URL must use `https://www.sec.gov/Archives/edgar/data/`. Redirects must remain in that scope. A 0.5-second pause precedes the request. The size limit is 20 MB; XML with DTD/entity declarations is rejected. No automatic retries run on a block. Raw XML is saved only after parsing finds supported holdings. Changed content at the same URL receives a timestamped filename. Each attempted request writes a success or failure manifest, with URL, UTC retrieval time, document/section, status and hash when available. Pre-request validation failures do not create a manifest.

Inspect and retain the raw XML before using `parse_holdings(path, net_assets=...)`. The parser is a holdings subset, not a complete regulatory filing reader. It ignores unsupported fields; some real schemas or optional-field combinations may fail. Do not report full filing reconciliation unless independently checked. Append the exact accession, reporting period, retrieval date, source URL and parsed section to `docs/source_verification.md` after a successful real run.

The script was written and local mocked tests were run. No live network call was run in this project build. SEC access guidance was verified separately through the web tool. See [source verification](source_verification.md).

