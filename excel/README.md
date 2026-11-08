# Excel schedules

Open `asset_management_toolkit.xlsx`. All inputs are synthetic. The workbook contains live formulas and cached baseline results.

- Reconcile: live Excel totals, saved Python totals and differences. All five baseline differences are zero.
- Tax lots: proposed sales, conservative purchase-window guard, realized gains/losses and cash. Edit price, cost, requested quantity or sale date to recalculate. Python owns HIFO selection, target routing and buy locks; rerun Python for a new trade plan.
- Purchases: editable known purchases in rows 6-25. Dates are real Excel dates. Declared groups must match the tax schedule. Include known future purchases. The guard blocks a whole loss sale when a matching purchase is present.
- Billing: editable service dates and marginal tier assumptions; live average AUM, active days and fees. Daily AUM holds raw calendar-day observations.

Rebuild after running `python -m am_toolkit.run`:

```powershell
./excel/build.ps1
```

The script uses the configured local `@oai/artifact-tool` runtime, stages a dependency junction and builder under gitignored `.work/`, exports the workbook, sets author metadata and inspects saved OOXML. No package install or network call occurs. Remove `.work/` after reviewing its PNG previews; remove the junction itself without recursively following its dependency target.

Automated spreadsheet checks change a sale price, shorten the purchase window and raise a billing rate, then restore baseline inputs. Python checks cached totals independently. Five rendered sheets were visually reviewed. Native Microsoft Excel recalculation remains untested. `examples/output/excel_verification.json` records these limits. The workbook does not optimize trades or update the static Python baseline when edited.

