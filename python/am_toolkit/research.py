"""Transparent manager scores based on synthetic evidence."""

import math
import statistics

from .config import BENCHMARK, DATE, FUND, RETURN, SCORE_WEIGHTS
from .validation import monthly_sequence

# Configuration
WINDOW = 12
ANNUAL_MONTHS = 12
CONSISTENCY_CUTOFFS = (.25, .40, .55, .70)
VOLATILITY_CUTOFFS = (.02, .04, .06, .08)
FEE_CUTOFFS_BPS = (15, 30, 45, 65)
DRIFT_CUTOFFS = (.025, .05, .10, .20)
APPROVE_SCORE = 75
WATCH_SCORE = 55


def compound(values):
    return math.prod(1 + value for value in values) - 1


def max_drawdown(values):
    wealth = peak = 1.0
    worst = 0.0
    for value in values:
        wealth *= 1 + value
        peak = max(peak, wealth)
        worst = min(worst, wealth / peak - 1)
    return worst


def low_score(value, cutoffs):
    return 5 - sum(value > cutoff for cutoff in cutoffs)


def score_manager(profile, observations):
    rows = sorted((row for row in observations if row[FUND] == profile[FUND]), key=lambda row: row[DATE])
    returns = [float(row[RETURN]) for row in rows]
    benchmark = [float(row[BENCHMARK]) for row in rows]
    if len(returns) < WINDOW or len({row[DATE] for row in rows}) != len(rows):
        raise ValueError("Need unique monthly observations covering at least 12 months")
    monthly_sequence([row[DATE] for row in rows])
    if any(not math.isfinite(value) or value <= -1 for value in returns + benchmark):
        raise ValueError("Invalid returns")
    if not math.isfinite(profile["fee_bps"]) or profile["fee_bps"] < 0:
        raise ValueError("Fee must be finite and nonnegative")
    if set(profile["style_policy"]) != set(profile["style_current"]):
        raise ValueError("Style categories differ")
    for name in ("style_policy", "style_current"):
        allocation = profile[name]
        if any(not math.isfinite(value) or value < 0 for value in allocation.values()) or not math.isclose(sum(allocation.values()), 1):
            raise ValueError("Style weights must be nonnegative and sum to one")
    wins = [compound(returns[end-WINDOW:end]) > compound(benchmark[end-WINDOW:end])
            for end in range(WINDOW, len(returns)+1)]
    consistency = sum(wins) / len(wins)
    volatility = statistics.stdev(returns) * math.sqrt(ANNUAL_MONTHS)
    drift = .5 * sum(abs(profile["style_current"][key] - weight)
                     for key, weight in profile["style_policy"].items())
    scores = {"consistency": 1 + sum(consistency >= cutoff for cutoff in CONSISTENCY_CUTOFFS),
              "risk": low_score(volatility, VOLATILITY_CUTOFFS),
              "fees": low_score(profile["fee_bps"], FEE_CUTOFFS_BPS),
              "style": low_score(drift, DRIFT_CUTOFFS),
              "operations": profile["operations_score"], "team": profile["team_score"]}
    if any(not 1 <= score <= 5 for score in scores.values()):
        raise ValueError("Scores must lie between 1 and 5")
    total = sum(scores[key] * SCORE_WEIGHTS[key] for key in scores) * 20
    recommendation = "Approve" if total >= APPROVE_SCORE else "Watch" if total >= WATCH_SCORE else "Decline"
    if scores["operations"] <= 2:
        recommendation = "Decline"
    elif scores["team"] <= 2 and recommendation == "Approve":
        recommendation = "Watch"
    return {FUND: profile[FUND], **{key + "_score": value for key, value in scores.items()},
            "total_score": round(total, 4), "rolling_win_rate": consistency,
            "volatility": volatility, "max_drawdown": max_drawdown(returns),
            "style_drift": drift, "fee_bps": profile["fee_bps"],
            "cumulative_return": compound(returns), "recommendation": recommendation}

