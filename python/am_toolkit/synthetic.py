"""Generate the seeded offline snapshot and its provenance manifest."""

import calendar
from datetime import date, timedelta
import random

from .config import (ACQUIRED, AMOUNT, ASSET, AS_OF, BENCHMARK, CLIENT, COST, CURRENCY,
                     DATA, DATE, DURATION, FUND, LOT, MATURITY, MONTHS,
                     QUANTITY, QUARTER_START, RATING, RETURN, SECURITY, SEED, START, YIELD)
from .config import SNAPSHOT_FILES
from .io import sha256, write_csv, write_json

# Configuration
AUTHOR = "Yazad Madan"
GENERATOR_SOURCE = "python/am_toolkit/synthetic.py"
RATE_SHOCK_SD = .0018
SPREAD_SHOCK_SD = .0010
BENCHMARK_CARRY = .0030
BENCHMARK_RATE_DURATION = 4.0
BENCHMARK_SPREAD_DURATION = 1.6
MONTHS_PER_YEAR = 12
DURATION_FACTOR = .8
MIN_DURATION = .1
DOWNGRADE_SECURITY = "C3"
DOWNGRADE_MONTH = 18
DOWNGRADE_RATING = "BB"
ENTRY_SECURITY = "C6"
ENTRY_MONTH = 24
ENTRY_AMOUNT = 600_000_000
TREASURY_YIELD = .035
CREDIT_YIELD_INCREMENT = .015
BOND_NOISE_SD = .0004
AUM_DAILY_DRIFT = .00005
AUM_DAILY_NOISE_SD = .0005
FUND_SPECS = (
    {FUND: "Harbor Core", "fee_bps": 22, "alpha": .0006, "noise": .001,
     "style_policy": {"treasury": .6, "credit": .4}, "style_current": {"treasury": .58, "credit": .42},
     "operations_score": 5, "team_score": 4,
     "operations_evidence": "Synthetic checklist: independent custody, daily reconciliation, tested recovery, dual trade approval, quarterly access review.",
     "team_evidence": "Synthetic record: four staff, documented deputy, one departure in three years."},
    {FUND: "Summit Credit", "fee_bps": 48, "alpha": .0009, "noise": .007,
     "style_policy": {"treasury": .3, "credit": .7}, "style_current": {"treasury": .12, "credit": .88},
     "operations_score": 4, "team_score": 2,
     "operations_evidence": "Synthetic checklist: four of five controls; recovery exercise pending.",
     "team_evidence": "Synthetic record: lead portfolio manager controls research and execution; no designated successor."},
    {FUND: "Orchard Flexible", "fee_bps": 78, "alpha": -.0004, "noise": .011,
     "style_policy": {"treasury": .5, "credit": .5}, "style_current": {"treasury": .2, "credit": .8},
     "operations_score": 2, "team_score": 3,
     "operations_evidence": "Synthetic checklist: two of five controls; no dual trade approval, recovery test, or access review.",
     "team_evidence": "Synthetic record: three staff and partial backup coverage, two departures in three years."},
)
BOND_SPECS = (
    ("T1", "Treasury", "AAA", 4.0, 2_000_000_000, "USD"),
    ("T2", "Treasury", "AAA", 7.0, 3_000_000_000, "USD"),
    ("T3", "Treasury", "AAA", 10.0, 4_000_000_000, "USD"),
    ("T4", "Treasury", "AAA", 2.0, 1_000_000_000, "USD"),
    ("C1", "Corporate", "AA", 5.0, 800_000_000, "USD"),
    ("C2", "Corporate", "A", 8.0, 1_200_000_000, "USD"),
    ("C3", "Corporate", "BBB", 6.0, 500_000_000, "USD"),
    ("C4", "Corporate", "AAA", 9.0, 900_000_000, "USD"),
    ("C5", "Corporate", "BB", 6.0, 700_000_000, "USD"),
    ("C6", "Corporate", "A", 8.0, 200_000_000, "USD"),
    ("X1", "Corporate", "A", 5.0, 600_000_000, "EUR"),
    ("X2", "Corporate", "AA", 12.0, 600_000_000, "USD"),
)
TAX_LOTS = (
    {LOT: "L1", SECURITY: "TREA", ACQUIRED: "2023-03-01", QUANTITY: 100, COST: 105},
    {LOT: "L2", SECURITY: "TREA", ACQUIRED: "2025-09-10", QUANTITY: 10, COST: 101},
    {LOT: "L3", SECURITY: "CORP", ACQUIRED: "2023-04-01", QUANTITY: 100, COST: 110},
    {LOT: "L4", SECURITY: "CORP", ACQUIRED: "2024-04-01", QUANTITY: 20, COST: 85},
)
TAX_PRICES = {"TREA": 98.0, "CORP": 90.0, "CORP_ALT": 100.0}
GROUPS = {"TREA": "treasury_fund", "CORP": "credit_fund", "CORP_ALT": "distinct_credit_strategy"}
MODEL = {"TREA": .6, "CORP": .4}
TAX_TARGETS = {"TREA": .4, "CORP": .6}
TAX_CASH = 2000.0
PURCHASES = [{DATE: "2025-09-10", SECURITY: "TREA", QUANTITY: 10.0}]
LOSS_SALES = []
CLIENT_SPECS = (
    {CLIENT: "SMA-001", "custodian": "Custodian-A", "opened": "2025-07-01", "cash": 100_000,
     "forbidden": [], "scale": 80, "checks": {"identity": True, "agreement": True, "tax_form": True, "custody": True, "restrictions_approved": True}},
    {CLIENT: "SMA-002", "custodian": "Custodian-B", "opened": "2025-08-15", "cash": 200_000,
     "forbidden": ["CORP"], "scale": 200, "checks": {"identity": True, "agreement": True, "tax_form": True, "custody": True, "restrictions_approved": True}},
    {CLIENT: "SMA-003", "custodian": "Custodian-A", "opened": "2025-09-01", "cash": 50_000,
     "forbidden": [], "scale": 20, "checks": {"identity": True, "agreement": True, "tax_form": False, "custody": True, "restrictions_approved": False}},
)


