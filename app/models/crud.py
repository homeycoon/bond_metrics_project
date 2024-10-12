from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from . import models, schemas


async def get_bonds(db: AsyncSession):
    result = await db.execute(
        select(
            models.Bond
        )
    )
    bonds = result.scalars().all()
    return bonds


async def get_bond_info_by_ticker(
        db: AsyncSession,
        ticker: str
):
    result = await db.execute(
        select(models.Bond).where(models.Bond.ticker == ticker)
    )
    bond_info = result.scalars().first()
    if bond_info:
        return bond_info
    else:
        raise HTTPException(status_code=404, detail="Ticker not found")


# async def get_bond_metrics_by_ticker(
#         db: AsyncSession,
#         ticker: schemas.Tickers
# ):
#     result = await db.execute(
#         select(models.Bond.id, models.Bond.ticker, models.Bond.name, models.Metric)
#         .join(models.Metric, models.Bond.id == models.Metric.bond_id)
#         .where(models.Bond.ticker == ticker)
#     )
#     bond_data = result.all()
#     if bond_data:
#         bond_id, bond_ticker, bond_name, metric_object = bond_data[0]
#         metric_dict = {
#             "fair_value_rub": metric_object.fair_value_rub,
#             "yield_to_maturity_rub": metric_object.yield_to_maturity_rub,
#             "duration": metric_object.duration,
#             "modified_duration": metric_object.modified_duration,
#             "credit_spread_rub": metric_object.credit_spread_rub,
#             "current_yield_rub": metric_object.current_yield_rub,
#             "calculated_date": metric_object.calculated_date
#         }
#         return {
#             "id": bond_id,
#             "ticker": bond_ticker,
#             "name": bond_name,
#             **metric_dict
#         }
#     else:
#         raise HTTPException(status_code=404, detail='Ticker not found')
