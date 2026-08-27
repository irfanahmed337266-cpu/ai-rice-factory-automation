from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import SessionLocal
from app.models.buyer import Buyer
from app.core.security import require_admin


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/buyers",
    tags=["Buyers"]
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

class BuyerCreate(BaseModel):
    name: str
    phone: str | None = None
    city: str | None = None
    address: str | None = None


class BuyerUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    city: str | None = None
    address: str | None = None


# =========================================================
# GET ALL BUYERS
# =========================================================

@router.get("/")
def get_buyers(
    db: Session = Depends(get_db)
):
    return db.query(Buyer).all()


# =========================================================
# GET SINGLE BUYER
# =========================================================

@router.get("/{buyer_id}")
def get_buyer(
    buyer_id: int,
    db: Session = Depends(get_db)
):

    buyer = (
        db.query(Buyer)
        .filter(Buyer.id == buyer_id)
        .first()
    )

    if not buyer:
        raise HTTPException(
            status_code=404,
            detail="Buyer not found"
        )

    return buyer


# =========================================================
# CREATE BUYER
# =========================================================

@router.post("/")
def create_buyer(
    buyer: BuyerCreate,
    db: Session = Depends(get_db)
):

    if not buyer.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Buyer name is required"
        )

    new_buyer = Buyer(
        name=buyer.name,
        phone=buyer.phone,
        city=buyer.city,
        address=buyer.address
    )

    db.add(new_buyer)

    try:
        db.commit()
        db.refresh(new_buyer)

    except Exception:
        db.rollback()
        raise

    return new_buyer


# =========================================================
# UPDATE BUYER
# =========================================================

@router.put("/{buyer_id}")
def update_buyer(
    buyer_id: int,
    buyer_update: BuyerUpdate,
    db: Session = Depends(get_db)
):

    buyer = (
        db.query(Buyer)
        .filter(Buyer.id == buyer_id)
        .first()
    )

    if not buyer:
        raise HTTPException(
            status_code=404,
            detail="Buyer not found"
        )

    if buyer_update.name is not None:

        if not buyer_update.name.strip():
            raise HTTPException(
                status_code=400,
                detail="Buyer name cannot be empty"
            )

        buyer.name = buyer_update.name

    if buyer_update.phone is not None:
        buyer.phone = buyer_update.phone

    if buyer_update.city is not None:
        buyer.city = buyer_update.city

    if buyer_update.address is not None:
        buyer.address = buyer_update.address

    try:
        db.commit()
        db.refresh(buyer)

    except Exception:
        db.rollback()
        raise

    return buyer


# =========================================================
# DELETE BUYER
# =========================================================

@router.delete("/{buyer_id}")
def delete_buyer(
    buyer_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):

    buyer = (
        db.query(Buyer)
        .filter(Buyer.id == buyer_id)
        .first()
    )

    if not buyer:
        raise HTTPException(
            status_code=404,
            detail="Buyer not found"
        )

    # -----------------------------------------------------
    # Check whether buyer is linked to sales
    # -----------------------------------------------------

    try:
        db.delete(buyer)
        db.commit()

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=(
                "Buyer cannot be deleted. "
                "Buyer may be linked to existing sales."
            )
        )

    return {
        "message": "Buyer deleted successfully",
        "buyer_id": buyer_id
    }