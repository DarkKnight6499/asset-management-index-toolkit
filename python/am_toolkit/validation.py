"""Shared time-series input checks."""

import calendar
from datetime import date


def monthly_sequence(values):
    dates = [date.fromisoformat(value) for value in values]
    if any(value.day != calendar.monthrange(value.year, value.month)[1] for value in dates):
        raise ValueError("Observations must use calendar month-end dates")
    numbers = [value.year*12+value.month for value in dates]
    if any(second-first != 1 for first, second in zip(numbers, numbers[1:])):
        raise ValueError("Monthly observations must be consecutive and unique")

