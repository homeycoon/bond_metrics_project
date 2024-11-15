from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from models import crud
from models.database import get_db
from services.loading_to_db import load_currency_to_db, load_bonds_to_db

router = APIRouter(
    prefix="/update",
    tags=["update"]
)


# Метод для первичной загрузки данных по валютам в БД
@router.get("/currencies")
async def update_all_currencies(db: AsyncSession = Depends(get_db)):
    await crud.delete_currencies(db=db)
    await load_currency_to_db(db=db)
    return {"message": "Данные по валютам успешно загружены"}


# Метод для первичной загрузки данных по облигациям в БД
@router.get("/bonds")
async def update_all_bonds(db: AsyncSession = Depends(get_db)):
    await crud.delete_bonds(db=db)
    await load_bonds_to_db(db=db)
    return {"message": "Данные по облигациям успешно загружены"}
