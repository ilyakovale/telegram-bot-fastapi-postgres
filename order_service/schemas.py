from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _parse_date_input(v: Any) -> Any:
    if isinstance(v, str):
        clean = v.strip()
        if "." in clean:
            parts = clean.split(".")
            if len(parts) == 3:
                try:
                    return date(int(parts[2]), int(parts[1]), int(parts[0]))
                except ValueError:
                    pass
        elif "-" in clean:
            parts = clean.split("-")
            if len(parts) == 3:
                try:
                    return date(int(parts[0]), int(parts[1]), int(parts[2]))
                except ValueError:
                    pass
    return v


class OrderCreateRequest(BaseModel):
    chat_id: int
    date: date
    last_date_before_registration: date
    products_max: list[Any] | dict[str, Any] = Field(default_factory=list)
    products_current: list[Any] | dict[str, Any] = Field(default_factory=list)

    @field_validator("date", "last_date_before_registration", mode="before")
    @classmethod
    def validate_dates(cls, v: Any) -> Any:
        return _parse_date_input(v)


class OrderResponse(BaseModel):
    id: int
    chat_id: int
    date: date
    last_date_before_registration: date
    products_max: list[Any] | dict[str, Any]
    products_current: list[Any] | dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

    @field_validator("date", "last_date_before_registration", mode="before")
    @classmethod
    def validate_dates(cls, v: Any) -> Any:
        return _parse_date_input(v)


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
