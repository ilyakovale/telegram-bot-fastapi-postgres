from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def parse_date(val: Any) -> date | None:
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if not isinstance(val, str):
        return None
    clean = val.strip().split("T")[0].split(" ")[0]
    if not clean:
        return None
    for sep in (".", "-", "/"):
        if sep in clean:
            parts = clean.split(sep)
            if len(parts) == 3:
                try:
                    p0, p1, p2 = int(parts[0]), int(parts[1]), int(parts[2])
                    if len(parts[0]) == 4:
                        return date(p0, p1, p2)
                    elif len(parts[2]) == 4 or p2 > 31:
                        return date(p2, p1, p0)
                    else:
                        return date(p0, p1, p2)
                except ValueError:
                    pass
    return None


def _parse_date_input(v: Any) -> Any:
    parsed = parse_date(v)
    return parsed if parsed is not None else v


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

    @model_validator(mode="after")
    def validate_deadline(self) -> "OrderCreateRequest":
        if self.last_date_before_registration > self.date:
            raise ValueError("last_date_before_registration cannot be later than date")
        return self


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

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Product name cannot be empty")
        return clean


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
