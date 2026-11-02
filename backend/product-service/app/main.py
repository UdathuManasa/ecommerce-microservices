from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.redis_client import check_redis_connection


from app.db.database import get_db
from app.api.products import router as products_router

app = FastAPI(
    title="E-Commerce Product Service",
    description="Product catalog microservice",
    version="1.0.0"
)

app.include_router(products_router)


@app.get("/")
def root():
    return {
        "service": "Product Service",
        "status": "running"
    }


@app.get("/health/db")
def database_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}


@app.get("/health/redis")
def redis_health():
    if not check_redis_connection():
        return {
            "redis": "disconnected"
        }

    return {
        "redis": "connected"
    }