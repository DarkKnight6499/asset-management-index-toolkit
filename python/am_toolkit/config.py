"""Shared names and explicit project assumptions."""

from pathlib import Path

# Configuration
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "synthetic"
OUTPUT = ROOT / "examples" / "output"
SEED = 73421
AS_OF = "2025-09-30"
START = "2022-09-30"
MONTHS = 36
WASH_DAYS = 30
BILLING_DAYS_YEAR = 365
QUARTER_START = "2025-07-01"
QUARTER_END = AS_OF
INDEX_MIN_MATURITY = 1.0
INDEX_MAX_MATURITY = 10.0
INDEX_MIN_AMOUNT = 300_000_000
INDEX_TREASURY_WEIGHT = 0.60
INDEX_COST_BPS = 5.0
IG_RATINGS = frozenset({"AAA", "AA", "A", "BBB"})
SCORE_WEIGHTS = {"consistency": .25, "risk": .20, "fees": .15,
                 "style": .15, "operations": .15, "team": .10}
FUND = "fund"
DATE = "date"
RETURN = "return"
BENCHMARK = "benchmark"
SECURITY = "security"
ISSUER = "issuer"
VALUE = "value_usd"
BALANCE = "balance"
WEIGHT = "weight"
REPORTED_PERCENT = "reported_percent"
CURRENCY = "currency"
ASSET = "asset"
MATURITY = "maturity"
RATING = "rating"
AMOUNT = "amount"
DURATION = "duration"
YIELD = "yield"
PRICE = "price"
CLIENT = "client"
QUANTITY = "quantity"
COST = "cost"
LOT = "lot"
ACQUIRED = "acquired"
SNAPSHOT_FILES = {
    "manager_returns": DATA / "manager_returns.csv",
    "manager_profiles": DATA / "manager_profiles.json",
    "bonds": DATA / "bonds.csv",
    "tax_lots": DATA / "tax_lots.csv",
    "portfolio": DATA / "portfolio.json",
    "clients": DATA / "clients.json",
    "daily_aum": DATA / "daily_aum.csv",
    "nport_style": DATA / "nport_style.xml",
    "manifest": DATA / "manifest.json",
}
OUTPUT_FILES = {
    "manager_scorecard": OUTPUT / "manager_scorecard.csv",
    "manager_recommendations": OUTPUT / "manager_recommendations.md",
    "parsed_holdings": OUTPUT / "parsed_holdings.csv",
    "tax_plan": OUTPUT / "tax_plan.json",
    "tax_trades": OUTPUT / "tax_trades.csv",
    "tax_lot_attempts": OUTPUT / "tax_lot_attempts.csv",
    "sma_workflows": OUTPUT / "sma_workflows.json",
    "custodian_trade_instructions": OUTPUT / "custodian_trade_instructions.csv",
    "custodian_cash_instructions": OUTPUT / "custodian_cash_instructions.csv",
    "billing": OUTPUT / "billing.csv",
    "index_monthly": OUTPUT / "index_monthly.csv",
    "index_constituents": OUTPUT / "index_constituents.csv",
    "index_summary": OUTPUT / "index_summary.json",
    "quarterly_review": OUTPUT / "quarterly_review.md",
    "workbook_inputs": OUTPUT / "workbook_inputs.json",
    "run_manifest": OUTPUT / "run_manifest.json",
}

