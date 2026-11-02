import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Integer,
    String,
    DateTime,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def utc_now():
    # Store UTC timestamps as naive DATETIME values in MySQL.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Inventory(Base):
    __tablename__ = "inventory"

    __table_args__ = (
        CheckConstraint(
            "available_quantity >= 0",
            name="ck_inventory_available_nonnegative",
        ),
        CheckConstraint(
            "reserved_quantity >= 0",
            name="ck_inventory_reserved_nonnegative",
        ),
        Index("ix_inventory_product_id", "product_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Product ID comes from Product Service.
    # No cross-service foreign key.
    product_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
    )

    available_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    reserved_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class InventoryReservation(Base):
    __tablename__ = "inventory_reservations"

    __table_args__ = (
        UniqueConstraint(
            "order_id",
            "product_id",
            name="uq_reservation_order_product",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_reservation_quantity_positive",
        ),
        Index("ix_reservation_order_id", "order_id"),
        Index("ix_reservation_product_id", "product_id"),
        Index("ix_reservation_status", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    order_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
    )

    product_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # PENDING -> COMMITTED or RELEASED
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )