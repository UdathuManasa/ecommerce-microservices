from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.inventory import Inventory, InventoryReservation


class ReservationError(Exception):
    pass


class InsufficientStockError(ReservationError):
    pass


class ReservationConflictError(ReservationError):
    pass


def reserve_stock(
    db: Session,
    order_id: str,
    product_id: str,
    quantity: int,
):
    try:
        # 1. Check whether this order already has a reservation.
        existing = db.scalar(
            select(InventoryReservation).where(
                InventoryReservation.order_id == order_id,
                InventoryReservation.product_id == product_id,
            )
        )

        if existing:
            if existing.quantity != quantity:
                raise ReservationConflictError(
                    "An existing reservation has a different quantity"
                )

            # Idempotent retry: don't deduct stock again.
            return existing

        # 2. Atomically deduct available stock.
        result = db.execute(
            update(Inventory)
            .where(
                Inventory.product_id == product_id,
                Inventory.available_quantity >= quantity,
            )
            .values(
                available_quantity=Inventory.available_quantity - quantity,
                reserved_quantity=Inventory.reserved_quantity + quantity,
            )
        )

        if result.rowcount != 1:
            raise InsufficientStockError(
                "Product not found or insufficient stock"
            )

        # 3. Record the reservation.
        reservation = InventoryReservation(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            status="PENDING",
        )

        db.add(reservation)

        # 4. Stock update and reservation record commit together.
        db.commit()
        db.refresh(reservation)

        return reservation

    except IntegrityError:
        db.rollback()

        # Another concurrent request may have inserted the same
        # order/product reservation. Check whether it won the race.
        existing = db.scalar(
            select(InventoryReservation).where(
                InventoryReservation.order_id == order_id,
                InventoryReservation.product_id == product_id,
            )
        )

        if existing and existing.quantity == quantity:
            return existing

        raise ReservationConflictError(
            "Could not create reservation because of a conflict"
        )

    except Exception:
        db.rollback()
        raise