from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import SessionLocal
from app.models.purchase import Purchase
from app.models.inventory import Inventory

from app.core.security import (
    require_staff_or_admin,
    require_admin
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/purchases",
    tags=["Purchases"]
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

class PurchaseCreate(BaseModel):
    supplier_id: int
    material_id: int
    quantity: int

    purchase_rate: float | None = None
    transport_cost: float | None = None

    availability_status: str = "Available"
    payment_status: str = "Pending"
    status: str = "Pending"

    notes: str | None = None


class PurchaseUpdate(BaseModel):
    supplier_id: int | None = None
    quantity: int | None = None
    purchase_rate: float | None = None
    transport_cost: float | None = None

    availability_status: str | None = None
    payment_status: str | None = None
    status: str | None = None

    notes: str | None = None


# =========================================================
# INVENTORY HELPERS
# =========================================================

def landed_unit_cost(
    quantity: int | float,
    purchase_rate: float,
    transport_cost: float
) -> float:
    """
    Calculate the actual inventory cost per unit.

    Landed Cost =
        Purchase Cost + Transport Cost

    Landed Unit Cost =
        (quantity * purchase_rate + transport_cost)
        / quantity
    """

    quantity = float(quantity or 0)
    purchase_rate = float(purchase_rate or 0)
    transport_cost = float(transport_cost or 0)

    if quantity <= 0:
        return 0.0

    total_landed_cost = (
        quantity * purchase_rate
        + transport_cost
    )

    return total_landed_cost / quantity


def add_inventory_stock(
    db: Session,
    material_id: int,
    quantity: int | float,
    unit_cost: float
):
    """
    Add stock using weighted-average valuation.
    """

    quantity = float(quantity or 0)
    unit_cost = float(unit_cost or 0)

    if quantity <= 0:
        return

    inventory = (
        db.query(Inventory)
        .filter(
            Inventory.material_id == material_id
        )
        .first()
    )

    if inventory:

        old_quantity = float(
            inventory.quantity or 0
        )

        old_average_rate = float(
            inventory.average_rate or 0
        )

        old_value = (
            old_quantity
            * old_average_rate
        )

        new_value = (
            quantity
            * unit_cost
        )

        total_quantity = (
            old_quantity
            + quantity
        )

        if total_quantity > 0:

            inventory.average_rate = (
                old_value
                + new_value
            ) / total_quantity

        inventory.quantity = total_quantity

    else:

        inventory = Inventory(
            material_id=material_id,
            quantity=quantity,
            average_rate=unit_cost
        )

        db.add(inventory)


def remove_inventory_stock(
    db: Session,
    material_id: int,
    quantity: int | float,
    unit_cost: float
):
    """
    Remove stock and its corresponding valuation.

    This is required when:
    - purchase is edited
    - purchase becomes unavailable
    - purchase is deleted
    """

    quantity = float(quantity or 0)
    unit_cost = float(unit_cost or 0)

    if quantity <= 0:
        return

    inventory = (
        db.query(Inventory)
        .filter(
            Inventory.material_id == material_id
        )
        .first()
    )

    if not inventory:
        raise HTTPException(
            status_code=400,
            detail=(
                "Inventory record not found "
                "for this material"
            )
        )

    current_quantity = float(
        inventory.quantity or 0
    )

    current_average_rate = float(
        inventory.average_rate or 0
    )

    if current_quantity < quantity:

        raise HTTPException(
            status_code=400,
            detail=(
                "Inventory quantity is less than "
                "the purchase quantity"
            )
        )

    # Current inventory value
    current_value = (
        current_quantity
        * current_average_rate
    )

    # Value belonging to the purchase being removed
    removed_value = (
        quantity
        * unit_cost
    )

    remaining_quantity = (
        current_quantity
        - quantity
    )

    remaining_value = (
        current_value
        - removed_value
    )

    # Protect against tiny floating-point errors
    if remaining_value < 0 and remaining_value > -0.01:
        remaining_value = 0.0

    if remaining_value < 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "Inventory valuation would become "
                "negative. Purchase cannot be changed "
                "or deleted."
            )
        )

    inventory.quantity = remaining_quantity

    if remaining_quantity > 0:

        inventory.average_rate = (
            remaining_value
            / remaining_quantity
        )

    else:

        inventory.average_rate = 0


# =========================================================
# GET ALL PURCHASES
# STAFF + ADMIN
# =========================================================

@router.get("/")
def get_purchases(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_staff_or_admin)
):
    return db.query(Purchase).all()


# =========================================================
# GET SINGLE PURCHASE
# STAFF + ADMIN
# =========================================================

