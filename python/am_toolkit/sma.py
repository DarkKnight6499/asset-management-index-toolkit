"""Synthetic onboarding, restrictions, trade and cash instructions, and billing."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import math

from .config import BILLING_DAYS_YEAR
from .tax import plan_rebalance

# Configuration
REQUIRED_CHECKS = ("identity", "agreement", "tax_form", "custody", "restrictions_approved")
FEE_FIRST_LIMIT = 1_000_000.0
FEE_SECOND_LIMIT = 5_000_000.0
FEE_RATES = (.0050, .0035, .0025)
MIN_CASH_WEIGHT = .02


def round_cents(value):
    return float(Decimal(str(value)).quantize(Decimal(".01"), rounding=ROUND_HALF_UP))


def billing(account, average_aum, quarter_start, quarter_end, opened, closed=None):
    if not math.isfinite(average_aum) or average_aum < 0:
        raise ValueError("Invalid AUM")
    start, end = date.fromisoformat(quarter_start), date.fromisoformat(quarter_end)
    if start > end:
        raise ValueError("Reversed billing period")
    active_start = max(start, date.fromisoformat(opened))
    active_end = min(end, date.fromisoformat(closed)) if closed else end
    if closed and date.fromisoformat(closed) < date.fromisoformat(opened):
        raise ValueError("Closed before opening")
    days = max(0, (active_end-active_start).days+1)
    first = min(average_aum, FEE_FIRST_LIMIT)
    second = min(max(average_aum-FEE_FIRST_LIMIT, 0), FEE_SECOND_LIMIT-FEE_FIRST_LIMIT)
    third = max(average_aum-FEE_SECOND_LIMIT, 0)
    annual = first*FEE_RATES[0]+second*FEE_RATES[1]+third*FEE_RATES[2]
    return {"client": account, "average_aum": average_aum, "opened": opened, "closed": closed or "",
            "active_days": days, "tier1_aum": first, "tier2_aum": second,
            "tier3_aum": third, "annual_fee": annual,
            "fee": round_cents(annual*days/BILLING_DAYS_YEAR)}


def simulate_account(account, lots, prices, model, as_of, groups, purchases=(), loss_sales=()):
    missing = [key for key in REQUIRED_CHECKS if not account["checks"].get(key, False)]
    if missing:
        return {"client": account["client"], "status": "HOLD", "missing_checks": missing,
                "instructions": [], "external_cash_instruction": None}
    forbidden = set(account["forbidden"])
    targets = {security: weight for security, weight in model.items() if security not in forbidden}
    total = sum(targets.values())
    if total > 0:
        targets = {security: weight/total*(1-MIN_CASH_WEIGHT) for security, weight in targets.items()}
    result = plan_rebalance(lots, prices, targets, account["cash"], as_of, groups, purchases, loss_sales)
    restricted_left = [lot["security"] for lot in result["lots"] if lot["security"] in forbidden]
    instructions = [{"client": account["client"], "custodian": account["custodian"],
                     "status": "SIMULATED_PENDING_REVIEW", **trade} for trade in result["trades"]]
    return {"client": account["client"], "status": "EXCEPTION" if restricted_left else "READY_FOR_REVIEW",
            "missing_checks": [], "restricted_positions_remaining": restricted_left,
            "instructions": instructions, "trade_cash_flow": sum(trade["cash_flow"] for trade in result["trades"]),
            "external_cash_instruction": {"action": "RETAIN_CASH", "amount": result["cash"],
                                          "custodian": account["custodian"], "status": "SIMULATED_PENDING_REVIEW"},
            "result": result}

