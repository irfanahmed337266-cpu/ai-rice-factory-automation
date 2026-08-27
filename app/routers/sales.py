from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import SessionLocal
from app.models.sale import Sale
from app.models.product import Product

from app.core.security import (
    get_current_user,
    require_staff_or_admin,
    require_admin
)


router = APIRouter(
    prefix="/sales",
    tags=["Sales"]
)


# =========================================================
# DATABASE
# =========================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================
# SCHEMAS
# =========================================================

class SaleCreate(BaseModel):
    buyer_id: int
    product_id: int
    quantity: int
    selling_rate: float | None = None
    transport_cost: float | None = None
    payment_status: str = "Pending"
    status: str = "Pending"
    notes: str | None = None


class SaleUpdate(BaseModel):
    buyer_id: int | None = None
    quantity: int | None = None
    selling_rate: float | None = None
    transport_cost: float | None = None
    payment_status: str | None = None
    status: str | None = None
    notes: str | None = None


# =========================================================
# GET ALL SALES
# STAFF + ADMIN
# =========================================================

@router.get("/")
def get_sales(
    current_user: dict = Depends(require_staff_or_admin),
    db: Session = Depends(get_db)
):
    return db.query(Sale).all()


# =========================================================
# GET SINGLE SALE
# STAFF + ADMIN
# =========================================================

@router.get("/{sale_id}")
def get_sale(
    sale_id: int,
    current_user: dict = Depends(require_staff_or_admin),
    db: Session = Depends(get_db)
):

    sale = db.query(Sale).filter(
        Sale.id == sale_id
    ).first()

    if not sale:
        raise HTTPException(
            status_code=404,
            detail="Sale not found"
        )

    return sale


# =========================================================
# CREATE SALE
# STAFF + ADMIN
# =========================================================

@router.post("/")
def create_sale(
    sale: SaleCreate,
    current_user: dict = Depends(require_staff_or_admin),
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # 1. FIND PRODUCT
    # -----------------------------------------------------

    product = db.query(Product).filter(
        Product.id == sale.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Finished product not found"
        )

    # -----------------------------------------------------
    # 2. VALIDATE QUANTITY
    # -----------------------------------------------------

    if sale.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than 0"
        )

    # -----------------------------------------------------
    # 3. CHECK STOCK
    # -----------------------------------------------------

    current_stock = int(
        product.stock_quantity or 0
    )

    if current_stock < sale.quantity:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Insufficient stock. "
                f"Available: {current_stock}"
            )
        )

    # -----------------------------------------------------
    # 4. VALIDATE SELLING RATE
    # -----------------------------------------------------

    if sale.selling_rate is None:
        raise HTTPException(
            status_code=400,
            detail="Selling rate is required"
        )

    selling_rate = Decimal(
        str(sale.selling_rate)
    )

    if selling_rate < 0:
        raise HTTPException(
            status_code=400,
            detail="Selling rate cannot be negative"
        )

    # -----------------------------------------------------
    # 5. TRANSPORT COST
    # -----------------------------------------------------

    transport_cost = Decimal(
        str(sale.transport_cost or 0)
    )

    if transport_cost < 0:
        raise HTTPException(
            status_code=400,
            detail="Transport cost cannot be negative"
        )

    # -----------------------------------------------------
    # 6. COST PRICE
    # -----------------------------------------------------

    cost_price = Decimal(
        str(product.average_rate or 0)
    )

    # -----------------------------------------------------
    # 7. COGS
    # -----------------------------------------------------

    cogs = cost_price * sale.quantity

    # -----------------------------------------------------
    # 8. SALES AMOUNT
    # -----------------------------------------------------

    sales_amount = selling_rate * sale.quantity

    # -----------------------------------------------------
    # 9. TOTAL AMOUNT
    # -----------------------------------------------------

    total_amount = sales_amount + transport_cost

    # -----------------------------------------------------
    # 10. GROSS PROFIT
    # -----------------------------------------------------

    gross_profit = sales_amount - cogs

    # -----------------------------------------------------
    # 11. CREATE SALE
    # -----------------------------------------------------

    new_sale = Sale(
        buyer_id=sale.buyer_id,
        product_id=sale.product_id,
        quantity=sale.quantity,

        cost_price=cost_price,
        cogs=cogs,
        gross_profit=gross_profit,

        selling_rate=selling_rate,
        transport_cost=transport_cost,
        total_amount=total_amount,

        payment_status=sale.payment_status,
        status=sale.status,
        notes=sale.notes
    )

    db.add(new_sale)

    # -----------------------------------------------------
    # 12. DEDUCT STOCK
    # -----------------------------------------------------

    product.stock_quantity = (
        current_stock - sale.quantity
    )

    # -----------------------------------------------------
    # 13. SAVE
    # -----------------------------------------------------

    try:
        db.commit()

        db.refresh(new_sale)
        db.refresh(product)

    except Exception:
        db.rollback()
        raise

    return new_sale


