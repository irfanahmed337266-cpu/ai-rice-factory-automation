from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import SessionLocal
from app.models.production import Production
from app.models.inventory import Inventory
from app.models.product import Product


router = APIRouter(
    prefix="/production",
    tags=["Production"]
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

class ProductionCreate(BaseModel):
    input_material_id: int
    output_product_id: int
    input_quantity: int
    output_quantity: int
    waste_quantity: int = 0
    status: str = "Pending"
    notes: str | None = None


class ProductionUpdate(BaseModel):
    input_quantity: int | None = None
    output_quantity: int | None = None
    waste_quantity: int | None = None
    status: str | None = None
    notes: str | None = None


# =========================
# GET ALL PRODUCTION
# =========================

@router.get("/")
def get_production(
    db: Session = Depends(get_db)
):
    return db.query(Production).all()


# =========================
# GET PRODUCTION BY ID
# =========================

@router.get("/{production_id}")
def get_production_item(
    production_id: int,
    db: Session = Depends(get_db)
):

    production = db.query(Production).filter(
        Production.id == production_id
    ).first()

    if not production:
        raise HTTPException(
            status_code=404,
            detail="Production record not found"
        )

    return production


# =========================
# CREATE PRODUCTION
# =========================

@router.post("/")
def create_production(
    production: ProductionCreate,
    db: Session = Depends(get_db)
):

    # 1. Validate input quantity
    if production.input_quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Input quantity must be greater than 0"
        )

    # 2. Validate output quantity
    if production.output_quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Output quantity must be greater than 0"
        )

    # 3. Validate waste quantity
    if production.waste_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Waste quantity cannot be negative"
        )

    # 4. Check input inventory
    inventory = db.query(Inventory).filter(
        Inventory.material_id == production.input_material_id
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=404,
            detail="Input material inventory not found"
        )

    # 5. Check available stock
    if inventory.quantity < production.input_quantity:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Insufficient stock. "
                f"Available: {inventory.quantity}"
            )
        )

    # 6. Check finished product
    product = db.query(Product).filter(
        Product.id == production.output_product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Finished product not found"
        )

    # 7. Calculate raw material cost
    input_cost = (
        float(production.input_quantity)
        * float(inventory.average_rate or 0)
    )

    # 8. Calculate production rate
    production_rate = (
        input_cost / production.output_quantity
    )

    # 9. Create production record
    new_production = Production(
        input_material_id=production.input_material_id,
        output_product_id=production.output_product_id,
        input_quantity=production.input_quantity,
        output_quantity=production.output_quantity,
        waste_quantity=production.waste_quantity,
        status=production.status,
        notes=production.notes
    )

    db.add(new_production)

    # 10. Only update stock when Completed
    if production.status == "Completed":

        # Reduce raw material
        inventory.quantity -= production.input_quantity

        # Existing finished product stock
        old_stock = float(product.stock_quantity or 0)

        # Existing finished product value
        old_value = (
            old_stock
            * float(product.average_rate or 0)
        )

        # New production value
        new_value = (
            float(production.output_quantity)
            * production_rate
        )

        # New finished product stock
        new_stock = (
            old_stock
            + production.output_quantity
        )

        # Weighted average product cost
        if new_stock > 0:
            product.average_rate = (
                old_value + new_value
            ) / new_stock

        # Add finished product stock
        product.stock_quantity = new_stock

    # 11. Save
    db.commit()

    db.refresh(new_production)
    db.refresh(inventory)
    db.refresh(product)

    return {
        "production": new_production,
        "production_cost": round(input_cost, 2),
        "production_rate": round(production_rate, 2),
        "product_stock": product.stock_quantity,
        "product_average_rate": round(
            float(product.average_rate or 0),
            2
        )
    }


# =========================
# UPDATE PRODUCTION
# =========================

