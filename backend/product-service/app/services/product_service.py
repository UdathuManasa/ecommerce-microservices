from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductNotFoundError(Exception):
    pass


class DuplicateSKUError(Exception):
    pass


def create_product(db: Session, product_data: ProductCreate) -> Product:
    existing = db.scalar(
        select(Product).where(Product.sku == product_data.sku)
    )

    if existing:
        raise DuplicateSKUError("SKU already exists")

    product = Product(**product_data.model_dump())

    db.add(product)

    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise DuplicateSKUError("SKU already exists")

    return product


def get_product(db: Session, product_id: str) -> Product:
    product = db.get(Product, product_id)

    if not product:
        raise ProductNotFoundError("Product not found")

    return product


def update_product(
    db: Session,
    product_id: str,
    product_data: ProductUpdate
) -> Product:
    product = get_product(db, product_id)

    update_data = product_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(product, field, value)

    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise

    return product


def delete_product(db: Session, product_id: str) -> None:
    product = get_product(db, product_id)

    # Soft delete: retain historical product information.
    product.is_active = False

    db.commit()