# Six-slide pitch outline

## 1. Mandate and investor use

- Core Income Allocation: a hypothetical USD fixed-income allocation.
- Objective: income and controlled rate/credit exposure over three years.
- Principal risk remains; all evidence is synthetic.
- Visual: 60% Treasury / 40% corporate allocation.

## 2. Rules and construction

- USD, 1-10 years to maturity, at least $300 million outstanding.
- Corporate rating allowlist: AAA, AA, A, BBB.
- Amount-weight sleeves; rebalance monthly with lagged decision weights.
- Evidence: `python/am_toolkit/index.py` and `index_constituents.csv`.

## 3. Risk and governance

- Review duration, spread exposure, concentration and missing returns.
- Code fails on missing held returns or an empty sleeve.
- Proposed duration/issuer bands require oversight outside the prototype.
- Evidence: hand-computed downgrade and eligibility tests; `index_summary.json`.

## 4. Synthetic results and comparator

- Plot `index_level` and `benchmark_level` from `index_monthly.csv`.
- Present return, volatility, drawdown, tracking error and turnover together.
- Benchmark: 50/50 sleeves, equal weighting within sleeves, same modeled costs.
- Label every chart synthetic; index results exclude management fees and taxes.

## 5. Implementation and proposed terms

- Pooled concept: daily indicative NAV and monthly dealing; no actual entity.
- Planning fees: 20 bps management plus 5 bps operating expenses annually.
- SMA alternative: restrictions, conservative tax guards and reviewable instructions.
- Evidence: `fund_concept.md`, `tax_plan.json`, `sma_workflows.json` and Excel.

## 6. Diligence and open decisions

- Three manager profiles receive approve, watch and decline decisions.
- Review fictional controls, real-data parser scope and incomplete tax coverage.
- Resolve legal form, actual service providers, real-data checks and execution design before implementation.
- Evidence: `manager_recommendations.md`, `rfp_ddq.md`, `limitations.md` and `source_verification.md`.

