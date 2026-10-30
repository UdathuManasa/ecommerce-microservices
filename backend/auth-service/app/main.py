
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db

app = FastAPI(
    title="E-Commerce Auth Service",
    description="Authentication and User Management",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "E-Commerce Auth Service is running"
    }


@app.get("/health/db")
def database_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))

        return {
            "database": "connected",
            "status": "healthy"
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"+str(e)
        )
