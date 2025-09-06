from typing import Sequence

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from models import schemas, crud
from models.database import get_db
from models.models import Bond
from utils.MOEX_gateway import MOEXGateway, NotEnoughObservations

from utils.evaluating_bond_metrics import (without_coupons_metrics, one_coupon_metrics,
                                           several_coupons_metrics)

router = APIRouter(
    prefix="/bonds",
    tags=["bonds"]
)


# Метод для получения списка доступных тикеров и названий облигаций
@router.get("/",
            response_model=list[schemas.TickerBase],
            name="Получение тикеров и названий всех облигаций")
async def get_all_bonds(db: AsyncSession = Depends(get_db)) -> Sequence[Bond]:
    bonds = await crud.get_bonds(db=db)
    return bonds


# Метод для получения основной информации об облигации по ее тикеру
@router.get("/{ticker}/info",
            response_model=schemas.BondInfo,
            name="Получение инфо об облигации по ее тикеру")
async def get_bond_info(
        ticker: str,
        db: AsyncSession = Depends(get_db)
) -> Bond:
    """
    Предупреждение! Информация о размере купона не гарантирует,
    что данный купон остается неизменным до погашения облигации,
    т.к. купон может быть переменным.
    """
    bond_info = await crud.get_bond_info_by_ticker(db=db, ticker=ticker)
    return bond_info


@router.get("/{ticker}/metrics",
            response_model=schemas.BondMetrics,
            name="Получение рассчитанных метрик облигации по ее тикеру")
async def get_bond_metrics(
        ticker: str,
        r: float = Query(..., gt=1, lt=50,
                         description="Ставка дисконтирования/желаемая доходность (в процентах)",
                         alias="r"),
        db: AsyncSession = Depends(get_db)
) -> schemas.BondMetrics:
    """
    Функция для получения рассчитанных метрик облигации по ее тикеру

    Предупреждение! При расчете метрик не учитывается возможность того,
    что облигации могут иметь переменный купон, т.к. Московская биржа
    не предоставляет соответствующую информацию через свой MOEX ISS.
    Потому все расчеты основаны на допущении, что размер купона и частота
    его выплаты остаются неизменными до погашения облигации.

    :param ticker: тикер облигации
    :param r: ставка дисконтирования (в процентах)
    :param db: объект подключения к БД
    :return: объект класса BondMetrics (метрики облигации)
    """

    bond_info = await crud.get_bond_info_by_ticker(db=db, ticker=ticker)

    if bond_info.prevwaprice_rub is None:
        raise HTTPException(status_code=422, detail='Недостаточно данных для расчетов '
                                                    '(отсутствует средневзвешенная цена '
                                                    'предыдущей торговой сессии)')

    # Если облигация бескупонная
    if bond_info.coupon_value_rub == 0:
        current_yield, round_ytm, fair_value = without_coupons_metrics(r, bond_info)

    # Если дата ближайшего купона совпадает с датой погашения
    # (то есть будет выплачен 1 купон одновременно с номиналом)
    elif bond_info.next_coupon_date == bond_info.maturity_date:
        current_yield, round_ytm, fair_value = one_coupon_metrics(r, bond_info)

    else:
        current_yield, round_ytm, fair_value = several_coupons_metrics(r, bond_info)

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


@router.get("/correlation",
            response_model=schemas.BondsCorrelation,
            name="Получение корреляции между облигациями")
async def get_bonds_corr(
        ticker_1: str = Query(..., description="Тикер первой облигации"),
        ticker_2: str = Query(..., description="Тикер второй облигации"),
        db: AsyncSession = Depends(get_db)
) -> schemas.BondsCorrelation:
    """
    Функция для получения данных о корреляции между двумя облигациями по их тикерам.
    В ответе выдается 4 разных коэффициента корреляции. При этом на основе
    проверок на нормальность и на наличие выбросов формулируется рекомендация о том,
    на какой из коэффициентов лучше ориентироваться в данной паре облигаций.

    :param ticker_1: тикер первой облигации
    :param ticker_2: тикер второй облигации
    :param db: объект подключения к БД
    :return: объект класса BondsCorrelation
            (данные о корреляции между двумя облигациями)
    """

    bond_1_info = await crud.get_bond_info_by_ticker(db=db, ticker=ticker_1)
    bond_2_info = await crud.get_bond_info_by_ticker(db=db, ticker=ticker_2)

    moex = MOEXGateway()

    try:
        corr_dict = await moex.load_hist_bond_data(ticker_1, ticker_2)
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
