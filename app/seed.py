from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.category import Category
from app.models.product import Product


def seed(db: Session) -> None:
    if db.scalar(select(Category.id).limit(1)):
        return  #Check if there's already data in the database, if yes, skip seeding

    electronics = Category(name="Electronics")
    books = Category(name="Books")
    laptops = Category(name="Laptops", parent=electronics)

    db.add_all([electronics, books, laptops])
    db.flush()

    db.add_all([
        Product(
            title="Widget Pro",
            sku="WDG-001",
            price=Decimal("29.99"),
            description="Premium widget",
            category_id=electronics.id,
        ),
        Product(
            title="Widget Basic",
            sku="WDG-002",
            price=Decimal("19.99"),
            category_id=electronics.id,
        ),
        Product(
            title="Python Guide",
            sku="BK-001",
            price=Decimal("45.00"),
            category_id=books.id,
        ),
        Product(
            title="Dev Laptop",
            sku="LT-001",
            price=Decimal("999.99"),
            description="Required for expensive items over 100",
            category_id=laptops.id,
        ),
    ])
    db.commit()


def main() -> None:
    with SessionLocal() as db:
        seed(db)
        print("Database seeded.")


if __name__ == "__main__":
    main()