# =========================================================
# UPDATE SALE
# STAFF + ADMIN
# =========================================================

@router.put("/{sale_id}")
def update_sale(
    sale_id: int,
    sale_update: SaleUpdate,
    current_user: dict = Depends(require_staff_or_admin),
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # 1. FIND EXISTING SALE
    # -----------------------------------------------------

    existing_sale = db.query(Sale).filter(
        Sale.id == sale_id
    ).first()

    if not existing_sale:
        raise HTTPException(
            status_code=404,
            detail="Sale not found"
        )

    # -----------------------------------------------------
    # 2. FIND PRODUCT
    # -----------------------------------------------------

    product = db.query(Product).filter(
        Product.id == existing_sale.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Finished product not found"
        )

    # -----------------------------------------------------
    # 3. OLD QUANTITY
    # -----------------------------------------------------

    old_quantity = int(
        existing_sale.quantity
    )

    # -----------------------------------------------------
    # 4. NEW QUANTITY
    # -----------------------------------------------------

    new_quantity = (
        sale_update.quantity
        if sale_update.quantity is not None
        else old_quantity
    )

    if new_quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than 0"
        )

    # -----------------------------------------------------
    # 5. QUANTITY DIFFERENCE
    # -----------------------------------------------------

    quantity_difference = (
        new_quantity - old_quantity
    )

    # -----------------------------------------------------
    # 6. CURRENT STOCK
    # -----------------------------------------------------

    current_stock = int(
        product.stock_quantity or 0
    )

    # -----------------------------------------------------
    # 7. CHECK ADDITIONAL STOCK
    # -----------------------------------------------------

    if quantity_difference > 0:

        if current_stock < quantity_difference:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Insufficient stock for increase. "
                    f"Available: {current_stock}"
                )
            )

    # -----------------------------------------------------
    # 8. SELLING RATE
    # -----------------------------------------------------

    if sale_update.selling_rate is not None:

        new_selling_rate = Decimal(
            str(sale_update.selling_rate)
        )

    else:

        new_selling_rate = Decimal(
            str(existing_sale.selling_rate or 0)
        )

    if new_selling_rate < 0:
        raise HTTPException(
            status_code=400,
            detail="Selling rate cannot be negative"
        )

    # -----------------------------------------------------
    # 9. TRANSPORT COST
    # -----------------------------------------------------

    if sale_update.transport_cost is not None:

        new_transport_cost = Decimal(
            str(sale_update.transport_cost)
        )

    else:

        new_transport_cost = Decimal(
            str(existing_sale.transport_cost or 0)
        )

    if new_transport_cost < 0:
        raise HTTPException(
            status_code=400,
            detail="Transport cost cannot be negative"
        )

    # -----------------------------------------------------
    # 10. COST PRICE
    # -----------------------------------------------------

    cost_price = Decimal(
        str(product.average_rate or 0)
    )

    # -----------------------------------------------------
    # 11. RECALCULATE COGS
    # -----------------------------------------------------

    cogs = cost_price * new_quantity

    # -----------------------------------------------------
    # 12. RECALCULATE SALES AMOUNT
    # -----------------------------------------------------

    sales_amount = (
        new_selling_rate * new_quantity
    )

    # -----------------------------------------------------
    # 13. RECALCULATE TOTAL
    # -----------------------------------------------------

    total_amount = (
        sales_amount + new_transport_cost
    )

    # -----------------------------------------------------
    # 14. RECALCULATE GROSS PROFIT
    # -----------------------------------------------------

    gross_profit = sales_amount - cogs

    # -----------------------------------------------------
    # 15. UPDATE STOCK
    # -----------------------------------------------------

    product.stock_quantity = (
        current_stock - quantity_difference
    )

    # -----------------------------------------------------
    # 16. UPDATE BUYER
    # -----------------------------------------------------

    if sale_update.buyer_id is not None:
        existing_sale.buyer_id = (
            sale_update.buyer_id
        )

    # -----------------------------------------------------
    # 17. UPDATE SALE VALUES
    # -----------------------------------------------------

    existing_sale.quantity = new_quantity

    existing_sale.cost_price = cost_price

    existing_sale.cogs = cogs

    existing_sale.gross_profit = gross_profit

    existing_sale.selling_rate = new_selling_rate

    existing_sale.transport_cost = (
        new_transport_cost
    )

    existing_sale.total_amount = total_amount

    # -----------------------------------------------------
    # 18. UPDATE PAYMENT STATUS
    # -----------------------------------------------------

    if sale_update.payment_status is not None:
        existing_sale.payment_status = (
            sale_update.payment_status
        )

    # -----------------------------------------------------
    # 19. UPDATE STATUS
    # -----------------------------------------------------

    if sale_update.status is not None:
        existing_sale.status = (
            sale_update.status
        )

    # -----------------------------------------------------
    # 20. UPDATE NOTES
    # -----------------------------------------------------

    if sale_update.notes is not None:
        existing_sale.notes = sale_update.notes

    # -----------------------------------------------------
    # 21. SAVE
    # -----------------------------------------------------

    try:

        db.commit()

        db.refresh(existing_sale)
        db.refresh(product)

    except Exception:

        db.rollback()
        raise

    return existing_sale


