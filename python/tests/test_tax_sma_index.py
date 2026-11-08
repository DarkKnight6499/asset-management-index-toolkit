import unittest

from am_toolkit.config import AMOUNT, ASSET, CURRENCY, DATE, DURATION, MATURITY, RATING, RETURN, SECURITY
from am_toolkit.index import backtest, eligible, one_way_turnover, weights
from am_toolkit.sma import billing, simulate_account
from am_toolkit.tax import Event, Lot, buy_locked, plan_rebalance, within_window

# Configuration
AS_OF = "2025-09-30"
GROUPS = {"A": "same", "B": "other", "A2": "same"}
PRICES = {"A": 8, "B": 10, "A2": 8}
LOTS = [Lot("old", "A", "2024-01-01", 100, 10)]
BOND = {ASSET: "Treasury", RATING: "AAA", CURRENCY: "USD", MATURITY: 5, AMOUNT: 300_000_000, DURATION: 4, RETURN: 0}


class TaxTests(unittest.TestCase):
    def test_loss_and_cash_conservation(self):
        result = plan_rebalance(LOTS, PRICES, {"B": 1}, 0, AS_OF, GROUPS)
        self.assertEqual(result["realized_loss"], 200)
        self.assertEqual(result["cash"], 0)
        self.assertEqual(result["lots"][0]["quantity"], 80)

    def test_prior_and_future_day_30_block_all(self):
        for event_date in ("2025-08-31", "2025-10-30"):
            result = plan_rebalance(LOTS, PRICES, {"B": 1}, 0, AS_OF, GROUPS, [Event(event_date, "A2", 1)])
            self.assertEqual(result["realized_loss"], 0)
            self.assertEqual(result["attempts"][0]["executed_qty"], 0)

    def test_day_31_not_blocked(self):
        for event_date in ("2025-08-30", "2025-10-31"):
            result = plan_rebalance(LOTS, PRICES, {"B": 1}, 0, AS_OF, GROUPS, [Event(event_date, "A", 1)])
            self.assertEqual(result["realized_loss"], 200)

    def test_buy_lock_after_loss_sale(self):
        result = plan_rebalance(LOTS, PRICES, {"A2": 1}, 0, AS_OF, GROUPS)
        self.assertEqual(result["cash"], 800)
        self.assertEqual(result["blocked"][0]["action"], "BUY")
        self.assertTrue(buy_locked("A2", "2025-10-30", [Event(AS_OF, "A", 100)], GROUPS))
        self.assertFalse(buy_locked("A2", "2025-10-31", [Event(AS_OF, "A", 100)], GROUPS))

    def test_partial_sale_and_hifo(self):
        lots = LOTS + [Lot("low", "A", "2024-02-01", 100, 7)]
        result = plan_rebalance(lots, PRICES, {"A": .75, "B": .25}, 0, AS_OF, GROUPS)
        self.assertEqual(result["attempts"][0]["lot"], "old")
        self.assertEqual(result["attempts"][0]["executed_qty"], 50)
        self.assertEqual(result["realized_gain"], -100)

    def test_harvest_substitution(self):
        result = plan_rebalance(LOTS, PRICES, {"A": 1}, 0, AS_OF, GROUPS, harvest_replacements={"A": "B"})
        self.assertEqual(result["effective_targets"], {"A": 0, "B": 1})
        self.assertEqual(result["realized_loss"], 200)

    def test_invalid_inputs(self):
        for arguments in ((LOTS, PRICES, {"B": 1.1}, 0), (LOTS+LOTS, PRICES, {"B": 1}, 0),
                          (LOTS, {"A": 0}, {"A": 1}, 0)):
            with self.assertRaises(ValueError):
                plan_rebalance(*arguments, AS_OF, GROUPS)


