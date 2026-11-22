# changes done by vb
from pydantic import BaseModel, Field


class AddressCreate(BaseModel):
    address: str = Field(..., min_length=5, max_length=1000)


class PlaceOrderItem(BaseModel):
    hardware_id: int
    quantity: int = Field(..., ge=1)


class PlaceOrderRequest(BaseModel):
    address_id: int
    items: list[PlaceOrderItem] = Field(..., min_length=1)
