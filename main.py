from fastapi import FastAPI
from app.routes.products import router as products_router
from app.routes.categories import router as categories_router

app = FastAPI()

app.include_router(products_router)
app.include_router(categories_router)

@app.get("/")
def index():
    return {"message": "Hello world!"}