# =========================================================
# DELETE SALE
# ADMIN ONLY
# =========================================================

@router.delete("/{sale_id}")
def delete_sale(
    sale_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):

    # -----------------------------------------------------
    # 1. FIND SALE
    # -----------------------------------------------------

    sale = db.query(Sale).filter(
        Sale.id == sale_id
    ).first()

    if not sale:
        raise HTTPException(
            status_code=404,
            detail="Sale not found"
        )

    # -----------------------------------------------------
    # 2. FIND PRODUCT
    # -----------------------------------------------------

    product = db.query(Product).filter(
        Product.id == sale.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Finished product not found"
        )

    # -----------------------------------------------------
    # 3. SAVE QUANTITY
    # -----------------------------------------------------

    deleted_quantity = int(
        sale.quantity
    )

    # -----------------------------------------------------
    # 4. RETURN STOCK
    # -----------------------------------------------------

    product.stock_quantity = (
        int(product.stock_quantity or 0)
        + deleted_quantity
    )

    # -----------------------------------------------------
    # 5. DELETE SALE
    # -----------------------------------------------------

    db.delete(sale)

    # -----------------------------------------------------
    # 6. SAVE
    # -----------------------------------------------------

    try:

        db.commit()

    except Exception:

        db.rollback()
        raise

    # -----------------------------------------------------
    # 7. RETURN RESULT
    # -----------------------------------------------------

    return {
        "message": "Sale deleted successfully",
        "sale_id": sale_id,
        "stock_returned": deleted_quantity,
        "product_id": product.id
    }