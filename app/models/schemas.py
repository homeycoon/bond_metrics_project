from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator
from typing import Optional


class TickerBase(BaseModel):
    ticker: str
    name: str


class BondInfo(TickerBase):
    prevwaprice_cur: Optional[Decimal | None] = None
    prevwaprice_rub: Optional[Decimal | None] = None
    nominal_cur: Optional[Decimal] = None
    nominal_rub: Optional[Decimal] = None
    coupon_value_cur: Optional[Decimal] = None
    coupon_value_rub: Optional[Decimal] = None
    coupon_period: Optional[int] = None
    accum_coupon_cur: Optional[Decimal] = None
    accum_coupon_rub: Optional[Decimal] = None
    cur_of_nominal: Optional[str] = None
    cur_of_market: Optional[str] = None
    lot_size: Optional[int] = None
    issue_size: Optional[int] = None
    prev_date: Optional[datetime] = None
    next_coupon_date: Optional[datetime] = None
    maturity_date: Optional[datetime] = None
    loading_date: datetime


class Currency(BaseModel):
    currency_name: str
    currency_code: str
    curs: Decimal


class BondMetrics(TickerBase):
    current_yield: Decimal
    ytm_prct: Decimal
    fair_value: Decimal
    conclusion: str


class BondsCorrelation(BaseModel):
    ticker_1: str
    name_1: str
    ticker_2: str
    name_2: str
    Pearson_correlation: float = 0.0
    Spearman_correlation: float = 0.0
    Kendall_correlation: float = 0.0
    Robust_correlation: float = 0.0
    Advice: str

    @field_validator(
        "Pearson_correlation", "Spearman_correlation",
        "Kendall_correlation", "Robust_correlation"
    )
    def round_float(cls, v: float):
        return round(v, 8)
