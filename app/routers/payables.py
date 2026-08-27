from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal
from app.models.purchase import Purchase
from app.models.payment import Payment


router = APIRouter(
    prefix="/payables",
    tags=["Payables"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================
# GET SUPPLIER PAYABLES
# =========================================================

@router.get("/")
def get_payables(
    db: Session = Depends(get_db)
):

    purchases = (
        db.query(Purchase)
        .all()
    )

    result = []

    for purchase in purchases:

        # -------------------------------------------------
        # GET TOTAL PAID
        # -------------------------------------------------

        paid_amount = db.query(
            func.coalesce(
                func.sum(Payment.amount),
                0
            )
        ).filter(
            Payment.purchase_id == purchase.id,
            Payment.party_type.ilike("Supplier"),
            Payment.payment_status.ilike("Paid")
        ).scalar()

        total_amount = float(
            purchase.total_amount or 0
        )

        paid_amount = float(
            paid_amount or 0
        )

        # -------------------------------------------------
        # ZERO / NULL TOTAL
        # -------------------------------------------------

        if total_amount <= 0:

            payable_amount = 0

            status = "Unknown"

        else:

            payable_amount = (
                total_amount - paid_amount
            )

            # -------------------------------------------------
            # STATUS
            # -------------------------------------------------

            if payable_amount <= 0:

                status = "Paid"

                payable_amount = 0

            elif paid_amount > 0:

                status = "Partial"

            else:

                status = "Pending"

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        result.append({

            "purchase_id":
                purchase.id,

            "supplier_id":
                purchase.supplier_id,

            "total_amount":
                total_amount,

            "paid_amount":
                paid_amount,

            "payable_amount":
                payable_amount,

            "status":
                status
        })

    return result