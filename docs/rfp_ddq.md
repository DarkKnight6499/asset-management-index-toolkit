# Institutional RFP/DDQ answer bank

Answers describe this project's implemented prototype or explicitly proposed design. All profiles, control records, accounts and performance data are synthetic. No operating organization or service-provider appointment is represented.

## 1. What is the investment objective?

The mock mandate targets core USD fixed-income income with controlled rate and credit exposure over a three-year evaluation horizon. There is no return guarantee. Evidence: [IPS](fund_concept.md), Mandate.

## 2. What vehicle and liquidity terms are proposed?

A hypothetical pooled contractual vehicle would use daily indicative NAV and monthly dealing. No entity, governing agreement or dealing operation exists. Evidence: [proposed structure](fund_concept.md).

## 3. What determines security eligibility?

The research policy uses USD Treasury/corporate instruments, 1-10 years of remaining maturity and at least $300 million outstanding. Corporate labels must be AAA, AA, A or BBB. These thresholds are project assumptions. Evidence: [methodology](methodology.md), Bond index; `python/am_toolkit/index.py`.

## 4. How are allocations and weights set?

The index allocates 60% to Treasuries and 40% to corporates, with amount-outstanding weights within each sleeve. Constituent weights are exported for every return period. Evidence: [constituents](../examples/output/index_constituents.csv).

## 5. How do you avoid using future returns to select holdings?

Each month earns returns using the preceding month's selected weights. A downgrade affects the following holding period after earning the exit-month return. A hand-computed test covers this timing. Evidence: `python/tests/test_tax_sma_index.py`, `test_lagged_returns_and_downgrade`.

## 6. What is the benchmark?

The internal comparator rebalances 50/50 Treasury/corporate sleeves monthly, equal-weighting eligible bonds within sleeves. It uses the same cost convention and is not a licensed external index. Evidence: [monthly results](../examples/output/index_monthly.csv), [methodology](methodology.md).

## 7. What performance evidence is available?

There are 36 synthetic monthly index returns and three synthetic manager histories. The outputs include compounded returns, volatility, drawdown and tracking error. No actual investment performance exists. Evidence: [index summary](../examples/output/index_summary.json), [manager scores](../examples/output/manager_scorecard.csv).

## 8. What costs are included in returns?

Index net returns deduct 5 bps times one-way rebalance turnover from ending wealth. They exclude management fees and taxes. Manager observations deduct each profile's fee monthly. Evidence: [methodology](methodology.md), Manager due diligence and Bond index.

## 9. How are interest-rate and credit risks measured?

The prototype reports opening weighted duration, monthly volatility, drawdown and tracking error. Synthetic returns use rate and spread shocks. It does not model default recovery or a full yield curve. Evidence: [monthly output](../examples/output/index_monthly.csv), [limits](limitations.md).

## 10. What happens when market data is missing?

The index fails if a held bond lacks its next-period return, if bond-month keys duplicate, or if an eligible sleeve is empty. Missing observations are not silently removed. Evidence: `python/am_toolkit/index.py` and associated missing-return tests.

## 11. How are managers assessed?

Six weighted dimensions cover performance consistency, volatility, fees, style drift, operations and team continuity. The full rubric and thresholds are documented. Evidence: [score methodology](methodology.md), [scorecard](../examples/output/manager_scorecard.csv).

## 12. Which managers pass the current review?

Harbor Core is approved at 91/100, Summit Credit is on watch at 59/100, and Orchard Flexible is declined at 50/100. These are fictional cases. Evidence: [three written recommendations](../examples/output/manager_recommendations.md).

## 13. What can override an attractive performance record?

An operations score of 2 or below produces decline. A team score of 2 or below prevents approval. Orchard triggers the operations veto; Summit's succession weakness supports watch. Evidence: [profile evidence](../data/synthetic/manager_profiles.json), [recommendations](../examples/output/manager_recommendations.md).