@router.put("/{production_id}")
def update_production(
    production_id: int,
    production_update: ProductionUpdate,
    db: Session = Depends(get_db)
):

    # 1. Find production
    existing_production = db.query(Production).filter(
        Production.id == production_id
    ).first()

    if not existing_production:
        raise HTTPException(
            status_code=404,
            detail="Production record not found"
        )

    # 2. Get inventory
    inventory = db.query(Inventory).filter(
        Inventory.material_id ==
        existing_production.input_material_id
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=404,
            detail="Input material inventory not found"
        )

    # 3. Get product
    product = db.query(Product).filter(
        Product.id ==
        existing_production.output_product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Finished product not found"
        )

    # 4. Old values
    old_input_quantity = existing_production.input_quantity
    old_output_quantity = existing_production.output_quantity

    old_status = existing_production.status

    # 5. New values
    new_input_quantity = (
        production_update.input_quantity
        if production_update.input_quantity is not None
        else old_input_quantity
    )

    new_output_quantity = (
        production_update.output_quantity
        if production_update.output_quantity is not None
        else old_output_quantity
    )

    new_waste_quantity = (
        production_update.waste_quantity
        if production_update.waste_quantity is not None
        else existing_production.waste_quantity
    )

    new_status = (
        production_update.status
        if production_update.status is not None
        else old_status
    )

    # 6. Validate
    if new_input_quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Input quantity must be greater than 0"
        )

    if new_output_quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Output quantity must be greater than 0"
        )

    if new_waste_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Waste quantity cannot be negative"
        )

    # 7. Reverse old stock changes if old production was Completed
    if old_status == "Completed":

        inventory.quantity += old_input_quantity

        product.stock_quantity -= old_output_quantity

        if product.stock_quantity < 0:
            product.stock_quantity = 0

    # 8. If new status is Completed, check inventory
    if new_status == "Completed":

        if inventory.quantity < new_input_quantity:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Insufficient stock. "
                    f"Available: {inventory.quantity}"
                )
            )

        # Calculate new production cost
        input_cost = (
            float(new_input_quantity)
            * float(inventory.average_rate or 0)
        )

        production_rate = (
            input_cost / new_output_quantity
        )

        # Reduce raw material
        inventory.quantity -= new_input_quantity

        # Add finished product
        old_product_stock = float(
            product.stock_quantity or 0
        )

        old_product_value = (
            old_product_stock
            * float(product.average_rate or 0)
        )

        new_product_value = (
            float(new_output_quantity)
            * production_rate
        )

        new_product_stock = (
            old_product_stock
            + new_output_quantity
        )

        if new_product_stock > 0:
            product.average_rate = (
                old_product_value
                + new_product_value
            ) / new_product_stock

        product.stock_quantity = new_product_stock

    # 9. Update production fields
    existing_production.input_quantity = new_input_quantity
    existing_production.output_quantity = new_output_quantity
    existing_production.waste_quantity = new_waste_quantity
    existing_production.status = new_status

    if production_update.notes is not None:
        existing_production.notes = production_update.notes

    # 10. Save
    db.commit()

    db.refresh(existing_production)
    db.refresh(inventory)
    db.refresh(product)

    return {
        "production": existing_production,
        "product_stock": product.stock_quantity,
        "product_average_rate": round(
            float(product.average_rate or 0),
            2
        )
    }


# =========================
# DELETE PRODUCTION
# =========================

@router.delete("/{production_id}")
def delete_production(
    production_id: int,
    db: Session = Depends(get_db)
):

    # 1. Find production
    production = db.query(Production).filter(
        Production.id == production_id
    ).first()

    if not production:
        raise HTTPException(
            status_code=404,
            detail="Production record not found"
        )

    # 2. Get inventory
    inventory = db.query(Inventory).filter(
        Inventory.material_id ==
        production.input_material_id
    ).first()

    # 3. Get finished product
    product = db.query(Product).filter(
        Product.id ==
        production.output_product_id
    ).first()

    # 4. Reverse stock only if production was Completed
    if production.status == "Completed":

        if inventory:
            inventory.quantity += production.input_quantity

        if product:
            if product.stock_quantity < production.output_quantity:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Cannot delete production because "
                        "finished product stock is insufficient "
                        "to reverse this production."
                    )
                )

            product.stock_quantity -= production.output_quantity

    # 5. Save IDs before deletion
    production_id_value = production.id
    input_material_id = production.input_material_id
    output_product_id = production.output_product_id

    # 6. Delete production
    db.delete(production)

    db.commit()

    return {
        "message": "Production deleted successfully",
        "production_id": production_id_value,
        "input_material_id": input_material_id,
        "output_product_id": output_product_id,
        "stock_reversed": production.status == "Completed"
    }