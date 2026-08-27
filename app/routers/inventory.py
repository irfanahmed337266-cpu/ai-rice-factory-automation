from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.inventory import Inventory


router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"]
)


def inventory_response(inventory):
    return {
        "id": inventory.id,
        "material_id": inventory.material_id,
        "quantity": inventory.quantity,
        "average_rate": inventory.average_rate,
        "stock_value": round(
            float(inventory.quantity or 0)
            * float(inventory.average_rate or 0),
            2
        ),
        "created_at": inventory.created_at,
        "updated_at": inventory.updated_at
    }


# GET ALL INVENTORY
@router.get("/")
def get_inventory(
    db: Session = Depends(get_db)
):
    inventories = db.query(Inventory).all()

    return [
        inventory_response(inventory)
        for inventory in inventories
    ]


# GET SINGLE INVENTORY
@router.get("/{inventory_id}")
def get_inventory_item(
    inventory_id: int,
    db: Session = Depends(get_db)
):
    inventory = db.query(Inventory).filter(
        Inventory.id == inventory_id
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found"
        )

    return inventory_response(inventory)


# CREATE INVENTORY
@router.post("/")
def create_inventory(
    material_id: int,
    quantity: int,
    average_rate: float,
    db: Session = Depends(get_db)
):

    if quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than 0"
        )

    if average_rate < 0:
        raise HTTPException(
            status_code=400,
            detail="Average rate cannot be negative"
        )

    # Prevent duplicate inventory records
    existing_inventory = db.query(Inventory).filter(
        Inventory.material_id == material_id
    ).first()

    if existing_inventory:
        raise HTTPException(
            status_code=400,
            detail="Inventory already exists for this material"
        )

    inventory = Inventory(
        material_id=material_id,
        quantity=quantity,
        average_rate=average_rate
    )

    db.add(inventory)
    db.commit()
    db.refresh(inventory)

    return inventory_response(inventory)


# UPDATE INVENTORY
@router.put("/{inventory_id}")
def update_inventory(
    inventory_id: int,
    material_id: int | None = None,
    quantity: int | None = None,
    average_rate: float | None = None,
    db: Session = Depends(get_db)
):

    inventory = db.query(Inventory).filter(
        Inventory.id == inventory_id
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found"
        )

    # Validate quantity
    if quantity is not None and quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than 0"
        )

    # Validate average rate
    if average_rate is not None and average_rate < 0:
        raise HTTPException(
            status_code=400,
            detail="Average rate cannot be negative"
        )

    # Change material only if provided
    if material_id is not None:

        existing_inventory = db.query(Inventory).filter(
            Inventory.material_id == material_id,
            Inventory.id != inventory_id
        ).first()

        if existing_inventory:
            raise HTTPException(
                status_code=400,
                detail="Inventory already exists for this material"
            )

        inventory.material_id = material_id

    # Update quantity
    if quantity is not None:
        inventory.quantity = quantity

    # Update average rate
    if average_rate is not None:
        inventory.average_rate = average_rate

    db.commit()
    db.refresh(inventory)

    return inventory_response(inventory)


# DELETE INVENTORY
@router.delete("/{inventory_id}")
def delete_inventory(
    inventory_id: int,
    db: Session = Depends(get_db)
):

    inventory = db.query(Inventory).filter(
        Inventory.id == inventory_id
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found"
        )

    # Do not allow deletion while stock exists
    if inventory.quantity > 0:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot delete inventory while stock exists. "
                f"Current quantity: {inventory.quantity}"
            )
        )

    material_id = inventory.material_id

    db.delete(inventory)
    db.commit()

    return {
        "message": "Inventory deleted successfully",
        "inventory_id": inventory_id,
        "material_id": material_id
    }