## 14. How is style drift identified?

Half the absolute distance between current and policy allocation weights measures drift. The model reads declared weights, not inferred factor exposures. The holdings-parser demonstration is separate. Evidence: `research.py`, `manager_profiles.json` and [methodology](methodology.md).

## 15. Who confirms manager operational controls?

No external party confirms them. Synthetic profiles declare passed controls and continuity evidence; independent confirmations would be required for a real review. Evidence: [profile file](../data/synthetic/manager_profiles.json), [limitations](limitations.md).

## 16. How is holdings transparency supported?

A narrow XML parser extracts issuer, identifier, balance, currency, USD value and percentage from N-PORT-style records. It ships with two synthetic holdings, not a real filing. Evidence: [parsed holdings](../examples/output/parsed_holdings.csv), [fetch instructions](fetching_public_filings.md).

## 17. Can real filings be fetched during analysis?

No. The analytical package has no network component. An optional standalone script saves a selected SEC XML document and provenance manifest to a separate public-data folder. The live fetch remains untested. Evidence: `scripts/fetch_nport.py`, [verification](source_verification.md).

## 18. How are tax-loss opportunities selected?

The tax planner routes an eligible loss sleeve to a declared alternative, then sells overweight lots in highest-unit-cost order. The snapshot realizes $2,000 of losses and $100 of gains. No tax saving is estimated. Evidence: [tax plan](../examples/output/tax_plan.json), [trade file](../examples/output/tax_trades.csv).

## 19. How does the wash-sale guard work?

The planner blocks an entire proposed loss sale when the supplied purchase ledger has a declared matching group within the inclusive 30-day window. It blocks modeled buys during an active loss lock. Partial-share adjudication is absent. Evidence: [verified context](source_verification.md), `test_prior_and_future_day_30_block_all` and `test_buy_lock_after_loss_sale`.

## 20. What tax information must the client supply?

The scenario requires complete relevant purchase history, known future purchases, prior loss locks and reviewed identity groups. The model does not discover household or external transactions. Unknown future trades remain a risk. Evidence: [tax methodology](methodology.md), [portfolio inputs](../data/synthetic/portfolio.json).

## 21. What prevents trading before account setup is complete?

Five process checks gate every simulated account: identity, agreement, tax form, custody and restriction approval. SMA-003 is held and receives no instructions or invoice. Evidence: [workflow output](../examples/output/sma_workflows.json).

## 22. How are client restrictions applied?

Forbidden model securities are removed and remaining weights renormalized to 98%, preserving a 2% cash target. Existing restricted positions are proposed for sale. A blocked liquidation produces an exception. Evidence: `python/am_toolkit/sma.py`, [custodian instructions](../examples/output/custodian_trade_instructions.csv).

## 23. How are cash and custodian instructions controlled?

Exports contain proposed trade cash flows and a retain-cash instruction with a pending-review status. No order, wire or debit is sent. Position value plus cash is conserved by the tax engine. Evidence: [cash instructions](../examples/output/custodian_cash_instructions.csv), `test_loss_and_cash_conservation`.

## 24. How are advisory fees calculated and checked?

Average active-day AUM feeds marginal annual tiers of 50, 35 and 25 bps, then inclusive service days/365 and invoice-level rounding. The mock total is $4,216.46. Excel recomputes averages, tiers and fees from raw daily AUM. Evidence: [billing CSV](../examples/output/billing.csv), [Excel workbook](../excel/asset_management_toolkit.xlsx).

## 25. What reporting, reproducibility and independent assurance are available?

The project provides a generated quarterly letter, seeded snapshots, hashes, unit tests and Excel tie-outs. These checks provide internal consistency only. There is no audit, real-world validation, real-data backtest or native Excel engine verification. Evidence: [quarterly review](../examples/output/quarterly_review.md), [verification report](../examples/output/excel_verification.json), [limitations](limitations.md).

