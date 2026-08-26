from decimal import Decimal
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

    @field_validator("price")
    @classmethod
    def price_must_have_two_decimal_places_max(cls, v: Decimal) -> Decimal:
        if v.as_tuple().exponent < -2:
            raise ValueError("Price must have at most 2 decimal places")
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

    @field_validator("price")
    @classmethod
    def price_must_have_two_decimal_places_max(cls, v: Decimal | None) -> Decimal | None:
        if v is None:
            return v
        if v.as_tuple().exponent < -2:
            raise ValueError("Price must have at most 2 decimal places")
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