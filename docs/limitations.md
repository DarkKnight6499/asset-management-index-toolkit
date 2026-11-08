# Limitations

## Synthetic

All security identifiers, prices, returns, ratings, amounts, fund profiles, manager evidence, tax lots, client details, AUM and fees are fictional. The seed produces repeatable scenarios, not representative market samples. No real filing is bundled. The return simulation does not estimate a historical covariance model or support forecasting claims.

## Stylized

- Tax handling prevents trades conservatively. It does not match partial replacement shares, adjust disallowed-loss basis or prepare tax returns. Declared groups do not establish substantial identity. Known purchases must be supplied; household, retirement, spouse and controlled-entity transactions are not discovered. Future unknown trades remain a risk. Loss locks must be carried forward by the caller.
- Harvest routing moves an entire target sleeve to an assumed alternative, can realize gains and can leave cash or drift. No tax alpha is estimated. No transaction costs or settlement rules enter tax or SMA trading.
- SMA checks are demonstration gates. There is no real identity verification, client consent, custody connection, execution, settlement, wire release, billing debit or reconciliation to custodian records. Instruction exports require review. Billing uses independently simulated daily AUM and hypothetical contract terms.
- Manager scores reflect chosen thresholds and overlapping windows. Control evidence is asserted by synthetic profiles. There are no live manager interviews, administrator confirmations, audited returns or independent operational reviews.
- Bond total returns use a duration approximation. There is no explicit coupon schedule, accrued interest, clean/dirty pricing, default recovery, curve interpolation, spread curve, real bid/ask data or liquidity limit. Eligibility does not implement rating-agency conventions. The fixed synthetic universe does not test survivor bias in real datasets.
- Index weighting has no issuer cap, no liquidity optimization, no tax effects and no investment vehicle expenses. Performance is an internal simulation, not real-world validation or an investable track record.
- The fund concept's governance limits are proposed terms. They are not all enforced by the index code. No entity, legal structure, distribution regime or accounting policy has been implemented.
- Excel recalculates sale schedules and billing. It does not optimize a new portfolio, regenerate trade locks or refresh baseline controls after edits. A fixed purchase-ledger range supports rows 6-25; extend formulas before adding more purchases. The external workbook builder is required only for rebuilding Excel.

## Not verified

Real SEC filing compatibility, full N-PORT schema coverage, current filing schedules and amendment status were not verified. The optional fetch script has not run against the live SEC service. Native Microsoft Excel recalculation was not tested. No legal, tax or accounting compliance opinion, audit assurance or real-world validation is claimed. Verified primary-text uses are limited to [source verification](source_verification.md).