def month_ends():
    start = date.fromisoformat(START)
    values = []
    for offset in range(MONTHS+1):
        month_number = start.year*12+start.month-1+offset
        year, month = divmod(month_number, 12)
        values.append(date(year, month+1, calendar.monthrange(year, month+1)[1]).isoformat())
    return values


def generate():
    rng = random.Random(SEED)
    DATA.mkdir(parents=True, exist_ok=True)
    dates = month_ends()
    fund_rows, bond_rows = [], []
    for number, current in enumerate(dates):
        rate_shock = rng.gauss(0, RATE_SHOCK_SD)
        spread_shock = rng.gauss(0, SPREAD_SHOCK_SD)
        benchmark = BENCHMARK_CARRY-BENCHMARK_RATE_DURATION*rate_shock-BENCHMARK_SPREAD_DURATION*spread_shock
        if number:
            for profile in FUND_SPECS:
                net_return = benchmark+profile["alpha"]+rng.gauss(0, profile["noise"])-profile["fee_bps"]/10000/MONTHS_PER_YEAR
                fund_rows.append({DATE: current, FUND: profile[FUND], RETURN: net_return, BENCHMARK: benchmark})
        for security, asset, rating, maturity, amount, currency in BOND_SPECS:
            remaining = maturity-number/MONTHS_PER_YEAR
            duration = max(MIN_DURATION, remaining*DURATION_FACTOR)
            current_rating = DOWNGRADE_RATING if security == DOWNGRADE_SECURITY and number >= DOWNGRADE_MONTH else rating
            current_amount = ENTRY_AMOUNT if security == ENTRY_SECURITY and number >= ENTRY_MONTH else amount
            annual_yield = TREASURY_YIELD + (CREDIT_YIELD_INCREMENT if asset == "Corporate" else 0)
            bond_return = annual_yield/MONTHS_PER_YEAR-duration*rate_shock-(duration*spread_shock if asset == "Corporate" else 0)+rng.gauss(0, BOND_NOISE_SD)
            bond_rows.append({DATE: current, SECURITY: security, ASSET: asset, RATING: current_rating,
                              MATURITY: remaining, AMOUNT: current_amount, CURRENCY: currency,
                              DURATION: duration, YIELD: annual_yield, RETURN: bond_return if number else 0})
    write_csv(SNAPSHOT_FILES["manager_returns"], fund_rows)
    write_json(SNAPSHOT_FILES["manager_profiles"], list(FUND_SPECS))
    write_csv(SNAPSHOT_FILES["bonds"], bond_rows)
    write_csv(SNAPSHOT_FILES["tax_lots"], TAX_LOTS)
    write_json(SNAPSHOT_FILES["portfolio"], {"prices": TAX_PRICES, "groups": GROUPS, "targets": TAX_TARGETS, "sma_model": MODEL,
                                         "cash": TAX_CASH, "purchases": PURCHASES, "loss_sales": LOSS_SALES,
                                         "harvest_replacements": {"CORP": "CORP_ALT"}, "as_of": AS_OF})
    write_json(SNAPSHOT_FILES["clients"], list(CLIENT_SPECS))
    daily_rows = []
    for account in CLIENT_SPECS:
        value = account["cash"] + account["scale"]*sum(lot[QUANTITY]*TAX_PRICES[lot[SECURITY]] for lot in TAX_LOTS)
        first = max(date.fromisoformat(QUARTER_START), date.fromisoformat(account["opened"]))
        current = first
        while current <= date.fromisoformat(AS_OF):
            value *= 1+rng.gauss(AUM_DAILY_DRIFT, AUM_DAILY_NOISE_SD)
            daily_rows.append({CLIENT: account[CLIENT], DATE: current.isoformat(), "aum": round(value, 2)})
            current += timedelta(days=1)
    write_csv(SNAPSHOT_FILES["daily_aum"], daily_rows)
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<edgarSubmission xmlns="urn:synthetic-nport"><formData><invstOrSecs>
<invstOrSec><name>Synthetic Treasury Pool</name><cusip>SYN000001</cusip><balance>6000</balance><curCd>USD</curCd><valUSD>600000</valUSD><pctVal>60</pctVal><assetCat>DBT</assetCat></invstOrSec>
<invstOrSec><name>Synthetic Corporate Pool</name><cusip>SYN000002</cusip><balance>4000</balance><curCd>USD</curCd><valUSD>400000</valUSD><pctVal>40</pctVal><assetCat>DBT</assetCat></invstOrSec>
</invstOrSecs></formData></edgarSubmission>
'''
    (SNAPSHOT_FILES["nport_style"]).write_text(xml, encoding="utf-8")
    files = sorted(path for path in DATA.iterdir() if path.name != SNAPSHOT_FILES["manifest"].name)
    write_json(SNAPSHOT_FILES["manifest"], {"author": AUTHOR, "kind": "synthetic", "seed": SEED,
                                         "as_of": AS_OF, "generator": GENERATOR_SOURCE,
                                         "public_observations": 0,
                                         "files": {path.name: sha256(path) for path in files}})


if __name__ == "__main__":
    generate()

