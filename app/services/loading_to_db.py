from sqlalchemy import selectfrom sqlalchemy.ext.asyncio import AsyncSessionfrom models import schemas, modelsfrom services.APIs import load_bond_data, load_currency_data# Функция для загрузки данных по валютам в БД (по расписанию)async def load_currency_to_db(db: AsyncSession):    currency_data = await load_currency_data()    for currency_dict in currency_data:        curr_df = schemas.Currency(**currency_dict)        db_currencies = models.Currency(**curr_df.dict())        db.add(db_currencies)        await db.commit()# Функция для загрузки данных по облигациям в БД (по расписанию)async def load_bonds_to_db(db: AsyncSession):    result = await db.execute(        select(            models.Currency.currency_code,            models.Currency.curs            )        )    data = [row for row in result]    curr_dict = dict(data)    bonds_data = await load_bond_data(curr_dict=curr_dict)    for bond_dict in bonds_data:        bond_df = schemas.BondInfo(**bond_dict)        db_bonds = models.Bond(**bond_df.dict())        db.add(db_bonds)        await db.commit()