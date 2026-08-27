# E-Commerce Product Service

A REST API for managing products and categories in an e-commerce system. Built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**, containerised with Docker for a clone-and-run demo.

---

## Task requirements

### Models

| Requirement                                                               | Implementation           |
| ------------------------------------------------------------------------- | ------------------------ |
| **Product** — title, description, image, unique SKU, price, category link | `app/models/product.py`  |
| **Category** — name, parent (self-referential)                            | `app/models/category.py` |

### Operations

| Requirement              | Implementation                                                                                 |
| ------------------------ | ---------------------------------------------------------------------------------------------- |
| CRUD for products        | `app/routes/products.py` — `POST`, `GET`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`           |
| CRUD for categories      | `app/routes/categories.py` — same pattern                                                      |
| Search / filter products | `GET /api/v1/products/search` — filter by title, SKU, price range, category; sort and paginate |

### Tests

| Requirement                | Implementation                           |
| -------------------------- | ---------------------------------------- |
| Unit tests for search only | `tests/test_product_search.py` (9 tests) |

---

## Tech stack

| Layer            | Choice                                     |
| ---------------- | ------------------------------------------ |
| Framework        | FastAPI                                    |
| Language         | Python 3.12                                |
| Database         | PostgreSQL 16                              |
| ORM              | SQLAlchemy 2.x                             |
| Migrations       | Alembic                                    |
| Validation       | Pydantic v2                                |
| HTTP server      | Uvicorn                                    |
| Testing          | pytest + httpx2 (via FastAPI `TestClient`) |
| Containerisation | Docker + Docker Compose                    |

---

## Quick start

```powershell
git clone <repo-url>
cd python-task
copy .env.example .env
docker compose up --build
```

On first boot the stack will:

1. Start PostgreSQL (with healthcheck)
2. Run Alembic migrations (create tables)
3. Seed demo data (if the database is empty)
4. Start the API on port **8000**

| URL                                                       | Purpose                |
| --------------------------------------------------------- | ---------------------- |
| http://localhost:8000/docs                                | Interactive Swagger UI |
| http://localhost:8000/redoc                               | ReDoc API reference    |
| http://localhost:8000/api/v1/products/                    | List products          |
| http://localhost:8000/api/v1/products/search?title=Widget | Search demo            |

### Demo data (seeded automatically)

**Categories:** Electronics → Laptops (nested), Books

**Products:**

| SKU     | Title        | Price  | Category    |
| ------- | ------------ | ------ | ----------- |
| WDG-001 | Widget Pro   | 29.99  | Electronics |
| WDG-002 | Widget Basic | 19.99  | Electronics |
| BK-001  | Python Guide | 45.00  | Books       |
| LT-001  | Dev Laptop   | 999.99 | Laptops     |

Disable seeding: set `SEED_ON_START=false` in `.env`.

### Run tests

```powershell
docker compose exec web pytest -v
```

Search tests use an in-memory SQLite database

---

## Project structure

```
python-task/
├── app/
│   ├── models/          # SQLAlchemy models (Product, Category)
│   ├── schemas/         # Pydantic request/response schemas
│   ├── routes/          # API route handlers
│   ├── database.py      # Engine, session, get_db dependency
│   └── seed.py          # Idempotent demo data seeder
├── alembic/             # Database migrations
├── tests/
│   ├── conftest.py      # Test DB + client fixtures
│   └── test_product_search.py
├── postman/             # Importable Postman collection
├── main.py              # FastAPI app entry point
├── entrypoint.sh        # Migrations + seed on container start
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## API reference

Base path: `/api/v1`

### Categories

| Method   | Path               | Description                                    |
| -------- | ------------------ | ---------------------------------------------- |
| `POST`   | `/categories/`     | Create category                                |
| `GET`    | `/categories/`     | List all (sorted by name)                      |
| `GET`    | `/categories/{id}` | Get one (includes parent & children)           |
| `PATCH`  | `/categories/{id}` | Update name and/or parent                      |
| `DELETE` | `/categories/{id}` | Delete (blocked if children or products exist) |

**Create example:**

```json
POST /api/v1/categories/
{
  "name": "Shirts",
  "parent_id": 1
}
```

### Products

