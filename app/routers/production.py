from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import SessionLocal
from app.models.production import Production
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.material import Material

from ml.service import predict_factory_production


router = APIRouter(
    prefix="/production",
    tags=["Production"]
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


def recalculate_product_average_rate(
    db: Session,
    product_id: int
):
    """
    Recalculate finished product average rate
    from completed production records.
    """

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if not product:
        return

    completed_productions = (
        db.query(Production)
        .filter(
            Production.output_product_id == product_id,
            Production.status == "Completed"
        )
        .order_by(
            Production.created_at.asc(),
            Production.id.asc()
        )
        .all()
    )

    total_quantity = 0.0
    total_value = 0.0

    for production in completed_productions:

        inventory = (
            db.query(Inventory)
            .filter(
                Inventory.material_id
                == production.input_material_id
            )
            .first()
        )

        if not inventory:
            continue

        production_input_cost = (
            float(production.input_quantity)
            * float(inventory.average_rate or 0)
        )

        production_rate = (
            production_input_cost
            / float(production.output_quantity)
            if production.output_quantity > 0
            else 0
        )

        total_quantity += float(
            production.output_quantity
        )

        total_value += (
            float(production.output_quantity)
            * production_rate
        )

    if total_quantity > 0:
        product.average_rate = (
            total_value / total_quantity
        )
    else:
        product.average_rate = 0

# =========================================================
# SCHEMAS
# =========================================================

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


class ProductionPredictionRequest(BaseModel):
    input_material_id: int
    input_quantity: int


# =========================================================
# GET ALL PRODUCTION
# =========================================================

@router.get("/")
def get_production(
    db: Session = Depends(get_db)
):
    return db.query(Production).order_by(
        Production.created_at.desc()
    ).all()


# =========================================================
# ML PRODUCTION PREDICTION
# =========================================================

@router.post("/prediction")
def predict_production_endpoint(
    request: ProductionPredictionRequest,
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. VALIDATE QUANTITY
    # =====================================================

    if request.input_quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Input quantity must be greater than 0"
        )

    # =====================================================
    # 2. GET MATERIAL
    # =====================================================

    material = db.query(Material).filter(
        Material.id == request.input_material_id
    ).first()

    if not material:
        raise HTTPException(
            status_code=404,
            detail="Input material not found"
        )

    # =====================================================
    # 3. GET INVENTORY
    # =====================================================

    inventory = db.query(Inventory).filter(
        Inventory.material_id == request.input_material_id
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=404,
            detail="Input material inventory not found"
        )

    # =====================================================
    # 4. CHECK STOCK
    # =====================================================

    if inventory.quantity < request.input_quantity:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Insufficient stock. "
                f"Available: {inventory.quantity}"
            )
        )

    # =====================================================
    # 5. FIND PREVIOUS COMPLETED PRODUCTION
    # =====================================================

    previous_production = (
        db.query(Production)
        .filter(
            Production.input_material_id
            == request.input_material_id,
            Production.status == "Completed",
            Production.input_quantity > 0
        )
        .order_by(
            Production.created_at.desc()
        )
        .first()
    )

    # =====================================================
    # 6. HISTORICAL VALUES
    # =====================================================

    if previous_production:

        previous_yield_rate = (
            float(previous_production.output_quantity)
            / float(previous_production.input_quantity)
        )

        previous_waste_rate = (
            float(previous_production.waste_quantity or 0)
            / float(previous_production.input_quantity)
        )

    else:

        previous_yield_rate = 0.90
        previous_waste_rate = 0.10

    # =====================================================
    # 7. CURRENT PRODUCTION TIME
    # =====================================================

    now = datetime.now()

    # =====================================================
    # 8. RUN ML PREDICTION
    # =====================================================

    try:

        ml_prediction = predict_factory_production(
            material=material.name,
            input_quantity=float(
                request.input_quantity
            ),
            production_hour=now.hour,
            production_weekday=now.weekday(),
            previous_yield_rate=previous_yield_rate,
            previous_waste_rate=previous_waste_rate,
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"ML prediction failed: {str(e)}"
        )

    # =====================================================
    # 9. PREDICTION VALUES
    # =====================================================

    predicted_yield = float(
        ml_prediction["predicted_yield_rate"]
    )

    predicted_output = float(
        ml_prediction["predicted_output_quantity"]
    )

    predicted_waste = float(
        ml_prediction["predicted_waste_quantity"]
    )

    # =====================================================
    # 10. ESTIMATED PRODUCTION COST
    # =====================================================

    estimated_input_cost = (
        float(request.input_quantity)
        * float(inventory.average_rate or 0)
    )

    estimated_output_rate = (
        estimated_input_cost / predicted_output
        if predicted_output > 0
        else 0
    )

    # =====================================================
    # 11. RECOMMENDATION
    # =====================================================

    if predicted_yield >= 0.90:

        recommendation = "GOOD"

        recommendation_message = (
            "Expected yield is good. "
            "Production can proceed."
        )

    elif predicted_yield >= 0.80:

        recommendation = "ACCEPTABLE"

        recommendation_message = (
            "Expected yield is acceptable. "
            "Production can proceed with monitoring."
        )

    else:

        recommendation = "LOW_YIELD"

        recommendation_message = (
            "Expected yield is low. "
            "Review production conditions before proceeding."
        )

    # =====================================================
    # 12. RETURN PREDICTION
    # =====================================================

    return {

        "material": {
            "id": material.id,
            "name": material.name
        },

        "input_quantity": request.input_quantity,

        "previous_production": {
            "yield_rate": round(
                previous_yield_rate,
                4
            ),
            "waste_rate": round(
                previous_waste_rate,
                4
            )
        },

        "ml_prediction": ml_prediction,

        "estimated_cost": {
            "input_material_cost": round(
                estimated_input_cost,
                2
            ),
            "estimated_output_rate": round(
                estimated_output_rate,
                2
            )
        },

        "recommendation": {
            "status": recommendation,
            "message": recommendation_message
        },

        "stock": {
            "available_quantity": inventory.quantity,
            "stock_after_production": (
                inventory.quantity
                - request.input_quantity
            )
        },

        "note": (
            "Prediction only. "
            "No inventory or production record was modified."
        )
    }


