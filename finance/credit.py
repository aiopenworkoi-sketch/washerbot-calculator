from __future__ import annotations

from typing import Dict, Tuple

import numpy as np


def annuity_payment(principal: float, annual_rate: float, n_months: int) -> float:
    """Месячный аннуитетный платёж по кредиту."""
    if principal <= 0 or n_months <= 0:
        return 0.0
    if annual_rate <= 0:
        return principal / n_months
    r = annual_rate / 12
    return principal * r * (1 + r) ** n_months / ((1 + r) ** n_months - 1)


def calculate_credit_schedule(
    amount: float,
    annual_rate: float,
    term_months: int,
    grace_months: int = 0,
) -> Dict[str, np.ndarray]:
    """
    Аннуитетный график с отсрочкой тела долга.
    В период grace платятся только проценты, тело не уменьшается.
    """
    if amount <= 0 or term_months <= 0:
        return {
            "interest": np.zeros(term_months if term_months > 0 else 0),
            "principal": np.zeros(term_months if term_months > 0 else 0),
            "payment": np.zeros(term_months if term_months > 0 else 0),
            "balance": np.zeros(term_months if term_months > 0 else 0),
        }

    grace_months = max(0, min(grace_months, term_months))
    monthly_rate = annual_rate / 12.0

    interest_arr = np.zeros(term_months)
    principal_arr = np.zeros(term_months)
    payment_arr = np.zeros(term_months)
    balance_arr = np.zeros(term_months)

    balance = amount

    # Период льготы — только проценты
    for i in range(grace_months):
        interest = balance * monthly_rate
        interest_arr[i] = interest
        principal_arr[i] = 0.0
        payment_arr[i] = interest
        balance_arr[i] = balance

    # Аннуитетный период
    remaining_term = term_months - grace_months
    if remaining_term > 0 and balance > 0:
        if monthly_rate > 0:
            annuity = balance * (monthly_rate * (1 + monthly_rate) ** remaining_term) / \
                      ((1 + monthly_rate) ** remaining_term - 1)
        else:
            annuity = balance / remaining_term

        for j in range(remaining_term):
            i = grace_months + j
            interest = balance * monthly_rate
            principal = min(max(annuity - interest, 0.0), balance)
            balance = max(0.0, balance - principal)

            interest_arr[i] = interest
            principal_arr[i] = principal
            payment_arr[i] = interest + principal
            balance_arr[i] = balance

    return {
        "interest": interest_arr,
        "principal": principal_arr,
        "payment": payment_arr,
        "balance": balance_arr,
    }
