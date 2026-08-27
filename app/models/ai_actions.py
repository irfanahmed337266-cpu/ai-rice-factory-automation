from sqlalchemy.orm import Session

from app.models.purchase import Purchase
from app.models.supplier import Supplier
from app.models.material import Material
from app.models.inventory import Inventory


def create_purchase_action(
    db: Session,
    supplier_name: str,
    material_name: str,
    quantity: int,
    purchase_rate: float | None = None,
    transport_cost: float | None = None,
    notes: str | None = None
):

    # --------------------------------------------------
    # FIND SUPPLIER
    # --------------------------------------------------

    supplier = db.query(Supplier).filter(
        Supplier.name.ilike(supplier_name.strip())
    ).first()

    if not supplier:
        return {
            "success": False,
            "message": f"Supplier '{supplier_name}' database میں نہیں ملا۔"
        }

    # --------------------------------------------------
    # FIND MATERIAL
    # --------------------------------------------------

    material = db.query(Material).filter(
        Material.name.ilike(material_name.strip())
    ).first()

    if not material:
        return {
            "success": False,
            "message": f"Material '{material_name}' database میں نہیں ملا۔"
        }

    # --------------------------------------------------
    # CALCULATE TOTAL
    # --------------------------------------------------

    total_amount = None

    if purchase_rate is not None:
        total_amount = (
            quantity * purchase_rate
        ) + (transport_cost or 0)

    # --------------------------------------------------
    # CREATE PURCHASE
    # --------------------------------------------------

    new_purchase = Purchase(
        supplier_id=supplier.id,
        material_id=material.id,
        quantity=quantity,
        purchase_rate=purchase_rate,
        transport_cost=transport_cost,
        total_amount=total_amount,
        availability_status="Available",
        payment_status="Pending",
        status="Pending",
        notes=notes
    )

    db.add(new_purchase)

    # --------------------------------------------------
    # UPDATE INVENTORY
    # --------------------------------------------------

    inventory = db.query(Inventory).filter(
        Inventory.material_id == material.id
    ).first()

    if inventory:

        old_quantity = inventory.quantity or 0
        old_rate = float(inventory.average_rate or 0)

        inventory.quantity = (
            old_quantity + quantity
        )

        if purchase_rate is not None:

            total_quantity = (
                old_quantity + quantity
            )

            if total_quantity > 0:

                inventory.average_rate = (
                    (old_quantity * old_rate)
                    + (quantity * purchase_rate)
                ) / total_quantity

    else:

        inventory = Inventory(
            material_id=material.id,
            quantity=quantity,
            average_rate=purchase_rate or 0
        )

        db.add(inventory)

    # --------------------------------------------------
    # SAVE
    # --------------------------------------------------

    db.commit()

    db.refresh(new_purchase)

    return {
        "success": True,
        "message": "Purchase successfully create ہو گئی۔",
        "purchase_id": new_purchase.id,
        "supplier": supplier.name,
        "material": material.name,
        "quantity": quantity,
        "purchase_rate": purchase_rate,
        "transport_cost": transport_cost,
        "total_amount": total_amount
    }
