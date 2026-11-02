from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory


def initialize_inventory(
    db: Session,
    product_id: str,
    initial_quantity: int,
):
    existing = db.scalar(
        select(Inventory).where(
            Inventory.product_id == product_id
        )
    )

    if existing:
        raise ValueError("Inventory already exists for this product")

    inventory = Inventory(
        product_id=product_id,
        available_quantity=initial_quantity,
        reserved_quantity=0,
    )

    db.add(inventory)
    db.commit()
    db.refresh(inventory)

    return inventory


def get_inventory(db: Session, product_id: str):
    return db.scalar(
        select(Inventory).where(
            Inventory.product_id == product_id
        )
    )