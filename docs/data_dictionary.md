# Data dictionary

Every input below is synthetic. Source: `python/am_toolkit/synthetic.py`, seed 73421. Types and units are explicit; return and weight fractions are not percentage points.

| File | Key and grain | Fields and units |
| :--- | :--- | :--- |
| `manager_returns.csv` | `(fund, date)`, month-end, 108 rows | `return`: monthly net fraction; `benchmark`: monthly fraction |
| `manager_profiles.json` | fund, three profiles | Fee in annual bps; policy/current style weights in fractions; operations/team scores 1-5; fictional evidence text |
| `bonds.csv` | `(date, security)`, 444 rows | `asset`, `rating`, `currency`; `maturity` and `duration` in years; `amount` in currency units, USD for eligible bonds; `yield` annual fraction; `return` monthly synthetic total-return fraction |
| `tax_lots.csv` | lot, four rows | `security`, ISO acquisition date; fractional quantity; cost per unit in USD |
| `portfolio.json` | scenario | USD prices, identity groups, tax target weights, separate SMA model weights, opening cash, purchase/loss events, replacement map and model date |
| `clients.json` | client, three profiles | Opening date, USD cash, forbidden securities, lot scale, custodian alias and five boolean process checks |
| `daily_aum.csv` | `(client, date)`, 169 rows | Calendar-day USD AUM, including held account; billing selects 92 and 47 active observations for eligible accounts |
| `nport_style.xml` | investment record, two rows | Artificial namespace/CUSIPs; `balance` units; `valUSD` USD; `pctVal` percentage points; asset-category fixture |
| `manifest.json` | snapshot | Seed, model date, generator, author, synthetic label and per-file SHA-256 hashes |

Output conventions: tax `cash_flow` is positive for sales and negative for purchases; `realized_gain` is signed; `realized_loss` is a positive loss amount. Instructions are simulated and pending review. Index weights at `decision_date` earn returns at `return_date`. Monthly output `duration` uses opening weights and opening attributes. Turnover is one-way. Billing `active_days` includes both endpoints. Empty closure dates mean active. `run_manifest.json` hashes analytical outputs and the snapshot manifest; Excel verification is a separate artifact.

