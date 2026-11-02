from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ReservationCreate(BaseModel):
    order_id: str
    product_id: str
    quantity: int = Field(gt=0)


class ReservationResponse(BaseModel):
    id: str
    order_id: str
    product_id: str
    quantity: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)