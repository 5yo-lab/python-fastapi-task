from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryRead,
    CategorySummary,
)

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


def _load_category(db: Session, category_id: int) -> Category | None:
    stmt = (
        select(Category)
        .where(Category.id == category_id)
        .options(
            joinedload(Category.parent),
            joinedload(Category.children),
        )
    )
    return db.scalars(stmt).unique().first()

def _validate_parent(db: Session, parent_id: int | None, category_id: int | None = None) -> None:
    if parent_id is None:
        return
    
    if category_id is not None and parent_id == category_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category cannot be its own parent",
        )
    
    parent = db.get(Category, parent_id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parent category not found",
        )
    
    current_id = parent_id
    visited: set[int] = set()
    while current_id is not None:
        if current_id in visited:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Circular parent chain not allowed",
            )
        visited.add(current_id)

        if current_id == category_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Circular parent chain not allowed")
        
        current_category = db.get(Category, current_id)
        current_id = current_category.parent_id if current_category else None

@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    _validate_parent(db, data.parent_id)

    category = Category(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)

    loaded = _load_category(db, category.id)
    return loaded

@router.get("/", response_model=list[CategorySummary])
def list_categories(db: Session = Depends(get_db)):
    return db.scalars(select(Category).order_by(Category.name)).all()

@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = _load_category(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    return category

@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
):
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    updates = data.model_dump(exclude_unset=True)

    if "parent_id" in updates:
        _validate_parent(db, updates["parent_id"], category_id=category_id)

    for field, value in updates.items():
        setattr(category, field, value)

    db.commit()

    loaded = _load_category(db, category_id)
    return loaded

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    if category.children:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with child categories",
        )

    if category.products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with products",
        )

    db.delete(category)
    db.commit()