from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.schemas.category import CategorySummary

class ProductCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=5, max_length=2048)
    image: str | None = Field(default=None, max_length=2048)
    sku: str = Field(min_length=1, max_length=255)
    price: Decimal = Field(gt=0, decimal_places=2, max_digits=10)
    category_id: int = Field(gt=0)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be blank")
        if len(v) < 3:
            raise ValueError("Title must be at least 3 characters")
        return v

    @model_validator(mode="after")
    def description_required_for_expensive_items(self):
        if self.price > Decimal("100") and not self.description:
            raise ValueError("Description required for products over 100")
        return self

class ProductUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=5, max_length=2048)
    image: str | None = Field(default=None, max_length=2048)
    sku: str | None = Field(default=None, min_length=1, max_length=255)
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2, max_digits=10)
    category_id: int | None = Field(default=None, gt=0)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be blank")
        if len(v) < 3:
            raise ValueError("Title must be at least 3 characters")
        return v

    @model_validator(mode="after")
    def description_required_for_expensive_items(self):
        if "price" not in self.model_fields_set:
            return self
        if self.price is None or self.price <= Decimal("100"):
            return self
        if "description" in self.model_fields_set and not self.description:
            raise ValueError("Description required for products over 100")
        return self

class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    image: str | None
    sku: str
    price: Decimal
    category_id: int
    category: CategorySummary


class ProductSearchParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=255)
    sku: str | None = Field(default=None, min_length=1, max_length=255)
    min_price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    max_price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    category_id: int | None = Field(default=None, gt=0)
    sort_by: Literal["title", "price", "sku"] = "title"
    sort_order: Literal["asc", "desc"] = "asc"
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_price_range(self):
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("min_price cannot be greater than max_price")
        return self