# =========================================================
# GET PRODUCTION BY ID
# =========================================================

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


# =========================================================
# CREATE PRODUCTION
# =========================================================

@router.post("/")
def create_production(
    production: ProductionCreate,
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. VALIDATION
    # =====================================================

    if production.input_quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Input quantity must be greater than 0"
        )

    if production.output_quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Output quantity must be greater than 0"
        )

    if production.waste_quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Waste quantity cannot be negative"
        )

    # =====================================================
    # 2. GET MATERIAL
    # =====================================================

    material = db.query(Material).filter(
        Material.id == production.input_material_id
    ).first()

    if not material:
        raise HTTPException(
            status_code=404,
            detail="Input material not found"
        )

    # =====================================================
    # 3. GET INPUT INVENTORY
    # =====================================================

    inventory = db.query(Inventory).filter(
        Inventory.material_id
        == production.input_material_id
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=404,
            detail="Input material inventory not found"
        )

    # =====================================================
    # 4. CHECK STOCK
    # =====================================================

    if inventory.quantity < production.input_quantity:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Insufficient stock. "
                f"Available: {inventory.quantity}"
            )
        )

    # =====================================================
    # 5. GET FINISHED PRODUCT
    # =====================================================

    product = db.query(Product).filter(
        Product.id == production.output_product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Finished product not found"
        )

    # =====================================================
    # 6. ML PRODUCTION PREDICTION
    # =====================================================

    ml_prediction = None

    previous_production = (
        db.query(Production)
        .filter(
            Production.input_material_id
            == production.input_material_id,
            Production.status == "Completed",
            Production.input_quantity > 0
        )
        .order_by(
            Production.created_at.desc()
        )
        .first()
    )

    if previous_production:

        previous_yield_rate = (
            float(previous_production.output_quantity)
            / float(previous_production.input_quantity)
        )

        previous_waste_rate = (
            float(previous_production.waste_quantity or 0)
            / float(previous_production.input_quantity)
        )

        now = datetime.now()

        try:

            ml_prediction = predict_factory_production(
                material=material.name,
                input_quantity=float(
                    production.input_quantity
                ),
                production_hour=now.hour,
                production_weekday=now.weekday(),
                previous_yield_rate=previous_yield_rate,
                previous_waste_rate=previous_waste_rate,
            )

        except Exception as e:

            ml_prediction = {
                "error": (
                    f"ML prediction unavailable: {str(e)}"
                )
            }

    # =====================================================
    # 7. CALCULATE RAW MATERIAL COST
    # =====================================================

    input_cost = (
        float(production.input_quantity)
        * float(inventory.average_rate or 0)
    )

    # =====================================================
    # 8. PRODUCTION RATE
    # =====================================================

    production_rate = (
        input_cost
        / float(production.output_quantity)
    )

    # =====================================================
    # 9. CREATE PRODUCTION
    # =====================================================

    new_production = Production(

        input_material_id=(
            production.input_material_id
        ),

        output_product_id=(
            production.output_product_id
        ),

        input_quantity=(
            production.input_quantity
        ),

        output_quantity=(
            production.output_quantity
        ),

        waste_quantity=(
            production.waste_quantity
        ),

        ml_predicted_yield_rate=(
            ml_prediction.get(
                "predicted_yield_rate"
            )
            if ml_prediction
            and "predicted_yield_rate"
            in ml_prediction
            else None
        ),

        ml_predicted_output_quantity=(
            ml_prediction.get(
                "predicted_output_quantity"
            )
            if ml_prediction
            and "predicted_output_quantity"
            in ml_prediction
            else None
        ),

        ml_predicted_waste_quantity=(
            ml_prediction.get(
                "predicted_waste_quantity"
            )
            if ml_prediction
            and "predicted_waste_quantity"
            in ml_prediction
            else None
        ),

        status=production.status,

        notes=production.notes
    )

    db.add(new_production)

    # =====================================================
    # 10. UPDATE STOCK ONLY WHEN COMPLETED
    # =====================================================

    if production.status == "Completed":

        # Reduce raw material
        inventory.quantity -= (
            production.input_quantity
        )

        # Existing finished product stock
        old_stock = float(
            product.stock_quantity or 0
        )

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

        # New product stock
        new_stock = (
            old_stock
            + production.output_quantity
        )

        # Weighted average product cost
        if new_stock > 0:

            product.average_rate = (
                old_value + new_value
            ) / new_stock

        product.stock_quantity = new_stock

    # =====================================================
    # 11. SAVE
    # =====================================================

    db.commit()

    db.refresh(new_production)
    db.refresh(inventory)
    db.refresh(product)

    # =====================================================
    # 12. RESPONSE
    # =====================================================

    return {

        "production": new_production,

        "ml_prediction": ml_prediction,

        "production_cost": round(
            input_cost,
            2
        ),

        "production_rate": round(
            production_rate,
            2
        ),

        "product_stock": product.stock_quantity,

        "product_average_rate": round(
            float(product.average_rate or 0),
            2
        )
    }


