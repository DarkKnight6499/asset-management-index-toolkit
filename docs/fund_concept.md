# Core Income Allocation: mock fund concept and IPS

## Mandate

Provide diversified USD Treasury and investment-grade corporate exposure through a transparent monthly allocation process. The objective is income and controlled rate/credit exposure over a three-year evaluation horizon. Principal can decline. The concept makes no return, yield or capital-preservation promise.

Intended use: the core fixed-income allocation of an institutional portfolio with capacity to tolerate mark-to-market losses. Taxable clients may instead use the separate SMA implementation, subject to household tax review. The synthetic examples do not establish suitability for any investor.

## Proposed structure and terms

The concept is a hypothetical pooled contractual vehicle with unit accounting, daily indicative NAV and monthly dealing. No entity has been formed. Domicile, registration, distribution eligibility, governing documents and accounting policies require a separate legal and operational design. These proposed terms do not assert a regulatory exemption or an available legal product.

Subscriptions and redemptions would be reviewed at month-end. The operational design would separate portfolio decisions, custody, valuation and investor records. Independent service-provider appointment and tested recovery would be prerequisites to launch; none has occurred in this project. The code implements monthly index research, not unit dealing or NAV accounting.

Hypothetical annual management fee: 20 bps on NAV, plus a 5 bps illustrative operating-expense budget. No performance fee or entry/exit charge is proposed. The combined 25 bps is a planning assumption, without actual contracts or an expense cap. Index outputs exclude these charges. SMA examples use a different marginal AUM schedule documented in methodology.

## Portfolio construction

Strategic weights: 60% Treasuries, 40% corporate bonds. Within each sleeve, weight eligible securities by amount outstanding. Use USD instruments with 1-10 years remaining maturity and at least $300 million outstanding; corporate rating labels must be AAA, AA, A or BBB. These are project choices. Reconstitute and rebalance monthly using information available at the preceding decision point.

The prototype is unlevered and has no derivatives, shorts, securities lending or foreign-currency positions. It approximates bond total returns through yield carry, duration exposure and synthetic shocks. Cash flows, accrued interest and dealing liquidity require a separate production valuation engine.

## Risk and governance

Proposed monitoring bands: duration 2-7 years, corporate exposure at the 40% target, corporate issuer exposure no more than 20% of NAV, and no borrowing. Treasury issuer exposure is exempt from the proposed corporate issuer limit. Duration and issuer bands are proposed oversight controls, not coded trade constraints. A breach would suspend discretionary additions pending committee review; the prototype does not implement that approval system.

Monthly review should inspect eligibility changes, rating exits, weight concentration, turnover, missing prices and return completeness. The research code fails on missing held returns or empty sleeves. SMA restrictions can produce an exception when a tax guard prevents liquidation. These are explicit unresolved instructions, not completed compliance reviews.

## Evaluation and reporting

Evaluate net trading-cost index results against the internal 50/50 Treasury/corporate equal-weight-sleeve benchmark. Review quarterly return, active return, duration, drawdown, tracking error and turnover together. Manager selection uses the six-part scorecard and operational veto; manager allocations are not embedded in the bond-index backtest.

Deliver a quarterly review from model outputs and retain snapshot hashes. Evidence: `examples/output/index_monthly.csv`, `index_summary.json`, `manager_scorecard.csv` and `quarterly_review.md`. No live performance history, administrator confirmation or real-world validation is claimed. See [limitations](limitations.md).

