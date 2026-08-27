from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import SessionLocal
from app.models.product import Product


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# SCHEMAS
# =========================

class ProductCreate(BaseModel):
    name: str
    unit: str
    stock_quantity: int = 0
    average_rate: float = 0


class ProductUpdate(BaseModel):
    name: str | None = None
    unit: str | None = None
    stock_quantity: int | None = None
    average_rate: float | None = None


# =========================
# GET ALL PRODUCTS
# =========================

@router.get("/")
def get_products(
    db: Session = Depends(get_db)
):
    return db.query(Product).all()


# =========================
# GET PRODUCT BY ID
# =========================

@router.get("/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


# =========================
# CREATE PRODUCT
# =========================

@router.post("/")
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):

    if product.stock_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Stock quantity cannot be negative"
        )

    if product.average_rate < 0:
        raise HTTPException(
            status_code=400,
            detail="Average rate cannot be negative"
        )

    existing_product = db.query(Product).filter(
        Product.name == product.name
    ).first()

    if existing_product:
        raise HTTPException(
            status_code=400,
            detail="Product already exists"
        )

    new_product = Product(
        name=product.name,
        unit=product.unit,
        stock_quantity=product.stock_quantity,
        average_rate=product.average_rate
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


# =========================
# UPDATE PRODUCT
# =========================

@router.put("/{product_id}")
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if (
        product_update.stock_quantity is not None
        and product_update.stock_quantity < 0
    ):
        raise HTTPException(
            status_code=400,
            detail="Stock quantity cannot be negative"
        )

    if (
        product_update.average_rate is not None
        and product_update.average_rate < 0
    ):
        raise HTTPException(
            status_code=400,
            detail="Average rate cannot be negative"
        )

    if product_update.name is not None:

        duplicate_product = db.query(Product).filter(
            Product.name == product_update.name,
            Product.id != product_id
        ).first()

        if duplicate_product:
            raise HTTPException(
                status_code=400,
                detail="Product already exists"
            )

        product.name = product_update.name

    if product_update.unit is not None:
        product.unit = product_update.unit

    if product_update.stock_quantity is not None:
        product.stock_quantity = product_update.stock_quantity

    if product_update.average_rate is not None:
        product.average_rate = product_update.average_rate

    db.commit()
    db.refresh(product)

    return product


# =========================
# DELETE PRODUCT
# =========================

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if product.stock_quantity > 0:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot delete product while stock exists. "
                f"Current quantity: {product.stock_quantity}"
            )
        )

    product_name = product.name

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully",
        "product_id": product_id,
        "product_name": product_name
    }