from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class InventoryCreate(BaseModel):
    product_id: str
    initial_quantity: int = Field(ge=0)


class InventoryResponse(BaseModel):
    id: str
    product_id: str
    available_quantity: int
    reserved_quantity: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)