class SmaTests(unittest.TestCase):
    def test_tier_fees_and_inclusive_days(self):
        result = billing("A", 2_000_000, "2025-07-01", AS_OF, "2025-08-15")
        self.assertEqual(result["annual_fee"], 8500)
        self.assertEqual(result["active_days"], 47)
        self.assertEqual(result["fee"], 1094.52)

    def test_three_tiers_and_no_active_days(self):
        result = billing("A", 6_000_000, "2025-07-01", AS_OF, "2025-07-01")
        self.assertEqual(result["annual_fee"], 21500)
        self.assertEqual(result["fee"], 5419.18)
        self.assertEqual(billing("A", 1, "2025-07-01", AS_OF, "2025-10-01")["fee"], 0)
        self.assertEqual(billing("A", 1_000_000, "2025-07-01", AS_OF, "2025-07-01", "2025-07-01")["fee"], 13.70)

    def test_onboarding_hold(self):
        result = simulate_account({"client": "A", "checks": {}}, LOTS, PRICES, {"A": 1}, AS_OF, GROUPS)
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["instructions"])

    def test_restriction_liquidation_and_cash_reserve(self):
        account = {"client": "A", "checks": dict.fromkeys(("identity", "agreement", "tax_form", "custody", "restrictions_approved"), True),
                   "forbidden": ["A"], "custodian": "C", "cash": 0}
        result = simulate_account(account, LOTS, PRICES, {"A": .6, "B": .4}, AS_OF, GROUPS)
        self.assertEqual(result["status"], "READY_FOR_REVIEW")
        self.assertAlmostEqual(result["external_cash_instruction"]["amount"], 16)
        self.assertTrue(all(lot["security"] != "A" for lot in result["result"]["lots"]))

    def test_restricted_sale_tax_exception(self):
        account = {"client": "A", "checks": dict.fromkeys(("identity", "agreement", "tax_form", "custody", "restrictions_approved"), True),
                   "forbidden": ["A"], "custodian": "C", "cash": 0}
        result = simulate_account(account, LOTS, PRICES, {"A": .6, "B": .4}, AS_OF, GROUPS,
                                  [Event("2025-09-10", "A2", 1)])
        self.assertEqual(result["status"], "EXCEPTION")
        self.assertEqual(result["restricted_positions_remaining"], ["A"])

    def test_all_model_securities_forbidden(self):
        account = {"client": "A", "checks": dict.fromkeys(("identity", "agreement", "tax_form", "custody", "restrictions_approved"), True),
                   "forbidden": ["A", "B"], "custodian": "C", "cash": 0}
        result = simulate_account(account, LOTS, PRICES, {"A": .6, "B": .4}, AS_OF, GROUPS)
        self.assertEqual(result["external_cash_instruction"]["amount"], 800)
        self.assertFalse(result["result"]["lots"])


class IndexTests(unittest.TestCase):
    def test_eligibility_boundaries(self):
        self.assertTrue(eligible(BOND))
        self.assertTrue(eligible({**BOND, MATURITY: 1}))
        for override in ({MATURITY: .99}, {MATURITY: 10.01}, {AMOUNT: 299_999_999}, {CURRENCY: "EUR"}, {ASSET: "Corporate", RATING: "BB"}):
            self.assertFalse(eligible({**BOND, **override}))

    def test_weights_and_turnover(self):
        rows = [{**BOND, SECURITY: "T"}, {**BOND, ASSET: "Corporate", SECURITY: "C"}]
        self.assertEqual(weights(rows), {"T": .6, "C": .4})
        self.assertAlmostEqual(one_way_turnover({"T": .6, "C": .4}, {"T": .5, "C": .5}), .1)

    def test_lagged_returns_and_downgrade(self):
        rows = []
        for current in ("2025-01-31", "2025-02-28", "2025-03-31"):
            rows.extend([{**BOND, SECURITY: "T", DATE: current, RETURN: .01},
                         {**BOND, SECURITY: "C", DATE: current, ASSET: "Corporate", RETURN: .02,
                          RATING: "BB" if current != "2025-01-31" else "A"},
                         {**BOND, SECURITY: "D", DATE: current, ASSET: "Corporate", RETURN: 0}])
        records, constituents, _ = backtest(rows, cost_bps=0)
        self.assertAlmostEqual(records[0]["gross_return"], .01)
        self.assertAlmostEqual(records[1]["gross_return"], .006)
        self.assertTrue(any(row[SECURITY] == "C" and row["return_date"] == "2025-02-28" for row in constituents))
        self.assertFalse(any(row[SECURITY] == "C" and row["return_date"] == "2025-03-31" for row in constituents))

    def test_transaction_cost_convention(self):
        rows = [{**BOND, SECURITY: key, ASSET: asset, DATE: current, RETURN: value}
                for current in ("2025-01-31", "2025-02-28")
                for key, asset, value in (("T", "Treasury", .10), ("C", "Corporate", 0))]
        records, _, _ = backtest(rows, 100)
        turnover = .6*1.10/1.06-.6
        self.assertAlmostEqual(records[0]["turnover"], turnover)
        self.assertAlmostEqual(records[0]["net_return"], 1.06*(1-turnover*.01)-1)

    def test_missing_return_and_duplicate_fail(self):
        rows = [{**BOND, SECURITY: key, ASSET: asset, DATE: current}
                for current in ("2025-01-31", "2025-02-28")
                for key, asset in (("T", "Treasury"), ("C", "Corporate"))]
        with self.assertRaises(ValueError):
            backtest(rows + [rows[0]])
        with self.assertRaises(ValueError):
            backtest([row for row in rows if not (row[DATE] == "2025-02-28" and row[SECURITY] == "C")])


if __name__ == "__main__":
    unittest.main()

