from fastapi import FastAPI

from routers import bond_endpoints


app = FastAPI(
    title="MOEX data service"
)

app.include_router(bond_endpoints.router)


@app.get("/")
async def read_root():
    return {"message": "Welcome to MOEX data service"}
