from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from . import models


async def delete_currencies(db: AsyncSession):
    await db.execute(
        delete(
            models.Currency
        )
    )
    await db.commit()


async def delete_bonds(db: AsyncSession):
    await db.execute(
        delete(
            models.Bond
        )
    )
    await db.commit()


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
