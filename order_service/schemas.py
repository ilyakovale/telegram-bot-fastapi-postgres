from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrderCreateRequest(BaseModel):
    chat_id: int
    date: date
    last_date_before_registration: date
    products_max: list[Any] | dict[str, Any] = Field(default_factory=list)
    products_current: list[Any] | dict[str, Any] = Field(default_factory=list)


class OrderResponse(BaseModel):
    id: int
    chat_id: int
    date: date
    last_date_before_registration: date
    products_max: list[Any] | dict[str, Any]
    products_current: list[Any] | dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class OrderUserRequest(BaseModel):
    chat_id: int


class OrderIDRequest(BaseModel):
    order_id: int


class ProductCreateRequest(BaseModel):
    name: str
    unit: str = "шт"
    is_active: bool = True
    available_dates: list[Any] = Field(default_factory=list)


class ProductResponse(BaseModel):
    id: int
    name: str
    unit: str = "шт"
    is_active: bool = True
    available_dates: list[Any] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AvailableProductsRequest(BaseModel):
    order_date: str | date | None = None
    target_date: str | date | None = None
