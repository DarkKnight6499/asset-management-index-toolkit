# Source verification

Retrieval date for all entries: **2026-11-08**. Sources were opened with the web tool. No public observations were downloaded into the analytical snapshot. Rule text is not treated as market data.

| Source and URL | Document and section | Verified use | Status |
| :--- | :--- | :--- | :--- |
| [IRS](https://www.irs.gov/publications/p550) | Publication 550 (2025), Chapter 4, Wash Sales; Substantially identical; More or less stock bought than sold | Loss-sale rules cover acquisitions of substantially identical securities within 30 days before or after the sale. Guidance includes specified related and retirement-account purchases. Partial quantities require matching. | Verified from the opened IRS text, lines 5731-5783. |
| [SEC](https://www.sec.gov/files/formn-port.pdf) | Form N-PORT reference copy, effective December 11, 2023, Part C, Items C.1, C.2 and C.4 | Investment identification, balance/units, currency, USD value, percentage of net assets, asset and issuer categories. | Verified from the opened form item blocks. No filing-timing claim is made. |
| [SEC](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) | Accessing EDGAR Data, Fair access | Maximum stated rate is 10 requests per second; requests should declare a user agent. | Verified from the opened SEC page, lines 26-41. Fetch script waits 0.5 seconds and sends one request, apart from any allowed redirect. |

## Model interpretation

The tax planner prevents a whole proposed loss sale if any supplied matching purchase falls within the inclusive window. It also prevents modeled purchases during a loss-sale lock. This is a conservative implementation policy, not the IRS partial-share allocation procedure. Security groups are supplied assumptions. The project does not adjudicate substantial identity or calculate basis adjustments.

The N-PORT parser reads a deliberately narrow XML subset. The form verifies the meaning of the reported fields, not XML schema conformance. The synthetic namespace and identifiers are artificial. SEC XSD conformance, derivatives, filing deadlines and the current status of every form amendment were not verified and are not implemented.

## Public-data fetch status

No real filing download was attempted from the offline shell. The optional fetch script is written for a later connected run. Authentication, SEC bot controls and real-file compatibility remain untested. The synthetic parser test does not validate a real filing.

## Project choices, not external rules

Index maturity limits of 1-10 years, USD denomination, a $300 million minimum amount, the AAA/AA/A/BBB rating allowlist, 60/40 allocation and 5 bps cost per one-way turnover are project assumptions. Manager score thresholds, operations veto, 30-day trade-prevention policy, cash reserve, fees, billing tiers and fund concept terms are hypothetical policies. No regulatory or accounting requirement is asserted for those choices.

No accounting recognition or valuation hierarchy rule is implemented. No unverified legal or accounting threshold is used as a confirmed requirement.

## Source outcomes and learned facts

Worked: IRS HTML, SEC reference-form PDF and SEC EDGAR access HTML. Failed: none of these three web opens. Not run: real filing network fetch. The SEC form fields distinguish USD value from percentage of net assets; `pctVal` is therefore treated as percentage points in the synthetic fixture. XML tag spellings remain a parser assumption pending real-file testing. Unknown or unsupported input is not presented as a fully parsed filing.

