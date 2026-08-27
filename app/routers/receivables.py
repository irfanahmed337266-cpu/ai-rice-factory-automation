from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal
from app.models.sale import Sale
from app.models.payment import Payment


router = APIRouter(
    prefix="/receivables",
    tags=["Receivables"]
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
# GET RECEIVABLES
# =========================================================

@router.get("/")
def get_receivables(
    db: Session = Depends(get_db)
):

    sales = db.query(Sale).all()

    result = []

    for sale in sales:

        # =================================================
        # ONLY PAID CUSTOMER PAYMENTS
        # =================================================

        paid_amount = db.query(
            func.coalesce(
                func.sum(Payment.amount),
                0
            )
        ).filter(

            Payment.sale_id == sale.id,

            Payment.party_type.ilike("Customer"),

            Payment.payment_status.ilike("Paid")

        ).scalar()

        # =================================================
        # DECIMAL CALCULATIONS
        # =================================================

        sale_total = Decimal(
            str(sale.total_amount or 0)
        )

        paid = Decimal(
            str(paid_amount or 0)
        )

        receivable = sale_total - paid

        # Avoid negative receivable
        if receivable < 0:

            receivable = Decimal("0")

        # =================================================
        # STATUS
        # =================================================

        if receivable <= 0:

            status = "Paid"

        elif paid > 0:

            status = "Partial"

        else:

            status = "Pending"

        # =================================================
        # RESULT
        # =================================================

        result.append({

            "sale_id": sale.id,

            "buyer_id": sale.buyer_id,

            "total_amount": float(
                sale_total
            ),

            "paid_amount": float(
                paid
            ),

            "receivable_amount": float(
                receivable
            ),

            "status": status
        })

    return result