import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, HTTPException
from scipy.optimize import fsolve
from sqlalchemy.ext.asyncio import AsyncSession

from models import schemas, crud
from models.database import get_db
from services.APIs import load_hist_bond_data, NotEnoughObservations

router = APIRouter(
    prefix="/bonds",
    tags=["bonds"]
)


# Метод для получения списка доступных тикеров и названий облигаций
@router.get("/", response_model=list[schemas.TickerBase], name="Получение тикеров и названий всех облигаций")
async def get_all_bonds(db: AsyncSession = Depends(get_db)):
    bonds = await crud.get_bonds(db=db)
    return bonds


# Метод для получения основной информации об облигации по ее тикеру
@router.get("/{ticker}/info", response_model=schemas.BondInfo, name="Получение инфо об облигации по ее тикеру")
async def get_bond_info(
        ticker: str,
        db: AsyncSession = Depends(get_db)
):
    """
    Предупреждение! Информация о размере купона не гарантирует,
    что данный купон остается неизменным до погашения облигации,
    т.к. купон может быть переменным.
    """
    bond_info = await crud.get_bond_info_by_ticker(db=db, ticker=ticker)
    return bond_info


# Метод для получения рассчитанных метрик облигации по ее тикеру
@router.get("/{ticker}/metrics",
            response_model=schemas.BondMetrics,
            name="Получение рассчитанных метрик облигации по ее тикеру")
async def get_bond_metrics(
        ticker: str,
        r: float = Query(..., gt=1, lt=50,
                         description="Ставка дисконтирования/желаемая доходность (в процентах)",
                         alias="r"),
        db: AsyncSession = Depends(get_db)
):
    """
    Предупреждение! При расчете метрик не учитывается возможность того,
    что облигации могут иметь переменный купон, т.к. Московская биржа
    не предоставляет соответствующую информацию через свой MOEX ISS.
    Потому все расчеты основаны на допущении, что размер купона и частота
    его выплаты остаются неизменными до погашения облигации.
    """
    bond_info = await crud.get_bond_info_by_ticker(db=db, ticker=ticker)

    if bond_info.prevwaprice_rub is None:
        raise HTTPException(status_code=422, detail='Недостаточно данных для расчетов '
                                                    '(отсутствует средневзвешенная цена '
                                                    'предыдущей торговой сессии)')

    # Если облигация бескупонная
    if bond_info.coupon_value_rub == 0:
        # Текущая доходность облигации равна 0, т.к. облигация бескупонная
        current_yield = 0.0000

        # Функция расчета справедливой стоимости бескупонной облигации
        def evaluate_fair_value_zero_coupon(rate, bond_info: schemas.BondInfo):
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

    # Если дата ближайшего купона совпадает с датой погашения (то есть будет выплачен 1 купон одновременно с номиналом)
    elif bond_info.next_coupon_date == bond_info.maturity_date:
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

    else:
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

    # Формируем вывод о сравнении справедливой стоимости облигации и ее средневзвешенной цены
    if fair_value > bond_info.prevwaprice_rub:
        conclusion = "Справедливая стоимость превышает средневзвешенную цену. Облигация может быть недооценена. "
    elif fair_value == bond_info.prevwaprice_rub:
        conclusion = ("Справедливая стоимость равна средневзвешенной цене. "
                      "Облигация торгуется близко к своей справедливой стоимости. ")
    else:
        conclusion = "Справедливая стоимость меньше средневзвешенной цены. Облигация может быть переоценена. "

    # Формируем вывод о сравнении ставки дисконтирования и доходности к погашению
    if round_ytm > r:
        conclusion += (f"Доходность к погашению {round_ytm:.2f}% может быть привлекательна для Вас,"
                       f"так как превышает введенную ставку дисконтирования {r:.2f}%.")
    elif round_ytm == r:
        conclusion += (f"Доходность к погашению {round_ytm:.2f}% соответствует введенной ставке"
                       f"дисконтирования {r:.2f}%.")
    else:
        conclusion += (f"Доходность к погашению {round_ytm:.2f}% ниже введенной ставки дисконтирования, "
                       f"потому может быть не привлекательной для Вас.")

    conclusion += " ВАЖНО: не является индивидуальной инвестиционной рекомендацией (ИИР)"

    # Формируем итоговый ответ
    bond_metrics = schemas.BondMetrics(
        ticker=bond_info.ticker,
        name=bond_info.name,
        current_yield=current_yield,
        ytm_prct=round_ytm,
        fair_value=fair_value,
        conclusion=conclusion
    )

    return bond_metrics


# Метод для получения данных о корреляции между двумя облигациями по их тикерам
@router.get("/correlation", response_model=schemas.BondsCorrelation, name="Получение корреляции между облигациями")
async def get_bonds_corr(
        ticker_1: str = Query(..., description="Тикер первой облигации"),
        ticker_2: str = Query(..., description="Тикер второй облигации"),
        db: AsyncSession = Depends(get_db)
):
    """
    Метод для получения данных о корреляции между двумя облигациями по их тикерам.
    В ответе выдается 4 разных коэффициента корреляции. При этом на основе
    проверок на нормальность и на наличие выбросов формулируется рекомендация о том,
    на какой из коэффициентов лучше ориентироваться в данной паре облигаций.
    """

    bond_1_info = await crud.get_bond_info_by_ticker(db=db, ticker=ticker_1)
    bond_2_info = await crud.get_bond_info_by_ticker(db=db, ticker=ticker_2)

    try:
        corr_dict = await load_hist_bond_data(ticker_1, ticker_2)
    except NotEnoughObservations as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail=f'Ошибка при расчете корреляции')

    corr_info = schemas.BondsCorrelation(
        ticker_1=bond_1_info.ticker,
        name_1=bond_1_info.name,
        ticker_2=bond_2_info.ticker,
        name_2=bond_2_info.name,
        Pearson_correlation=corr_dict['corr_p'],
        Spearman_correlation=corr_dict['corr_s'],
        Kendall_correlation=corr_dict['corr_k'],
        Robust_correlation=corr_dict['rob_corr'],
        Advice=corr_dict['advice']
    )

    return corr_info
