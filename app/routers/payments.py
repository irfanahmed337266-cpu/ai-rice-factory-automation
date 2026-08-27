


from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.payment import Payment
from app.models.sale import Sale
from app.models.purchase import Purchase


router = APIRouter(
    prefix="/payments",
    tags=["Payments"]
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
# SCHEMA
# =========================================================

class PaymentCreate(BaseModel):
    purchase_id: int | None = None
    sale_id: int | None = None

    party_type: str

    amount: float

    payment_method: str = "Cash"

    payment_status: str = "Pending"

    reference: str | None = None

    notes: str | None = None


# =========================================================
# GET ALL PAYMENTS
# =========================================================

@router.get("/")
def get_payments(
    db: Session = Depends(get_db)
):
    return db.query(Payment).all()


# =========================================================
# CREATE PAYMENT
# =========================================================

@router.post("/")
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db)
):

    try:

        # =================================================
        # 1. VALIDATE AMOUNT
        # =================================================

        if payment.amount <= 0:

            raise HTTPException(
                status_code=400,
                detail="Payment amount must be greater than 0"
            )

        # =================================================
        # 2. MUST HAVE PURCHASE OR SALE
        # =================================================

        if (
            payment.purchase_id is None
            and payment.sale_id is None
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Either purchase_id or sale_id "
                    "is required"
                )
            )

        # =================================================
        # 3. CANNOT HAVE BOTH
        # =================================================

        if (
            payment.purchase_id is not None
            and payment.sale_id is not None
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Payment cannot belong to both "
                    "purchase and sale"
                )
            )

        # =================================================
        # 4. PAYMENT STATUS
        # =================================================

        payment_status = (
            payment.payment_status.strip().lower()
        )

        party_type = (
            payment.party_type.strip().lower()
        )

        amount = Decimal(
            str(payment.amount)
        )

        # =================================================
        # SALE PAYMENT / CUSTOMER
        # =================================================

        sale = None
        purchase = None

        already_paid = Decimal("0")

        if payment.sale_id is not None:

            sale = (
                db.query(Sale)
                .filter(
                    Sale.id == payment.sale_id
                )
                .first()
            )

            if not sale:

                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"Sale {payment.sale_id} "
                        "not found"
                    )
                )

            # Customer validation

            if party_type != "customer":

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Sale payment must have "
                        "party_type='Customer'"
                    )
                )

            # -------------------------------------------------
            # GET EXISTING PAID AMOUNT
            # -------------------------------------------------

            existing_paid = (
                db.query(Payment)
                .filter(
                    Payment.sale_id == sale.id,
                    Payment.payment_status.ilike("Paid")
                )
                .all()
            )

            already_paid = sum(
                (
                    Decimal(str(p.amount or 0))
                    for p in existing_paid
                ),
                Decimal("0")
            )

            # -------------------------------------------------
            # ONLY PAID PAYMENT COUNTS
            # -------------------------------------------------

            new_paid_amount = Decimal("0")

            if payment_status == "paid":

                new_paid_amount = amount

            total_paid = (
                already_paid
                + new_paid_amount
            )

            sale_total = Decimal(
                str(sale.total_amount or 0)
            )

            # -------------------------------------------------
            # PREVENT OVERPAYMENT
            # -------------------------------------------------

            if total_paid > sale_total:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Payment exceeds Sale {sale.id}. "
                        f"Sale total is {sale_total}, "
                        f"already paid is {already_paid}, "
                        f"new payment is "
                        f"{new_paid_amount}."
                    )
                )

        # =================================================
        # PURCHASE PAYMENT / SUPPLIER
        # =================================================

        if payment.purchase_id is not None:

            purchase = (
                db.query(Purchase)
                .filter(
                    Purchase.id == payment.purchase_id
                )
                .first()
            )

            if not purchase:

                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"Purchase {payment.purchase_id} "
                        "not found"
                    )
                )

            # Supplier validation

            if party_type != "supplier":

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Purchase payment must have "
                        "party_type='Supplier'"
                    )
                )

            # -------------------------------------------------
            # GET EXISTING PAID AMOUNT
            # -------------------------------------------------

            existing_paid = (
                db.query(Payment)
                .filter(
                    Payment.purchase_id == purchase.id,
                    Payment.payment_status.ilike("Paid")
                )
                .all()
            )

            already_paid = sum(
                (
                    Decimal(str(p.amount or 0))
                    for p in existing_paid
                ),
                Decimal("0")
            )

            # -------------------------------------------------
            # ONLY PAID PAYMENT COUNTS
            # -------------------------------------------------

            new_paid_amount = Decimal("0")

            if payment_status == "paid":

                new_paid_amount = amount

            total_paid = (
                already_paid
                + new_paid_amount
            )

            purchase_total = Decimal(
                str(purchase.total_amount or 0)
            )

            # -------------------------------------------------
            # PREVENT OVERPAYMENT
            # -------------------------------------------------

            if total_paid > purchase_total:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Payment exceeds Purchase "
                        f"{purchase.id}. "
                        f"Purchase total is "
                        f"{purchase_total}, "
                        f"already paid is "
                        f"{already_paid}, "
                        f"new payment is "
                        f"{new_paid_amount}."
                    )
                )

        # =================================================
        # CREATE PAYMENT
        # =================================================

        new_payment = Payment(

            purchase_id=payment.purchase_id,

            sale_id=payment.sale_id,

            party_type=payment.party_type,

            amount=amount,

            payment_method=payment.payment_method,

            payment_status=payment.payment_status,

            reference=payment.reference,

            notes=payment.notes
        )

        db.add(new_payment)

        # =================================================
        # UPDATE SALE STATUS
        # =================================================

        if sale is not None:

            total_paid = already_paid

            if payment_status == "paid":

                total_paid += amount

            sale_total = Decimal(
                str(sale.total_amount or 0)
            )

            if (
                sale_total > 0
                and total_paid >= sale_total
            ):

                sale.payment_status = "Paid"
                sale.status = "Completed"

            elif total_paid > 0:

                sale.payment_status = "Partial"
                sale.status = "Pending"

            else:

                sale.payment_status = "Pending"
                sale.status = "Pending"

        # =================================================
        # UPDATE PURCHASE STATUS
        # =================================================

        if purchase is not None:

            total_paid = already_paid

            if payment_status == "paid":

                total_paid += amount

            purchase_total = Decimal(
                str(purchase.total_amount or 0)
            )

            if (
                purchase_total > 0
                and total_paid >= purchase_total
            ):

                purchase.payment_status = "Paid"
                purchase.status = "Completed"

            elif total_paid > 0:

                purchase.payment_status = "Partial"
                purchase.status = "Pending"

            else:

                purchase.payment_status = "Pending"
                purchase.status = "Pending"

        # =================================================
        # SAVE
        # =================================================

        db.commit()

        db.refresh(new_payment)

        return new_payment

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Payment creation failed: {str(e)}"
        )


