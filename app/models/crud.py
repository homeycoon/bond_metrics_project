from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from . import models, schemas


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


async def add_user(
        db: AsyncSession,
        user_to_db: schemas.UserToDB
):
    user = models.Users(**user_to_db.dict())
    db.add(user)
    await db.commit()


async def get_user(
        db: AsyncSession,
        username: str
):
    result = await db.execute(
        select(models.Users).where(models.Users.username == username)
    )
    user_info = result.scalars().first()
    if user_info:
        return user_info
    else:
        raise HTTPException(status_code=404, detail="User not found")
