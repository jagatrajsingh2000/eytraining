from enum import Enum

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class OrderBase(BaseModel):
    customer_name: str = Field(..., min_length=1, examples=["Ananya Sharma"])
    product_name: str = Field(..., min_length=1, examples=["Wireless Mouse"])
    quantity: int = Field(..., gt=0, examples=[2])
    price: float = Field(..., gt=0, examples=[1499.99])
    status: OrderStatus = Field(default=OrderStatus.pending)


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    customer_name: str | None = Field(default=None, min_length=1)
    product_name: str | None = Field(default=None, min_length=1)
    quantity: int | None = Field(default=None, gt=0)
    price: float | None = Field(default=None, gt=0)
    status: OrderStatus | None = None


class OrderResponse(OrderBase):
    id: int