# =========================================================
# UPDATE PAYMENT
# =========================================================

class PaymentUpdate(BaseModel):

    amount: float | None = None

    payment_method: str | None = None

    payment_status: str | None = None

    reference: str | None = None

    notes: str | None = None


def _get_paid_total(
    db: Session,
    *,
    sale_id: int | None = None,
    purchase_id: int | None = None,
    exclude_payment_id: int | None = None
) -> Decimal:

    query = db.query(Payment).filter(
        Payment.payment_status.ilike("Paid")
    )

    if sale_id is not None:
        query = query.filter(
            Payment.sale_id == sale_id
        )

    if purchase_id is not None:
        query = query.filter(
            Payment.purchase_id == purchase_id
        )

    if exclude_payment_id is not None:
        query = query.filter(
            Payment.id != exclude_payment_id
        )

    payments = query.all()

    return sum(
        (
            Decimal(str(p.amount or 0))
            for p in payments
        ),
        Decimal("0")
    )


def _update_sale_payment_status(
    db: Session,
    sale: Sale
):

    total_paid = _get_paid_total(
        db,
        sale_id=sale.id
    )

    sale_total = Decimal(
        str(sale.total_amount or 0)
    )

    if sale_total > 0 and total_paid >= sale_total:

        sale.payment_status = "Paid"
        sale.status = "Completed"

    elif total_paid > 0:

        sale.payment_status = "Partial"
        sale.status = "Pending"

    else:

        sale.payment_status = "Pending"
        sale.status = "Pending"