# =========================================================
# UPDATE PRODUCTION
# =========================================================

@router.put("/{production_id}")
def update_production(
    production_id: int,
    production_update: ProductionUpdate,
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. GET EXISTING PRODUCTION
    # =====================================================

    existing_production = (
        db.query(Production)
        .filter(
            Production.id == production_id
        )
        .first()
    )

    if not existing_production:
        raise HTTPException(
            status_code=404,
            detail="Production record not found"
        )

    # =====================================================
    # 2. GET INVENTORY
    # =====================================================

    inventory = (
        db.query(Inventory)
        .filter(
            Inventory.material_id
            == existing_production.input_material_id
        )
        .first()
    )

    if not inventory:
        raise HTTPException(
            status_code=404,
            detail="Input material inventory not found"
        )

    # =====================================================
    # 3. GET PRODUCT
    # =====================================================

    product = (
        db.query(Product)
        .filter(
            Product.id
            == existing_production.output_product_id
        )
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Finished product not found"
        )

    # =====================================================
    # 4. GET MATERIAL
    # =====================================================

    material = (
        db.query(Material)
        .filter(
            Material.id
            == existing_production.input_material_id
        )
        .first()
    )

    if not material:
        raise HTTPException(
            status_code=404,
            detail="Input material not found"
        )

    # =====================================================
    # 5. OLD VALUES
    # =====================================================

    old_input_quantity = (
        existing_production.input_quantity
    )

    old_output_quantity = (
        existing_production.output_quantity
    )

    old_status = (
        existing_production.status
    )

    # =====================================================
    # 6. NEW VALUES
    # =====================================================

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

    # =====================================================
    # 7. VALIDATION
    # =====================================================

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

    # =====================================================
    # 8. ML PREDICTION FOR UPDATED PRODUCTION
    # =====================================================

    ml_prediction = None

    previous_production = (
        db.query(Production)
        .filter(
            Production.input_material_id
            == existing_production.input_material_id,

            Production.status == "Completed",

            Production.input_quantity > 0,

            Production.id
            != existing_production.id
        )
        .order_by(
            Production.created_at.desc()
        )
        .first()
    )

    if previous_production:

        previous_yield_rate = (
            float(previous_production.output_quantity)
            / float(previous_production.input_quantity)
        )

        previous_waste_rate = (
            float(previous_production.waste_quantity or 0)
            / float(previous_production.input_quantity)
        )

    else:

        previous_yield_rate = 0.90
        previous_waste_rate = 0.10

    now = datetime.now()

    try:

        ml_prediction = predict_factory_production(

            material=material.name,

            input_quantity=float(
                new_input_quantity
            ),

            production_hour=now.hour,

            production_weekday=now.weekday(),

            previous_yield_rate=(
                previous_yield_rate
            ),

            previous_waste_rate=(
                previous_waste_rate
            )
        )

    except Exception as e:

        ml_prediction = {
            "error": (
                f"ML prediction unavailable: {str(e)}"
            )
        }

    # =====================================================
    # 9. REVERSE PREVIOUS COMPLETED TRANSACTION
    # =====================================================

    if old_status == "Completed":

        inventory.quantity += (
            old_input_quantity
        )

        product.stock_quantity = (
            float(product.stock_quantity or 0)
            - old_output_quantity
        )

        if product.stock_quantity < 0:
            product.stock_quantity = 0

        recalculate_product_average_rate(
            db,
            existing_production.output_product_id
        )
    # =====================================================
    # 10. APPLY NEW COMPLETED TRANSACTION
    # =====================================================

    input_cost = 0
    production_rate = 0

    if new_status == "Completed":

        if inventory.quantity < new_input_quantity:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Insufficient stock. "
                    f"Available: {inventory.quantity}"
                )
            )

        # -------------------------------------------------
        # INPUT COST
        # -------------------------------------------------

        input_cost = (
            float(new_input_quantity)
            * float(inventory.average_rate or 0)
        )

        # -------------------------------------------------
        # PRODUCTION RATE
        # -------------------------------------------------

        production_rate = (
            input_cost
            / float(new_output_quantity)
        )

        # -------------------------------------------------
        # REDUCE RAW MATERIAL
        # -------------------------------------------------

        inventory.quantity -= (
            new_input_quantity
        )

        # -------------------------------------------------
        # EXISTING PRODUCT STOCK
        # -------------------------------------------------

        old_product_stock = float(
            product.stock_quantity or 0
        )

        # -------------------------------------------------
        # EXISTING PRODUCT VALUE
        # -------------------------------------------------

        old_product_value = (
            old_product_stock
            * float(product.average_rate or 0)
        )

        # -------------------------------------------------
        # NEW PRODUCT VALUE
        # -------------------------------------------------

        new_product_value = (
            float(new_output_quantity)
            * production_rate
        )

        # -------------------------------------------------
        # NEW PRODUCT STOCK
        # -------------------------------------------------

        new_product_stock = (
            old_product_stock
            + new_output_quantity
        )

        # -------------------------------------------------
        # WEIGHTED AVERAGE RATE
        # -------------------------------------------------

        if new_product_stock > 0:

            product.average_rate = (
                old_product_value
                + new_product_value
            ) / new_product_stock

        product.stock_quantity = (
            new_product_stock
        )

    # =====================================================
    # 11. UPDATE PRODUCTION RECORD
    # =====================================================

    existing_production.input_quantity = (
        new_input_quantity
    )

    existing_production.output_quantity = (
        new_output_quantity
    )

    existing_production.waste_quantity = (
        new_waste_quantity
    )

    existing_production.status = (
        new_status
    )

    # =====================================================
    # 12. UPDATE NOTES
    # =====================================================

    if production_update.notes is not None:

        existing_production.notes = (
            production_update.notes
        )

    # =====================================================
    # 13. SAVE UPDATED ML PREDICTION
    # =====================================================

    existing_production.ml_predicted_yield_rate = (
        ml_prediction.get(
            "predicted_yield_rate"
        )
        if ml_prediction
        and "predicted_yield_rate"
        in ml_prediction
        else None
    )

    existing_production.ml_predicted_output_quantity = (
        ml_prediction.get(
            "predicted_output_quantity"
        )
        if ml_prediction
        and "predicted_output_quantity"
        in ml_prediction
        else None
    )

    existing_production.ml_predicted_waste_quantity = (
        ml_prediction.get(
            "predicted_waste_quantity"
        )
        if ml_prediction
        and "predicted_waste_quantity"
        in ml_prediction
        else None
    )

    # =====================================================
    # 14. COMMIT
    # =====================================================

    db.commit()

    db.refresh(existing_production)
    db.refresh(inventory)
    db.refresh(product)

    # =====================================================
    # 15. RESPONSE
    # =====================================================

    return {

        "production": existing_production,

        "ml_prediction": ml_prediction,

        "production_cost": round(
            input_cost,
            2
        ),

        "production_rate": round(
            production_rate,
            2
        ),

        "product_stock": product.stock_quantity,

        "product_average_rate": round(
            float(product.average_rate or 0),
            2
        )
    }