@router.get("/{purchase_id}")
def get_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_staff_or_admin)
):

    purchase = (
        db.query(Purchase)
        .filter(Purchase.id == purchase_id)
        .first()
    )

    if not purchase:

        raise HTTPException(
            status_code=404,
            detail="Purchase not found"
        )

    return purchase


# =========================================================
# CREATE PURCHASE
# STAFF + ADMIN
# =========================================================

@router.post("/")
def create_purchase(
    purchase: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_staff_or_admin)
):

    try:

        # -------------------------------------------------
        # 1. VALIDATE QUANTITY
        # -------------------------------------------------

        if purchase.quantity <= 0:

            raise HTTPException(
                status_code=400,
                detail="Quantity must be greater than 0"
            )

        # -------------------------------------------------
        # 2. VALIDATE PURCHASE RATE
        # -------------------------------------------------

        if purchase.purchase_rate is None:

            raise HTTPException(
                status_code=400,
                detail="Purchase rate is required"
            )

        if purchase.purchase_rate < 0:

            raise HTTPException(
                status_code=400,
                detail="Purchase rate cannot be negative"
            )

        # -------------------------------------------------
        # 3. TRANSPORT COST
        # -------------------------------------------------

        transport_cost = (
            purchase.transport_cost
            if purchase.transport_cost is not None
            else 0
        )

        if transport_cost < 0:

            raise HTTPException(
                status_code=400,
                detail="Transport cost cannot be negative"
            )

        # -------------------------------------------------
        # 4. CALCULATE PURCHASE AMOUNT
        # -------------------------------------------------

        purchase_amount = (
            purchase.quantity
            * purchase.purchase_rate
        )

        # -------------------------------------------------
        # 5. TOTAL PURCHASE AMOUNT
        # -------------------------------------------------

        total_amount = (
            purchase_amount
            + transport_cost
        )

        # -------------------------------------------------
        # 6. LANDED UNIT COST
        # -------------------------------------------------

        unit_landed_cost = landed_unit_cost(
            purchase.quantity,
            purchase.purchase_rate,
            transport_cost
        )

        # -------------------------------------------------
        # 7. CREATE PURCHASE
        # -------------------------------------------------

        new_purchase = Purchase(
            supplier_id=purchase.supplier_id,
            material_id=purchase.material_id,
            quantity=purchase.quantity,
            purchase_rate=purchase.purchase_rate,
            transport_cost=transport_cost,
            total_amount=total_amount,

            availability_status=(
                purchase.availability_status
            ),

            payment_status=(
                purchase.payment_status
            ),

            status=purchase.status,
            notes=purchase.notes
        )

        db.add(new_purchase)

        # -------------------------------------------------
        # 8. UPDATE INVENTORY
        # -------------------------------------------------

        if purchase.availability_status == "Available":

            add_inventory_stock(
                db=db,
                material_id=purchase.material_id,
                quantity=purchase.quantity,
                unit_cost=unit_landed_cost
            )

        # -------------------------------------------------
        # 9. SAVE
        # -------------------------------------------------

        db.commit()

        db.refresh(new_purchase)

        return new_purchase

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Purchase creation failed: {str(e)}"
        )


# =========================================================
# UPDATE PURCHASE
# STAFF + ADMIN
# =========================================================

