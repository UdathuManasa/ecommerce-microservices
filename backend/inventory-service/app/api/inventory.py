from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.schemas.inventory import InventoryCreate, InventoryResponse
from app.services.inventory_service import (
    initialize_inventory,
    get_inventory,
)

router = APIRouter(
    prefix="/api/v1/inventory",
    tags=["Inventory"],
)


@router.post(
    "",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_inventory(
    payload: InventoryCreate,
    db: Session = Depends(get_db),
):
    try:
        return initialize_inventory(
            db=db,
            product_id=payload.product_id,
            initial_quantity=payload.initial_quantity,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inventory already exists for this product",
        )


@router.get(
    "/{product_id}",
    response_model=InventoryResponse,
)
def read_inventory(
    product_id: str,
    db: Session = Depends(get_db),
):
    inventory = get_inventory(db, product_id)

    if inventory is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory not found for this product",
        )

    return inventory