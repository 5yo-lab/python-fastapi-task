from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/products", tags=["products"])

@router.get("/")
def get_products():
    return []