from datetime import datetime
from decimal import Decimal

from sqlalchemy import (Integer, String, DateTime,
                        DECIMAL, ForeignKey, BigInteger)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .database import Base


class Bond(Base):
    __tablename__ = "bonds"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    ticker: Mapped[str] = mapped_column(
        String,
        unique=True
    ) # SECID
    name: Mapped[str] = mapped_column(
        String
    ) # SECNAME
    prev_close_price_cur: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=20, scale=4), nullable=True
    ) # PREVLEGALCLOSEPRICE (в валюте расчетов CURRENCYID)
    prev_close_price_rub: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=20, scale=4), nullable=True
    )  # PREVLEGALCLOSEPRICE * rate
    nominal_cur: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=20, scale=4), nullable=True
    ) # LOTVALUE (в валюте номинала FACEUNIT)
    nominal_rub: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=20, scale=4), nullable=True
    )  # LOTVALUE * rate
    coupon_rate: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=20, scale=4), nullable=True
    ) # COUPONPERCENT
    coupon_period: Mapped[int] = mapped_column(
        Integer, nullable=True
    ) # COUPONPERIOD
    accum_coupon_cur: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=20, scale=4), nullable=True
    )  # ACCRUEDINT (в валюте расчетов CURRENCYID)
    accum_coupon_rub: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=20, scale=4), nullable=True
    )  # ACCRUEDINT * rate
    valuta_nominal: Mapped[str] = mapped_column(
        String, nullable=True
    ) # FACEUNIT
    currency_curr: Mapped[str] = mapped_column(
        String, nullable=True
    ) # CURRENCYID
    lot_size: Mapped[int] = mapped_column(
        Integer, nullable=True
    ) # LOTSIZE
    issue_size: Mapped[int] = mapped_column(
        BigInteger, nullable=True
    ) # ISSUESIZE
    prev_date: Mapped[datetime] = mapped_column(DateTime, nullable=True) # PREVDATE
    next_coupon_date: Mapped[datetime] = mapped_column(DateTime, nullable=True) # NEXTCOUPON
    maturity_date: Mapped[datetime] = mapped_column(DateTime, nullable=True) # MATDATE
    loading_date: Mapped[datetime] = mapped_column(DateTime) # yesterday date


class Currency(Base):
    __tablename__ = "currencies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    currency_name: Mapped[str] = mapped_column(
        String
    )
    currency_code: Mapped[str] = mapped_column(
        String
    )
    curs: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=10, scale=2)
    )


# class Metric(Base):
#     __tablename__ = "metrics"
#
#     id: Mapped[int] = mapped_column(
#         Integer,
#         primary_key=True,
#         index=True
#     )
#     bond_id: Mapped[int] = mapped_column(
#         Integer,
#         ForeignKey("bonds.id", ondelete="CASCADE"),
#         nullable=False,
#         index=True
#     )
#     bond: Mapped["Bond"] = relationship(back_populates="metrics")
#     fair_value_rub: Mapped[Decimal] = mapped_column(
#         Decimal(precision=10, scale=2)
#     )
#     yield_to_maturity_rub: Mapped[Decimal] = mapped_column(
#         Decimal(precision=10, scale=4)
#     )
#     duration: Mapped[int] = mapped_column(Integer)
#     modified_duration: Mapped[int] = mapped_column(Integer)
#     credit_spread_rub = Mapped[Decimal] = mapped_column(
#         Decimal(precision=10, scale=2)
#     )
#     current_yield_rub = Mapped[Decimal] = mapped_column(
#         Decimal(precision=10, scale=2)
#     )
#     calculated_date = Mapped[datetime] = mapped_column(DateTime)