# =========================================================
# DELETE PRODUCTION
# =========================================================

@router.delete("/{production_id}")
def delete_production(
    production_id: int,
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. GET PRODUCTION
    # =====================================================

    production = (
        db.query(Production)
        .filter(
            Production.id == production_id
        )
        .first()
    )

    if not production:
        raise HTTPException(
            status_code=404,
            detail="Production record not found"
        )

    # =====================================================
    # 2. GET INVENTORY
    # =====================================================

    inventory = (
        db.query(Inventory)
        .filter(
            Inventory.material_id
            == production.input_material_id
        )
        .first()
    )

    # =====================================================
    # 3. GET PRODUCT
    # =====================================================

    product = (
        db.query(Product)
        .filter(
            Product.id
            == production.output_product_id
        )
        .first()
    )

    # =====================================================
    # 4. CHECK STATUS
    # =====================================================

    was_completed = (
        production.status == "Completed"
    )

    # =====================================================
    # 5. REVERSE COMPLETED PRODUCTION
    # =====================================================

    if was_completed:

        # Restore raw material
        if inventory:

            inventory.quantity += (
                production.input_quantity
            )

        # Remove finished product
        if product:

            if (
                float(product.stock_quantity or 0)
                < production.output_quantity
            ):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Cannot delete production because "
                        "finished product stock is insufficient "
                        "to reverse this production."
                    )
                )

            product.stock_quantity -= (
                production.output_quantity
            )

            recalculate_product_average_rate(
                db,
                production.output_product_id
            )

    # =====================================================
    # 6. SAVE IDs BEFORE DELETE
    # =====================================================

    production_id_value = (
        production.id
    )

    input_material_id = (
        production.input_material_id
    )

    output_product_id = (
        production.output_product_id
    )

    # =====================================================
    # 7. DELETE
    # =====================================================

    db.delete(production)

    db.commit()

    # =====================================================
    # 8. RESPONSE
    # =====================================================

    return {

        "message": (
            "Production deleted successfully"
        ),

        "production_id": (
            production_id_value
        ),

        "input_material_id": (
            input_material_id
        ),

        "output_product_id": (
            output_product_id
        ),

        "stock_reversed": (
            was_completed
        )
    }