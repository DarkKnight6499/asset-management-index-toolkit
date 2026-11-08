"""Regenerate analytical outputs using only the shipped local snapshot."""

from datetime import date
import math

from .config import (ACQUIRED, AS_OF, CLIENT, COST, DATA, DATE, FUND, LOT, OUTPUT,
                     QUANTITY, QUARTER_END, QUARTER_START, SECURITY)
from .holdings import parse_holdings
from .index import backtest
from .config import SNAPSHOT_FILES, OUTPUT_FILES
from .io import read_csv, read_json, sha256, write_csv, write_json
from .research import compound, score_manager
from .sma import billing, simulate_account
from .tax import Event, Lot, plan_rebalance

# Configuration
AUTHOR = "Yazad Madan"
AUM_COLUMN = "aum"
REVIEW_TITLE = "Quarterly portfolio review"
NPORT_NET_ASSETS = 1_000_000


def verify_snapshot():
    manifest = read_json(SNAPSHOT_FILES["manifest"])
    if manifest["kind"] != "synthetic":
        raise ValueError("Expected the synthetic snapshot")
    for filename, expected in manifest["files"].items():
        if sha256(DATA / filename) != expected:
            raise ValueError("Snapshot hash mismatch: " + filename)
    return manifest


def load_lots(rows):
    return [Lot(row[LOT], row[SECURITY], row[ACQUIRED], float(row[QUANTITY]), float(row[COST])) for row in rows]


def active_average(rows, account, start, end):
    first = max(start, account["opened"])
    last = min(end, account.get("closed") or end)
    selected = [row for row in rows if row[CLIENT] == account[CLIENT] and first <= row[DATE] <= last]
    expected = max(0, (date.fromisoformat(last)-date.fromisoformat(first)).days+1)
    if len(selected) != expected or len({row[DATE] for row in selected}) != expected:
        raise ValueError("Daily AUM coverage mismatch")
    values = [float(row[AUM_COLUMN]) for row in selected]
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Invalid daily AUM")
    return sum(values)/len(values) if values else 0


def manager_memo(profiles, scores):
    text = ["# Manager due-diligence recommendations", "", "All profiles, evidence and returns are synthetic. Scores are policy judgments, not probabilities.", ""]
    for profile, score in zip(profiles, scores):
        text.extend([f"## {score[FUND]}: {score['recommendation']}", "",
                     f"Weighted score: {score['total_score']:.1f}/100. Rolling 12-month benchmark win rate: {score['rolling_win_rate']:.1%}. Annualized net-return volatility: {score['volatility']:.2%}. Maximum drawdown: {score['max_drawdown']:.2%}. Fee: {score['fee_bps']} bps annually. Style distance: {score['style_drift']:.1%}.", "",
                     profile["operations_evidence"], "", profile["team_evidence"], ""])
        if score["recommendation"] == "Approve":
            text.extend(["Recommendation: include in the mock approved list. Review control evidence and style weights quarterly; remove approval if the operations score falls to 2.", ""])
        elif score["recommendation"] == "Watch":
            text.extend(["Recommendation: defer allocation. Require a named successor, an execution backup and a return to policy style weights before reconsideration.", ""])
        else:
            text.extend(["Recommendation: decline allocation. Operations controls fail the veto threshold. Require documented remediation and a fresh score before reconsideration.", ""])
    return "\n".join(text)


def quarterly_letter(records, summary, scores, tax, simulations, invoices):
    quarter = [row for row in records if QUARTER_START <= row[DATE] <= QUARTER_END]
    net = compound([row["net_return"] for row in quarter])
    benchmark = compound([row["benchmark_return"] for row in quarter])
    gross = compound([row["gross_return"] for row in quarter])
    turnover = sum(row["turnover"] for row in quarter)
    held = sum(result["status"] == "HOLD" for result in simulations)
    lines = [f"# {REVIEW_TITLE}", "", f"Quarter ended {AS_OF}", "", "Dear investors,", "",
             f"The synthetic index portfolio returned {net:.2%} after modeled trading costs this quarter, compared with {benchmark:.2%} for the 50/50 Treasury and corporate benchmark. Active return was {(net-benchmark)*100:.2f} percentage points. Gross return was {gross:.2%}. These results exclude management fees and taxes. They are simulated results, with no real capital or market validation.", "",
             f"Quarterly one-way turnover totaled {turnover:.2%}. Duration entering the final month was {quarter[-1]['duration']:.2f} years. Since inception, maximum monthly drawdown was {summary['max_drawdown']:.2%}. Interest-rate exposure and corporate spread exposure remain the principal modeled risks. The prototype does not capture default recovery or trading liquidity.", "",
             f"The separate tax-lot model realized ${tax['realized_loss']:,.2f} of losses and a net realized {'loss' if tax['realized_gain'] < 0 else 'gain'} of ${abs(tax['realized_gain']):,.2f}. Ending cash was ${tax['cash']:,.2f}. A declared replacement strategy changed the effective target allocation. Group mappings are assumptions. The 30-day guard blocked {len(tax['blocked'])} instructions; future unknown trades can still invalidate an intended harvest. No tax saving is estimated.", "",
             f"The SMA simulation held {held} of {len(simulations)} accounts for incomplete onboarding. Proposed instructions remain subject to review. Active-account billing totaled ${sum(row['fee'] for row in invoices):,.2f} under the hypothetical tier schedule. These separate account examples are not aggregated into index returns.", "",
             "Manager review decisions: " + "; ".join(f"{row[FUND]}: {row['recommendation'].lower()} ({row['total_score']:.0f}/100)" for row in scores) + ".", "",
             "Next quarter, monitor rating exits, maturity eligibility, account restrictions and purchase-ledger coverage before releasing trades. No forecast or distribution commitment is made.", "", "Portfolio Review Committee", ""]
    return "\n".join(lines)


