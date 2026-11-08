# Methodology

## Synthetic design

Seed 73421 creates 108 monthly manager observations, 444 bond observations across 37 dates, a four-lot portfolio, three client profiles and calendar-day AUM. Dates run from the September 2022 opening bond snapshot through September 2025. The 36 return periods begin October 2022. Prescribed operational scenarios are deterministic fixtures in the same generator. Every snapshot file has a SHA-256 entry in `data/synthetic/manifest.json`.

The simulated managers hold stylized Treasury/credit allocations. Each net monthly manager return combines a common benchmark, prescribed alpha, idiosyncratic noise and the stated annual fee divided by 12. These are scenario mechanics, not an estimated return model. Style weights and controls are synthetic declarations, separate from the two-record holdings parser demonstration.

## Manager due diligence

Six scores use a 1-5 scale. Weighted total equals 20 times the sum of score times weight.

| Dimension | Weight | Rule |
| :--- | ---: | :--- |
| Performance consistency | 25% | Fraction of rolling 12-month compounded returns beating the benchmark; add one point at each of 25%, 40%, 55%, 70%, starting at 1 |
| Risk | 20% | Annualized sample volatility of monthly net returns; start at 5 and subtract one above each of 2%, 4%, 6%, 8% |
| Fees | 15% | Annual bps; start at 5 and subtract one above each of 15, 30, 45, 65 |
| Style drift | 15% | Half the sum of absolute allocation differences from policy; start at 5 and subtract one above 2.5%, 5%, 10%, 20% |
| Operations | 15% | One point per passed synthetic control: custody, daily reconciliation, recovery test, dual trade approval, access review |
| Team | 10% | 5: full succession and tested backup; 4: documented deputy; 3: partial backup; 2: lead dependence without successor; 1: no continuity evidence |

Approve at 75 or above, watch at 55 or above, otherwise decline. Operations of 2 or below vetoes approval and produces decline. Team of 2 or below caps the decision at watch. The metrics also report compounded return and maximum drawdown, including the initial wealth level of 1. There is no risk-adjusted alpha inference. Overlapping windows do not provide independent observations.

## Holdings parser

Parse `invstOrSec` children by local XML tag name, accepting any namespace. Read issuer, identifier, balance, currency, USD value, percentage and asset category. Require finite numeric fields. No identifier is fabricated if CUSIP is absent. Optional net assets provide value-based weights; otherwise divide reported percentages by 100. Weights need not sum to one for an arbitrary filing because cash, liabilities and unsupported records may differ. The shipped two-record fixture sums to one and reconciles to $1 million.

Reject entity declarations, oversized XML, missing required fields and empty supported holdings. There is no complete SEC taxonomy, XSD validation, derivative look-through or duplicate-security aggregation. Raw values are retained, including signed holdings.

## Tax lots

Mark current lots at supplied prices. Portfolio value includes opening cash. Replace a target security with its declared alternative when an eligible loss lot exceeds the $100 harvesting threshold and no supplied matching purchase blocks the harvest. Replacement groups must differ. Routing transfers the original security's entire target weight, which can also sell appreciated lots. This is deliberately simple; the example realizes a $2,000 loss and a $100 gain.

Sell overweight securities in descending unit-cost order, with lot ID breaking ties. A supplied matching purchase in the inclusive 30-day window prevents the entire loss-sale instruction. A blocked lot does not consume the required sell amount, so the planner can try another lot. A successful loss sale creates a buy lock through day 30. The caller must retain returned loss locks for later runs and provide a complete purchase ledger, including known future acquisitions and relevant household accounts. Unknown future transactions are outside the model.

Then buy underweight securities alphabetically, subject to available cash and locks. Fractional units are allowed. Return blocked attempts, proposed trades, remaining lots, cash, effective weights and absolute drift. No commissions, settlement timing, interest, tax rate, gain budget, partial wash-share matching, basis adjustment or holding-period classification is modeled. Tax-law context is in [source verification](source_verification.md).

## SMA operations and billing

All five onboarding checks must pass before trading: identity, agreement, tax form, custody and approved restrictions. These are simulated process gates, not a regulatory checklist. Remove forbidden securities from the target and renormalize allowed weights to 98%, leaving a 2% cash target. Attempt to liquidate existing restricted positions. A tax guard can prevent that sale; report an exception rather than silently treating the account as compliant. If every model security is forbidden, the target is all cash.

Custodian files are proposed trade instructions and a retain-cash instruction, each pending review. Cash flow equals sales proceeds less purchases, with no external transfer, broker routing or settlement operation. Billing excludes onboarding-held accounts. SMA-001 has a full quarter; SMA-002 opens August 15; SMA-003 is held.

Use average daily AUM over active calendar days, with complete one-row-per-day coverage. The daily AUM scenario is independently generated around each account's opening portfolio value; it is not a ledger derived from the proposed September trades. Apply marginal annual fees of 0.50% on the first $1 million, 0.35% from $1 million to $5 million and 0.25% above $5 million. Multiply annual fees by inclusive active days divided by 365. Bill in arrears, round each invoice to cents using half-up rounding, then sum invoices. No minimum fee, taxes, cash exclusion, rebates or flow adjustment is included. These are hypothetical contract terms.

## Bond index

At each month-end, include USD Treasury and corporate bonds with 1-10 years of remaining maturity and at least $300 million outstanding. Corporate ratings must be in the exact AAA/AA/A/BBB allowlist. There are no plus/minus modifiers. Allocate 60% to Treasuries and 40% to corporates, proportional to amount outstanding within each sleeve. Issuers are unique synthetic securities; no corporate issuer cap is coded. Fail if an eligible sleeve is empty.

Weights selected at month-end t earn the supplied total return at t+1. Rating exits therefore earn their exit-month return before removal. The fixture includes a credit downgrade, a size-based entry and maturity exits. It retains returns for every held security; a missing held return fails rather than disappearing. The generator uses annual yield/12 minus duration times synthetic rate and spread changes plus noise. Coupons and reinvestment are implicit in that approximation, not an explicit cash-flow engine.

After earning returns, drift weights by each security's return. One-way turnover equals half the sum of absolute differences between drifted and new target weights. Deduct 5 bps times this turnover from end-of-month wealth: net return equals `(1 + gross return) * (1 - turnover * 0.0005) - 1`. The initial allocation is free; every subsequent scheduled rebalance, including the final month-end, incurs the modeled cost. This cost convention is per one-way turnover, not per traded notional on each side.

Benchmark: monthly rebalanced 50/50 Treasury/corporate sleeves, equal weight within the same eligible universe, with the same cost rule. It is a simple internal comparator, not a licensed index. Start both levels at 100. Report compounded and annualized returns, sample annualized volatility, tracking error, drawdown and turnover. Index returns exclude management fees and taxes.

## Excel reconciliation

Tax formulas independently gate supplied sale attempts using `SUMIFS` on the purchase ledger, then calculate quantities, proceeds, basis and losses. Planned buys are inputs to the cash schedule. Python retains target optimization, HIFO ordering and buy-lock decisions. Billing formulas independently average raw daily AUM, calculate active dates, apply tiers and prorate fees. The Reconcile sheet reads these calculations and compares five totals with saved Python outputs.

The spreadsheet engine checks price, wash-window and fee-rate input changes. Saved OOXML caches are separately checked. Author metadata is explicitly set to Yazad Madan. Five sheets were visually reviewed. Microsoft Excel itself was not used for recalculation; that remains an unverified engine check. A scenario edit changes reconciliation differences until the Python baseline is regenerated.