@router.put("/{purchase_id}")
def update_purchase(
    purchase_id: int,
    purchase_update: PurchaseUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_staff_or_admin)
):

    try:

        # -------------------------------------------------
        # 1. FIND PURCHASE
        # -------------------------------------------------

        existing_purchase = (
            db.query(Purchase)
            .filter(
                Purchase.id == purchase_id
            )
            .first()
        )

        if not existing_purchase:

            raise HTTPException(
                status_code=404,
                detail="Purchase not found"
            )

        # -------------------------------------------------
        # 2. OLD VALUES
        # -------------------------------------------------

        old_quantity = int(
            existing_purchase.quantity
        )

        old_rate = float(
            existing_purchase.purchase_rate or 0
        )

        old_transport = float(
            existing_purchase.transport_cost or 0
        )

        old_available = (
            existing_purchase.availability_status
            == "Available"
        )

        old_material_id = (
            existing_purchase.material_id
        )

        old_landed_cost = landed_unit_cost(
            old_quantity,
            old_rate,
            old_transport
        )

        # -------------------------------------------------
        # 3. NEW VALUES
        # -------------------------------------------------

        new_supplier_id = (
            purchase_update.supplier_id
            if purchase_update.supplier_id is not None
            else existing_purchase.supplier_id
        )

        new_quantity = (
            purchase_update.quantity
            if purchase_update.quantity is not None
            else old_quantity
        )

        if new_quantity <= 0:

            raise HTTPException(
                status_code=400,
                detail="Quantity must be greater than 0"
            )

        new_rate = (
            purchase_update.purchase_rate
            if purchase_update.purchase_rate is not None
            else old_rate
        )

        if new_rate < 0:

            raise HTTPException(
                status_code=400,
                detail="Purchase rate cannot be negative"
            )

        new_transport = (
            purchase_update.transport_cost
            if purchase_update.transport_cost is not None
            else old_transport
        )

        if new_transport < 0:

            raise HTTPException(
                status_code=400,
                detail="Transport cost cannot be negative"
            )

        new_available = (
            purchase_update.availability_status
            == "Available"
            if purchase_update.availability_status is not None
            else old_available
        )

        new_landed_cost = landed_unit_cost(
            new_quantity,
            new_rate,
            new_transport
        )

        # -------------------------------------------------
        # 4. REMOVE OLD INVENTORY CONTRIBUTION
        # -------------------------------------------------
        #
        # We remove the OLD purchase using its OLD
        # landed cost before adding the NEW purchase.
        #
        # This fixes:
        # - quantity changes
        # - rate changes
        # - transport changes
        # - Available -> Unavailable
        # - Unavailable -> Available
        #

        if old_available:

            remove_inventory_stock(
                db=db,
                material_id=old_material_id,
                quantity=old_quantity,
                unit_cost=old_landed_cost
            )

        # -------------------------------------------------
        # 5. ADD NEW INVENTORY CONTRIBUTION
        # -------------------------------------------------

        if new_available:

            add_inventory_stock(
                db=db,
                material_id=old_material_id,
                quantity=new_quantity,
                unit_cost=new_landed_cost
            )

        # -------------------------------------------------
        # 6. CALCULATE NEW PURCHASE AMOUNT
        # -------------------------------------------------

        purchase_amount = (
            new_quantity
            * new_rate
        )

        total_amount = (
            purchase_amount
            + new_transport
        )

        # -------------------------------------------------
        # 7. UPDATE PURCHASE
        # -------------------------------------------------

        existing_purchase.supplier_id = (
            new_supplier_id
        )

        existing_purchase.quantity = (
            new_quantity
        )

        existing_purchase.purchase_rate = (
            new_rate
        )

        existing_purchase.transport_cost = (
            new_transport
        )

        existing_purchase.total_amount = (
            total_amount
        )

        if purchase_update.availability_status is not None:

            existing_purchase.availability_status = (
                purchase_update.availability_status
            )

        if purchase_update.payment_status is not None:

            existing_purchase.payment_status = (
                purchase_update.payment_status
            )

        if purchase_update.status is not None:

            existing_purchase.status = (
                purchase_update.status
            )

        if purchase_update.notes is not None:

            existing_purchase.notes = (
                purchase_update.notes
            )

        # -------------------------------------------------
        # 8. SAVE
        # -------------------------------------------------

        db.commit()

        db.refresh(existing_purchase)

        return existing_purchase

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Purchase update failed: {str(e)}"
        )


# =========================================================
# DELETE PURCHASE
# ADMIN ONLY
# =========================================================

@router.delete("/{purchase_id}")
def delete_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):

    try:

        # -------------------------------------------------
        # 1. FIND PURCHASE
        # -------------------------------------------------

        purchase = (
            db.query(Purchase)
            .filter(
                Purchase.id == purchase_id
            )
            .first()
        )

        if not purchase:

            raise HTTPException(
                status_code=404,
                detail="Purchase not found"
            )

        # -------------------------------------------------
        # 2. OLD PURCHASE VALUES
        # -------------------------------------------------

        deleted_quantity = int(
            purchase.quantity
        )

        material_id = (
            purchase.material_id
        )

        purchase_rate = float(
            purchase.purchase_rate or 0
        )

        transport_cost = float(
            purchase.transport_cost or 0
        )

        purchase_landed_cost = landed_unit_cost(
            deleted_quantity,
            purchase_rate,
            transport_cost
        )

        # -------------------------------------------------
        # 3. REMOVE INVENTORY CONTRIBUTION
        # -------------------------------------------------

        if purchase.availability_status == "Available":

            remove_inventory_stock(
                db=db,
                material_id=material_id,
                quantity=deleted_quantity,
                unit_cost=purchase_landed_cost
            )

        # -------------------------------------------------
        # 4. DELETE PURCHASE
        # -------------------------------------------------

        db.delete(purchase)

        # -------------------------------------------------
        # 5. SAVE
        # -------------------------------------------------

        db.commit()

        return {
            "message": "Purchase deleted successfully",
            "purchase_id": purchase_id,
            "stock_removed": deleted_quantity,
            "material_id": material_id
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Purchase deletion failed: {str(e)}"
        )