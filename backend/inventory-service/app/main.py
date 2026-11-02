from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.inventory import router as inventory_router
from app.api.reservations import router as reservations_router


app = FastAPI(
    title="E-Commerce Inventory Service",
    description="Inventory and stock reservation microservice",
    version="1.0.0",
)


app.include_router(reservations_router)
app.include_router(inventory_router)


@app.get("/")
def root():
    return {
        "service": "Inventory Service",
        "status": "running",
    }


@app.get("/health/db")
def database_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}