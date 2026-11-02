from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi import Response
from app.db.database import get_db
from app.models.product import Product
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse
)
from app.services.product_service import (
    create_product,
    get_product,
    update_product,
    delete_product,
    ProductNotFoundError,
    DuplicateSKUError
)

from app.core.dependencies import get_current_user, require_admin

from decimal import Decimal
from fastapi import Query
from app.schemas.product import ProductListResponse
from app.services.product_service import list_products

from app.services.product_cache import (
    get_cached_product,
    cache_product,
    invalidate_product_cache
)

router = APIRouter(
    prefix="/api/v1/products",
    tags=["Products"]
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED
)
def create(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    try:
        return create_product(db, product_data)
    except DuplicateSKUError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{product_id}", response_model=ProductResponse)
def read(
    product_id: str,
    db: Session = Depends(get_db)
):
    try:
        product = get_product(db, product_id)

        if not product.is_active:
            raise ProductNotFoundError("Product not found")

        return product

    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{product_id}", response_model=ProductResponse)
def update(
    product_id: str,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    try:
        #return update_product(db, product_id, product_data)
        product = update_product(db, product_id, product_data)

        invalidate_product_cache(product_id)

        return product
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    product_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    try:
        delete_product(db, product_id)

        invalidate_product_cache(product_id)

        return Response(status_code=204)
        
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@router.get("", response_model=ProductListResponse)
def read_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: str | None = None,
    category: str | None = None,
    min_price: Decimal | None = Query(default=None, gt=0),
    max_price: Decimal | None = Query(default=None, gt=0),
    db: Session = Depends(get_db)
):
    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise HTTPException(
            status_code=400,
            detail="min_price cannot exceed max_price"
        )

    return list_products(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        category=category,
        min_price=min_price,
        max_price=max_price
    )


@router.get("/{product_id}", response_model=ProductResponse)
def read(
    product_id: str,
    db: Session = Depends(get_db)
):
    # 1. Check Redis first
    cached_product = get_cached_product(product_id)

    if cached_product is not None:
        if not cached_product.is_active:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        return cached_product

    # 2. Cache miss: query MySQL
    try:
        product = get_product(db, product_id)

        if not product.is_active:
            raise ProductNotFoundError("Product not found")

        # 3. Save result in Redis
        cache_product(product)

        return product

    except ProductNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        )