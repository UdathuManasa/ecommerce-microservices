from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.reservation import (
    ReservationCreate,
    ReservationResponse,
)
from app.services.reservation_service import (
    reserve_stock,
    InsufficientStockError,
    ReservationConflictError,
)

router = APIRouter(
    prefix="/api/v1/reservations",
    tags=["Reservations"],
)


@router.post(
    "",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
):
    try:
        return reserve_stock(
            db=db,
            order_id=payload.order_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
        )

    except InsufficientStockError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    except ReservationConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )