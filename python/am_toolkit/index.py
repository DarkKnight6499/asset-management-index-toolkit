"""Point-in-time monthly index decisions with synthetic total returns."""

import math
import statistics

from .config import (AMOUNT, ASSET, DATE, DURATION, IG_RATINGS, INDEX_COST_BPS,
                     INDEX_MAX_MATURITY, INDEX_MIN_AMOUNT, INDEX_MIN_MATURITY,
                     INDEX_TREASURY_WEIGHT, MATURITY, RATING, RETURN, SECURITY)
from .research import compound, max_drawdown
from .validation import monthly_sequence

# Configuration
TREASURY = "Treasury"
CORPORATE = "Corporate"
USD = "USD"
CURRENCY = "currency"
BENCHMARK_TREASURY_WEIGHT = .50
EPSILON = 1e-10


def eligible(row):
    maturity = float(row[MATURITY])
    return (row[CURRENCY] == USD and INDEX_MIN_MATURITY <= maturity <= INDEX_MAX_MATURITY
            and float(row[AMOUNT]) >= INDEX_MIN_AMOUNT
            and (row[ASSET] == TREASURY or row[ASSET] == CORPORATE and row[RATING] in IG_RATINGS))


def weights(rows, treasury_weight=INDEX_TREASURY_WEIGHT, equal=False):
    selected = [row for row in rows if eligible(row)]
    result = {}
    for asset, allocation in ((TREASURY, treasury_weight), (CORPORATE, 1-treasury_weight)):
        sleeve = [row for row in selected if row[ASSET] == asset]
        denominator = sum(1 if equal else float(row[AMOUNT]) for row in sleeve)
        if denominator == 0:
            raise ValueError("Eligible sleeve empty; review required")
        for row in sleeve:
            result[row[SECURITY]] = allocation*(1 if equal else float(row[AMOUNT]))/denominator
    return result


def one_way_turnover(previous, target):
    return .5*sum(abs(target.get(key, 0)-previous.get(key, 0)) for key in set(previous)|set(target))


def backtest(rows, cost_bps=INDEX_COST_BPS):
    if not math.isfinite(cost_bps) or cost_bps < 0:
        raise ValueError("Invalid trading cost")
    by_date = {}
    seen = set()
    for row in rows:
        key = (row[DATE], row[SECURITY])
        if key in seen:
            raise ValueError("Duplicate bond month")
        seen.add(key)
        for column in (AMOUNT, MATURITY, DURATION, RETURN):
            if not math.isfinite(float(row[column])):
                raise ValueError("Nonfinite bond data")
        if float(row[RETURN]) <= -1 or float(row[AMOUNT]) <= 0 or float(row[DURATION]) < 0:
            raise ValueError("Invalid bond data")
        by_date.setdefault(row[DATE], {})[row[SECURITY]] = row
    dates = sorted(by_date)
    monthly_sequence(dates)
    if len(dates) < 2:
        raise ValueError("Need opening snapshot and one return period")
    target = weights(list(by_date[dates[0]].values()))
    benchmark_target = weights(list(by_date[dates[0]].values()), BENCHMARK_TREASURY_WEIGHT, equal=True)
    records, constituents = [], []
    level = benchmark_level = 100.0
    for previous_date, current_date in zip(dates, dates[1:]):
        current = by_date[current_date]
        if not (set(target)|set(benchmark_target)) <= set(current):
            raise ValueError("Held bond lacks next-period return")
        gross = sum(weight*float(current[key][RETURN]) for key, weight in target.items())
        benchmark_gross = sum(weight*float(current[key][RETURN]) for key, weight in benchmark_target.items())
        drifted = {key: weight*(1+float(current[key][RETURN]))/(1+gross) for key, weight in target.items()}
        benchmark_drifted = {key: weight*(1+float(current[key][RETURN]))/(1+benchmark_gross) for key, weight in benchmark_target.items()}
        next_target = weights(list(current.values()))
        next_benchmark = weights(list(current.values()), BENCHMARK_TREASURY_WEIGHT, equal=True)
        turnover = one_way_turnover(drifted, next_target)
        benchmark_turnover = one_way_turnover(benchmark_drifted, next_benchmark)
        net = (1+gross)*(1-turnover*cost_bps/10000)-1
        benchmark_net = (1+benchmark_gross)*(1-benchmark_turnover*cost_bps/10000)-1
        level *= 1+net
        benchmark_level *= 1+benchmark_net
        duration = sum(weight*float(by_date[previous_date][key][DURATION]) for key, weight in target.items())
        records.append({DATE: current_date, "decision_date": previous_date, "gross_return": gross,
                        "net_return": net, "benchmark_return": benchmark_net, "turnover": turnover,
                        "benchmark_turnover": benchmark_turnover, "index_level": level,
                        "benchmark_level": benchmark_level, "duration": duration})
        constituents.extend({"decision_date": previous_date, "return_date": current_date, SECURITY: key, "weight": weight}
                            for key, weight in target.items())
        target, benchmark_target = next_target, next_benchmark
    values = [row["net_return"] for row in records]
    benchmark_values = [row["benchmark_return"] for row in records]
    annualized = (1+compound(values))**(12/len(values))-1
    tracking_error = statistics.stdev([first-second for first, second in zip(values, benchmark_values)])*math.sqrt(12) if len(values)>1 else 0
    summary = {"months": len(values), "cumulative_return": compound(values), "annualized_return": annualized,
               "benchmark_cumulative_return": compound(benchmark_values), "max_drawdown": max_drawdown(values),
               "annualized_volatility": statistics.stdev(values)*math.sqrt(12) if len(values)>1 else 0,
               "tracking_error": tracking_error, "total_turnover": sum(row["turnover"] for row in records),
               "cost_bps": cost_bps}
    return records, constituents, summary

