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

class ReservationNotFoundError(ReservationError):
    pass


class InvalidReservationStateError(ReservationError):
    pass


class InventoryConsistencyError(ReservationError):
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

def transition_reservation(
    db: Session,
    reservation_id: str,
    target_status: str,
):
    if target_status not in ("COMMITTED", "RELEASED"):
        raise ValueError("Invalid target status")

    try:
        # Lock the reservation row so concurrent commit/release
        # requests for this reservation cannot process it together.
        reservation = db.scalar(
            select(InventoryReservation)
            .where(InventoryReservation.id == reservation_id)
            .with_for_update()
        )

        if reservation is None:
            raise ReservationNotFoundError("Reservation not found")

        # Repeated identical operation: return without changing stock.
        if reservation.status == target_status:
            return reservation

        if reservation.status != "PENDING":
            raise InvalidReservationStateError(
                f"Cannot change {reservation.status} reservation "
                f"to {target_status}"
            )

        # Lock the corresponding inventory row as well.
        inventory = db.scalar(
            select(Inventory)
            .where(Inventory.product_id == reservation.product_id)
            .with_for_update()
        )

        if inventory is None:
            raise InventoryConsistencyError(
                "Inventory record not found for reservation"
            )

        if inventory.reserved_quantity < reservation.quantity:
            raise InventoryConsistencyError(
                "Reserved quantity is inconsistent"
            )

        if target_status == "COMMITTED":
            # Payment succeeded. Stock is sold.
            inventory.reserved_quantity -= reservation.quantity

        else:
            # Payment failed/cancelled. Return stock.
            inventory.reserved_quantity -= reservation.quantity
            inventory.available_quantity += reservation.quantity

        reservation.status = target_status

        db.commit()
        db.refresh(reservation)

        return reservation

    except Exception:
        db.rollback()
        raise