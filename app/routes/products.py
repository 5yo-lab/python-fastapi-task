from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductRead

router = APIRouter(prefix="/api/v1/products", tags=["products"])


def _load_product(db: Session, product_id: int) -> Product | None:
    stmt = (
        select(Product)
        .where(Product.id == product_id)
        .options(joinedload(Product.category))
    )
    return db.scalars(stmt).first()

def _load_products_with_categories(db: Session) -> list[Product]:
    stmt = select(Product).options(joinedload(Product.category)).order_by(Product.title)
    return db.scalars(stmt).unique().all()

def _validate_category(db: Session, category_id: int) -> None:
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found",
        )

def _validate_expensive_product_description(
    price: Decimal,
    description: str | None,
) -> None:
    if price > Decimal("100") and not description:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description required for expensive products over 100 in price",
        )

@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    _validate_category(db, data.category_id)

    product = Product(**data.model_dump())
    db.add(product)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product with this SKU already exists",
        )

    db.refresh(product)
    loaded = _load_product(db, product.id)
    return loaded

@router.get("/search", response_model=list[ProductRead])
def search_products(db: Session = Depends(get_db)):
    return []

@router.get("/", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db)):
    return _load_products_with_categories(db)

@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = _load_product(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product

@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    updates = data.model_dump(exclude_unset=True)

    if "category_id" in updates and updates["category_id"] is not None:
        _validate_category(db, updates["category_id"])

    final_price = updates.get("price", product.price)
    if "description" in updates:
        final_description = updates["description"]
    else:
        final_description = product.description
    _validate_expensive_product_description(final_price, final_description)

    for field, value in updates.items():
        setattr(product, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product with this SKU already exists",
        )

    loaded = _load_product(db, product_id)
    return loaded

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    db.delete(product)
    db.commit()