def _update_purchase_payment_status(
    db: Session,
    purchase: Purchase
):

    total_paid = _get_paid_total(
        db,
        purchase_id=purchase.id
    )

    purchase_total = Decimal(
        str(purchase.total_amount or 0)
    )

    if purchase_total > 0 and total_paid >= purchase_total:

        purchase.payment_status = "Paid"
        purchase.status = "Completed"

    elif total_paid > 0:

        purchase.payment_status = "Partial"
        purchase.status = "Pending"

    else:

        purchase.payment_status = "Pending"
        purchase.status = "Pending"


@router.put("/{payment_id}")
def update_payment(
    payment_id: int,
    payment_update: PaymentUpdate,
    db: Session = Depends(get_db)
):

    try:

        # -------------------------------------------------
        # 1. FIND PAYMENT
        # -------------------------------------------------

        payment = (
            db.query(Payment)
            .filter(Payment.id == payment_id)
            .first()
        )

        if not payment:

            raise HTTPException(
                status_code=404,
                detail="Payment not found"
            )

        # -------------------------------------------------
        # 2. NEW VALUES
        # -------------------------------------------------

        new_amount = (
            Decimal(str(payment_update.amount))
            if payment_update.amount is not None
            else Decimal(str(payment.amount or 0))
        )

        if new_amount <= 0:

            raise HTTPException(
                status_code=400,
                detail="Payment amount must be greater than 0"
            )

        new_status = (
            payment_update.payment_status.strip()
            if payment_update.payment_status is not None
            else payment.payment_status
        )

        new_status_lower = new_status.lower()

        if new_status_lower not in {
            "pending",
            "paid",
            "partial"
        }:

            raise HTTPException(
                status_code=400,
                detail=(
                    "payment_status must be "
                    "'Pending', 'Paid' or 'Partial'"
                )
            )

        # -------------------------------------------------
        # 3. GET EXISTING PAID TOTAL EXCLUDING THIS PAYMENT
        # -------------------------------------------------

        already_paid = Decimal("0")

        if payment.sale_id is not None:

            sale = (
                db.query(Sale)
                .filter(Sale.id == payment.sale_id)
                .first()
            )

            if not sale:

                raise HTTPException(
                    status_code=404,
                    detail="Related sale not found"
                )

            already_paid = _get_paid_total(
                db,
                sale_id=sale.id,
                exclude_payment_id=payment.id
            )

            new_paid_amount = (
                new_amount
                if new_status_lower == "paid"
                else Decimal("0")
            )

            total_paid_after = (
                already_paid + new_paid_amount
            )

            sale_total = Decimal(
                str(sale.total_amount or 0)
            )

            if total_paid_after > sale_total:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Payment exceeds Sale {sale.id}. "
                        f"Sale total is {sale_total}, "
                        f"other paid payments are "
                        f"{already_paid}, "
                        f"new payment is "
                        f"{new_paid_amount}."
                    )
                )

        elif payment.purchase_id is not None:

            purchase = (
                db.query(Purchase)
                .filter(
                    Purchase.id == payment.purchase_id
                )
                .first()
            )

            if not purchase:

                raise HTTPException(
                    status_code=404,
                    detail="Related purchase not found"
                )

            already_paid = _get_paid_total(
                db,
                purchase_id=purchase.id,
                exclude_payment_id=payment.id
            )

            new_paid_amount = (
                new_amount
                if new_status_lower == "paid"
                else Decimal("0")
            )

            total_paid_after = (
                already_paid + new_paid_amount
            )

            purchase_total = Decimal(
                str(purchase.total_amount or 0)
            )

            if total_paid_after > purchase_total:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Payment exceeds Purchase "
                        f"{purchase.id}. "
                        f"Purchase total is "
                        f"{purchase_total}, "
                        f"other paid payments are "
                        f"{already_paid}, "
                        f"new payment is "
                        f"{new_paid_amount}."
                    )
                )

        # -------------------------------------------------
        # 4. UPDATE PAYMENT
        # -------------------------------------------------

        payment.amount = new_amount
        payment.payment_status = new_status

        if payment_update.payment_method is not None:

            payment.payment_method = (
                payment_update.payment_method
            )

        if payment_update.reference is not None:

            payment.reference = (
                payment_update.reference
            )

        if payment_update.notes is not None:

            payment.notes = payment_update.notes

        # -------------------------------------------------
        # 5. UPDATE RELATED SALE/PURCHASE STATUS
        # -------------------------------------------------

        if payment.sale_id is not None:

            _update_sale_payment_status(
                db,
                sale
            )

        if payment.purchase_id is not None:

            _update_purchase_payment_status(
                db,
                purchase
            )

        # -------------------------------------------------
        # 6. SAVE
        # -------------------------------------------------

        db.commit()
        db.refresh(payment)

        return payment

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Payment update failed: {str(e)}"
        )


