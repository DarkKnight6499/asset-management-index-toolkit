# Asset Management and Index Toolkit

An offline research and operations prototype for manager selection, tax-aware portfolios, SMA workflows and a Treasury plus corporate bond index.

**All portfolio data, fund profiles, control evidence, clients and performance observations are synthetic.** Seed: 73421. Model date: September 30, 2025. Public rule text is used only as documented in [source verification](docs/source_verification.md). No real investments, filings, clients or trading connections are included.

## Run

Python 3.12 or later, standard library only. No installation or runtime network access is required.

```powershell
$Python = 'python'
$env:PYTHONPATH = 'python'
& $Python -m unittest discover -s python/tests -v
& $Python -m am_toolkit.run
```

Use a Python executable available on the machine. The project does not import third-party Python packages.

Regenerate the snapshot explicitly with `& $Python -m am_toolkit.synthetic`. Configuration and field names live in `python/am_toolkit/config.py`; scenario inputs and generating assumptions live in the top configuration block of `synthetic.py`. Snapshot hashes are checked before analysis. Change the generator and regenerate rather than editing a hashed CSV in place.

## Contents

| Area | Implementation and evidence |
| :--- | :--- |
| Manager review | `research.py`, three profiles, `manager_scorecard.csv`, and three written recommendations |
| Holdings | `holdings.py`, synthetic XML, `parsed_holdings.csv`, and optional SEC fetch script |
| Fund concept | [IPS, structure, fees and construction](docs/fund_concept.md); [six-slide outline](docs/pitch_outline.md) |
| Institutional diligence | [25-question RFP/DDQ bank](docs/rfp_ddq.md), linked to local evidence |
| Tax lots | HIFO sale planning, harvest substitution, purchase guards, buy locks and cash conservation |
| SMA operations | Three accounts, onboarding holds, restricted models, proposed custodian instructions and tier billing |
| Index | Monthly eligibility, lagged weights, turnover, costs and a 36-month synthetic backtest |
| Investor reporting | [Generated quarterly review](examples/output/quarterly_review.md) |
| Excel | [Live tax-lot and billing workbook](excel/asset_management_toolkit.xlsx), with independent Python tie-outs |

Python code and tests are under `python/`; seeded inputs under `data/synthetic/`; generated tables and reports under `examples/output/`. Start with [methodology](docs/methodology.md), [data dictionary](docs/data_dictionary.md) and [limitations](docs/limitations.md).

## Workbook

The delivered workbook is ready to open. Reconcile compares five live formula totals with the Python baseline. Tax lots calculates sale guards, proceeds, basis, losses and cash. Billing calculates active dates, AUM averages, marginal fees and day proration from Daily AUM. Purchases provides an editable household purchase ledger.

To rebuild with the available local spreadsheet runtime, run `./excel/build.ps1` after the Python pipeline. The builder requires the external `@oai/artifact-tool` runtime at the configured path. It does not install packages or access the network. See [Excel notes](excel/README.md). Python alone can regenerate every analytical output; the workbook builder is a separate step.

## Public filing fetch

`scripts/fetch_nport.py` is the only network component. It is never imported by the analytical package. It accepts a manually selected SEC filing XML URL, writes raw XML and a manifest under gitignored `data/public/nport/`, and leaves the synthetic pipeline unchanged. Commands, failure behavior and parser scope are in [fetch instructions](docs/fetching_public_filings.md).

## Limitations

This is a stylized simulation, without real-world validation. Wash-sale prevention is conservative and incomplete; no tax-return reporting or disallowed-loss basis adjustment is implemented. Declared security groups are assumptions. Bond returns are generated approximations, without default recovery or liquidity modeling. Manager control evidence is fictional. The pooled vehicle is a concept, without a legal or accounting implementation. Native Microsoft Excel recalculation has not been tested. Full limits and unverified areas appear in [limitations](docs/limitations.md).

