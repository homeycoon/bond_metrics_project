import asyncio

from models.database import get_db
from models import crud
from utils.loading_to_db import load_currency_to_db, load_bonds_to_db


async def init_data_load():
    async for db in get_db():
        async with db:
            await crud.delete_currencies(db=db)
            await crud.delete_bonds(db=db)
            await load_currency_to_db(db=db)
            await load_bonds_to_db(db=db)

if __name__ == '__main__':
    asyncio.run(init_data_load())
