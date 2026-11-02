from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func, or_

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from decimal import Decimal



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

def list_products(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
    category: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None
):
    query = select(Product).where(Product.is_active.is_(True))

    # Search by product name or SKU
    if search:
        search_term = f"%{search.strip()}%"

        query = query.where(
            or_(
                Product.name.ilike(search_term),
                Product.sku.ilike(search_term)
            )
        )

    # Category filter
    if category:
        query = query.where(
            Product.category.ilike(category.strip())
        )

    # Price filters
    if min_price is not None:
        query = query.where(Product.price >= min_price)

    if max_price is not None:
        query = query.where(Product.price <= max_price)

    # Count matching products before pagination
    count_query = select(func.count()).select_from(
        query.order_by(None).subquery()
    )

    total = db.scalar(count_query)

    # Fetch only the requested page
    products = db.scalars(
        query
        .order_by(Product.created_at.desc(), Product.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    total_pages = (total + page_size - 1) // page_size

    return {
        "items": products,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }