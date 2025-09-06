from datetime import datetime
from decimal import Decimal

from scipy.optimize import fsolve

from models import schemas


def without_coupons_metrics(r: float, bond_info: schemas.BondInfo) -> tuple:
    """
    Функция для расчета текущей доходности,
    доходности к погашению, справедливой стоимости
    бескупонной облигации

    :param r: ставка дисконтирования (в процентах)
    :param bond_info: объект класса BondInfo (информация по облигации)
    :return: кортеж с рассчитанными метриками облигации
    """

    # Текущая доходность облигации равна 0, т.к. облигация бескупонная
    current_yield = 0.0000

    # Функция расчета справедливой стоимости бескупонной облигации
    def evaluate_fair_value_zero_coupon(rate: float, bond_info: schemas.BondInfo):
        time_to_maturity_days = (bond_info.maturity_date - bond_info.loading_date).days
        time_to_maturity_years = time_to_maturity_days / 365
        fair_value = round(bond_info.nominal_rub / Decimal((1 + rate / 100) ** time_to_maturity_years), 4)
        return fair_value

    # Функция для построения модели разницы между справедливой стоимостью
    # и средневзвешенной ценой облигации (используется для расчета ytm)
    def f(x, bond_info: schemas.BondInfo):
        fair_value = evaluate_fair_value_zero_coupon(x[0], bond_info)
        return [fair_value - bond_info.prevwaprice_rub]

    # Считаем доходность к погашению
    ytm = fsolve(f, [0.05], bond_info)
    round_ytm = round(Decimal(ytm[0]), 4)

    # Считаем справедливую стоимость облигации на основе ставки дисконтирования r
    fair_value = evaluate_fair_value_zero_coupon(r, bond_info)

    return current_yield, round_ytm, fair_value


def one_coupon_metrics(r: float, bond_info: schemas.BondInfo) -> tuple:
    """
    Функция для расчета текущей доходности,
    доходности к погашению, справедливой стоимости
    облигации с одним купоном в конце срока погашения

    :param r: ставка дисконтирования (в процентах)
    :param bond_info: объект класса BondInfo (информация по облигации)
    :return: кортеж с рассчитанными метриками облигации
    """

    # Считаем текущую доходность
    current_yield = round((bond_info.coupon_value_rub * Decimal((365 / bond_info.coupon_period)))
                          / bond_info.prevwaprice_rub * 100, 4)

    # Функция расчета справедливой стоимости облигации с 1 купоном в конце срока погашения
    def evaluate_fair_value_one_coupon(rate, bond_info: schemas.BondInfo):
        time_to_maturity_days = (bond_info.maturity_date - bond_info.loading_date).days
        time_to_maturity_years = time_to_maturity_days / 365
        fair_value_nominal = bond_info.nominal_rub / Decimal((1 + rate / 100) ** time_to_maturity_years)
        fair_value_coupon = bond_info.coupon_value_rub / Decimal((1 + rate / 100) ** time_to_maturity_years)
        fair_value = round(fair_value_nominal + fair_value_coupon, 4)
        return fair_value

    # Функция для построения модели разницы между справедливой стоимостью
    # и средневзвешенной ценой облигации (используется для расчета ytm)
    def f(x, bond_info: schemas.BondInfo):
        fair_value = evaluate_fair_value_one_coupon(x[0], bond_info)
        return [fair_value - bond_info.prevwaprice_rub]

    # Считаем доходность к погашению
    ytm = fsolve(f, [0.05], bond_info)
    round_ytm = round(Decimal(ytm[0]), 4)

    # Считаем справедливую стоимость облигации
    fair_value = evaluate_fair_value_one_coupon(r, bond_info)

    return current_yield, round_ytm, fair_value


def several_coupons_metrics(r: float, bond_info: schemas.BondInfo) -> tuple:
    """
    Функция для расчета текущей доходности,
    доходности к погашению, справедливой стоимости
    облигации с несколькими купонами в конце срока погашения

    :param r: ставка дисконтирования (в процентах)
    :param bond_info: объект класса BondInfo (информация по облигации)
    :return: кортеж с рассчитанными метриками облигации
    """

    # Считаем текущую доходность
    current_yield = round((bond_info.coupon_value_rub * Decimal((365 / bond_info.coupon_period)))
                          / bond_info.prevwaprice_rub * 100, 4)

    # Функция расчета справедливой стоимости облигации с несколькими купонами
    def evaluate_fair_value_many_coupons(rate, bond_info: schemas.BondInfo):
        # Считаем справедливую стоимость номинала
        time_to_maturity_days = (bond_info.maturity_date - bond_info.loading_date).days
        time_to_maturity_years = time_to_maturity_days / 365
        fair_value_nominal = bond_info.nominal_rub / Decimal((1 + rate / 100) ** time_to_maturity_years)

        # Считаем справедливую стоимость ближайшего купона
        time_to_next_coupon_days = (bond_info.next_coupon_date - bond_info.loading_date).days
        time_to_next_coupon_years = time_to_next_coupon_days / 365
        fair_value_coupon = (bond_info.coupon_value_rub /
                             Decimal((1 + rate / 100) ** time_to_next_coupon_years))

        # Считаем справедливую стоимость остальных купонов
        next_date = bond_info.next_coupon_date + datetime.timedelta(bond_info.coupon_period)
        other_coupons_value = 0
        while next_date <= bond_info.maturity_date:
            time_to_next_other_coupon_days = (next_date - bond_info.loading_date).days
            time_to_next_other_coupon_years = time_to_next_other_coupon_days / 365
            fair_value_other_coupon = (bond_info.coupon_value_rub /
                                       Decimal((1 + rate / 100) ** time_to_next_other_coupon_years))
            other_coupons_value += fair_value_other_coupon
            next_date += datetime.timedelta(bond_info.coupon_period)

        # Считаем общую справедливую стоимость
        fair_value = round(fair_value_nominal + fair_value_coupon + other_coupons_value, 4)
        return fair_value

    # Функция для построения модели разницы между справедливой стоимостью
    # и средневзвешенной ценой облигации (используется для расчета ytm)
    def f(x, bond_info: schemas.BondInfo):
        fair_value = evaluate_fair_value_many_coupons(x[0], bond_info)
        return [fair_value - bond_info.prevwaprice_rub]

    # Считаем доходность к погашению
    ytm = fsolve(f, [0.05], bond_info)
    round_ytm = round(Decimal(ytm[0]), 4)

    # Считаем справедливую стоимость
    fair_value = evaluate_fair_value_many_coupons(r, bond_info)

    return current_yield, round_ytm, fair_value