def run():
    manifest = verify_snapshot()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    profiles = read_json(SNAPSHOT_FILES["manager_profiles"])
    scores = [score_manager(profile, read_csv(SNAPSHOT_FILES["manager_returns"])) for profile in profiles]
    write_csv(OUTPUT_FILES["manager_scorecard"], scores)
    (OUTPUT_FILES["manager_recommendations"]).write_text(manager_memo(profiles, scores), encoding="utf-8")
    write_csv(OUTPUT_FILES["parsed_holdings"], parse_holdings(SNAPSHOT_FILES["nport_style"], NPORT_NET_ASSETS))
    portfolio = read_json(SNAPSHOT_FILES["portfolio"])
    lots = load_lots(read_csv(SNAPSHOT_FILES["tax_lots"]))
    purchases = [Event(**event) for event in portfolio["purchases"]]
    losses = [Event(**event) for event in portfolio["loss_sales"]]
    tax = plan_rebalance(lots, portfolio["prices"], portfolio["targets"], portfolio["cash"], AS_OF,
                         portfolio["groups"], purchases, losses, portfolio["harvest_replacements"])
    write_json(OUTPUT_FILES["tax_plan"], tax)
    write_csv(OUTPUT_FILES["tax_trades"], tax["trades"])
    write_csv(OUTPUT_FILES["tax_lot_attempts"], tax["attempts"])
    simulations, invoices = [], []
    daily_aum = read_csv(SNAPSHOT_FILES["daily_aum"])
    for account in read_json(SNAPSHOT_FILES["clients"]):
        scaled_lots = [Lot(lot.lot, lot.security, lot.acquired, lot.quantity*account["scale"], lot.cost) for lot in lots]
        simulation = simulate_account(account, scaled_lots, portfolio["prices"], portfolio["sma_model"], AS_OF,
                                      portfolio["groups"], purchases, losses)
        simulations.append(simulation)
        if simulation["status"] != "HOLD":
            average_aum = active_average(daily_aum, account, QUARTER_START, QUARTER_END)
            invoices.append(billing(account[CLIENT], average_aum, QUARTER_START, QUARTER_END,
                                    account["opened"], account.get("closed")))
    write_json(OUTPUT_FILES["sma_workflows"], simulations)
    write_csv(OUTPUT_FILES["custodian_trade_instructions"], [instruction for simulation in simulations for instruction in simulation["instructions"]])
    write_csv(OUTPUT_FILES["custodian_cash_instructions"], [{CLIENT: simulation[CLIENT], **simulation["external_cash_instruction"]}
                                                         for simulation in simulations if simulation["external_cash_instruction"]])
    write_csv(OUTPUT_FILES["billing"], invoices)
    records, constituents, summary = backtest(read_csv(SNAPSHOT_FILES["bonds"]))
    write_csv(OUTPUT_FILES["index_monthly"], records)
    write_csv(OUTPUT_FILES["index_constituents"], constituents)
    write_json(OUTPUT_FILES["index_summary"], summary)
    (OUTPUT_FILES["quarterly_review"]).write_text(quarterly_letter(records, summary, scores, tax, simulations, invoices), encoding="utf-8")
    write_json(OUTPUT_FILES["workbook_inputs"], {"author": AUTHOR, "as_of": AS_OF,
               "quarter_start": QUARTER_START, "quarter_end": QUARTER_END,
               "portfolio": portfolio, "tax": tax, "billing": invoices, "daily_aum": daily_aum})
    write_json(OUTPUT_FILES["run_manifest"], {"author": AUTHOR, "kind": "synthetic_outputs", "seed": manifest["seed"],
               "as_of": AS_OF, "snapshot_manifest_sha256": sha256(SNAPSHOT_FILES["manifest"]),
               "outputs": {path.name: sha256(path) for path in sorted(OUTPUT.iterdir()) if path.name != "run_manifest.json"}})
    print(f"Generated offline outputs: {OUTPUT}")
    print(f"Tax loss: {tax['realized_loss']:.2f}; invoices: {sum(row['fee'] for row in invoices):.2f}; index months: {summary['months']}")


if __name__ == "__main__":
    run()

