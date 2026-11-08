"""Conservative trade prevention, not tax-return wash-sale adjudication."""

from dataclasses import asdict, dataclass, replace
from datetime import date
import math

from .config import WASH_DAYS

# Configuration
EPSILON = 1e-8
MIN_HARVEST_LOSS = 100.0


@dataclass(frozen=True)
class Lot:
    lot: str
    security: str
    acquired: str
    quantity: float
    cost: float


@dataclass(frozen=True)
class Event:
    date: str
    security: str
    quantity: float


def within_window(first, second):
    return abs((date.fromisoformat(first) - date.fromisoformat(second)).days) <= WASH_DAYS


def matching_purchases(security, as_of, purchases, groups):
    return sum(event.quantity for event in purchases if event.quantity > 0
               and groups[event.security] == groups[security]
               and within_window(event.date, as_of))


def buy_locked(security, as_of, loss_sales, groups):
    return any(event.quantity > 0 and groups[event.security] == groups[security]
               and 0 <= (date.fromisoformat(as_of) - date.fromisoformat(event.date)).days <= WASH_DAYS
               for event in loss_sales)


def plan_rebalance(lots, prices, targets, cash, as_of, groups, purchases=(), loss_sales=(),
                   harvest_replacements=None):
    lots = list(lots)
    if len({lot.lot for lot in lots}) != len(lots):
        raise ValueError("Duplicate lot identifier")
    required = set(targets) | {lot.security for lot in lots}
    replacements = harvest_replacements or {}
    required |= set(replacements.values())
    if cash < 0 or not math.isfinite(cash) or any(not math.isfinite(weight) or weight < 0 for weight in targets.values()):
        raise ValueError("Invalid cash or target")
    if sum(targets.values()) > 1 + EPSILON:
        raise ValueError("Targets exceed portfolio value")
    if any(security not in prices or security not in groups or not math.isfinite(prices[security])
           or prices[security] <= 0 for security in required):
        raise ValueError("Missing group or positive price")
    for lot in lots:
        if lot.quantity <= 0 or lot.cost < 0 or not math.isfinite(lot.quantity + lot.cost):
            raise ValueError("Invalid lot")
        if date.fromisoformat(lot.acquired) > date.fromisoformat(as_of):
            raise ValueError("Future acquisition in current holdings")
    nav = cash + sum(lot.quantity * prices[lot.security] for lot in lots)
    if nav <= 0:
        raise ValueError("Portfolio value must be positive")
    effective = dict(targets)
    for security, replacement in replacements.items():
        if groups[security] == groups[replacement]:
            raise ValueError("Harvest replacement must have a different declared group")
        candidates = [lot for lot in lots if lot.security == security and
                      (lot.cost - prices[security]) * lot.quantity >= MIN_HARVEST_LOSS]
        if candidates and not matching_purchases(security, as_of, purchases, groups):
            effective[replacement] = effective.get(replacement, 0) + effective.get(security, 0)
            effective[security] = 0
    trades, attempts, blocked = [], [], []
    remaining = list(lots)
    locks = list(loss_sales)
    for security in sorted({lot.security for lot in lots}):
        current = sum(lot.quantity for lot in remaining if lot.security == security)
        excess = max(0, current - effective.get(security, 0) * nav / prices[security])
        candidates = sorted((lot for lot in remaining if lot.security == security), key=lambda lot: (-lot.cost, lot.lot))
        for lot in candidates:
            requested = min(excess, lot.quantity)
            if requested <= EPSILON:
                continue
            price = prices[security]
            purchase_qty = matching_purchases(security, as_of, purchases, groups)
            is_blocked = price < lot.cost and purchase_qty > 0
            attempts.append({**asdict(lot), "requested_qty": requested, "price": price,
                             "group": groups[security], "purchase_qty": purchase_qty,
                             "executed_qty": 0 if is_blocked else requested})
            if is_blocked:
                blocked.append({"security": security, "action": "SELL", "reason": "Purchase inside 30-day window", "quantity": requested})
                continue
            gain = requested * (price - lot.cost)
            trades.append({"security": security, "lot": lot.lot, "side": "SELL", "quantity": requested,
                           "price": price, "cash_flow": requested * price, "realized_gain": gain})
            cash += requested * price
            remaining.remove(lot)
            if lot.quantity > requested + EPSILON:
                remaining.append(replace(lot, quantity=lot.quantity-requested))
            excess -= requested
            if gain < 0:
                locks.append(Event(as_of, security, requested))
    for security, weight in sorted(effective.items()):
        current = sum(lot.quantity * prices[security] for lot in remaining if lot.security == security)
        needed = max(0, weight * nav - current)
        if needed <= EPSILON:
            continue
        if buy_locked(security, as_of, locks, groups):
            blocked.append({"security": security, "action": "BUY", "reason": "Loss sale lock through day 30", "quantity": needed/prices[security]})
            continue
        amount = min(needed, cash)
        if amount <= EPSILON:
            continue
        quantity = amount / prices[security]
        new_id = "new_" + security
        if any(lot.lot == new_id for lot in remaining):
            raise ValueError("New lot identifier collision")
        remaining.append(Lot(new_id, security, as_of, quantity, prices[security]))
        cash -= amount
        trades.append({"security": security, "lot": new_id, "side": "BUY", "quantity": quantity,
                       "price": prices[security], "cash_flow": -amount, "realized_gain": 0})
    ending = cash + sum(lot.quantity * prices[lot.security] for lot in remaining)
    if abs(ending - nav) > EPSILON * nav:
        raise ArithmeticError("Value not conserved")
    actual = {security: sum(lot.quantity * prices[security] for lot in remaining if lot.security == security)/nav
              for security in required}
    return {"opening_nav": nav, "cash": max(0, cash), "trades": trades, "attempts": attempts,
            "blocked": blocked, "lots": [asdict(lot) for lot in remaining],
            "effective_targets": effective, "actual_weights": actual,
            "realized_gain": sum(trade["realized_gain"] for trade in trades),
            "realized_loss": -sum(min(0, trade["realized_gain"]) for trade in trades),
            "loss_locks": [asdict(event) for event in locks],
            "absolute_drift": sum(abs(actual.get(security, 0)-effective.get(security, 0)) for security in required)}

