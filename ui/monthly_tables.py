from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Tuple, TypeVar

import pandas as pd

from domain.results import ProResult, SimpleResult

ResultT = TypeVar("ResultT")


@dataclass(frozen=True)
class MonthlyColumnSpec:
    label: str
    extract: Callable[[Any], Any]


def build_simple_monthly_table_schema() -> Tuple[MonthlyColumnSpec, ...]:
    return (
        MonthlyColumnSpec("Месяц", lambda res: res.months),
        MonthlyColumnSpec("Авто", lambda res: res.cars_per_month.astype(int)),
        MonthlyColumnSpec("Выручка, ₽", lambda res: res.revenue_month),
        MonthlyColumnSpec("Перем. расходы, ₽", lambda res: res.var_costs_month),
        MonthlyColumnSpec("Пост. расходы, ₽", lambda res: res.fix_costs_month),
        MonthlyColumnSpec("ЗП+взносы, ₽", lambda res: res.salary_total_month),
        MonthlyColumnSpec("Налог, ₽", lambda res: res.tax_month),
        MonthlyColumnSpec("Прибыль, ₽", lambda res: res.profit_month),
        MonthlyColumnSpec("Накопл. CF, ₽", lambda res: res.cumulative[1:]),
    )


def build_pro_monthly_table_schema() -> Tuple[MonthlyColumnSpec, ...]:
    return (
        MonthlyColumnSpec("Месяц", lambda res: res.months),
        MonthlyColumnSpec("Авто", lambda res: res.cars_per_month.astype(int)),
        MonthlyColumnSpec("Выручка", lambda res: res.revenue_month),
        MonthlyColumnSpec("Перем.", lambda res: res.var_costs_month),
        MonthlyColumnSpec("OPEX", lambda res: res.opex_month),
        MonthlyColumnSpec("ЗП+взн.", lambda res: res.salary_total_month),
        MonthlyColumnSpec("EBITDA", lambda res: res.ebitda_month),
        MonthlyColumnSpec("% кредит", lambda res: res.credit_interest_month),
        MonthlyColumnSpec("Аморт.", lambda res: res.amortization_month),
        MonthlyColumnSpec("Налог", lambda res: res.tax_month),
        MonthlyColumnSpec("Прибыль", lambda res: res.profit_month),
        MonthlyColumnSpec("Тело кредит", lambda res: res.credit_principal_month),
        MonthlyColumnSpec("Накопл. CF", lambda res: res.cumulative[1:]),
    )


SIMPLE_MONTHLY_TABLE_SCHEMA: Tuple[MonthlyColumnSpec, ...] = build_simple_monthly_table_schema()
PRO_MONTHLY_TABLE_SCHEMA: Tuple[MonthlyColumnSpec, ...] = build_pro_monthly_table_schema()


def build_monthly_table_dataframe(
    res: ResultT,
    schema: Tuple[MonthlyColumnSpec, ...],
) -> pd.DataFrame:
    return pd.DataFrame({spec.label: spec.extract(res) for spec in schema})


def build_simple_monthly_table_df(res: SimpleResult) -> pd.DataFrame:
    return build_monthly_table_dataframe(res, SIMPLE_MONTHLY_TABLE_SCHEMA)


def build_pro_monthly_table_df(res: ProResult) -> pd.DataFrame:
    return build_monthly_table_dataframe(res, PRO_MONTHLY_TABLE_SCHEMA)
