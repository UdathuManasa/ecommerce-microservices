from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

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
        return update_product(db, product_id, product_data)
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
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))