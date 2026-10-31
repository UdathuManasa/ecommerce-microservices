from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    sku: str = Field(min_length=3, max_length=64)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category: str = Field(min_length=2, max_length=100)

    @field_validator("name", "sku", "category")
    @classmethod
    def normalize_strings(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty")
        return value

    @field_validator("sku")
    @classmethod
    def normalize_sku(cls, value: str) -> str:
        return value.upper()


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=12,
        decimal_places=2
    )
    category: str | None = Field(default=None, min_length=2, max_length=100)
    is_active: bool | None = None

    @field_validator("name", "category")
    @classmethod
    def normalize_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Field cannot be empty")
        return value


class ProductResponse(BaseModel):
    id: str
    name: str
    description: str | None
    sku: str
    price: Decimal
    category: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)