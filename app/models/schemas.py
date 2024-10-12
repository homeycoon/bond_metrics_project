from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel
from typing import Optional


class TickerBase(BaseModel):
    ticker: str
    name: str


class TickerOut(TickerBase):
    id: int


class BondInfo(TickerBase):
    prev_close_price_cur: Optional[Decimal] = None
    prev_close_price_rub: Optional[Decimal] = None
    nominal_cur: Optional[Decimal] = None
    nominal_rub: Optional[Decimal] = None
    coupon_rate: Optional[Decimal] = None
    coupon_period: Optional[int] = None
    accum_coupon_cur: Optional[Decimal] = None
    accum_coupon_rub: Optional[Decimal] = None
    valuta_nominal: Optional[str] = None
    currency_curr: Optional[str] = None
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


# class BondMetrics(TickerBase):
#     fair_value_rub: Decimal
#     yield_to_maturity_rub: Decimal
#     duration: int
#     modified_duration: int
#     credit_spread_rub = Decimal
#     current_yield_rub = Decimal
#     calculated_date = datetime