# =========================================================
# DELETE PAYMENT
# =========================================================

@router.delete("/{payment_id}")
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):

    try:

        # -------------------------------------------------
        # 1. FIND PAYMENT
        # -------------------------------------------------

        payment = (
            db.query(Payment)
            .filter(Payment.id == payment_id)
            .first()
        )

        if not payment:

            raise HTTPException(
                status_code=404,
                detail="Payment not found"
            )

        sale = None
        purchase = None

        if payment.sale_id is not None:

            sale = (
                db.query(Sale)
                .filter(
                    Sale.id == payment.sale_id
                )
                .first()
            )

        if payment.purchase_id is not None:

            purchase = (
                db.query(Purchase)
                .filter(
                    Purchase.id == payment.purchase_id
                )
                .first()
            )

        deleted_amount = Decimal(
            str(payment.amount or 0)
        )

        # -------------------------------------------------
        # 2. DELETE PAYMENT
        # -------------------------------------------------

        db.delete(payment)

        db.flush()

        # -------------------------------------------------
        # 3. RECALCULATE RELATED STATUS
        # -------------------------------------------------

        if sale is not None:

            _update_sale_payment_status(
                db,
                sale
            )

        if purchase is not None:

            _update_purchase_payment_status(
                db,
                purchase
            )

        # -------------------------------------------------
        # 4. SAVE
        # -------------------------------------------------

        db.commit()

        return {
            "message": "Payment deleted successfully",
            "payment_id": payment_id,
            "deleted_amount": float(deleted_amount),
            "sale_id": sale.id if sale else None,
            "purchase_id": (
                purchase.id if purchase else None
            )
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Payment deletion failed: {str(e)}"
        )

# =========================================================
# CUSTOMER RECEIVABLE PAYMENTS
# =========================================================

@router.get("/receivables")
def get_receivable_payments(
    db: Session = Depends(get_db)
):

    payments = (
        db.query(Payment)
        .filter(
            Payment.party_type.ilike("Customer")
        )
        .all()
    )

    result = []

    for payment in payments:

        result.append({

            "sale_id": payment.sale_id,

            "received_amount": float(
                payment.amount or 0
            ),

            "payment_status":
                payment.payment_status,

            "payment_method":
                payment.payment_method,

            "reference":
                payment.reference,

            "notes":
                payment.notes
        })

    return result


# =========================================================
# SUPPLIER PAYABLE PAYMENTS
# =========================================================

@router.get("/payables")
def get_payable_payments(
    db: Session = Depends(get_db)
):

    payments = (
        db.query(Payment)
        .filter(
            Payment.party_type.ilike("Supplier")
        )
        .all()
    )

    result = []

    for payment in payments:

        result.append({

            "purchase_id": payment.purchase_id,

            "paid_amount": float(
                payment.amount or 0
            ),

            "payment_status":
                payment.payment_status,

            "payment_method":
                payment.payment_method,

            "reference":
                payment.reference,

            "notes":
                payment.notes
        })

    return result