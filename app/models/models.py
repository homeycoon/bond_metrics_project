from datetime import datetime
from decimal import Decimal

from sqlalchemy import (Integer, String, DateTime,
                        DECIMAL, BigInteger, Boolean)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


# Модель данных облигаций
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
    )  # SECID
    name: Mapped[str] = mapped_column(
        String
    )  # SECNAME
    prevwaprice_cur: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=20, scale=4), nullable=True
    )  # PREVWAPRICE (в валюте номинала FACEUNIT)
    prevwaprice_rub: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=20, scale=4), nullable=True
    )  # PREVWAPRICE * rate
    nominal_cur: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=20, scale=4), nullable=True
    )  # FACEVALUE (в валюте номинала FACEUNIT)
    nominal_rub: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=20, scale=4), nullable=True
    )  # FACEVALUE * rate
    coupon_value_cur: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=20, scale=4), nullable=True
    )  # COUPONVALUE (в валюте номинала FACEUNIT)
    coupon_value_rub: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=20, scale=4), nullable=True
    )  # COUPONVALUE * rate
    coupon_period: Mapped[int] = mapped_column(
        Integer, nullable=True
    )  # COUPONPERIOD (в днях)
    accum_coupon_cur: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=20, scale=4), nullable=True
    )  # ACCRUEDINT (в валюте расчетов CURRENCYID)
    accum_coupon_rub: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=20, scale=4), nullable=True
    )  # ACCRUEDINT * rate
    cur_of_nominal: Mapped[str] = mapped_column(
        String, nullable=True
    )  # FACEUNIT
    cur_of_market: Mapped[str] = mapped_column(
        String, nullable=True
    )  # CURRENCYID
    lot_size: Mapped[int] = mapped_column(
        Integer, nullable=True
    )  # LOTSIZE
    issue_size: Mapped[int] = mapped_column(
        BigInteger, nullable=True
    )  # ISSUESIZE
    prev_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)  # PREVDATE
    next_coupon_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)  # NEXTCOUPON
    maturity_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)  # MATDATE
    loading_date: Mapped[datetime] = mapped_column(DateTime)  # loading date


# Модель данных валют
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


# Модель данных пользователей
class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        index=True
    )
    username: Mapped[str] = mapped_column(
        String,
        unique=True
    )
    first_name: Mapped[str] = mapped_column(
        String
    )
    last_name: Mapped[str] = mapped_column(
        String,
        nullable=True
    )
    patronymic_name: Mapped[str] = mapped_column(
        String,
        nullable=True
    )
    hashed_password: Mapped[str] = mapped_column(
        String
    )
    disabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=True
    )
