import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.models.category import Category
from app.seed import seed
from main import app as fastapi_app
import app.models.category
import app.models.product

TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}, # needed as sqlite doesn support multi thread
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db

    with TestClient(fastapi_app, raise_server_exceptions=False) as test_client:
        yield test_client

    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def seed_products(db):
    seed(db)

    electronics = db.scalars(select(Category).where(Category.name == "Electronics")).one()
    books = db.scalars(select(Category).where(Category.name == "Books")).one()

    return {"electronics": electronics, "books": books}
