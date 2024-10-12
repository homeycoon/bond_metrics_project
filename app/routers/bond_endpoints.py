from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from models import schemas, crud
from models.database import get_db

router = APIRouter(
    prefix="/bonds",
    tags=["bonds"]
)


@router.get("/", response_model=list[schemas.TickerOut])
async def get_all_bonds(db: AsyncSession = Depends(get_db)):
    bonds = await crud.get_bonds(db=db)
    return bonds


@router.get("/{ticker}/info", response_model=schemas.BondInfo)
async def get_bond_info(
        ticker: str,
        db: AsyncSession = Depends(get_db)
):
    bond_info = await crud.get_bond_info_by_ticker(db=db, ticker=ticker)
    return bond_info


# @router.get("/{ticker}/metrics", response_model=schemas.BondMetrics)
# async def get_bond_metrics(
#         ticker: str,
#         db: AsyncSession = Depends(get_db)
# ):
#     bond_metrics = await crud.get_bond_metrics_by_ticker(db=db, ticker=ticker)
#     return bond_metrics
