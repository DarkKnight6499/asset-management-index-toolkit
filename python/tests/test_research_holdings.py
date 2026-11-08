import tempfile
import unittest
import calendar
from datetime import date
from pathlib import Path

from am_toolkit.config import BENCHMARK, DATE, FUND, RETURN, ROOT, VALUE, WEIGHT
from am_toolkit.holdings import parse_holdings
from am_toolkit.research import compound, max_drawdown, score_manager

# Configuration
PROFILE = {FUND: "Test", "fee_bps": 10, "style_current": {"treasury": .6, "credit": .4},
           "style_policy": {"treasury": .6, "credit": .4}, "operations_score": 5, "team_score": 5}
WORK = ROOT / ".work"


class ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        WORK.mkdir(exist_ok=True)

    def test_compound_and_initial_peak(self):
        self.assertAlmostEqual(compound([.1, -.1]), -.01)
        self.assertAlmostEqual(max_drawdown([-.1, .1, -.2]), -.208)

    def test_perfect_score(self):
        rows = [{FUND: "Test", DATE: date(2024, month, calendar.monthrange(2024, month)[1]).isoformat(), RETURN: .01, BENCHMARK: 0} for month in range(1, 13)]
        result = score_manager(PROFILE, rows)
        self.assertEqual(result["total_score"], 100)
        self.assertEqual(result["rolling_win_rate"], 1)
        self.assertEqual(score_manager({**PROFILE, "operations_score": 2}, rows)["recommendation"], "Decline")

    def test_xml_namespace_and_weight(self):
        xml = '<root xmlns="urn:test"><invstOrSec><name>A</name><cusip>X</cusip><balance>10</balance><valUSD>600</valUSD><pctVal>60</pctVal><curCd>USD</curCd></invstOrSec></root>'
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            path = Path(directory) / "sample.xml"
            path.write_text(xml)
            row = parse_holdings(path, 1000)[0]
            self.assertEqual(row[VALUE], 600)
            self.assertEqual(row[WEIGHT], .6)
            path.write_text(xml.replace("600", "nan"))
            with self.assertRaises(ValueError):
                parse_holdings(path)

    def test_no_holdings_fails(self):
        with tempfile.TemporaryDirectory(dir=WORK) as directory:
            path = Path(directory) / "sample.xml"
            path.write_text("<root/>")
            with self.assertRaises(ValueError):
                parse_holdings(path)


if __name__ == "__main__":
    unittest.main()

