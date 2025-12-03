from fastapi import FastAPI

from routers import bond_endpoints, update_endpoints, auth_endpoints

app = FastAPI(
    title="MOEX data service"
)

app.include_router(auth_endpoints.router)
app.include_router(bond_endpoints.router)
app.include_router(update_endpoints.router)


@app.get("/")
async def read_root():
    return {"message": "Welcome to MOEX data service"}
