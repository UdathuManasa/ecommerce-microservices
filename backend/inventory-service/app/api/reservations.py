from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.reservation import (
    ReservationCreate,
    ReservationResponse,
)
from app.services.reservation_service import (
    reserve_stock,
    transition_reservation,
    InsufficientStockError,
    ReservationConflictError,
    ReservationNotFoundError,
    InvalidReservationStateError,
    InventoryConsistencyError,
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

@router.post(
    "/{reservation_id}/commit",
    response_model=ReservationResponse,
)
def commit_reservation(
    reservation_id: str,
    db: Session = Depends(get_db),
):
    try:
        return transition_reservation(
            db=db,
            reservation_id=reservation_id,
            target_status="COMMITTED",
        )

    except ReservationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except InvalidReservationStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    except InventoryConsistencyError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post(
    "/{reservation_id}/release",
    response_model=ReservationResponse,
)
def release_reservation(
    reservation_id: str,
    db: Session = Depends(get_db),
):
    try:
        return transition_reservation(
            db=db,
            reservation_id=reservation_id,
            target_status="RELEASED",
        )

    except ReservationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    except InvalidReservationStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    except InventoryConsistencyError as exc:
        raise HTTPException(status_code=409, detail=str(exc))