| Method   | Path               | Description                                   |
| -------- | ------------------ | --------------------------------------------- |
| `POST`   | `/products/`       | Create product                                |
| `GET`    | `/products/`       | List all (sorted by title, includes category) |
| `GET`    | `/products/{id}`   | Get one                                       |
| `PATCH`  | `/products/{id}`   | Partial update                                |
| `DELETE` | `/products/{id}`   | Delete                                        |
| `GET`    | `/products/search` | Search and filter (see below)                 |

**Create example:**

```json
POST /api/v1/products/
{
  "title": "New Gadget",
  "sku": "GAD-001",
  "price": "49.99",
  "category_id": 1,
  "description": "Optional unless price > 100"
}
```

### Search endpoint

`GET /api/v1/products/search`

All query parameters are optional. Filters combine with **AND** logic.

| Parameter     | Type                        | Description                             |
| ------------- | --------------------------- | --------------------------------------- |
| `title`       | string                      | Case-insensitive partial match on title |
| `sku`         | string                      | Case-insensitive partial match on SKU   |
| `min_price`   | decimal                     | Minimum price (inclusive)               |
| `max_price`   | decimal                     | Maximum price (inclusive)               |
| `category_id` | integer                     | Exact category match                    |
| `sort_by`     | `title` \| `price` \| `sku` | Sort field (default: `title`)           |
| `sort_order`  | `asc` \| `desc`             | Sort direction (default: `asc`)         |
| `limit`       | integer                     | Page size, 1–100 (default: 10)          |
| `offset`      | integer                     | Skip N results (default: 0)             |

**Response shape:**

```json
{
  "items": [
    /* ProductRead[] */
  ],
  "total": 42,
  "limit": 10,
  "offset": 0
}
```

**Examples:**

```
GET /api/v1/products/search?title=Widget
GET /api/v1/products/search?sku=WDG-001
GET /api/v1/products/search?min_price=20&max_price=50
GET /api/v1/products/search?category_id=1&title=Widget
GET /api/v1/products/search?sort_by=price&sort_order=desc&limit=5
```

Returns `400` if `category_id` does not exist.

---

## Design decisions

Features were kept small and production-minded rather than over-scoped.

**Validation at the schema layer (Pydantic)** — field lengths, positive prices, blank-string rejection, and price-range consistency on search params are validated before hitting the database.

**Business rules at the route layer** — e.g. products over 100 require a description; category parent must exist; SKU uniqueness returns `409 Conflict`.

**Category hierarchy safeguards** — prevents a category from being its own parent and walks the ancestor chain to block circular references (A → B → A).

**Category delete protection** — cannot delete a category that still has child categories or assigned products.

**Schema vs demo data separation** — Alembic handles schema migrations; `app/seed.py` handles demo content. The seeder is idempotent (skips if data already exists).

**Search route ordering** — `/products/search` is registered before `/products/{id}` so FastAPI does not treat `"search"` as an integer ID.

**Test isolation** — search tests override the `get_db` dependency with an in-memory SQLite session, independent of Docker Postgres.

---

## Postman

Import the collection from:

```
postman/E-Commerce-Products-API.postman_collection.json
```

1. Open Postman → **Import** → select the file
2. Collection variable `baseUrl` defaults to `http://localhost:8000`
3. Run **Health Check** first, then explore folders: Categories, Products, Search

---

## Environment variables

Copy `.env.example` to `.env`:

| Variable            | Purpose                                                         |
| ------------------- | --------------------------------------------------------------- |
| `POSTGRES_USER`     | Postgres username (also used to init the DB)                    |
| `POSTGRES_PASSWORD` | Postgres password                                               |
| `POSTGRES_DB`       | Database name                                                   |
| `DATABASE_URL`      | SQLAlchemy connection string — use host `postgre` inside Docker |
| `SEED_ON_START`     | Run demo seeder on container start (`true` / `false`)           |

---

## Local development (without Docker)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Point DATABASE_URL to a local Postgres instance
alembic upgrade head
python -m app.seed
uvicorn main:app --reload
```

---

## Presentation notes

- The project runs with a single `docker compose up --build` after copying `.env`
- Swagger UI at `/docs` is the fastest way to demo live
- Search tests: `docker compose exec web pytest tests/test_product_search.py -v`
- Postman collection covers every endpoint with example payloads
